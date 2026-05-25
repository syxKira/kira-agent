---
name: ad-attribution-validation
description: 发送归因测试数据后，按实时链路场景选择结果表、触发 DS 查询工作流，并根据落表结果与 match_type 判断暂未落表、暂未归因、精准归因或模糊归因；离线数据验证走 Trino，当前支持 device 表的设备新增、设备回流、设备新增归因、设备回流归因校验。仅当用户明确要求查有没有归因、查结果表、校验实时链路、校验离线数据、自动选表、拼 SQL、传参给 DS、判断精准归因或模糊归因时使用。
disable-model-invocation: true
---

# Ad Attribution Validation

## Quick Start

这个 skill 只负责发送后的实时链路查询校验，以及离线数据验证的 Trino 查询校验；不负责造数和发数。

默认规则：

- 只有用户**明确要求**“查有没有归因”“查结果表”“校验实时链路”“校验离线数据”时才触发本 skill。
- 如果用户只是让你造数、发数、改 case、确认发送成功，不要主动去查归因结果表。
- 离线数据验证目前只支持设备表校验点，不预设账号、事件、付费等其他离线验证点。

实时链路执行顺序固定为：

1. 识别场景
2. 自动选表
3. 计算 `dt`
4. 触发 DS 实时查询工作流
5. 读取查询结果
6. 根据查询结果输出结论

## 场景规则

| 场景 | 落表表 | 归因表 | 主体字段 | `match_type` 字段 |
|------|--------|--------|----------|-------------------|
| 新增设备 | `device_activation_rt` | `device_activation_attribution_rt` | `#device_id` | `#activation_match_type` |
| 回流设备 | `device_backflow_rt` | `device_backflow_attribution_rt` | `#device_id` | `#backflow_match_type` |
| 新增用户 | `user_activation_rt` | `user_activation_attribution_rt` | `#user_id` | `#activation_device_activation_match_type` |
| 回流用户 | `user_backflow_rt` | `user_backflow_attribution_rt` | `#user_id` | `#backflow_device_activation_match_type` |
| 启动器设备新增 | `launcher_device_activation_rt` | `launcher_device_activation_attribution_rt` | `#device_id` | `#activation_match_type` |
| 启动器设备回流 | `launcher_device_backflow_rt` | `launcher_device_backflow_attribution_rt` | `#device_id` | `#backflow_match_type` |

实时链路默认库名按 `hgbi_{env}_{app_id}` 组织。  
如果用户直接给了完整库名或完整 SQL，优先沿用用户输入。

## 离线数据验证库名规则

离线数据验证走 Trino 查询。验证时用户需要提供完整库名。

- 如果用户提供了完整库名，直接使用用户提供的库名。
- 如果用户直接提供了完整 SQL，优先使用 SQL 中的库表，不要改写库名。
- 如果用户没有提供库名，默认使用 `hive.hgbi_staging_17iyh6hngzwwbd2me1ag6rqm`。
- 只要走了默认库名逻辑，回复时必须提示用户：`未提供库名，已默认使用 hive.hgbi_staging_17iyh6hngzwwbd2me1ag6rqm`。

## 离线设备校验点

离线设备校验走 Trino 查询 `{database}.device` 表，并根据 `#device_id` 查询对应设备信息。  
这里的 `{database}` 必须遵守上面的离线数据验证库名规则。

离线设备日期过滤字段固定为 `dt`，字段类型是 `date`：

- 用户说“日期”“date 字段”“分区日期”时，都理解为 `dt`
- SQL 条件必须写成 `dt = DATE 'YYYY-MM-DD'`
- 不要写成 `"date"` 或 `date`

基础查询 SQL：

```sql
SELECT
  "#device_id",
  "#activation_ts",
  "#backflow_ts",
  "#activation_match_type",
  "#ad_conversion_ts",
  dt
FROM {database}.device
WHERE "#device_id" = '{device_id}'
  AND dt = DATE '{dt}'
LIMIT 20
```

校验场景：

| 场景 | 校验字段 | 判断规则 |
|------|----------|----------|
| 设备新增 | `#activation_ts` | 判断 `#activation_ts` 是否和发送数据的 `ts` 一致 |
| 设备回流 | `#backflow_ts` | 判断 `#backflow_ts` 是否和回流数据的 `ts` 一致 |
| 设备新增归因 | `#activation_match_type` | 判断 `#activation_match_type` 是否符合预期归因结果 |
| 设备回流归因 | `#backflow_ts`、`#ad_conversion_ts` | 判断 `#backflow_ts` 和 `#ad_conversion_ts` 是否相等 |

离线设备校验输出至少包含：

- 查询库表
- 查询主体：`#device_id`
- 用户提供的发送数据 `ts` 或回流数据 `ts`
- 查询到的关键字段值
- 每个校验场景的判断结果

## Trino 离线设备校验脚本

离线设备校验使用独立脚本：

`scripts/query_offline_device_validation.py`

不要用实时链路的 `scripts/start_validation_workflow.py` 查询离线数据。

该脚本负责：

- 读取 `TRINO_CN_PASSWORD`、`TRINO_OVERSEAS_PASSWORD`、`TRINO_USER`、`TRINO_HOST` 或项目根目录 `.env.local`
- 连接 Trino 查询 `{database}.device`
- 按 `#device_id` 和 `dt = DATE 'YYYY-MM-DD'` 过滤
- 输出查询 SQL、关键字段、行数和场景判断结果
- 如果命令未传 `--database`，自动使用默认库名并输出默认库名提示

常用调用方式：

```bash
python ".cursor/skills/ad-attribution-validation/scripts/query_offline_device_validation.py" \
  --scene-type device_activation_attribution \
  --device-id ad_gaid_s_48 \
  --dt 2023-12-29
```

支持场景：

- `device_activation`：设备新增，必须传 `--event-timestamp-ms`
- `device_backflow`：设备回流，必须传 `--event-timestamp-ms`
- `device_activation_attribution`：设备新增归因
- `device_backflow_attribution`：设备回流归因

如果用户提供了完整库名，追加：

```bash
--database hive.hgbi_staging_17iyh6hngzwwbd2me1ag6rqm
```

如果查询海外数据，追加：

```bash
--region overseas
```

## 实时链路口径

查询分两段：

1. 落表表：只判断主体字段能否查到数据，且 `dt` 是否正确
2. 归因表：判断主体字段能否查到数据，并读取 `match_type`

这是**实时链路验证**，不是离线最终报表校验。  
因此结论按“当前查询时点”解释，不要过度表述成最终结论。

结论口径固定为：

- 落表表无数据：`暂未落表`
- 落表表有数据，归因表无数据：`已落表，暂未归因`
- 归因表有数据且 `match_type = id_matching`：`已落表，精准归因`
- 归因表有数据且 `match_type = probabilistic`：`已落表，模糊归因`
- 归因表有数据但 `match_type` 不是上述两种：`已落表，归因结果异常`

## `dt` 规则

- `dt` 不是执行命令当天
- `dt` 必须按被校验主体事件的业务时间戳换算自然日
- 若用户明确给了查表用的 `#ts`，直接按该值换算
- 否则默认取当前主体事件的主时间字段换算

示例：

- `1774989000000 -> 2026-04-01`
- 查询条件应写成 `dt = '2026-04-01'`

## DS 触发脚本

默认使用：

`scripts/start_validation_workflow.py`

该脚本负责：

- 读取 `DS_TOKEN` 或项目根目录 `.env.local`
- 触发查询 workflow：`173307975548163`
- 传入实时链路验证所需的启动参数
- 可选等待任务结束

常用调用方式：

```bash
python ".cursor/skills/ad-attribution-validation/scripts/start_validation_workflow.py" \
  --scene-type device_activation \
  --query-target attribution \
  --event-timestamp-ms 1778688000000 \
  --biz-env staging \
  --app-id 17IYH6HNGZwwbD2mE1ag6Rqm \
  --device-id plain_sdid_20260514_device_01 \
  --wait
```

如果用户明确要求查“落表有没有数据”，则把 `--query-target` 改成 `landing`。  
如果用户明确要求查“新增用户 / 回流用户”，改传 `--user-id`。  
除非用户明确要求，否则不要主动触发查询 workflow。

## SQL 模板

落表 SQL：

```sql
SELECT *
FROM `{database}`.`{landing_table}`
WHERE `{subject_field}` = '{subject_value}'
  AND `dt` = '{dt}'
LIMIT 20
```

归因 SQL：

```sql
SELECT *
FROM `{database}`.`{attribution_table}`
WHERE `{subject_field}` = '{subject_value}'
  AND `dt` = '{dt}'
LIMIT 20
```

如果用户直接给了 SQL：

1. 先反推场景、库表、主体字段、主体值
2. 识别对应 `match_type` 字段
3. 再补成统一的规则输出

## DS 参数模板

如果接一个“执行 SQL 的 DS 工作流”，默认由 skill 负责选表与拼 SQL，DS 只负责执行。

推荐参数：

- `scene_type`
- `database`
- `landing_table`
- `attribution_table`
- `subject_field`
- `subject_value`
- `dt`
- `landing_sql`
- `attribution_sql`
- `match_type_field`
- `result_limit`

推荐 `startParams`：

```json
[
  {"prop":"scene_type","direct":"IN","type":"VARCHAR","value":"device_activation"},
  {"prop":"database","direct":"IN","type":"VARCHAR","value":"hgbi_staging_17IYH6HNGZwwbD2mE1ag6Rqm"},
  {"prop":"landing_table","direct":"IN","type":"VARCHAR","value":"device_activation_rt"},
  {"prop":"attribution_table","direct":"IN","type":"VARCHAR","value":"device_activation_attribution_rt"},
  {"prop":"subject_field","direct":"IN","type":"VARCHAR","value":"#device_id"},
  {"prop":"subject_value","direct":"IN","type":"VARCHAR","value":"plain_sdid_20260514_device_01"},
  {"prop":"dt","direct":"IN","type":"VARCHAR","value":"2026-04-01"},
  {"prop":"landing_sql","direct":"IN","type":"VARCHAR","value":"SELECT * FROM `hgbi_staging_17IYH6HNGZwwbD2mE1ag6Rqm`.`device_activation_rt` WHERE `#device_id` = 'plain_sdid_20260514_device_01' AND `dt` = '2026-04-01' LIMIT 20"},
  {"prop":"attribution_sql","direct":"IN","type":"VARCHAR","value":"SELECT * FROM `hgbi_staging_17IYH6HNGZwwbD2mE1ag6Rqm`.`device_activation_attribution_rt` WHERE `#device_id` = 'plain_sdid_20260514_device_01' AND `dt` = '2026-04-01' LIMIT 20"},
  {"prop":"match_type_field","direct":"IN","type":"VARCHAR","value":"#activation_match_type"},
  {"prop":"result_limit","direct":"IN","type":"INT","value":"20"}
]
```

## 输出要求

执行查询校验后，回复至少包含：

- 自动识别到的场景
- 落表表和归因表名
- 本次查询的主体字段、主体值、`dt`
- 落表结果
- 归因结果
- 最终结论

如果是离线数据验证，且用户未提供库名，回复必须包含默认库名提示。

如果是实时链路验证，优先使用下面这些说法：

- `暂未落表`
- `已落表，暂未归因`
- `已落表，精准归因`
- `已落表，模糊归因`
- `已落表，归因结果异常`

建议输出结构：

```markdown
场景：新增设备实时归因校验
查询主体：`#device_id = plain_sdid_20260514_device_01`
查询日期：`2026-04-01`

落表表：`device_activation_rt`
归因表：`device_activation_attribution_rt`

结论：已落表，精准归因
```
