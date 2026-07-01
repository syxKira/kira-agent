# Windows / PC tracking_code 归因

## 链路

Windows / PC 文件名归因没有常规移动端设备 ID。链路是：

1. 用户落地启动器下载页。
2. 页面生成追踪 Code，并随广告落地事件 `#ad_landing` 上报。
3. 启动器把追踪 Code 放入文件名。
4. 后续启动器启动或游戏启动时，行为事件带同一个 `#tracking_code`。
5. 广告落地日志与行为日志按 `#tracking_code` 或模糊字段匹配。

## 事件

广告侧使用 `#ad_landing`：

- topic: `data-lake_ods_staging_phlbx43ypzzk23ujqrbic3c7`
- `data.#name = "#ad_landing"`
- 必须有 `data.#tracking_code`
- 常见归因字段：`#media`、`#link_code`、`#campaign_id`、`#adset_id`、`#ad_id`、`#keyword_id`、`#tracking_id`、`#raw0`、`#url`、`#url_path`

行为侧使用 Windows `#app_start` 或启动器相关行为：

- `#os = "Windows"`
- `#sdk_type = "Windows"`
- 携带同一个 `#tracking_code`
- 不要强行补 `idfa/anid/gaid/oaid`

## 精准匹配

`#tracking_code` 必须满足：

- 12 位字符串。
- 仅包含小写英文字母 `a-z` 与数字 `0-9`。
- 大小写敏感，广告侧与行为侧完全一致。
- 不允许下划线、连字符、大写字母或其他符号。

符合规则且窗口期内匹配成功时，取最近一条广告作为归因结果，`match_type = id_matching`，`match_id_type = tracking_code`。

## 模糊匹配

当 `#tracking_code` 不合法或未匹配成功，进入模糊归因。PC 模糊常用字段：

| 行为日志 | 广告落地日志 |
| --- | --- |
| `#ipv4` | `#ipv4` |
| `#os` | `#os` |
| `#os_ver` | `#os_ver` |

PC 模糊归因的归因属性：

- `source_type = media`
- `source = hypergryph`
- `match_type = probabilistic`
- `match_id_type = ipv4`
- `touch_type = impression`
- `touch_ts` 取广告落地日志 `#ts`

构造 Windows 模糊 case 时通常只使用 `ipv4`，不要补移动端 `ipv6` 或设备 ID 精准字段。

## 实时和离线产物

标准模块：

- 实时行为表：`device_activation_rt`、`device_backflow_rt`、`event_log_rt`
- 实时归因表：`device_activation_attribution_rt`、`device_backflow_attribution_rt`、`user_activation_attribution_rt`、`user_backflow_attribution_rt`
- 离线表：`device`、`user`、`event_log`

启动器模块：

- 实时行为表：`launcher_device_activation_rt`、`launcher_device_backflow_rt`、`launcher_event_log_rt`
- 实时归因表：`launcher_device_activation_attribution_rt`、`launcher_device_backflow_attribution_rt`
- 离线表：`launcher_device`、`launcher_event_log`

## 常见错误

- 用移动端 `ad_tracker` 代替 Windows 广告落地 `#ad_landing`。
- `#tracking_code` 写成 13 位、带下划线、带大写字母。
- 广告侧和行为侧 `#tracking_code` 不完全一致。
- Windows 行为里乱补 `#idfa_c/#anid_c/#gaid_c/#oaid_c`。
- PC 模糊 case 同日复用同一个 IP，导致结果难以排查。
