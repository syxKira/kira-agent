# 归因结果校验工作流

## 使用边界

只在用户明确要求“查有没有归因”“查结果表”“校验实时链路”“校验离线数据”“拼 SQL”“判断精准/模糊归因”时使用。用户只是造数、发数、确认发送成功时，不主动查询结果表。

## 实时链路顺序

1. 识别场景。
2. 自动选表。
3. 按被校验主体事件时间计算 `dt`。
4. 触发 DS 查询工作流。
5. 读取查询结果。
6. 根据落表与归因结果输出结论。

## 实时场景选表

| 场景 | 落表表 | 归因表 | 主体字段 | `match_type` 字段 |
| --- | --- | --- | --- | --- |
| 新增设备 | `device_activation_rt` | `device_activation_attribution_rt` | `#device_id` | `#activation_match_type` |
| 回流设备 | `device_backflow_rt` | `device_backflow_attribution_rt` | `#device_id` | `#backflow_match_type` |
| 新增用户 | `user_activation_rt` | `user_activation_attribution_rt` | `#user_id` | `#activation_device_activation_match_type` |
| 回流用户 | `user_backflow_rt` | `user_backflow_attribution_rt` | `#user_id` | `#backflow_device_activation_match_type` |
| 启动器设备新增 | `launcher_device_activation_rt` | `launcher_device_activation_attribution_rt` | `#device_id` | `#activation_match_type` |
| 启动器设备回流 | `launcher_device_backflow_rt` | `launcher_device_backflow_attribution_rt` | `#device_id` | `#backflow_match_type` |

实时链路默认库名按 `hgbi_{env}_{app_id}` 组织。用户提供完整库名或完整 SQL 时优先沿用用户输入。

## `dt` 规则

- `dt` 不是执行命令当天。
- `dt` 必须按被校验主体事件的业务时间戳换算自然日。
- 用户明确给了查表用 `#ts` 时，直接按该值换算。
- 否则默认取当前主体事件主时间字段。
- 实时 SQL 的 `dt` 条件写字符串：`dt = 'YYYY-MM-DD'`。

## 实时结论口径

- 落表表无数据：`暂未落表`
- 落表表有数据，归因表无数据：`已落表，暂未归因`
- 归因表有数据且 `match_type = id_matching`：`已落表，精准归因`
- 归因表有数据且 `match_type = probabilistic`：`已落表，模糊归因`
- 归因表有数据但 `match_type` 不是上述两种：`已落表，归因结果异常`

## 实时查询脚本

```bash
python .kira/skills/ad-attribution/scripts/start_validation_workflow.py \
  --scene-type device_activation \
  --query-target attribution \
  --event-timestamp-ms 1778688000000 \
  --biz-env staging \
  --app-id 17IYH6HNGZwwbD2mE1ag6Rqm \
  --device-id plain_sdid_20260514_device_01 \
  --wait
```

如果用户明确查“落表有没有数据”，`--query-target landing`。用户查新增用户/回流用户时传 `--user-id`，不要传错主体字段。

## 实时 SQL 模板

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

## 离线数据验证

离线验证走 Trino，不使用实时链路 DS 查询脚本。当前只支持设备表校验点，不预设账号、事件、付费等其他离线验证点。

库名规则：

- 用户提供完整库名，直接使用。
- 用户提供完整 SQL，优先使用 SQL 中的库表。
- 用户未提供库名，默认 `hive.hgbi_staging_17iyh6hngzwwbd2me1ag6rqm`，回复必须提示：`未提供库名，已默认使用 hive.hgbi_staging_17iyh6hngzwwbd2me1ag6rqm`。

离线设备表：`{database}.device`。日期字段固定为 `dt`，类型是 `date`，SQL 必须写成：

```sql
dt = DATE 'YYYY-MM-DD'
```

基础 SQL：

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

离线校验场景：

| 场景 | 校验字段 | 判断 |
| --- | --- | --- |
| 设备新增 | `#activation_ts` | 是否等于发送数据 `ts` |
| 设备回流 | `#backflow_ts` | 是否等于回流数据 `ts` |
| 设备新增归因 | `#activation_match_type` | 是否符合预期归因结果 |
| 设备回流归因 | `#backflow_ts`、`#ad_conversion_ts` | 两者是否相等 |

离线脚本：

```bash
python .kira/skills/ad-attribution/scripts/query_offline_device_validation.py \
  --scene-type device_activation_attribution \
  --device-id ad_gaid_s_48 \
  --dt 2023-12-29
```

用户提供库名时追加：

```bash
--database hive.hgbi_staging_17iyh6hngzwwbd2me1ag6rqm
```

海外数据追加：

```bash
--region overseas
```

## 校验输出

实时校验至少输出：自动识别场景、落表表、归因表、主体字段和值、`dt`、落表结果、归因结果、最终结论。

离线校验至少输出：查询库表、`#device_id`、用户提供的发送或回流 `ts`、查询到的关键字段、每个校验点判断结果。使用默认库名时必须输出默认库名提示。
