# 通用归因测试数据构造示例

## 使用原则

- 示例优先展示事件顺序、匹配键、时间间隔和关键字段差异；实际输出时仍以 `SKILL.md` 的构造约束为准。
- 语义空值用 `null`；自造业务字段值不能包含 `/`，固定外层 UA 使用标准格式 `curl/7.87.0`。
- 完整 JSON 示例用于字段位置参考，新的测试数据不要复用示例里的设备、账号、IP、bundle、channel、订单号。

## 示例1：基础 idfa_c 归因（iOS新增设备+账号+回流）

**场景**：广告a19 → 新增设备d19 → 新增账号u19 → 回流广告a19 → 回流设备d19 → 回流账号u19
**前缀**：`qa19`
**归因字段**：idfa / #idfa_c
**平台**：iOS

关键设计：
- 新增阶段：广告 idfa=`idfa_qa19_new`，设备 #idfa_c=`idfa_qa19_new` → 匹配归因
- 回流阶段：回流广告 idfa=`idfa_qa19_ret`，回流设备 #idfa_c=`idfa_qa19_ret` → 匹配归因
- 设备身份通过 #sdid_s=`sdid_qd19_001` 识别为同一设备
- 回流间隔3天（Feb 2 → Feb 5）

### 广告a19#1（新增）
```json
{"ts":1769997600000,"ua":"curl/7.87.0","ip":"27.100.19.1","app_name":"data-lake_event-log-api","app_env":"staging","module":"batch_event","topic":"data-lake_ods_staging_x48mn2zq83dx1flj7bds6xgk","data":{"#ts":1769997600000,"gaid":null,"anid":null,"oaid":null,"idfa":"idfa_qa19_new","uuid":"QaUUID19New","#part_id":"QaUUID19New","ua":"iOS","raw1":"raw1_ad_qa19_new","raw0":"raw0_ad_qa19_new","raw2":"raw2_ad_qa19_new","ipv4":388877619,"ipv6":"2001:0db8:abcd:a219:1234:5678:abcd:0019","channel1":"ad_ch1_qa19_new","channel2":"ad_ch2_qa19_new","os":"iOS","brand":"apple","model":"iPhone16","campaign_type":"campaign_type_qa19_new","third_party_conversion_type":"third_party_qa19_new","adset":"adset_qa19_new","appsflyer_id":null,"match_type":"match_type_qa19_new","keyword":"keyword_qa19_new","keyword_id":"keyword_id_qa19_new","adset_id":"adset_id_qa19_new","ad":"ad_qa19_new","os_ver":"15.4.0","project_id":4,"source_type":"media","source":"taptap","touch_type":"click","raw_ts":null,"partner":"partner_qa19_new","media":"taptap","link_campaign":"campaign_qa19_new","link_adset":"link-adset_qa19_new","link_ad":"tap-qa19-new","campaign_id":"campaign_id_qa19_new","campaign":"campaign_qa19_new","ad_id":"ad_id_qa19_new","attribution_party":null,"link_code":"lc_qa19_new","#name":"ad_tracker","#app_id":"x48mn2zq83dx1flj7bds6xgk","touch_ts":1769997600000,"sys_boot_ts":1769997600000,"sys_upd_ts":1769997600000}}
```

### 新增设备d19
```json
{"ts":1770001200000,"ua":"curl/7.87.0","ip":"27.100.19.1","app_name":"data-lake_event-log-api","app_env":"staging","module":"batch_event","topic":"data-lake_ods_staging_17IYH6HNGZwwbD2mE1ag6Rqm","data":{"#name":"#app_start","#os":"iOS","#channel1":"dev_ch1_qd19_new","#channel2":"dev_ch2_qd19_new","#sdid_s":"sdid_qd19_001","#idfa_c":"idfa_qa19_new","#firebase_app_instance_id":"firebase_qd19_new","#idfv_c":"idfv_qd19_new","#os_ver":"16.4.0","#appsflyer_id":"af_qd19_new","#ipv4":"488877619000","#ipv6":"3A0D:1091:8780:D219:35C6:8CFA:D7B2:D19A","#brand":"apple","#model":"iPhone16","#app_id":"17IYH6HNGZwwbD2mE1ag6Rqm","#seq":1,"#sdk_type":"iOS","#sdk_vn":"2.2.0.1","#sdk_vc":"2201","#bundle_id":"com.qa.d19.new","#app_vn":"2.2.0","#app_vc":"220","#height":2622,"#width":1206,"#ram":8192,"#disk":512000,"#consumed_ram":1600,"#remaining_disk":480000,"#remaining_battery":90,"#carrier":"中国电信","#language":"zh","#network":"5G","#network_std":"5G","#cpu":"A18Pro","#gpu":"Apple GPU","#gpu_ram":8192,"#ua":"ua_qd19_new","#browser":"Safari","#browser_ver":"16.4","#title":"title_qd19_new","#url":"url_qd19_new","#url_path":"url_path_qd19_new","#referrer":"referrer_qd19_new","#referrer_host":"referrer_host_qd19_new","#ts_c":1770001200000,"#ts_s":1770001200000}}
```

### 新增账号u19
```json
{"ts":1770004800000,"ua":"curl/7.87.0","ip":"27.100.19.1","app_name":"data-lake_event-log-api","app_env":"staging","module":"batch_event","topic":"data-lake_ods_staging_17IYH6HNGZwwbD2mE1ag6Rqm","data":{"#name":"#user_login","#user_id":"user_qu19_001","#os":"iOS","#channel1":"usr_ch1_qu19_new","#channel2":"usr_ch2_qu19_new","#sdid_s":"sdid_qd19_001","#idfa_c":"idfa_qa19_new","#firebase_app_instance_id":"firebase_qu19_new","#idfv_c":"idfv_qu19_new","#os_ver":"17.2.0","#appsflyer_id":"af_qu19_new","#ipv4":"588877619000","#ipv6":"4B0D:2092:9890:D219:46D7:9DEB:E8C3:D19B","#brand":"apple","#model":"iPhone16","#app_id":"17IYH6HNGZwwbD2mE1ag6Rqm","#seq":1,"#sdk_type":"iOS","#sdk_vn":"2.2.0.1","#sdk_vc":"2201","#bundle_id":"com.qa.u19.new","#app_vn":"2.2.0","#app_vc":"220","#height":2622,"#width":1206,"#ram":8192,"#disk":512000,"#consumed_ram":1600,"#remaining_disk":480000,"#remaining_battery":90,"#carrier":"中国联通","#language":"zh","#network":"5G","#network_std":"5G","#cpu":"A18Pro","#gpu":"Apple GPU","#gpu_ram":8192,"#ua":"ua_qu19_new","#browser":"Safari","#browser_ver":"17.2","#title":"title_qu19_new","#url":"url_qu19_new","#url_path":"url_path_qu19_new","#referrer":"referrer_qu19_new","#referrer_host":"referrer_host_qu19_new","#ts_c":1770004800000,"#ts_s":1770004800000}}
```

### 回流广告a19#2
```json
{"ts":1770256800000,"ua":"curl/7.87.0","ip":"27.100.19.2","app_name":"data-lake_event-log-api","app_env":"staging","module":"batch_event","topic":"data-lake_ods_staging_x48mn2zq83dx1flj7bds6xgk","data":{"#ts":1770256800000,"gaid":null,"anid":null,"oaid":null,"idfa":"idfa_qa19_ret","uuid":"QaUUID19Ret","#part_id":"QaUUID19Ret","ua":"iOS","raw1":"raw1_ad_qa19_ret","raw0":"raw0_ad_qa19_ret","raw2":"raw2_ad_qa19_ret","ipv4":398877619,"ipv6":"2001:0db8:abcd:b219:5678:9abc:def0:0019","channel1":"ad_ch1_qa19_ret","channel2":"ad_ch2_qa19_ret","os":"iOS","brand":"apple","model":"iPhone16","campaign_type":"campaign_type_qa19_ret","third_party_conversion_type":"third_party_qa19_ret","adset":"adset_qa19_ret","appsflyer_id":null,"match_type":"match_type_qa19_ret","keyword":"keyword_qa19_ret","keyword_id":"keyword_id_qa19_ret","adset_id":"adset_id_qa19_ret","ad":"ad_qa19_ret","os_ver":"15.6.0","project_id":4,"source_type":"media","source":"taptap","touch_type":"click","raw_ts":null,"partner":"partner_qa19_ret","media":"taptap","link_campaign":"campaign_qa19_ret","link_adset":"link_adset_qa19_ret","link_ad":"tap-qa19-ret","campaign_id":"campaign_id_qa19_ret","campaign":"campaign_qa19_ret","ad_id":"ad_id_qa19_ret","attribution_party":null,"link_code":"lc_qa19_ret","#name":"ad_tracker","#app_id":"x48mn2zq83dx1flj7bds6xgk","touch_ts":1770256800000,"sys_boot_ts":1770256800000,"sys_upd_ts":1770256800000}}
```

### 回流设备d19（关键字段与新增时不同）
```json
{"ts":1770260400000,"ua":"curl/7.87.0","ip":"27.100.19.3","app_name":"data-lake_event-log-api","app_env":"staging","module":"batch_event","topic":"data-lake_ods_staging_17IYH6HNGZwwbD2mE1ag6Rqm","data":{"#name":"#app_start","#os":"iOS","#channel1":"dev_ch1_qd19_ret","#channel2":"dev_ch2_qd19_ret","#sdid_s":"sdid_qd19_001","#idfa_c":"idfa_qa19_ret","#firebase_app_instance_id":"firebase_qd19_ret","#idfv_c":"idfv_qd19_ret","#os_ver":"16.6.0","#appsflyer_id":"af_qd19_ret","#ipv4":"498877619000","#ipv6":"3B1E:2192:9891:D219:46E8:AE0C:F9D4:E19C","#brand":"apple","#model":"iPhone16","#app_id":"17IYH6HNGZwwbD2mE1ag6Rqm","#seq":1,"#sdk_type":"iOS","#sdk_vn":"2.2.0.1","#sdk_vc":"2201","#bundle_id":"com.qa.d19.ret","#app_vn":"2.2.1","#app_vc":"221","#height":2622,"#width":1206,"#ram":8192,"#disk":512000,"#consumed_ram":2100,"#remaining_disk":460000,"#remaining_battery":50,"#carrier":"中国移动","#language":"zh","#network":"Wi-Fi","#network_std":"Wi-Fi","#cpu":"A18Pro","#gpu":"Apple GPU","#gpu_ram":8192,"#ua":"ua_qd19_ret","#browser":"Safari","#browser_ver":"16.6","#title":"title_qd19_ret","#url":"url_qd19_ret","#url_path":"url_path_qd19_ret","#referrer":"referrer_qd19_ret","#referrer_host":"referrer_host_qd19_ret","#ts_c":1770260400000,"#ts_s":1770260400000}}
```

### 回流账号u19
```json
{"ts":1770264000000,"ua":"curl/7.87.0","ip":"27.100.19.3","app_name":"data-lake_event-log-api","app_env":"staging","module":"batch_event","topic":"data-lake_ods_staging_17IYH6HNGZwwbD2mE1ag6Rqm","data":{"#name":"#user_login","#user_id":"user_qu19_001","#os":"iOS","#channel1":"usr_ch1_qu19_ret","#channel2":"usr_ch2_qu19_ret","#sdid_s":"sdid_qd19_001","#idfa_c":"idfa_qa19_ret","#firebase_app_instance_id":"firebase_qu19_ret","#idfv_c":"idfv_qu19_ret","#os_ver":"17.6.0","#appsflyer_id":"af_qu19_ret","#ipv4":"598877619000","#ipv6":"4C2F:3193:A9A2:D219:57E8:BF1D:FA05:F19D","#brand":"apple","#model":"iPhone16","#app_id":"17IYH6HNGZwwbD2mE1ag6Rqm","#seq":1,"#sdk_type":"iOS","#sdk_vn":"2.2.0.1","#sdk_vc":"2201","#bundle_id":"com.qa.u19.ret","#app_vn":"2.2.1","#app_vc":"221","#height":2622,"#width":1206,"#ram":8192,"#disk":512000,"#consumed_ram":2100,"#remaining_disk":460000,"#remaining_battery":50,"#carrier":"中国移动","#language":"zh","#network":"Wi-Fi","#network_std":"Wi-Fi","#cpu":"A18Pro","#gpu":"Apple GPU","#gpu_ram":8192,"#ua":"ua_qu19_ret","#browser":"Safari","#browser_ver":"17.6","#title":"title_qu19_ret","#url":"url_qu19_ret","#url_path":"url_path_qu19_ret","#referrer":"referrer_qu19_ret","#referrer_host":"referrer_host_qu19_ret","#ts_c":1770264000000,"#ts_s":1770264000000}}
```

---

## 示例2：回流不归因 + 再次回流归因

**场景**：广告 → 新增设备 → 新增账号 → 回流设备#1(不归因) → 广告#2 → 回流设备#2(归因) → 回流账号
**前缀**：`qb20`
**要点**：第一次回流 idfa_c=`idfa_qb20_nomatch`（不匹配任何广告→不归因），第二次回流匹配新广告→归因

关键数据片段（仅展示核心差异字段）：

### 回流设备#1（不归因）
- `#idfa_c`: `idfa_qb20_nomatch`（不匹配任何广告）
- 不归因原因：精准匹配失败 + 精准排除阻止模糊匹配（双方idfa均非空）
- 关键字段后缀：`_ret1`

### 回流设备#2（归因）
- `#idfa_c`: `idfa_qb20_ret2`（匹配回流广告 idfa=`idfa_qb20_ret2`）
- 关键字段后缀：`_ret2`

---

## 示例3：Android anid_c 归因

**场景**：广告a22 → 新增设备d22 → 新增账号u22 → 回流广告a22 → 回流设备d22 → 回流账号u22
**前缀**：`qd22`
**归因字段**：anid / #anid_c
**平台差异**：

```
OS: Android（非iOS）
brand: samsung
model: SM-S918B
sdk_type: Android
cpu: Snapdragon8Gen2
browser: Chrome
广告匹配字段：anid（非idfa）
行为匹配字段：#anid_c（非#idfa_c），#idfa_c 置空
```

广告数据中 `idfa`, `gaid`, `oaid` 置空，仅 `anid` 有值：
```json
"gaid":null,"anid":"anid_qd22_new","oaid":null,"idfa":null
```

设备数据中 `#idfa_c` 置空，增加 `#anid_c` 字段：
```json
"#idfa_c":null,"#anid_c":"anid_qd22_new"
```

---

## 时间戳速查（2026年2月，北京时间10:00起）

| 日期 | 10:00 | 11:00 | 12:00 | 13:00 |
|------|-------|-------|-------|-------|
| Feb 2 | 1769997600000 | 1770001200000 | 1770004800000 | 1770008400000 |
| Feb 5 | 1770256800000 | 1770260400000 | 1770264000000 | 1770267600000 |
| Feb 8 | 1770516000000 | 1770519600000 | 1770523200000 | 1770526800000 |
| Feb 11 | 1770775200000 | 1770778800000 | 1770782400000 | 1770786000000 |

计算规则：每天 +86400000ms，每小时 +3600000ms

---

## 命名规范速查

| 数据类型 | 前缀模式 | 示例 |
|---------|---------|------|
| 广告channel | `ad_ch1_{{prefix}}_new` 或 `ad_ch1_{{prefix}}_ret` | ad_ch1_qa19_new |
| 设备channel | `dev_ch1_{{prefix}}_new` 或 `dev_ch1_{{prefix}}_ret` | dev_ch1_qd19_new |
| 账号channel | `usr_ch1_{{prefix}}_new` 或 `usr_ch1_{{prefix}}_ret` | usr_ch1_qu19_new |
| 设备bundle_id | `com.{{prefix}}.d{{N}}.new` 或 `com.{{prefix}}.d{{N}}.ret` | com.qa.d19.new |
| 账号bundle_id | `com.{{prefix}}.u{{N}}.new` 或 `com.{{prefix}}.u{{N}}.ret` | com.qa.u19.new |
| appsflyer_id | `af_{{prefix}}_new` 或 `af_{{prefix}}_ret` | af_qd19_new |
| firebase | `firebase_{{prefix}}_new` 或 `firebase_{{prefix}}_ret` | firebase_qd19_new |
| idfv_c | `idfv_{{prefix}}_new` 或 `idfv_{{prefix}}_ret` | idfv_qd19_new |
| idfa匹配值 | `idfa_{{prefix}}_new` 或 `idfa_{{prefix}}_ret` | idfa_qa19_new |
| anid匹配值 | `anid_{{prefix}}_new` 或 `anid_{{prefix}}_ret` | anid_qd22_new |
| 不匹配值 | `idfa_{{prefix}}_nomatch` | idfa_qb20_nomatch |
| sdid_s | `sdid_{{prefix}}_001` | sdid_qd19_001 |
| user_id | `user_{{prefix}}_001` | user_qu19_001 |

---

## 说明

- 本文件仅放通用广告归因示例。
- 初始口径、初始设备、空设备、`device_initial`、`activation_device_initial` 相关示例，见 `../initial-device-coloring-test-data/examples.md`
