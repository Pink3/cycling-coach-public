#!/usr/bin/env python3
"""公路车训练教练：功率/心率区间与宏量营养目标计算器。

用法示例：
    python3 calc_zones.py --ftp 250 --lthr 172 --weight 70 --level medium --goal maintain
    python3 calc_zones.py --ftp 250                       # 只算功率区间
    python3 calc_zones.py --lthr 172                      # 只算心率区间
    python3 calc_zones.py --ftp 240 --weight 72 --level high --goal lose

参数：
    --ftp     FTP（阈值功率，瓦特），可选
    --lthr    阈值心率（bpm），可选
    --weight  体重（kg），可选，计算营养时必填
    --level   训练强度：low / medium / high（低/中/高训练负荷日），默认 medium
    --goal    目标：maintain / lose / gain（维持/减重/增肌），默认 maintain
    --json    输出 JSON 格式
"""
import argparse
import json
import sys

POWER_ZONES = [
    ("Z1 恢复",      0.00, 0.55),
    ("Z2 耐力",      0.56, 0.75),
    ("Z3 节奏",      0.76, 0.90),
    ("Z4 阈值",      0.91, 1.05),
    ("Z5 VO2max",    1.06, 1.20),
    ("Z6 无氧",      1.21, 1.50),
    ("Z7 冲刺",      1.51, 9.99),
]

HR_ZONES = [
    ("Z1 恢复",   0.00, 0.80),
    ("Z2 耐力",   0.81, 0.89),
    ("Z3 节奏",   0.90, 0.93),
    ("Z4 阈值",   0.94, 0.99),
    ("Z5 VO2max", 1.00, 9.99),
]

# 碳水 g/kg/天、蛋白质 g/kg/天（按训练负荷与目标）
CARB = {"low": 4.0, "medium": 6.0, "high": 8.0}
PROTEIN = {
    "maintain": (1.4, 1.6),
    "lose":     (1.8, 2.0),
    "gain":     (1.8, 2.2),
}
FAT_PCT = (0.20, 0.35)


def compute_power_zones(ftp: float):
    if ftp <= 0:
        raise ValueError("FTP 必须为正数")
    return {name: (round(ftp * lo), round(ftp * hi)) for name, lo, hi in POWER_ZONES}


def compute_hr_zones(lthr: float):
    if lthr <= 0:
        raise ValueError("LTHR 必须为正数")
    return {name: (round(lthr * lo), round(lthr * hi)) for name, lo, hi in HR_ZONES}


def compute_macros(weight: float, level: str, goal: str):
    if weight <= 0:
        raise ValueError("体重必须为正数")
    if level not in CARB:
        raise ValueError(f"level 必须是 {list(CARB)} 之一")
    if goal not in PROTEIN:
        raise ValueError(f"goal 必须是 {list(PROTEIN)} 之一")

    carb_g = round(weight * CARB[level])
    p_lo, p_hi = PROTEIN[goal]
    protein_g = (round(weight * p_lo), round(weight * p_hi))
    # 热量估算：碳水4 + 蛋白4 kcal/g；脂肪按总热量 20-35% 反推
    base_kcal = carb_g * 4 + sum(protein_g) * 2  # 用蛋白均值粗估
    fat_lo = round(base_kcal * FAT_PCT[0] / 9)
    fat_hi = round(base_kcal * FAT_PCT[1] / 9)
    kcal_lo = carb_g * 4 + protein_g[0] * 4 + fat_lo * 9
    kcal_hi = carb_g * 4 + protein_g[1] * 4 + fat_hi * 9
    return {
        "碳水(g/天)": carb_g,
        "蛋白质(g/天)": protein_g,
        "脂肪(g/天)": (fat_lo, fat_hi),
        "估算热量(kcal/天)": (kcal_lo, kcal_hi),
    }


def main():
    ap = argparse.ArgumentParser(description="公路车训练教练：区间与营养计算")
    ap.add_argument("--ftp", type=float, help="FTP（瓦特）")
    ap.add_argument("--lthr", type=float, help="阈值心率（bpm）")
    ap.add_argument("--weight", type=float, help="体重（kg）")
    ap.add_argument("--level", default="medium", choices=sorted(CARB), help="训练负荷日")
    ap.add_argument("--goal", default="maintain", choices=sorted(PROTEIN), help="目标")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    if not args.ftp and not args.lthr:
        ap.error("至少需要 --ftp 或 --lthr 之一")

    result = {"功率区间": None, "心率区间": None, "营养目标": None}
    try:
        if args.ftp:
            result["功率区间"] = compute_power_zones(args.ftp)
        if args.lthr:
            result["心率区间"] = compute_hr_zones(args.lthr)
        if args.weight:
            result["营养目标"] = compute_macros(args.weight, args.level, args.goal)
    except ValueError as e:
        print(f"输入错误：{e}", file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    def fmt_zones(zones):
        lines = []
        for name, (lo, hi) in zones.items():
            hi_txt = f"{hi}" if hi < 9999 else "上限"
            lines.append(f"  {name:<10} {lo}-{hi_txt}")
        return "\n".join(lines)

    out = []
    if result["功率区间"]:
        out.append(f"功率区间（基于 FTP {args.ftp:.0f}W，Coggan）：\n" + fmt_zones(result["功率区间"]))
    if result["心率区间"]:
        out.append(f"心率区间（基于 LTHR {args.lthr:.0f}bpm）：\n" + fmt_zones(result["心率区间"]))
    if result["营养目标"]:
        n = result["营养目标"]
        out.append(
            f"每日营养目标（{args.weight:.0f}kg，{args.level} 负荷日，目标：{args.goal}）：\n"
            f"  碳水：{n['碳水(g/天)']} g/天\n"
            f"  蛋白质：{n['蛋白质(g/天)'][0]}-{n['蛋白质(g/天)'][1]} g/天\n"
            f"  脂肪：{n['脂肪(g/天)'][0]}-{n['脂肪(g/天)'][1]} g/天\n"
            f"  估算热量：{n['估算热量(kcal/天)'][0]}-{n['估算热量(kcal/天)'][1]} kcal/天"
        )
    print("\n\n".join(out))


if __name__ == "__main__":
    main()
