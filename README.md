# cycling-coach

公路车训练与饮食教练 · 基于 Intervals.icu 数据的自动化训练管理系统。

一套可部署的「AI 骑行教练」：通过 Intervals.icu API 自动拉取骑行活动、睡眠与
恢复指标（CTL / ATL / TSB / HRV / 静息心率 / 压力值），按科学训练规则生成
每日训练计划（训练类型、目标区间、时长、结构、补给），并依据恢复状态自动
降档或强制减量。

---

## 功能特性

- **数据自动采集**：Intervals.icu API 一键拉取（活动 / 睡眠 / 负荷状态 / 日历计划）
- **科学训练规则**：TSB 解读、恢复指标监测、80/20 极化训练、周期化课表
- **每日自动分析**：定时任务每天生成「数据摘要 → 今晚训练计划 → 理由」
- **饮食配合**：骑行前后补给、日常宏量营养建议
- **训练日志**：Markdown 日志 + JSON 数据快照，可追溯、可统计
- **力量与核心课库**：简单器械力量 + 骑行专项核心，恢复达标自动提醒启动
- **饮食打卡闭环**：21:00 打卡，教练按实际摄入微调建议
- **微信推送**：每日提醒（同步 / 训练计划 / 打卡）通过 PushPlus 推送到微信，18:00 推送完整报告格式（状态摘要 + 计划 + 理由）

## 目录结构

```
cycling-coach/
├── README.md                  # 项目总览（本文件）
├── LICENSE                    # 开源许可（MIT）
├── CHANGELOG.md               # 版本变更记录
├── skill/                     # 技能本体（可分发给豆包，运行时部署于 .user_skills/）
│   ├── SKILL.md               # 教练工作流 + TSB 解读 + 安全边界
│   ├── references/            # 训练科学 / 营养 / 课库
│   └── scripts/               # fetch_icu.py 取数、calc_zones.py 算区间
├── docs/
│   ├── setup-guide.md         # 部署指南（技术文档）
│   └── user-guide.md          # 使用教程
├── config/
│   └── api_key.example        # API key 配置模板（勿提交真实 key）
├── data/
│   ├── training-log/          # 训练日志（Markdown 归档）
│   ├── diet-log.md            # 每日饮食打卡日志
│   └── raw/                   # 每日 JSON 数据快照（自动生成）
└── tests/
    └── test_fetch_icu.py      # 取数脚本纯函数单元测试
```

## 快速开始

```bash
# 1. 配置 API key（在 intervals.icu → Settings → Developer Settings 生成）
cp config/api_key.example ~/.config/intervals_icu/api_key
chmod 600 ~/.config/intervals_icu/api_key
# 编辑 ~/.config/intervals_icu/api_key 填入真实 key

# 2. 部署技能到豆包运行时
cp -r skill/ ~/.doubao/agent_mode/workspace/.user_skills/doubao-cycling-coach/

# 3. 验证取数
python3 skill/scripts/fetch_icu.py --days 7

# 4. 配置定时任务（详见 docs/setup-guide.md 第 4 节）
```

## 运行时与仓库的关系

| 位置 | 角色 | 说明 |
|---|---|---|
| `cycling-coach/skill/` | 发布形态（源码） | Git 管理，可归档/分享 |
| `~/.doubao/agent_mode/workspace/.user_skills/doubao-cycling-coach/` | 部署形态（运行时） | 定时任务引用；技能迭代后用 `cp -r skill/ <运行时路径>/` 同步 |

## 使用教程

（详见 [user-guide.md](/docs/user-guide.md)）


## 版本

当前版本：v1.6.3（详见 [CHANGELOG.md](CHANGELOG.md)）

## 许可

[MIT](LICENSE)

## 安全声明

- API key 等同训练数据访问权，仅存于 `~/.config/intervals_icu/api_key`（权限 600），
  不得写入聊天记录、日志、定时任务内容或任何分享文件；
- 本技能不提供医疗诊断；出现胸痛、眩晕、异常疲劳应立即停练并就医。
