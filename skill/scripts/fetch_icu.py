#!/usr/bin/env python3
"""通过 Intervals.icu API 自动获取骑手的真实训练数据。

拉取内容：
- 骑手资料与阈值（profile + sport-settings）：FTP、阈值心率、体重、最大/静息心率
- 最近活动（activities）：距离、时长、TSS、NP、IF、平均功率等
- 负荷状态（wellness）：CTL / ATL / TSB / rampRate / 体重 / 静息心率
- 可选：日历上的计划训练（events）

认证：Basic，用户名固定为 API_KEY，密码是你的 API key（在 intervals.icu → Settings →
Developer Settings 生成）。路径中的 athlete id 用 0 表示"API key 归属的骑手本人"。

用法示例：
    INTERVALS_ICU_API_KEY=xxxx python3 fetch_icu.py --days 14
    python3 fetch_icu.py --api-key xxxx --athlete-id 0 --days 30 --events --json

参数：
    --api-key     API key（更推荐用环境变量 INTERVALS_ICU_API_KEY，避免留在命令行历史）
    --athlete-id  Athlete id，默认 0（API key 本人）
    --days        拉取最近 N 天活动，默认 14
    --oldest      起始日期 YYYY-MM-DD（与 --days 互斥）
    --newest      结束日期 YYYY-MM-DD，默认今天
    --limit       活动条数上限，默认 50
    --no-wellness 不拉取负荷状态
    --events      额外拉取未来 14 天日历计划
    --json        输出 JSON 格式
    --base-url    测试用，覆盖 API 基地址
    --timeout     请求超时秒数，默认 30

安全：脚本永不输出 API key；请用环境变量或 --api-key 传入，不要把 key 写进聊天记录。
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta

DEFAULT_BASE = "https://intervals.icu/api/v1"
USER_AGENT = "doubao-cycling-coach/1.0"
WELLNESS_FIELDS = "id,ctl,atl,rampRate,weight,restingHR,hrv,sleepSecs,vo2max,stress"


def get_creds(args):
    api_key = args.api_key or os.environ.get("INTERVALS_ICU_API_KEY")
    if not api_key:
        # 兜底：本地配置文件（供定时任务等场景使用，避免把 key 写进命令行或任务内容）
        cfg = os.path.expanduser("~/.config/intervals_icu/api_key")
        if os.path.isfile(cfg):
            with open(cfg, "r", encoding="utf-8") as f:
                api_key = f.read().strip()
    if not api_key:
        sys.exit(
            "缺少 API key：请设置环境变量 INTERVALS_ICU_API_KEY，或写入 ~/.config/intervals_icu/api_key，"
            "或用 --api-key 传入（在 intervals.icu → Settings → Developer Settings 生成）。"
        )
    athlete_id = args.athlete_id or os.environ.get("INTERVALS_ICU_ATHLETE_ID") or "0"
    return athlete_id, api_key


def build_headers(api_key):
    token = base64.b64encode(f"API_KEY:{api_key}".encode("utf-8")).decode("ascii")
    return {
        "Authorization": f"Basic {token}",
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }


def api_get(base, path, params, headers, timeout):
    url = base + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            sys.exit("认证失败（401）：API key 无效或已被禁用，请检查后重试。")
        if e.code == 403:
            sys.exit("访问被拒绝（403）：该 key 无权访问此数据。")
        if e.code == 429:
            sys.exit("请求过于频繁（429）：被限流，请稍后重试。")
        sys.exit(f"API 请求失败（HTTP {e.code}）：{path}")
    except urllib.error.URLError as e:
        sys.exit(f"网络错误：无法连接 {base}（{e.reason}）。请检查网络或 --base-url。")


def extract_thresholds(profile, sport_settings):
    """从 profile 与 sport-settings 中提取阈值信息（防御式解析）。"""
    info = {}
    # profile 返回 {"athlete": {...}, ...}，先解包
    src = profile.get("athlete") if isinstance(profile, dict) and isinstance(profile.get("athlete"), dict) else profile
    for key in ("id", "name", "weight", "maxHR", "restingHR", "vo2max"):
        if isinstance(src, dict) and key in src and src[key] is not None:
            info[key] = src[key]
    CYCLE_TYPES = ("ride", "virtualride", "mountainbikeride", "gravelride", "trackride", "cyclocross", "bike", "bicycle")
    ftp, lthr, max_hr = None, None, None
    sports = sport_settings if isinstance(sport_settings, list) else [sport_settings]
    for s in sports:
        if not isinstance(s, dict):
            continue
        types = {str(t).lower() for t in (s.get("types") or [])}
        id_s = str(s.get("id") or s.get("type") or s.get("sport") or "").lower()
        is_cycle = bool(types & set(CYCLE_TYPES)) or any(k in id_s for k in ("cycl", "ride", "bike"))
        if is_cycle:
            ftp = s.get("ftp") or s.get("eftp") or ftp
            lthr = s.get("lthr") or lthr
            max_hr = s.get("max_hr") or s.get("maxHR") or max_hr
    info["ftp"] = ftp
    info["lthr"] = lthr
    if max_hr is not None and "maxHR" not in info:
        info["maxHR"] = max_hr
    return info


def fmt_activities(acts):
    rows = []
    for a in acts:
        if not isinstance(a, dict):
            continue
        date_s = (a.get("start_date_local") or "")[:10]
        name = (a.get("name") or "未命名")[:18]
        dist_km = round(a["distance"] / 1000, 1) if a.get("distance") else None
        minutes = round(a["moving_time"] / 60) if a.get("moving_time") else None
        rows.append({
            "date": date_s,
            "type": a.get("type") or "",
            "name": name,
            "distance_km": dist_km,
            "minutes": minutes,
            "load": a.get("icu_training_load"),
            "np": a.get("icu_weighted_avg_watts"),
            "if": round(a["icu_intensity"] / 100, 2) if a.get("icu_intensity") is not None else None,
            "avg_power": a.get("icu_average_watts"),
            "avg_hr": a.get("average_heartrate"),
        })
    return rows


def interpret_tsb(tsb):
    if tsb is None:
        return None
    if tsb > 25:
        return "过渡/减载期，适合安排恢复周"
    if tsb >= 15:
        return "状态新鲜，接近比赛窗口"
    if tsb >= 5:
        return "灰色地带，可做高质量课"
    if tsb >= -10:
        return "最佳训练区，可承受有效训练刺激"
    if tsb >= -30:
        return "过度训练（计划内可接受，不超过 2 周）"
    return "高风险区，应立即减量并加强恢复"


def interpret_ramp(ramp):
    if ramp is None:
        return None
    if ramp < 3:
        return "维持或轻微减训"
    if ramp <= 5:
        return "保守积累（推荐）"
    if ramp <= 7:
        return "积极积累（有经验者，需密切监测）"
    return "增长过快，受伤风险高"


def fmt_wellness(wl):
    """从 wellness 数据中提取最新负荷快照。"""
    if not wl:
        return None
    latest = wl[-1] if isinstance(wl, list) else wl
    ctl = latest.get("ctl")
    atl = latest.get("atl")
    tsb = round(ctl - atl, 1) if ctl is not None and atl is not None else None
    return {
        "date": latest.get("id"),
        "ctl": ctl,
        "atl": atl,
        "tsb": tsb,
        "rampRate": latest.get("rampRate"),
        "weight": latest.get("weight"),
        "restingHR": latest.get("restingHR"),
        "hrv": latest.get("hrv"),
        "sleepSecs": latest.get("sleepSecs"),
        "stress": latest.get("stress"),
        "vo2max": latest.get("vo2max"),
    }


def fmt_events(events):
    rows = []
    for e in events or []:
        if not isinstance(e, dict):
            continue
        rows.append({
            "date": (e.get("start_date_local") or "")[:10],
            "category": e.get("category") or "",
            "type": e.get("type") or "",
            "name": e.get("name") or "",
            "description": (e.get("description") or "")[:60],
        })
    return rows


def render(result):
    lines = []
    p = result.get("profile") or {}
    lines.append(f"骑手：{p.get('name') or '未知'}（id {p.get('id') or '?'}）")
    ftp = p.get("ftp")
    lthr = p.get("lthr")
    if ftp:
        lines.append(f"FTP：{ftp} W")
    else:
        lines.append("FTP：未在 Intervals.icu 中设置（可在设置页填写后重跑）")
    if lthr:
        lines.append(f"阈值心率：{lthr} bpm")
    for key, label in (("weight", "体重"), ("maxHR", "最大心率"), ("restingHR", "静息心率"), ("vo2max", "VO2max")):
        if p.get(key) is not None:
            unit = " kg" if key == "weight" else ""
            lines.append(f"{label}：{p[key]}{unit}")

    acts = result.get("activities") or []
    lines.append("")
    lines.append(f"【最近活动】共 {len(acts)} 条")
    if acts:
        header = f"{'日期':<12}{'类型':<10}{'名称':<20}{'距离km':>7}{'时长min':>8}{'负荷':>6}{'NP':>6}{'IF':>5}{'均功':>6}"
        lines.append(header)
        for r in acts:
            dist = f"{r['distance_km']}" if r["distance_km"] is not None else "-"
            mins = f"{r['minutes']}" if r["minutes"] is not None else "-"
            load = f"{r['load']}" if r["load"] is not None else "-"
            np = f"{r['np']}" if r["np"] is not None else "-"
            if_ = f"{r['if']}" if r["if"] is not None else "-"
            avg = f"{r['avg_power']}" if r["avg_power"] is not None else "-"
            lines.append(f"{r['date']:<12}{r['type']:<10}{r['name']:<20}{dist:>7}{mins:>8}{load:>6}{np:>6}{if_:>5}{avg:>6}")
    else:
        lines.append("（该时间范围内没有活动记录）")

    w = result.get("wellness")
    if w:
        lines.append("")
        tsb_txt = f"{w['tsb']}（{interpret_tsb(w['tsb'])}）" if w.get("tsb") is not None else "无数据"
        ramp_txt = f"{w['rampRate']}（{interpret_ramp(w['rampRate'])}）" if w.get("rampRate") is not None else "无数据"
        lines.append(f"【负荷状态】截至 {w.get('date') or '最新'}")
        lines.append(f"CTL（适应度）：{w.get('ctl')} | ATL（疲劳）：{w.get('atl')} | TSB（状态）：{tsb_txt}")
        lines.append(f"CTL 周变化（rampRate）：{ramp_txt}")
        extra = []
        if w.get("weight") is not None:
            extra.append(f"体重 {w['weight']}kg")
        if w.get("restingHR") is not None:
            extra.append(f"静息心率 {w['restingHR']}")
        if w.get("hrv") is not None:
            extra.append(f"HRV {w['hrv']}")
        if w.get("sleepSecs") is not None:
            extra.append(f"睡眠 {round(w['sleepSecs'] / 3600, 1)}h")
        if w.get("stress") is not None:
            extra.append(f"压力值 {w['stress']}")
        if extra:
            lines.append("恢复指标：" + " | ".join(extra))

    evs = result.get("events")
    if evs is not None:
        lines.append("")
        if evs:
            lines.append("【日历计划】未来安排：")
            for e in evs:
                lines.append(f"  {e['date']} [{e['category']}] {e['name']}（{e['type']}） {e['description']}".rstrip())
        else:
            lines.append("【日历计划】未来 14 天无计划训练")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Intervals.icu 训练数据自动获取")
    ap.add_argument("--api-key", help="API key（建议用环境变量 INTERVALS_ICU_API_KEY）")
    ap.add_argument("--athlete-id", help="Athlete id，默认 0（API key 本人）")
    ap.add_argument("--days", type=int, default=14, help="最近 N 天活动，默认 14")
    ap.add_argument("--oldest", help="起始日期 YYYY-MM-DD")
    ap.add_argument("--newest", help="结束日期 YYYY-MM-DD，默认今天")
    ap.add_argument("--limit", type=int, default=50, help="活动条数上限，默认 50")
    ap.add_argument("--no-wellness", action="store_true", help="不拉取负荷状态")
    ap.add_argument("--events", action="store_true", help="拉取未来 14 天日历计划")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--snapshot", metavar="DIR", help="将拉取结果另存 JSON 快照到指定目录（文件名：<日期>.json）")
    ap.add_argument("--base-url", default=DEFAULT_BASE, help="API 基地址（默认官方）")
    ap.add_argument("--timeout", type=int, default=30, help="请求超时秒数")
    args = ap.parse_args()

    athlete_id, api_key = get_creds(args)
    headers = build_headers(api_key)

    if args.oldest:
        oldest = args.oldest
    else:
        oldest = (date.today() - timedelta(days=max(1, args.days - 1))).isoformat()
    newest = args.newest or date.today().isoformat()

    result = {}
    result["profile"] = extract_thresholds(
        api_get(args.base_url, f"/athlete/{athlete_id}/profile", {}, headers, args.timeout),
        api_get(args.base_url, f"/athlete/{athlete_id}/sport-settings", {}, headers, args.timeout),
    )

    params = {"oldest": oldest, "newest": newest, "limit": args.limit}
    acts = api_get(args.base_url, f"/athlete/{athlete_id}/activities", params, headers, args.timeout)
    result["activities"] = fmt_activities(acts if isinstance(acts, list) else [])

    if not args.no_wellness:
        wl = api_get(
            args.base_url, f"/athlete/{athlete_id}/wellness",
            {"oldest": oldest, "newest": newest, "fields": WELLNESS_FIELDS}, headers, args.timeout,
        )
        result["wellness"] = fmt_wellness(wl)

    if args.events:
        ev_oldest = date.today().isoformat()
        ev_newest = (date.today() + timedelta(days=14)).isoformat()
        events = api_get(
            args.base_url, f"/athlete/{athlete_id}/events",
            {"oldest": ev_oldest, "newest": ev_newest}, headers, args.timeout,
        )
        result["events"] = fmt_events(events)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(result))

    if args.snapshot:
        os.makedirs(args.snapshot, exist_ok=True)
        snap = {
            "saved_at": date.today().isoformat(),
            "profile": result.get("profile"),
            "activities": result.get("activities"),
            "wellness": result.get("wellness"),
            "events": result.get("events"),
        }
        path = os.path.join(args.snapshot, f"{date.today().isoformat()}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snap, f, ensure_ascii=False, indent=2)
        print(f"\n[快照] 已保存：{path}")


if __name__ == "__main__":
    main()
