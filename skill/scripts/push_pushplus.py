#!/usr/bin/env python3
"""通过 PushPlus 推送消息到微信。

用法：
    python3 push_pushplus.py "今晚训练计划" --content "**VO2max 4×4m**\n\n- 时长 75min\n- 18:15 开骑"
    PUSHPLUS_TOKEN=xxxx python3 push_pushplus.py "标题" --content "正文"

token 来源（按优先级）：
1. 环境变量 PUSHPLUS_TOKEN
2. 配置文件 ~/.config/cycling_coach/pushplus_token（推荐，权限 600）

安全：token 等同微信推送权限，绝不写入聊天记录、日志或分享文件。
"""
import argparse
import json
import os
import sys
import urllib.request

CONFIG = os.path.expanduser("~/.config/cycling_coach/pushplus_token")
API = "http://www.pushplus.plus/send"


def get_token():
    tok = os.environ.get("PUSHPLUS_TOKEN", "").strip()
    if not tok and os.path.isfile(CONFIG):
        with open(CONFIG, "r", encoding="utf-8") as f:
            tok = f.read().strip()
    if not tok:
        sys.exit(
            "缺少 PushPlus token：请设置环境变量 PUSHPLUS_TOKEN，"
            "或写入 ~/.config/cycling_coach/pushplus_token（在 pushplus.plus 获取）。"
        )
    return tok


def push(title, content="", template="markdown"):
    tok = get_token()
    body = json.dumps({
        "token": tok,
        "title": title[:100],
        "content": content,
        "template": template,
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        API,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "cycling-coach/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit(f"推送失败（HTTP {e.code}）：{e.read().decode('utf-8', 'ignore')[:200]}")
    except urllib.error.URLError as e:
        sys.exit(f"网络错误：{e.reason}")
    if result.get("code") != 200:
        sys.exit(f"推送失败：{result.get('msg')}")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="PushPlus 微信推送")
    ap.add_argument("title", help="消息标题")
    ap.add_argument("--content", default="", help="正文（默认 HTML，可空）")
    ap.add_argument("--template", default="html", choices=["html", "markdown", "txt"], help="模板类型（默认 html，微信渲染最稳定）")
    args = ap.parse_args()
    push(args.title, args.content, args.template)
    print("已推送到微信")
