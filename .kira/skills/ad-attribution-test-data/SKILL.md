---
name: ad-attribution-test-data
description: >-
  构造广告归因 Kafka 测试数据 JSON，覆盖 ad_tracker、#app_start、#user_login、#charge、角色事件，
  支持 idfa_c、anid_c、gaid_c、oaid_c 精准归因、Windows tracking_code 归因、ipv4/ipv6 模糊排查、设备新增/回流、账号新增/回流、
  已归因与未归因场景。当用户提到构造归因数据、广告匹配测试、设备归因、账号归因、
  设备回流、自然回流、账号付费，或用“广告a3 新增设备d3 注册账号u3 账号u3付费”
  这类简写描述场景时使用。
---

# 通用广告归因测试数据

## 快速开始

1. 把用户的自然语言或简写场景翻译成事件序列，再补齐 Kafka JSON。
2. 除非用户明确说“续上一个场景”，否则每个场景都必须隔离，设备、账号、IP、bundle、channel、订单号都用独立前缀。
3. 用户指定过全局约定（起始日期、平台、空值表示等）后，后续场景沿用。
4. 输出 JSON 前先给 1-3 句场景摘要：验证目标、事件顺序、谁应归因、谁不应归因。
5. 如果用户给的是大段背景，先整理成 5 项：验证目标、事件顺序、匹配键、期望结果、关键差异字段。
6. 如果用户问“初始口径、初始设备、初始染色、空设备链路”，改用单独的初始口径 Skill。

关键判断：
- “设备归因”和“账号继承设备归因”是两层目标，不要混写。
- 如果用户要造回传、callback、event_type、次留或 8 留，改用 `../ad-callback-test-data/SKILL.md`；回传造数会把归因链路作为前置背景。

## 场景输入映射

| 用户描述 | 事件 | 说明 |
|------|------|------|
| 广告a3 | `ad_tracker` | 一条广告日志 |
| 新增设备d1 | `#app_start` | 设备首次出现 |
| 设备回流d1 | `#app_start` | 同一 `#sdid_s`，距上次出现 >2 天 |
| 注册账号u1 | `#user_login` | 新账号首次出现 |
| 新账号登陆老设备 | `#user_login` | 老设备场景 |
| 老账号登陆新设备 | `#app_start` | 新设备场景，且必须带 `#user_id` |
| 账号u1付费 | `#charge` | 按 `#user_id` 和 `#sdid_s` 关联 |

补充规则：
- `#app_start` 按设备事件结构构造；但如果它表达的是“老账号登陆新设备”，则必须带 `#user_id`。
- `#user_login` 必须带 `#user_id`。
- “新账号登陆老设备”和“老账号登陆新设备”都可以只发一条，事件类型取决于设备是不是新设备。
- 付费、角色等后续事件只验证归属链路，不负责起始归因。

## 核心概念

### 归因链路

广告 →(精准匹配字段)→ 设备 →(`#sdid_s`)→ 账号 →(`#user_id` + `#sdid_s`)→ 付费

### 精准匹配字段

| 平台 | 行为日志 | 广告日志 | 匹配逻辑 |
|------|---------|---------|---------|
| iOS | `#idfa_c` | `idfa` | `upper(A) = upper(B)` 或 `upper(md5(A)) = upper(B)`（A=行为，B=广告） |
| Android | `#anid_c` | `anid` | 同上 |
| Android | `#gaid_c` | `gaid` | 同上 |
| Android | `#oaid_c` | `oaid` | 同上 |
| Windows | `#tracking_code` | `#tracking_code` | 广告落地事件 `#ad_landing` 与行为事件按相同 `#tracking_code` 归因 |

- 默认造数时，`idfa/anid/gaid/oaid` 及其对应行为字段尽量使用原值，不要主动改造成 `md5` 形式；只有用户显式说明要验证 `md5` 场景时才使用。
- `appsflyer_id` 如需造归因成功 case，广告侧至少满足：`source_type = "third_party"`、`source = "appsflyer"`；未满足这两个条件时，不要默认认为仅靠 `appsflyer_id` 相等就能归因成功。

### 模糊匹配与 IP 排查

- 广告侧通常看 `ad_tracker.data.ipv4`、`ad_tracker.data.ipv6`
- 行为侧通常看外层 `#ipv4`是外层`ip`字段转的，ipv6则是 里层的`#ipv6` 
- 如果精准字段双方都非空但不匹配，则退化成模糊匹配
- 做“不归因”场景时，除了把精准字段改成不匹配值，也要检查没有其他字段意外命中

### 关键定义

| 术语 | 定义 |
|------|------|
| 设备新增 | 设备首次出现在系统中 |
| 设备回流 | 距上次出现 >2 天 |
| 设备活跃 | 距上次设备发送 <2 天 |
| 账号新增 | 账号首次出现 |
| 账号回流 | 距上次出现 >2 天 |
| 设备归因 | 设备新增或回流时匹配到广告 |
| 账号归因 | 账号所属设备已归因 |

补充理解：

- 设备是否归因，看的是设备事件和广告事件能否匹配，活跃设备不参与归因计算
- 账号是否归因，看的是账号是否通过 `#sdid_s` 归属到某台已归因设备
- 所以“设备归因成功”与“账号归因成功”是两层验证，不要混成一层

## 构造约束（必须遵守）

1. **业务字段禁用 `/`**：设备、账号、广告归因参数等自造业务字段值不能包含 `/`，会影响 Kafka 发送；固定外层 UA 按标准填 `"ua": "curl/7.87.0"`；输出必须是合法 JSON。
2. **时间顺序**：按数据发送顺序构造严格递增时间戳。
3. **场景隔离**：每个场景使用独立前缀，设备、账号、IP、bundle、channel 都不能复用，除非用户明确要求续上一个场景。
4. **关键字段区分**：广告、设备、账号之间至少区分这些字段，用于验证取值来源：
   `channel1, channel2, bundle_id, os_ver, ipv4, ipv6, appsflyer_id, firebase_app_instance_id, idfv_c`
5. **回流间隔**：回流时间戳距上次出现 >2 天，默认用 3 天。
6. **活跃设备不归因**：若同一设备距上一次设备发送 <2 天，则按活跃设备处理，不能归因。
7. **新增后的短间隔设备事件不归因**：新增设备后，下一次新增或回流若距新增 <2 天，也按活跃设备处理，不能归因。
8. **回流关键字段变化**：回流场景关键字段值必须与上次不同，常用 `_new`、`_ret`、`_ret1`、`_ret2` 后缀区分。
9. **语义空值用 `null`**：不要用空字符串表达真正的空值。
10. **订单号唯一归属**：同一个 `#order_id` 只能对应一个 `#user_id`，不能跨账号复用同一订单号。
11. **避免误命中**：做未归因场景时，不仅要改精准字段，也要检查 IP、bundle、channel 等不会误导排查。
12. **角色事件后置**：若用户要验证角色、区服、角色付费链路，`#character_login` 必须晚于账号事件。
13. **IP 字段合法性**：构造 `ipv4` / `#ipv4` 与 `ipv6` / `#ipv6` 时必须使用合法地址。IPv4 每段取值必须在 `0-255`；IPv6 必须符合标准冒号分隔格式，不要使用随手拼接的非法占位值。
14. **tracking_code 合法性**：`#tracking_code` 必须是 12 位字符串，只能由小写英文字母 `a-z` 与阿拉伯数字 `0-9` 组成，例如 `wwwdows00001`。
15. **`source` 必须真实**：`source` 必须填写真实渠道值；如果用户没有额外说明，就沿用模板中的真实值，例如 `taptap`，不要自造默认占位值或虚构渠道名。
16. **只输出不落文件**：构造的数据默认直接在对话中输出，不要创建、修改或覆盖任何项目文件，除非用户明确要求写入文件；普通 case 可按固定间隔排，回流场景必须先满足 `> 2 天`。
17. **未要求发送不发送**：用户没有明确要求“发送”“发数据”或“造完直接发”时，只生成并展示 JSON，不调用任何发送脚本，也不要自行执行发送动作。

## 数据模板

### 广告数据（`ad_tracker`）

- topic: `data-lake_ods_staging_x48mn2zq83dx1flj7bds6xgk`
- `#name`: `ad_tracker`
- 根据平台填写一个精准匹配字段，其余匹配字段置 `null`
- `source` / `media` 优先填写用户明确指定的真实渠道；若用户未说明，默认沿用模板值 `taptap`
- 若造 `appsflyer_id` 归因成功 case，广告侧至少改成：`source_type = "third_party"`、`source = "appsflyer"`；`media` 建议同步写成 `appsflyer`
- 所有时间戳字段都按数值填写，不要给 `ts` / `#ts` / `touch_ts` / `sys_*_ts` 加双引号
- `match_type` 是模板默认空字段，构造原始 `ad_tracker` 广告日志时保持 `""`；不要把 `idfa`、`anid`、`gaid`、`oaid` 写入 `match_type`，除非用户明确要求构造已回填归因结果。
- 广告归因字段重点覆盖：
  `source_type, source, media, partner, campaign_id, adset_id, ad_id, keyword_id, link_code, touch_type, touch_ts`

```json
{
  "ts": {{时间戳ms}},
  "ua": "curl/7.87.0",
  "ip": "{{外层IP}}",
  "app_name": "data-lake_event-log-api",
  "app_env": "staging",
  "module": "batch_event",
  "topic": "data-lake_ods_staging_x48mn2zq83dx1flj7bds6xgk",
  "data": {
    "#ts": {{时间戳ms}},
    "gaid": null, "anid": null, "oaid": null, "idfa": null,
    "uuid": "{{唯一ID}}", "#part_id": "{{同uuid}}",
    "ua": "{{OS}}", "os": "{{OS}}", "brand": "{{品牌}}", "model": "{{型号}}",
    "ipv4": "{{广告ipv4数值}}", "ipv6": "{{广告ipv6}}",
    "channel1": "{{广告channel1}}", "channel2": "{{广告channel2}}",
    "os_ver": "{{广告os_ver}}",
    "campaign_type": "", "adset": "", "ad": "",
    "appsflyer_id": null, "match_type": "", "keyword": "", "keyword_id": "",
    "adset_id": "", "ad_id": "", "campaign_id": "", "campaign": "",
    "source_type": "media", "source": "taptap", "touch_type": "click",
    "partner": "", "media": "taptap",
    "link_campaign": "", "link_adset": "", "link_ad": "",
    "link_code": "", "attribution_party": null,
    "raw0": null, "raw1": null, "raw2": null, "raw_ts": null,
    "project_id": 4,
    "#name": "ad_tracker",
    "#app_id": "x48mn2zq83dx1flj7bds6xgk",
    "touch_ts": {{时间戳ms}},
    "sys_boot_ts": {{时间戳ms}},
    "sys_upd_ts": {{时间戳ms}}
  }
}
```

### 设备数据（`#app_start`）

- topic: `data-lake_ods_staging_17IYH6HNGZwwbD2mE1ag6Rqm`
- `#name`: `#app_start`
- 设备身份键：`#sdid_s`
- 精准匹配字段：`#idfa_c` 或 `#anid_c` / `#gaid_c` / `#oaid_c`

```json
{
  "ts": {{时间戳ms}},
  "ua": "curl/7.87.0",
  "ip": "{{外层IP}}",
  "app_name": "data-lake_event-log-api",
  "app_env": "staging",
  "module": "batch_event",
  "topic": "data-lake_ods_staging_17IYH6HNGZwwbD2mE1ag6Rqm",
  "data": {
    "#name": "#app_start",
    "#os": "{{OS}}", "#brand": "{{品牌}}", "#model": "{{型号}}",
    "#sdid_s": "{{设备ID}}",
    "#idfa_c": null, "#anid_c": null, "#gaid_c": null, "#oaid_c": null,
    "#channel1": "{{设备channel1}}", "#channel2": "{{设备channel2}}",
    "#bundle_id": "{{设备bundle_id}}", "#os_ver": "{{设备os_ver}}",
    "#ipv4": "{{设备ipv4}}", "#ipv6": "{{设备ipv6}}",
    "#appsflyer_id": "{{设备appsflyer_id}}",
    "#firebase_app_instance_id": "{{设备firebase}}",
    "#idfv_c": "{{设备idfv_c}}",
    "#app_id": "17IYH6HNGZwwbD2mE1ag6Rqm",
    "#seq": 1, "#sdk_type": "{{OS}}",
    "#sdk_vn": "", "#sdk_vc": "",
    "#app_vn": "", "#app_vc": "",
    "#height": 0, "#width": 0, "#ram": 0, "#disk": 0,
    "#consumed_ram": 0, "#remaining_disk": 0, "#remaining_battery": 0,
    "#carrier": "", "#language": "zh",
    "#network": "", "#network_std": "",
    "#cpu": "", "#gpu": "", "#gpu_ram": 0,
    "#ua": "", "#browser": "", "#browser_ver": "",
    "#title": "", "#url": "", "#url_path": "",
    "#referrer": "", "#referrer_host": "",
    "#ts_c": {{时间戳ms}}, "#ts_s": {{时间戳ms}}
  }
}
```

### Windows `tracking_code` 归因数据

- 适用场景：Windows 行为根据广告落地事件中的 `#tracking_code` 归因。
- 广告侧事件：`#name` 使用 `#ad_landing`，广告与行为的 `#tracking_code` 必须一致。
- 行为侧事件：`#app_start`，`#os` / `#sdk_type` 使用 `Windows`，并携带同一个 `#tracking_code`。
- `#tracking_code` 必须满足 12 位、小写英文字母与阿拉伯数字组成；不要使用大写字母、下划线、连字符或其他符号。
- Windows 场景不要强行补 `idfa/anid/gaid/oaid`，demo 中这些字段保持 `null`。
- 输出此场景时不要省略 demo 字段；以下两条 JSON 可作为完整字段模板。

#### 广告落地数据（`#ad_landing`）

```json
{"ts":1770688920000,"#ua":"curl/7.87.0","ip":"16.152.26.0","app_name":"data-lake_event-log-api","app_env":"staging","module":"batch_event","topic":"data-lake_ods_staging_phlbx43ypzzk23ujqrbic3c7","data":{"#ts":1773108000000,"gaid":null,"anid":null,"oaid":null,"idfa":null,"uuid":"MVpHNVszogSSezIp03fqw700","#part_id":"MVpHNVszogSSezIp03fqwM53","#ua":"Windows","raw1":"raw1401","#raw0":"https://www.pixiv.net/","raw2":"raw2401","#ipv4":null,"ipv6":null,"#os":"Windows","brand":"apple","model":"iPad13","campaign_type":"campaign_type401","third_party_conversion_type":"third_party401","adset":"adset401","appsflyer_id":null,"match_type":"match_type401","keyword":"keyword401","sys_boot_ts":1702664100051,"sys_upd_ts":1702664100051,"#keyword_id":"keyword_id401","#adset_id":"adset_id401","ad":"adad401","#os_ver":"1.2.0","project_id":4,"source_type":"media","source":"oceanengine","touch_type":"click","raw_ts":null,"partner":"letui401","#media":"oceanengine","link_campaign":"test_campaign401","link_adset":"link-adset401","link_ad":"tap-401","#campaign_id":"campaign_id401","campaign":"campaign401","#ad_id":"ad_id401","#name":"#ad_landing","#tracking_code":"wwwdows00001","#tracking_id":"trackingid0123456789","#app_id":"phlbx43ypzzk23ujqrbic3c7","touch_ts":1773108000000}}
```

#### Windows 设备数据（`#app_start`）

```json
{"ts":1770688930000,"#ua":"curl/7.87.0","ip":null,"app_name":"data-lake_event-log-api","app_env":"staging","module":"batch_event","topic":"data-lake_ods_staging_17IYH6HNGZwwbD2mE1ag6Rqm","data":{"#name":"#app_start","#os":"Windows","#channel1":"1","#channel2":"prd-lala","#sdid_s":"oceanengine_260210_g5_sdid_02","#os_ver":"1.2.0","#brand":"apple","#model":"iPad13","#app_id":"17IYH6HNGZwwbD2mE1ag6Rqm","#seq":1,"#sdk_type":"Windows","#sdk_vn":"1.1.1.1","#sdk_vc":"1113","#bundle_id":"com.hypergryph.arknights","#app_vn":"1.1.1","#app_vc":"111","#height":2160,"#width":3840,"#ram":3034,"#disk":128887,"#consumed_ram":901,"#remaining_disk":126568,"#remaining_battery":0,"#carrier":"中国移动1","#language":"zh1","#network":"Wi-Fi1","#network_std":"Wi-Fi1","#cpu":"cpu1","#gpu":"gpu1","#gpu_ram":5464,"#ua":"ua1","#browser":"browser1","#browser_ver":"browser_ver1","#title":"title1","#url":"url1","#url_path":"url_path1","#referrer":"referrer1","#referrer_host":"referrer_host1","#tracking_code":"wwwdows00001","#ts_c":1701364271000,"#ts_s":1701364271000}}
```

### 账号数据（`#user_login`）

- topic: 同设备数据
- `#name`: `#user_login`
- 账号身份键：`#user_id`
- 设备关联键：`#sdid_s`
- 结构与 `#app_start` 相同，但必须增加 `#user_id`

### 付费数据（`#charge`）

- topic: 同设备数据
- `#name`: `#charge`
- 关联键：`#user_id` + `#sdid_s`
- 结构对齐 `归因相关知识/create_attribution_data.txt` 的完整 `#charge` 示例，公共字段不要只剩 `#amount` / `#order_id`
- 关键公共字段：至少保留 `#os`、`#channel1`、`#bundle_id`、`#app_id`、`#seq`、`#sdk_type`、`#ts_c`、`#ts_s`
- 订单唯一性：若同一场景有多条付费，每条 `#order_id` 都必须唯一归属到对应的 `#user_id`

```json
{
  "ts": {{时间戳ms}},
  "ua": "curl/7.87.0",
  "ip": "{{外层IP}}",
  "app_name": "data-lake_event-log-api",
  "app_env": "staging",
  "module": "batch_event",
  "topic": "data-lake_ods_staging_17IYH6HNGZwwbD2mE1ag6Rqm",
  "data": {
    "#name": "#charge",
    "#os": "{{OS}}",
    "#channel1": "{{设备channel1}}",
    "#sdid_s": "{{设备ID}}",
    "#user_id": "{{账号ID}}",
    "#os_ver": "{{设备os_ver}}",
    "#brand": "{{品牌}}",
    "#model": "{{型号}}",
    "#app_id": "17IYH6HNGZwwbD2mE1ag6Rqm",
    "#seq": 1,
    "#sdk_type": "{{OS}}",
    "#sdk_vn": "",
    "#sdk_vc": "",
    "#bundle_id": "{{设备bundle_id}}",
    "#app_vn": "",
    "#app_vc": "",
    "#height": 0,
    "#width": 0,
    "#ram": 0,
    "#disk": 0,
    "#consumed_ram": 0,
    "#remaining_disk": 0,
    "#remaining_battery": 0,
    "#carrier": "",
    "#language": "zh",
    "#network": "",
    "#network_std": "",
    "#cpu": "",
    "#gpu": "",
    "#gpu_ram": 0,
    "#ua": "",
    "#browser": "",
    "#browser_ver": "",
    "#title": "",
    "#url": "",
    "#url_path": "",
    "#referrer": "",
    "#referrer_host": "",
    "#ts_c": {{时间戳ms}},
    "#ts_s": {{时间戳ms}},
    "#amount": 10000,
    "#order_id": "{{唯一订单号}}"
  }
}
```

### 角色数据（按需）

- 常见事件：`#character_login`
- 适用场景：验证角色登录、区服归属、角色后续付费
- 最少应带：`#user_id`、`#sdid_s`、`#server_id`、`#character_id`
- 角色事件不负责起始归因，但常用于验证账号后的行为链是否接对

## 不归因场景设计

使设备回流不归因：
1. 将设备 `#idfa_c`（或 `#anid_c` 等）设为不匹配任何广告的值。
2. 精准排除规则会阻止模糊匹配：当行为和广告的精准 ID 都非空但不匹配时，不允许退化为模糊归因。
3. 若同一设备距上一次设备发送 <2 天，则按活跃设备处理，即使有广告匹配也不能归因。

```sql
(A.#oaid_c is null or B.oaid is null)
AND (A.#gaid_c is null or B.gaid is null)
AND (A.#idfa_c is null or B.idfa is null)
```

## 构造流程

1. **解析场景**：把用户简写转换成事件序列，判断是独立场景还是续上一个场景。
2. **选平台和匹配键**：iOS 用 `idfa/idfa_c`，Android 用 `anid/anid_c`，必要时也可用 `gaid` 或 `oaid`。
   - Windows 根据 `tracking_code` 归因时，使用广告侧 `#ad_landing.data.#tracking_code` 与行为侧 `#app_start.data.#tracking_code` 对齐。
3. **设置时间基准**：沿用用户指定的起始日期；若无，先说明你采用的时间基准。
4. **分配唯一前缀**：设备、账号、IP、bundle、channel、order_id 都带当前场景前缀。
5. **填关键差异字段**：广告、设备、账号、付费的关键字段必须不同，方便验证取值来源。
6. **对齐关联键**：
   - 广告 `idfa/anid/gaid/oaid` 与设备 `#idfa_c/#anid_c/#gaid_c/#oaid_c` 对齐。
   - 账号 `#sdid_s` 与设备 `#sdid_s` 对齐。
   - 付费 `#user_id`、`#sdid_s` 与目标账号和设备对齐。
   - 同一个 `#order_id` 不得绑定多个 `#user_id`。
7. **补场景摘要**：在输出 JSON 前，先用 1-3 句说明“要验证什么、谁应该归因、谁不应该归因”。
8. **检查禁止项**：确认自造业务字段值不含 `/`（固定外层 UA 例外），时间戳递增，回流间隔满足要求。

## 输出格式

默认直接在对话中输出，按事件发送顺序排列。不要输出成数组，除非用户明确要求；每条 Kafka 消息保持为独立 JSON 对象，便于逐条发送。用户未明确要求发送时，只展示数据，不执行发送。

若用户要求“发送”，回复中必须先明确展示“本次要发送的具体数据”，不能只回发送结果。最低要求：
- 先标明这是第几条、事件类型、场景名（若有）
- 原样展示将要发送的单条 JSON，或在用户已贴出 JSON 时明确说明“本次发送的就是这条”
- 再执行发送
- 发送完成后，再补 workflow instance id、task instance id 和基础验证点

## 发送 `ad_tracker` 广告数据

发送脚本会优先读取环境变量 `DS_TOKEN`，若为空则自动读取项目根目录 `.env.local` 中的 `DS_TOKEN`；不要在输出中打印 token。

当用户明确要求“发送广告数据”“发 adtracker”或“造完广告后直接发”时，先按广告模板生成单条 `ad_tracker` Kafka JSON，再调用：

```bash
python .cursor/skills/ad-attribution-test-data/scripts/send_adtracker.py --json '<单条ad_tracker JSON>' --wait
```

规则：
- 该脚本只用于发送 `data.#name = ad_tracker` 的广告数据，不用于发送行为数据。
- DolphinScheduler 项目级 token 通过 `DS_TOKEN`、项目根目录 `.env.local` 或 `--token` 传入，脚本会放到请求的 `token` header 中。
- 脚本会把 Kafka JSON 包装成 DolphinScheduler 的 `startParams`。包装值必须是 Python 字符串数组表达式，不要改回三引号格式，否则 `caid` 等嵌套转义字段会导致 DS 任务里的 `json.loads` 失败。
- 真正发送前，必须先在回复中说明“本次发送的广告数据是什么”，不能跳过数据回显直接发送。
- 发送后优先使用 `--wait` 确认 DS task state 为 `SUCCESS`，并给出“校验点”：事件类型，以及本条广告的关键匹配 ID（如 `idfa/anid/gaid/oaid/appsflyer_id/#tracking_code`）。

## 数据发送顺序与失败处理

当用户要求发送多条数据时，必须按事件顺序逐条发送、逐条等待 DS task state 为 `SUCCESS` 后再发送下一条；不要把多条 Kafka JSON 打包进同一个 `startParams` 一次性发送，避免实时任务消费乱序。

如果任意一条发送失败，立即停止发送后续数据，并告诉用户失败的是第几条、事件类型，以及能从 DS 日志中看到的失败原因摘要。只有全部发送成功后，才汇总告诉用户每条数据的验证点。

## 发送 `#ad_landing` 广告落地数据

当用户明确要求“发送 ad_landing”“发广告落地数据”或 Windows `tracking_code` 归因场景里的广告侧事件时，先按广告落地模板生成单条 `#ad_landing` Kafka JSON，再调用：

```bash
python .cursor/skills/ad-attribution-test-data/scripts/send_ad_landing.py --json '<单条#ad_landing JSON>' --wait
```

规则：
- 该脚本只用于发送 `data.#name = #ad_landing`、topic `data-lake_ods_staging_phlbx43ypzzk23ujqrbic3c7` 的广告落地数据。
- 默认使用 workflowDefinitionCode `172774078531841`、version `3`；如 DS 工作流版本变更，用 `DS_AD_LANDING_WORKFLOW_CODE`、`DS_AD_LANDING_WORKFLOW_VERSION` 或命令参数覆盖。
- `#tracking_code` 必须存在，且要与后续 Windows 行为数据里的 `#tracking_code` 完全一致。
- DolphinScheduler 项目级 token 通过 `DS_TOKEN`、项目根目录 `.env.local` 或 `--token` 传入，脚本会放到请求的 `token` header 中。
- 真正发送前，必须先在回复中说明“本次发送的广告落地数据是什么”，不能跳过数据回显直接发送。
- 发送后优先使用 `--wait` 确认 DS task state 为 `SUCCESS`，并给出“校验点”：事件类型，以及 `#tracking_code`。

## 发送行为数据

当用户明确要求“发送行为数据”“发设备/账号/付费数据”时，先按行为模板生成单条 Kafka JSON，再调用：

```bash
python .cursor/skills/ad-attribution-test-data/scripts/send_behavior.py --json '<单条行为JSON>' --wait
```

规则：
- 该脚本只用于发送行为 topic `data-lake_ods_staging_17IYH6HNGZwwbD2mE1ag6Rqm` 的数据，常见事件包括 `#app_start`、`#user_login`、`#charge`、`#character_login`、`#downloader_start`、`#installer_start`。
- 默认使用行为 workflowDefinitionCode `172773151769857`、version `4`；如 DS 工作流版本变更，用 `DS_BEHAVIOR_WORKFLOW_CODE`、`DS_BEHAVIOR_WORKFLOW_VERSION` 或命令参数覆盖。
- DolphinScheduler 项目级 token 通过 `DS_TOKEN`、项目根目录 `.env.local` 或 `--token` 传入，脚本会放到请求的 `token` header 中；不要使用网页 cookie/session 作为脚本认证方式。
- 行为发送脚本同样使用 Python 字符串数组表达式包装 `startParams`，不要改回三引号格式。
- 真正发送前，必须先在回复中说明“本次发送的行为数据是什么”，不能跳过数据回显直接发送。
- 发送后优先使用 `--wait` 确认 DS task state 为 `SUCCESS`，并给出“校验点”：事件类型、`#sdid_s`；若有账号则补 `#user_id`，并补本条行为使用的匹配键（如 `#idfa_c/#anid_c/#gaid_c/#oaid_c/#appsflyer_id/#tracking_code`）。

````markdown
场景摘要：...
期望结果：...

### 1. 广告a1
```json
{...}
```

### 2. 新增设备d1
```json
{...}
```
````

## 输出前自检

- 事件顺序是否与用户目标一致
- 平台与匹配键是否统一
- 回流时间是否确实 `> 2 天`
- 广告、设备、账号三层关键字段是否足够区分
- 不归因场景是否真的没有留下其他可命中的匹配字段
- `#order_id` 是否唯一归属到一个 `#user_id`
- 若涉及角色，角色事件是否晚于账号事件
- 若涉及 Windows 归因，`#tracking_code` 是否为 12 位且仅包含小写字母和数字，且广告侧与行为侧完全一致
- 所有 `ipv4` / `#ipv4` 与 `ipv6` / `#ipv6` 是否都是合法 IP 地址
- 若用户给的是混乱背景，最终是否已经被整理成清晰的场景摘要

## 常见通用场景

| 场景 | 数据发送顺序 | 要点 |
|------|------------|------|
| 设备已归因 | 广告→新增设备 | 验设备归因字段 |
| 基础新增归因 | 广告→新增设备→新增账号 | 最简设备和账号归因 |
| 未归因设备新增后注册 | 新增设备→新增账号 | 无广告，不归因 |
| 回流归因 | 广告#1→新增设备→新增账号→广告#2→回流设备→回流账号 | 回流设备匹配回流广告 |
| 活跃设备不归因 | 新增或回流→<2天→设备再次发送 | 按活跃设备处理，不生成归因 |
| 回流不归因 | 广告→新增设备→回流设备(nomatch) | 精准匹配失败，阻止模糊归因 |
| 设备先于广告 | 新增设备→广告→回流设备 | 新增未归因，回流时归因 |
| 账号付费 | 新增设备→新增账号→付费 | 验证付费归属链路 |
| Windows tracking_code 归因 | 广告落地(`#ad_landing`)→Windows 新增设备(`#app_start`) | 两侧 `#tracking_code` 保持一致，验证 Windows 设备归因 |

## 平台差异速查

| 维度 | iOS | Android | Windows |
|------|-----|---------|---------|
| 归因字段(行为) | `#idfa_c` | `#anid_c` / `#gaid_c` / `#oaid_c` | `#tracking_code` |
| 归因字段(广告) | `idfa` | `anid` / `gaid` / `oaid` | `#tracking_code` |
| 广告事件 | `ad_tracker` | `ad_tracker` | `#ad_landing` |
| OS | iOS | Android | Windows |
| sdk_type | iOS | Android | Windows |
| 典型brand | apple | samsung / xiaomi / huawei | apple |
| 典型model | iPhone16Pro | SM-S918B | iPad13 |
| 典型cpu | A18Pro | Snapdragon8Gen2 | cpu1 |
| browser | Safari | Chrome | browser1 |

## 参考资料

- 详细场景示例见 [examples.md](examples.md)
- 广告归因字段取值：`归因相关知识/广告归因字段.md`
- 数据构造参考：`归因相关知识/create_attribution_data.txt`
- 回传、callback、次留/8 留、快手 raw0 必填请使用 `../ad-callback-test-data/SKILL.md`
- 初始口径与初始设备染色请使用单独 Skill
