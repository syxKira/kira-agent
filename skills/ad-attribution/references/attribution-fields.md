# 归因字段与 match_type 口径

## 自归因监测日志

移动端 `ad_tracker` 归因成功后，归因属性主要从广告监测日志取值：

| 归因属性 | 取值逻辑 |
| --- | --- |
| `source` | 广告监测日志 `source` |
| `media` | 广告监测日志 `media` |
| `partner` | 广告监测日志 `partner` |
| `link_code` | 监测链接 Code |
| `link_campaign` | 广告监测日志 `link_campaign` |
| `link_adset` | 广告监测日志 `link_adset` |
| `link_ad` | 广告监测日志 `link_ad` |
| `campaign_type` | 广告监测日志 `campaign_type` |
| `account_id` | 广告监测日志 `account_id` |
| `campaign_id` | 广告监测日志 `campaign_id` |
| `campaign` | 广告监测日志 `campaign` |
| `adset_id` | 广告监测日志 `adset_id` |
| `adset` | 广告监测日志 `adset` |
| `ad_id` | 广告监测日志 `ad_id` |
| `ad` | 广告监测日志 `ad` |
| `keyword_id` | 广告监测日志 `keyword_id` |
| `keyword` | 广告监测日志 `keyword` |
| `material_id` | 广告监测日志 `material_id` |
| `source_type` | 通常为 `media` |
| `attribution_party` | 通常为 `hypergryph` |
| `match_type` | `id_matching` 精准匹配；`probabilistic` 模糊匹配 |
| `touch_type` | 广告监测日志 `touch_type` |
| `touch_ts` | 广告互动时间 |

## 自归因落地页日志

Windows / PC `#ad_landing` 归因属性主要来自广告落地日志：

| 归因属性 | 取值逻辑 |
| --- | --- |
| `attribution_party` | 固定 `hypergryph` |
| `source_type` | 固定 `media` |
| `source` | 固定 `hypergryph` |
| `media` | 广告落地日志 `#media` |
| `match_type` | `id_matching` 或 `probabilistic` |
| `match_id_type` | 精准为 `tracking_code`，模糊为 `ipv4` |
| `touch_type` | 固定 `impression` |
| `touch_ts` | 广告落地日志 `#ts` |
| `link_code` | 广告落地日志 `#link_code` |
| `campaign_id` | 广告落地日志 `#campaign_id` |
| `adset_id` | 广告落地日志 `#adset_id` |
| `ad_id` | 广告落地日志 `#ad_id` |
| `keyword_id` | 广告落地日志 `#keyword_id` |
| `url` | 广告落地日志 `#url` |
| `url_path` | 广告落地日志 `#url_path` |
| `landing_page_id` | 广告落地日志 `#landing_page_id` |
| `ga_client_id` | 广告落地日志 `#ga_client_id` |
| `tracking_id` | 广告落地日志 `#tracking_id` |
| `raw0` | 广告落地日志 `#raw0` |

## 第三方平台 AppsFlyer

AppsFlyer 归因成功时广告侧至少满足：

- `source_type = "third_party"`
- `source = "appsflyer"`
- `media` 建议同步为 `appsflyer`

归因属性从广告监测日志中的 AppsFlyer 字段取值，包括 `source`、`media`、`partner`、`campaign_id`、`adset_id`、`ad_id`、`keyword_id`、`third_party_conversion_type`、`touch_type`、`touch_ts` 等。

## 解释结果时的固定说法

- `match_type = id_matching`：精准归因。
- `match_type = probabilistic`：模糊归因。
- 归因表有记录但 `match_type` 不是上述值：归因结果异常，需要展示实际值。
- 账号侧字段如 `#activation_device_activation_match_type` 表示账号继承设备新增归因类型，不要说成账号自己直接匹配广告。
