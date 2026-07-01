# 归因造数与发送工作流

## 场景解析

把用户自然语言或简写翻译成事件序列：

| 用户描述 | 事件 | 要点 |
| --- | --- | --- |
| 广告 a3 | `ad_tracker` | 移动端广告监测日志 |
| 广告落地 / Windows 广告 | `#ad_landing` | PC `tracking_code` 归因广告侧 |
| 新增设备 d1 | `#app_start` | 设备首次出现 |
| 设备回流 d1 | `#app_start` | 同一 `#sdid_s`，距上次出现 `> 2 天` |
| 注册账号 u1 | `#user_login` | 新账号首次出现，必须带 `#user_id` |
| 新账号登陆老设备 | `#user_login` | 账号新增发生在已有设备上 |
| 老账号登陆新设备 | `#app_start` | 新设备事件必须带 `#user_id` |
| 账号 u1 付费 | `#charge` | 通过 `#user_id` + `#sdid_s` 关联 |

先整理为：验证目标、事件顺序、匹配键、期望结果、关键差异字段。

## 匹配字段

| 平台 | 行为日志 | 广告日志 | 逻辑 |
| --- | --- | --- | --- |
| iOS | `#idfa_c` | `idfa` | 原值或 `md5(行为值)` 匹配广告值 |
| iOS | `#fdid` | `caid` | 两侧保持 JSON 数组字符串结构，内层 ID 和 `version` 一致 |
| Android | `#anid_c` | `anid` | 原值或 md5 匹配 |
| Android | `#gaid_c` | `gaid` | 原值或 md5 匹配 |
| Android | `#oaid_c` | `oaid` | 原值或 md5 匹配 |
| Windows | `#tracking_code` | `#tracking_code` | `#ad_landing` 与行为事件完全一致 |

默认造数使用原值，不主动改成 md5。只有用户明确要验证 md5 时才构造 md5 场景。

## 必守约束

- 每个独立场景使用独立前缀；设备、账号、IP、bundle、channel、订单号不能复用。
- 自造业务字段不要包含 `/`；固定外层 UA 可使用 `"ua": "curl/7.87.0"`。
- 所有时间戳按发送顺序递增；回流默认间隔 3 天。
- 同一设备距上次设备发送 `< 2 天` 是活跃设备，不参与新归因。
- 语义空值用 `null`，不要用空字符串。
- 同一个 `#order_id` 只能绑定一个 `#user_id`。
- 未归因场景不仅要改精准字段，还要排除 IP、bundle、channel 等误命中。
- 构造 `ipv4` / `#ipv4` 与 `ipv6` / `#ipv6` 时使用合法地址。
- 模糊归因 case 中同一 IP 同一自然日只能用一次。
- `source` 必须是真实渠道值；未指定时沿用模板默认 `taptap`，不要虚构渠道。
- `appsflyer_id` 归因成功 case 中广告侧至少满足 `source_type = "third_party"`、`source = "appsflyer"`。

## 输出格式

默认按发送顺序输出，且每条 Kafka 消息为独立单行 JSON：

1. 场景摘要：验证目标与事件链。
2. 期望结果：设备/账号/回流谁应归因，谁不应归因。
3. 时间与平台：起始日期 UTC+8、相邻间隔、回流间隔、匹配键、topic。
4. 身份键：`#sdid_s`、`#user_id`、匹配 ID。
5. 分条 JSON：`### N · 名称 \`#event\`` + 单行 JSON 代码块。
6. 时间对照表：序号、事件、ts、UTC+8 时间。

## 关键 topic

- `ad_tracker`：`data-lake_ods_staging_x48mn2zq83dx1flj7bds6xgk`
- 标准行为：`data-lake_ods_staging_17IYH6HNGZwwbD2mE1ag6Rqm`
- Windows 广告落地：`data-lake_ods_staging_phlbx43ypzzk23ujqrbic3c7`
- 云游戏行为：`data-lake_ods_staging_o6tecvdb5vbkzzjjiea38b9v`

## 发送规则

只有用户明确要求“发送”“发数据”“造完直接发”时才执行。执行前必须先展示本次要发送的具体 JSON。

按事件顺序逐条发送、逐条等待 `SUCCESS`，不要把多条消息打包成一次 `startParams`。广告侧事件发送成功后，如果下一条紧接行为侧事件，广告发送命令追加 `--post-send-wait-seconds 60`；行为到行为、行为到广告或单条数据不加。

脚本路径以当前安装 skill 的实际路径为准：

```bash
python .kira/skills/ad-attribution/scripts/send_adtracker.py --json '<单条ad_tracker JSON>' --wait
python .kira/skills/ad-attribution/scripts/send_ad_landing.py --json '<单条#ad_landing JSON>' --wait
python .kira/skills/ad-attribution/scripts/send_behavior.py --json '<单条行为JSON>' --wait
python .kira/skills/ad-attribution/scripts/send_cloud_game_behavior.py --topic data-lake_ods_staging_o6tecvdb5vbkzzjjiea38b9v --json '<单条云游戏行为JSON>' --wait
```

令牌读取顺序：环境变量 `DS_TOKEN`，再读项目根目录 `.env.local`。不要把 token 输出到回复、日志摘要或上下文。

## 刷数工作流

用户明确说“刷数”“补刷”“刷新归因数据”或“造完后刷数”才触发。

周期规则：

- 用户给了造数周期就用用户周期。
- 用户没给周期但本轮刚造过数据，从事件时间取最早自然日和最晚自然日。
- 传给 DS 的 `start_dt` / `end_dt` 是造数起止日期分别 `+1 天`。
- 例：造数周期 `2025-11-01` 到 `2025-11-02`，传 `start_dt=2025-11-02`、`end_dt=2025-11-03`。

执行前必须说明造数周期和实际 DS 参数，并等待用户明确确认。

```bash
python .kira/skills/ad-attribution/scripts/start_refresh_workflow.py \
  --data-start-date 2025-11-01 \
  --data-end-date 2025-11-02 \
  --wait
```

## 造数前自检

- 事件顺序是否符合目标。
- 平台和匹配键是否统一。
- 回流是否 `> 2 天`，活跃是否 `< 2 天`。
- 广告、设备、账号、付费关键字段是否能区分来源。
- 不归因场景是否没有其他可命中的匹配字段。
- `#order_id` 是否唯一归属。
- Windows `#tracking_code` 是否 12 位且只含小写字母和数字。
- iOS `caid/#fdid` 是否保持数组结构。
