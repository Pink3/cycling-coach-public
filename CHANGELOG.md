# 变更记录

## [v1.6.3] - 2026-09-29

### 更新
- `docs/setup-guide.md` v1.4：新增 PushPlus 微信推送配置（3.4 节）、架构图、目录结构、推送故障排查
- `docs/user-guide.md` v1.1：新增「如何读微信推送」（今日状态块含义 + 完整报告三段式解读）
- 新增 `config/pushplus_token.example` 模板

## [v1.6.2] - 2026-09-29

### 新增
- 推送格式规范文档 `docs/push-notification.md`（HTML 模板 / 今日状态块 / 完整报告三段式）
- SKILL.md 增加「微信推送（PushPlus）」小节，引用推送规范

### 变更
- 18:00 定时任务推送升级为完整报告格式：一、当天状态摘要 → 二、今晚训练计划 → 三、决策理由 → 补给，对齐豆包内完整报告结构

## [v1.6.0] - 2026-09-29

### 变更
- 推送排版统一：push_pushplus.py 增加 --template 参数（默认 html），微信渲染整齐
- 三个定时任务（17:00 / 18:00 / 21:00）推送前先拉取最新身体状态，每条推送均含「📊 今日状态」块（两行：睡眠/HRV/静息心率/压力 + CTL/ATL/TSB/体重），缺失项标 "—"

## [v1.5.0] - 2026-09-29

### 新增
- PushPlus 微信推送：`scripts/push_pushplus.py`（token 存 ~/.config/cycling_coach/pushplus_token）
- 三个定时任务（17:00 同步提醒 / 18:00 训练分析 / 21:00 饮食打卡）接入 PushPlus 推送

## [v1.4.1] - 2026-09-29

### 移除
- Server酱微信推送：删除 `scripts/push_wechat.py`、SendKey 本地配置（~/.config/cycling_coach/sendkey）
- 三个定时任务（17:00 / 18:00 / 21:00）移除微信推送步骤，恢复豆包会话内提醒

## [v1.4.0] - 2026-09-29

### 新增
- 微信推送：`scripts/push_wechat.py`（Server酱封装，SendKey 存 ~/.config/cycling_coach/sendkey）
- 三个定时任务（17:00 同步提醒 / 18:00 训练分析 / 21:00 饮食打卡）均接入微信推送

## [v1.3.0] - 2026-09-29

### 新增
- 使用教程 `docs/user-guide.md`：每日流程、计划执行、饮食打卡、力量训练、指令速查、FAQ
- 部署指南升级 v1.3：新增 21:00 饮食打卡任务、力量/核心课库、数据快照、压力值说明

## [v1.2.1] - 2026-09-29

### 变更
- SKILL.md 新增「每日饮食打卡」节：打卡文件、时机、评估口径、应用方式
- 工作流第 6 步（饮食配合）纳入打卡闭环：按实际摄入微调建议

## [v1.2.0] - 2026-09-29

### 新增
- 每日饮食打卡闭环：`data/diet-log.md`（宏量目标速查 + 打卡模板 + 逐日记录）
- 定时任务：每天 21:00 饮食打卡提醒

## [v1.1.0] - 2026-09-29

### 新增
- 力量训练课库（workouts.md 第 11 节：简单器械力量）
- 核心训练课库（workouts.md 第 12 节：骑行专项核心）
- 定时任务增加恢复达标自动提醒力量训练逻辑（TSB > -10 且睡眠 ≥6h）

## [v1.0.0] - 2026-09-29

### 新增
- 项目正规化：目录结构标准化（skill / docs / config / data / tests 分离）
- Git 版本管理 + MIT 开源许可
- 单元测试（tests/test_fetch_icu.py）：取数脚本纯函数测试
- 数据快照：fetch_icu.py 新增 `--snapshot` 参数，每日自动归档 JSON
- 配置模板（config/api_key.example）与 .gitignore 敏感信息保护

### 变更
- 项目命名：doubao-cycling-coach → cycling-coach（发布名）
- 训练日志归位：`data/training-log/training-log.md`
- 部署指南规范化：`docs/setup-guide.md`（技术文档 v1.1）
- fetch_icu.py：wellness 增加 `stress`（压力值）字段
