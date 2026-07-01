FROM ops-harbor.hypergryph.net/biz-platform-web/build-22 AS web-build

WORKDIR /app/web

COPY web/package.json web/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY web/ ./
RUN VITE_KIRA_API_BASE=/api pnpm build


FROM ops-harbor.hypergryph.net/paas/python/build:3.10 AS python-build

WORKDIR /build

COPY server/ /build/server

RUN pip install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    --timeout 300 \
    --target /opt/python \
    /build/server

RUN PYTHONPATH=/opt/python python -m uvicorn --version


FROM ops-harbor.hypergryph.net/paas/python/runtime:3.10 AS runtime

ENV PYTHONPATH=/opt/python \
    KIRA_WEB_DIST=/opt/web/dist \
    KIRA_RUNTIME_DB_PATH=/data/kira.db \
    KIRA_CONFIG_PATH=/data/conf/config.yaml \
    KIRA_SKILL_PATHS=/opt/skills \
    HOST=0.0.0.0 \
    PORT=8000 \
    PATH="/opt/python/bin:${PATH}"

WORKDIR /opt

RUN mkdir -p /data/conf

COPY server/ /opt/server
COPY scripts/ /opt/scripts
COPY skills/ /opt/skills
COPY --from=python-build /opt/python /opt/python
COPY --from=web-build /app/web/dist /opt/web/dist

RUN cat > /run.sh <<'EOF' && chmod +x /run.sh
#!/bin/sh
set -eu

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
export PYTHONUNBUFFERED=1
export PYTHONPATH="/opt/python:${PYTHONPATH:-}"
export PATH="/opt/python/bin:${PATH}"

echo "[kira-start] starting"
echo "[kira-start] uid=$(id -u) gid=$(id -g)"
echo "[kira-start] pwd=$(pwd)"
echo "[kira-start] host=$HOST port=$PORT"
echo "[kira-start] python=$(command -v python)"
python --version
echo "[kira-start] checking files"
ls -ld /opt /opt/server /opt/python /opt/web /opt/web/dist /data /data/conf || true
echo "[kira-start] checking imports"
python -c "import uvicorn; print('uvicorn ok', uvicorn.__version__)"
python -c "import kira_server; print('kira_server ok')"
python -c "import sqlite3; print('sqlite ok')"
echo "[kira-start] launching uvicorn"
cd /opt/server
python -u -m uvicorn kira_server.main:app --host "$HOST" --port "$PORT" --log-level debug 2>&1
status="$?"
echo "[kira-start] uvicorn exited with status $status"
echo "[kira-start] keeping container alive after uvicorn exit for debugging"
tail -f /dev/null
EOF

RUN chmod +x /opt/scripts/paas-start && ls -l /run.sh && PYTHONPATH=/opt/python python -c "import uvicorn; print('uvicorn import ok')"

EXPOSE 8000

WORKDIR /opt

CMD ["/bin/sh", "-c", "cd /opt/server && PYTHONPATH=/opt/python exec python -m uvicorn kira_server.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level debug --access-log"]
