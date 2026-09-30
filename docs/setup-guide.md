# cycling-coach 部署指南

| 项目 | 内容 |
|---|---|
| 文档版本 | v1.4 |
| 更新日期 | 2026-09-29 |
| 适用对象 | 需要独立部署「公路车训练 + 饮食教练」系统的 Intervals.icu 用户 |
| 配套产物 | `doubao-cycling-coach.zip`（技能包）；使用教程见 `docs/user-guide.md` |

---

## 1. 概述

### 1.1 功能特性

`cycling-coach` 是一套基于豆包工作模式的公路车训练与饮食教练系统：

1. **数据自动采集**：Intervals.icu API 自动拉取骑行活动、睡眠、恢复指标（CTL / ATL / TSB / HRV / 静息心率 / 压力值）；
2. **每日训练分析**：按规则（训练量 + 睡眠 + 恢复状态）自动生成当晚训练计划；
3. **强度自动调节**：TSB / 睡眠阈值触发降档或强制减量；
4. **力量与核心课库**：简单器械（哑铃/弹力带/自重）力量训练 + 骑行专项核心训练，恢复达标后自动提醒启动；
5. **每日饮食打卡**：21:00 提醒打卡，教练按实际摄入微调宏量与补给建议（饮食闭环）；
6. **微信推送（PushPlus）**：每日提醒与训练计划推送到微信，排版统一（HTML），每条推送附「今日状态」块，18:00 推送完整报告格式；
7. **数据快照归档**：每日拉取结果自动存 JSON 快照，可追溯、可统计。

### 1.2 架构说明

```
┌─────────────────┐       ┌──────────────────┐       ┌──────────────────────────┐
│  可穿戴设备       │ ───▶ │  Intervals.icu    │ ◀──▶ │  豆包定时任务（每日）      │
│  (Garmin/Wahoo) │ 同步  │  云端数据平台      │  API │  17:00 同步提醒 + 推送    │
└─────────────────┘       └──────────────────┘       │  18:00 训练分析 + 快照    │
                                                     │        + 完整报告推送     │
                                                     │  21:00 饮食打卡 + 推送    │
                                                     └────────┬─────────────────┘
                                                              │ 调度
                                                     ┌────────▼─────────────────┐
                                                     │  fetch_icu.py             │
                                                     │  数据拉取 + JSON 快照      │
                                                     └────────┬─────────────────┘
                                                              │ 推送
                                                     ┌────────▼─────────────────┐
                                                     │  push_pushplus.py         │
                                                     │  PushPlus → 微信          │
                                                     └──────────────────────────┘
```

### 1.3 隐私与安全声明

- 技能包**不包含任何个人数据**；每位部署者独立使用自己的 Intervals.icu 账号；
- API key 属个人凭证，仅存于 `~/.config/intervals_icu/api_key`（权限 600），不得写入聊天记录、日志、定时任务内容或共享文件；
- PushPlus token 仅存于 `~/.config/cycling_coach/pushplus_token`（权限 600），同样不得外泄或写入定时任务内容；
- 训练日志与饮食打卡仅存于本地项目目录。

### 1.4 目录结构

```
cycling-coach/
├── README.md                  # 项目总览
├── LICENSE · CHANGELOG.md     # 许可与版本记录
├── skill/                     # 技能本体（可分发给豆包）
│   ├── SKILL.md               # 工作流 + TSB 解读 + 饮食打卡 + 微信推送 + 安全边界
│   ├── references/            # training / nutrition / workouts（含力量·核心）
│   └── scripts/               # fetch_icu.py（含快照）、calc_zones.py、push_pushplus.py
├── docs/
│   ├── setup-guide.md         # 本文件（部署指南）
│   ├── user-guide.md          # 使用教程
│   └── push-notification.md   # 微信推送格式规范（HTML 模板 / 状态块 / 完整报告）
├── config/
│   ├── api_key.example        # API key 模板
│   └── pushplus_token.example # PushPlus token 模板
├── data/
│   ├── training-log/          # 训练日志（Markdown 归档）
│   ├── diet-log.md            # 每日饮食打卡日志
│   └── raw/                   # 每日 JSON 数据快照
└── tests/test_fetch_icu.py    # 单元测试
```

---

## 2. 前置条件

| 序号 | 条件 | 说明 |
|---|---|---|
| 1 | Intervals.icu 账号 | 免费注册：https://intervals.icu |
| 2 | 设备数据同步 | Garmin / Wahoo 等设备已连接 Intervals.icu，并至少完成一次活动与睡眠同步 |
| 3 | 豆包工作模式 | 手机或电脑端可运行工作 / 办公模式 |
| 4 | 阈值数据（可选） | 建议填写 FTP 或阈值心率；缺失时技能将安排 FTP 测试 |
| 5 | 力量器械（可选） | 启动力量训练时需：可调哑铃 5-20 kg 或弹力带 |

---

## 3. 安装部署

### 3.1 技能安装

1. 打开豆包工作 / 办公模式；
2. 上传 `doubao-cycling-coach.zip`；
3. 输入以下指令并执行：

```
帮我安装并激活这个公路车训练教练技能（zip 内的 doubao-cycling-coach），
按其中的 SKILL.md、references 和 scripts 完整创建，并校验可用。
```

4. 等待技能创建完成，AI 将返回就绪确认。

### 3.2 API 凭据配置

1. 浏览器登录 Intervals.icu，进入 **Settings → Developer Settings**；
2. 点击 **Generate API key**，复制生成的密钥；
3. 在豆包工作模式中执行：

```
我的 Intervals.icu API key 是 <YOUR_API_KEY>，请保存到配置文件
~/.config/intervals_icu/api_key（权限 600），不要打印在对话中。
```

4. 终端手动配置（备用方案）：

```bash
mkdir -p ~/.config/intervals_icu
echo -n '<YOUR_API_KEY>' > ~/.config/intervals_icu/api_key
chmod 600 ~/.config/intervals_icu/api_key
```

> ⚠️ API key 等同训练数据访问权，不得分享或写入公开渠道。

### 3.3 安装验证

- 指令：「拉取我的最新训练数据」，AI 应返回 FTP、最近活动、负荷状态；
- 脚本验证：

```bash
python3 <技能路径>/scripts/fetch_icu.py --days 7
```

预期输出：骑手信息、FTP、最近活动列表、CTL / ATL / TSB 及恢复指标（含压力值，若有数据）。

### 3.4 微信推送配置（PushPlus，可选但推荐）

1. 打开 https://www.pushplus.plus/ 注册并登录，首页获取你的 **token**；
2. 在豆包工作模式中执行：

```
我的 PushPlus token 是 <YOUR_TOKEN>，请保存到配置文件
~/.config/cycling_coach/pushplus_token（权限 600），不要打印在对话中。
```

3. 终端手动配置（备用方案）：

```bash
mkdir -p ~/.config/cycling_coach
echo -n '<YOUR_TOKEN>' > ~/.config/cycling_coach/pushplus_token
chmod 600 ~/.config/cycling_coach/pushplus_token
```

4. 验证推送：

```bash
python3 <技能路径>/scripts/push_pushplus.py "测试" --content "<b>📊 测试</b><br>推送链路正常"
```

微信应能收到消息；推送格式规范见 `docs/push-notification.md`。

> ⚠️ token 等同微信推送权限，不得分享或写入公开渠道；若曾泄露，请在 PushPlus 重置。没有 PushPlus 也不影响核心功能，训练分析与打卡提醒仍在豆包会话内进行。

---

## 4. 定时任务配置

建议配置三个每日任务（时间可按个人作息调整）：

| 任务 | 触发时间 | 功能 |
|---|---|---|
| 同步手表数据提醒 | 每日 17:00 | 提醒同步设备数据至 Intervals.icu，并推送提醒到微信 |
| 每日骑行训练分析 | 每日 18:00 | 拉取最新数据（含 JSON 快照）→ 分析当日状态 → 生成当晚训练计划 → 更新训练日志 → 推送完整报告到微信 |
| 饮食打卡提醒 | 每日 21:00 | 提醒记录当日三餐 / 加餐 / 水分，教练评估并给次日建议，推送提醒到微信 |

配置指令模板：

```
帮我创建三个每天定时任务，并接入 PushPlus 微信推送：
1. 每天 17:00 先拉取最新身体状态，提醒我同步手表/码表数据到 Intervals.icu，
   并用 push_pushplus.py 推送（内容含今日状态块：睡眠/HRV/静息心率/压力 + CTL/ATL/TSB/体重）；
2. 每天 18:00 拉取 Intervals.icu 最新数据，查看当天训练量、睡眠、恢复指标
   （CTL/ATL/TSB、HRV、静息心率、压力值），按规则制定今晚训练计划
   （前一天高强度或睡眠不足 → 恢复骑；TSB < -30 → 强制减量等），
   并输出训练类型、目标区间、时长、热身/主项/冷身、补水补食和理由；
   恢复达标（TSB > -10 且睡眠 ≥6h）时提示启动力量/核心训练；
   用 push_pushplus.py 按完整报告格式推送（状态摘要 → 计划 → 理由 → 补给）；
3. 每天 21:00 先拉取最新身体状态，提醒我按模板打卡三餐、加餐与水分，
   并用 push_pushplus.py 推送（含今日状态块）。
```

> 训练时间在早间或午间的用户，可将 18:00 调整为训练开始前 1-2 小时，21:00 打卡随之调整。

---

## 5. 首次使用指引

1. 执行「帮我做骑手评估，按我的数据算功率 / 心率区间」，完成基线建立；
2. 确认 Intervals.icu 中已填写 FTP 或阈值心率；缺失时按教练安排完成 FTP 测试；
3. 前两周严格按计划执行，**禁止超量**——系统基于 TSB / HRV / 静息心率自动监测疲劳并提示减量；
4. 每晚 21:00 开始饮食打卡，让饮食建议逐步贴合实际；
5. 力量训练在**恢复达标后**（TSB > -10 且连续 2-3 晚睡眠 ≥6h）自动启动，届时系统会提示动作与时间安排；
6. 每周执行「复盘本周训练数据」，对比趋势调整下一周计划。

---

## 6. 故障排查

| 现象 | 可能原因 | 处理方案 |
|---|---|---|
| 认证失败（HTTP 401） | API key 错误或已禁用 | 重新生成 key 并更新本地配置 |
| 数据拉取为空 | 设备未同步活动 | 确认 Intervals.icu 已连接设备并完成至少一次同步 |
| 睡眠 / HRV 缺失 | 设备不支持睡眠监测或未同步 | 检查设备设置；同步后次日数据生效 |
| 压力值缺失 | 设备不支持压力监测 | 不影响使用，其余指标照常评估 |
| 推送收不到（PushPlus） | token 错误/过期/被重置 | 重新获取 token 并更新 `~/.config/cycling_coach/pushplus_token` |
| 推送排版乱 | 使用了 Markdown 换行 | 按 `docs/push-notification.md` 用 HTML 模板（`<br>`/`<b>`/`｜`） |
| 分析时间不符 | 定时任务未按需配置 | 指令调整：将每日分析改至目标时间 |

---

## 7. 安全边界

- **医疗边界**：本技能不提供疾病诊断；出现胸痛、眩晕、异常疲劳应立即停练并就医；
- **营养边界**：不提供极端节食方案，热量底线男性 ≥ 1500 kcal/日；有疾病者先咨询医生或注册营养师；
- **力量边界**：膝盖/腰部不适立即停止；重量宁轻勿重，不做到力竭；
- **数据边界**：API key 与 PushPlus token 属个人凭证，仅存本地配置（权限 600），个人训练数据仅限本人使用，不得外泄。
