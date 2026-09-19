# -*- coding: utf-8 -*-
"""
城邦争夺分数计算器 (City-State Contest Score Calculator)
=========================================================
复刻 MPDLL CvDiplomacyAI::GetBestApproachTowardsMinorCiv 的权重逻辑，
计算「每个大文明领袖 × 每个城邦」的争夺分数（FRIENDLY + PROTECTIVE 权重之和）。

数据来源（全部直接从 Civ5 数据库读取，SP 模组加载后的最终值）:
  - Defines 表           : 49 个 MINOR_APPROACH_* 权重常量（含 SP 覆盖值）
  - Leaders              : 领袖列表
  - Civilization_Leaders : 文明 -> 领袖映射
  - Leader_Flavors       : 领袖倾向数值（38 种 flavor）
  - Leader_MinorCivApproachBiases : 领袖对城邦各 approach 的个性偏置
  - Leader_Traits/Traits : 领袖城邦相关 trait 修正（友谊/加成/战斗）
  - MinorCivilizations   : 城邦列表（原生 trait + SP V11 UAType）
  - MinorCivilization_Flavors : 城邦原生 flavor
  - CityStateUAs         : SP V11 城邦 UA 映射

城邦「争夺倾向」（CSUA 收益方向）是正在设计的新数据，通过 CSV 提供，
未提供时使用内置默认值（按各城邦 UA 的实际收益方向）。

用法:
  python cs_contest_calculator.py [--db 路径] [--csv 城邦倾向.csv] [--strategy DIPLO|CULTURE|CONQUEST|SCIENCE|ALL] [--out 报告.html]
"""

import sys
import os
import csv
import json
import argparse
import sqlite3

# 终端输出统一 UTF-8（Windows 下避免 GBK 乱码）
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# =====================================================================
# 倾向维度：把 38 种 flavor 聚合到 7 个玩法倾向维度
# =====================================================================
DIMENSION_FLAVORS = {
    "CULTURE":   ["FLAVOR_CULTURE", "FLAVOR_GREAT_PEOPLE", "FLAVOR_WONDER", "FLAVOR_ARCHAEOLOGY"],
    "SCIENCE":   ["FLAVOR_SCIENCE", "FLAVOR_SPACESHIP"],
    "MILITARY":  ["FLAVOR_OFFENSE", "FLAVOR_DEFENSE", "FLAVOR_CITY_DEFENSE",
                  "FLAVOR_MILITARY_TRAINING", "FLAVOR_RANGED", "FLAVOR_MOBILE",
                  "FLAVOR_AIR", "FLAVOR_NAVAL", "FLAVOR_NAVAL_RECON", "FLAVOR_NUKE", "FLAVOR_RECON"],
    "GOLD":      ["FLAVOR_GOLD", "FLAVOR_I_LAND_TRADE_ROUTE", "FLAVOR_I_SEA_TRADE_ROUTE",
                  "FLAVOR_I_TRADE_ORIGIN", "FLAVOR_I_TRADE_DESTINATION", "FLAVOR_WATER_CONNECTION"],
    "RELIGION":  ["FLAVOR_RELIGION"],
    "GROWTH":    ["FLAVOR_GROWTH", "FLAVOR_EXPANSION", "FLAVOR_HAPPINESS",
                  "FLAVOR_PRODUCTION", "FLAVOR_INFRASTRUCTURE", "FLAVOR_TILE_IMPROVEMENT"],
    "DIPLOMACY": ["FLAVOR_DIPLOMACY", "FLAVOR_ESPIONAGE"],
}
DIMENSIONS = list(DIMENSION_FLAVORS.keys())

# =====================================================================
# 城邦「争夺倾向」默认值（CSUA 收益方向，0-10）。CSV 可覆盖。
# =====================================================================
DEFAULT_CS_INCLINATION = {
    "MINOR_CIV_ZURICH":      {"SCIENCE": 10, "CULTURE": 3},              # 科技伟人点
    "MINOR_CIV_ANTWERP":     {"GOLD": 10, "GROWTH": 2},                   # 商人伟人点
    "MINOR_CIV_FLORENCE":    {"CULTURE": 8, "RELIGION": 6},               # 信仰购伟人
    "MINOR_CIV_MALACCA":     {"GOLD": 7, "GROWTH": 6},                    # 奢侈快乐
    "MINOR_CIV_PANAMA_CITY": {"GOLD": 10, "GROWTH": 3},                   # 贸易路线
    "MINOR_CIV_BRUSSELS":    {"CULTURE": 10, "GOLD": 3},                  # 音乐家
    "MINOR_CIV_COLOMBO":     {"GOLD": 8, "GROWTH": 4},                    # 到城邦贸易路线
    "MINOR_CIV_HONG_KONG":   {"GOLD": 8, "GROWTH": 6},                    # Dubai UA: 金币捐赠
    "MINOR_CIV_VALLETTA":    {"MILITARY": 10, "GROWTH": 2},               # 军事围城
}

# =====================================================================
# 中文城邦名 -> MinorCiv Type 映射（Civ5DebugDatabase 无本地化表，手工维护）
# =====================================================================
CN_NAME_TO_TYPE = {
    "波哥大": "MINOR_CIV_BOGOTA", "布拉迪斯拉发": "MINOR_CIV_BRATISLAVA",
    "布鲁塞尔": "MINOR_CIV_BRUSSELS", "布加勒斯特": "MINOR_CIV_BUCHAREST",
    "布宜诺斯艾利斯": "MINOR_CIV_BUENOS_AIRES", "佛罗伦萨": "MINOR_CIV_FLORENCE",
    "喀布尔": "MINOR_CIV_KABUL", "基辅": "MINOR_CIV_KIEV",
    "吉隆坡": "MINOR_CIV_KUALA_LUMPUR", "克孜勒": "MINOR_CIV_KYZYL",
    "米兰": "MINOR_CIV_MILAN", "摩纳哥": "MINOR_CIV_MONACO",
    "布拉格": "MINOR_CIV_PRAGUE", "埃里温": "MINOR_CIV_YEREVAN",
    "比布鲁斯": "MINOR_CIV_BYBLOS", "开普敦": "MINOR_CIV_CAPE_TOWN",
    "马尼拉": "MINOR_CIV_MANILA", "摩加迪沙": "MINOR_CIV_MOGADISHU",
    "蒙巴萨": "MINOR_CIV_MOMBASA", "霍尔木兹": "MINOR_CIV_ORMUS",
    "巴拿马": "MINOR_CIV_PANAMA_CITY", "魁北克": "MINOR_CIV_QUEBEC_CITY",
    "拉古萨": "MINOR_CIV_RAGUSA", "里加": "MINOR_CIV_RIGA",
    "悉尼": "MINOR_CIV_SYDNEY", "乌尔": "MINOR_CIV_UR",
    "温哥华": "MINOR_CIV_VANCOUVER", "惠灵顿": "MINOR_CIV_WELLINGTON",
    "塔那那利佛": "MINOR_CIV_ANTANANARIVO", "安特卫普": "MINOR_CIV_ANTWERP",
    "卡霍基亚": "MINOR_CIV_CAHOKIA", "科伦坡": "MINOR_CIV_COLOMBO",
    "迪拜": "MINOR_CIV_DUBAI", "热那亚": "MINOR_CIV_GENOA",
    "马六甲": "MINOR_CIV_MALACCA", "墨尔本": "MINOR_CIV_MELBOURNE",
    "撒马尔罕": "MINOR_CIV_SAMARKAND", "新加坡": "MINOR_CIV_SINGAPORE",
    "推罗": "MINOR_CIV_TYRE", "维尔纽斯": "MINOR_CIV_VILNIUS",
    "桑给巴尔": "MINOR_CIV_ZANZIBAR", "苏黎世": "MINOR_CIV_ZURICH",
    "日内瓦": "MINOR_CIV_GENEVA", "伊费": "MINOR_CIV_IFE",
    "耶路撒冷": "MINOR_CIV_JERUSALEM", "加德满都": "MINOR_CIV_KATHMANDU",
    "拉本塔": "MINOR_CIV_LA_VENTA", "甘托克": "MINOR_CIV_GANGTOK",
    "梵蒂冈": "MINOR_CIV_VATICAN_CITY", "维滕贝格": "MINOR_CIV_WITTENBERG",
    "阿拉木图": "MINOR_CIV_ALMATY", "贝尔格莱德": "MINOR_CIV_BELGRADE",
    "布达佩斯": "MINOR_CIV_BUDAPEST", "河内": "MINOR_CIV_HANOI",
    "姆班扎刚果": "MINOR_CIV_MBANZA_KONGO", "西顿": "MINOR_CIV_SIDON",
    "索非亚": "MINOR_CIV_SOFIA", "瓦莱塔": "MINOR_CIV_VALLETTA",
}

# 用户CSV四路线列名 -> 工具内 Grand Strategy key
GS_CN_KEY = {"征服胜利": "CONQUEST", "文化胜利": "CULTURE", "科技胜利": "SCIENCE", "外交胜利": "DIPLO"}

# =====================================================================
# C++ 里没有进 Defines 表、硬编码在 CvDiplomacyAI.cpp 的权重（antonjs: todo constant/XML）
# =====================================================================
HARDCODED = {
    # grand strategy 里的 BULLY 修正
    "BULLY_CONQUEST_GS": 8,
    "BULLY_DIPLO_GS": -15,
    "BULLY_CULTURE_GS": -10,
    # 城邦 trait
    "BULLY_MILITARISTIC": -2,
    # 城邦 personality hostile
    "PERSONALITY_HOSTILE": {"FRIENDLY": -1, "PROTECTIVE": -2, "CONQUEST": 1, "BULLY": 1},
    # proximity 里的 BULLY 修正
    "BULLY_PROXIMITY_NEIGHBORS": 1,
    "BULLY_PROXIMITY_CLOSE": 1,
    "BULLY_PROXIMITY_DISTANT": -2,
}

# approach 顺序（对应 MinorCivApproachTypes 表 ID）
APPROACHES = ["IGNORE", "FRIENDLY", "PROTECTIVE", "CONQUEST", "BULLY"]
APPROACH_ID = {"IGNORE": 0, "FRIENDLY": 1, "PROTECTIVE": 2, "CONQUEST": 3, "BULLY": 4}

# 领袖 approach 偏置表用的类型字符串 -> 我们的 approach key
BIAS_KEY = {
    "MINOR_CIV_APPROACH_IGNORE": "IGNORE",
    "MINOR_CIV_APPROACH_FRIENDLY": "FRIENDLY",
    "MINOR_CIV_APPROACH_PROTECTIVE": "PROTECTIVE",
    "MINOR_CIV_APPROACH_CONQUEST": "CONQUEST",
    "MINOR_CIV_APPROACH_BULLY": "BULLY",
}


# =====================================================================
# 数据读取
# =====================================================================
def load_db(db_path):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # 1. MINOR_APPROACH_* 常量
    defines = {r["Name"]: r["Value"] for r in cur.execute(
        "SELECT Name, Value FROM Defines WHERE Name LIKE 'MINOR_APPROACH%'")}

    # 2. 领袖
    leaders = {}
    for r in cur.execute("SELECT Type, Description FROM Leaders WHERE Type != 'LEADER_BARBARIAN'"):
        leaders[r["Type"]] = {
            "type": r["Type"], "civ": None, "flavors": {}, "biases": {},
            "cs_friendship": 0, "cs_bonus": 0, "cs_combat": 0,
        }

    # 3. 文明 -> 领袖
    for r in cur.execute("SELECT CivilizationType, LeaderheadType FROM Civilization_Leaders"):
        if r["LeaderheadType"] in leaders:
            leaders[r["LeaderheadType"]]["civ"] = r["CivilizationType"]

    # 4. 领袖 flavor
    for r in cur.execute("SELECT LeaderType, FlavorType, Flavor FROM Leader_Flavors"):
        if r["LeaderType"] in leaders:
            leaders[r["LeaderType"]]["flavors"][r["FlavorType"]] = r["Flavor"]

    # 5. 领袖 approach 偏置
    for r in cur.execute("SELECT LeaderType, MinorCivApproachType, Bias FROM Leader_MinorCivApproachBiases"):
        if r["LeaderType"] in leaders and r["MinorCivApproachType"] in BIAS_KEY:
            leaders[r["LeaderType"]]["biases"][BIAS_KEY[r["MinorCivApproachType"]]] = r["Bias"]

    # 6. 领袖 CS trait 修正
    q = ("SELECT lt.LeaderType, t.CityStateFriendshipModifier, t.CityStateBonusModifier, "
         "t.CityStateCombatModifier FROM Leader_Traits lt JOIN Traits t ON t.Type = lt.TraitType")
    for r in cur.execute(q):
        if r["LeaderType"] in leaders:
            leaders[r["LeaderType"]]["cs_friendship"] = r["CityStateFriendshipModifier"] or 0
            leaders[r["LeaderType"]]["cs_bonus"] = r["CityStateBonusModifier"] or 0
            leaders[r["LeaderType"]]["cs_combat"] = r["CityStateCombatModifier"] or 0

    # 7. 城邦
    minors = {}
    for r in cur.execute("SELECT Type, MinorCivTrait, UAType FROM MinorCivilizations"):
        minors[r["Type"]] = {"type": r["Type"], "trait": r["MinorCivTrait"],
                             "uatype": r["UAType"] or "", "flavors": {}}

    # 8. 城邦原生 flavor
    for r in cur.execute("SELECT MinorCivType, FlavorType, Flavor FROM MinorCivilization_Flavors"):
        if r["MinorCivType"] in minors:
            minors[r["MinorCivType"]]["flavors"][r["FlavorType"]] = r["Flavor"]

    con.close()
    return defines, leaders, minors


def load_inclination_csv(csv_path):
    """读取城邦争夺倾向 CSV。格式:
    MinorCivType,CULTURE,SCIENCE,MILITARY,GOLD,RELIGION,GROWTH,DIPLOMACY
    """
    inc = {}
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            minor = row.get("MinorCivType", "").strip()
            if not minor:
                continue
            vec = {}
            for d in DIMENSIONS:
                val = row.get(d, "").strip()
                vec[d] = float(val) if val else 0.0
            inc[minor] = vec
    return inc


def load_contest_csv(csv_path):
    """读取城邦UA四路线争夺偏置CSV（GBK编码，Excel 保存）。
    格式: 城邦名,UA描述,征服胜利,文化胜利,科技胜利,外交胜利,总分数
    返回 {Type: {CONQUEST/CULTURE/SCIENCE/DIPLO: int}}。
    """
    bias = {}
    with open(csv_path, "r", encoding="gbk", newline="") as f:
        for row in csv.DictReader(f):
            cn = (row.get("城邦名") or "").strip()
            if not cn:
                continue
            typ = CN_NAME_TO_TYPE.get(cn, cn)
            vec = {}
            for col, gs in GS_CN_KEY.items():
                v = (row.get(col) or "0").strip()
                vec[gs] = int(v) if v.lstrip("-").isdigit() else 0
            bias[typ] = vec
    return bias


# =====================================================================
# 倾向聚合与匹配
# =====================================================================
def aggregate_flavor(flavors):
    """把 38 种 flavor 聚合为 7 个倾向维度（各维度 flavor 值之和）。"""
    return {d: sum(flavors.get(f, 0) for f in fs) for d, fs in DIMENSION_FLAVORS.items()}


def _normalize(vec):
    """L2 归一化为单位向量（只保留方向，消除 flavor 聚合后的量级差异）。"""
    import math
    s = math.sqrt(sum(v * v for v in vec.values()))
    if s == 0:
        return {k: 0.0 for k in vec}
    return {k: v / s for k, v in vec.items()}


def inclination_match(cs_incl, leader_dim):
    """城邦 CSUA 倾向 与 领袖倾向 的匹配度 = 余弦相似度（两单位向量点积，范围 -1~1）。
    只衡量「方向」是否一致，不受城邦/领袖倾向绝对数值大小影响。
    """
    cs_n = _normalize(cs_incl)
    ld_n = _normalize(leader_dim)
    return sum(cs_n.get(d, 0.0) * ld_n.get(d, 0.0) for d in DIMENSIONS)


# =====================================================================
# 复刻 C++ 权重计算
# =====================================================================
class Scenario:
    def __init__(self, grand_strategy="DIPLO", proximity="FAR", personality="NEUTRAL"):
        self.grand_strategy = grand_strategy  # DIPLO | CULTURE | CONQUEST | SCIENCE
        self.proximity = proximity            # NEIGHBORS | CLOSE | FAR | DISTANT
        self.personality = personality        # FRIENDLY | NEUTRAL | HOSTILE | IRRATIONAL
        # 倾向匹配加成：余弦相似度(0~1) × 此系数，转为 FRIENDLY/PROTECTIVE 权重。
        # 默认 20，与 C++ 里 grand strategy / 领袖偏置权重(5~20)同一量级。
        self.match_scale = 20.0


def compute_weights(leader, minor, cs_incl, defines, scenario, cs_contest_bias=None):
    """复刻 GetBestApproachTowardsMinorCiv 的可静态确定权重项。
    返回 (weights dict, 分解明细 dict)。
    """
    w = {a: 0 for a in APPROACHES}
    detail = {}

    def add(key, approach, val):
        w[approach] += val
        detail.setdefault(key, 0)
        detail[key] += val

    # 1. 默认 IGNORE
    add("IGNORE默认", "IGNORE", defines.get("MINOR_APPROACH_IGNORE_DEFAULT", 1))

    # 2. 领袖 approach 个性偏置
    for a, bias in leader["biases"].items():
        add("领袖approach偏置", a, bias)

    # 3. Grand Strategy（胜利路线）
    gs = scenario.grand_strategy
    if gs == "CONQUEST":
        add("征服路线", "CONQUEST", defines.get("MINOR_APPROACH_WAR_CONQUEST_GRAND_STRATEGY", 8))
        add("征服路线", "PROTECTIVE", defines.get("MINOR_APPROACH_PROTECTIVE_CONQUEST_GRAND_STRATEGY", -15))
        add("征服路线", "FRIENDLY", defines.get("MINOR_APPROACH_FRIENDLY_CONQUEST_GRAND_STRATEGY", -5))
        add("征服路线", "BULLY", HARDCODED["BULLY_CONQUEST_GS"])
    elif gs == "DIPLO":
        add("外交路线", "CONQUEST", defines.get("MINOR_APPROACH_WAR_DIPLO_GRAND_STRATEGY", -20))
        add("外交路线", "IGNORE", defines.get("MINOR_APPROACH_IGNORE_DIPLO_GRAND_STRATEGY", -15))
        add("外交路线", "BULLY", HARDCODED["BULLY_DIPLO_GS"])
        if scenario.proximity in ("NEIGHBORS", "CLOSE"):
            add("外交路线(近邻)", "PROTECTIVE",
                defines.get("MINOR_APPROACH_PROTECTIVE_DIPLO_GRAND_STRATEGY_NEIGHBORS", 5))
    elif gs == "CULTURE":
        add("文化路线", "CONQUEST", defines.get("MINOR_APPROACH_WAR_CULTURE_GRAND_STRATEGY", -20))
        add("文化路线", "IGNORE", defines.get("MINOR_APPROACH_IGNORE_CULTURE_GRAND_STRATEGY", -15))
        add("文化路线", "BULLY", HARDCODED["BULLY_CULTURE_GS"])
        if minor["trait"] == "MINOR_TRAIT_CULTURED":
            add("文化路线(文化城邦)", "PROTECTIVE",
                defines.get("MINOR_APPROACH_PROTECTIVE_CULTURE_GRAND_STRATEGY_CST", 5))
    # SCIENCE 路线在 C++ 里走 bCheckIfGoodWarTarget，依赖运行时状态，此处不复制

    # 4. 领袖 CS trait 修正（希腊/暹罗等）
    bonus = 0
    if leader["cs_friendship"] > 0:
        bonus += 100
    if leader["cs_bonus"] > 0:
        bonus += 100
    if leader["cs_combat"] > 0:
        bonus -= 100
    if bonus:
        add("领袖城邦trait", "CONQUEST", -bonus)
        add("领袖城邦trait", "BULLY", -bonus // 5)
        add("领袖城邦trait", "FRIENDLY", bonus // 5)
        add("领袖城邦trait", "PROTECTIVE", bonus)

    # 5. 城邦原生 trait（军事城邦更难被勒索）
    if minor["trait"] == "MINOR_TRAIT_MILITARISTIC":
        add("军事城邦", "BULLY", HARDCODED["BULLY_MILITARISTIC"])

    # 6. 城邦 personality（运行时随机，作为场景参数）
    if scenario.personality == "HOSTILE":
        for a, v in HARDCODED["PERSONALITY_HOSTILE"].items():
            add("城邦敌意性格", a, v)

    # 7. proximity（距离）
    prox = scenario.proximity
    if prox == "NEIGHBORS":
        add("邻近", "IGNORE", defines.get("MINOR_APPROACH_IGNORE_PROXIMITY_NEIGHBORS", -2))
        add("邻近", "FRIENDLY", defines.get("MINOR_APPROACH_FRIENDLY_PROXIMITY_NEIGHBORS", -1))
        add("邻近", "PROTECTIVE", defines.get("MINOR_APPROACH_PROTECTIVE_PROXIMITY_NEIGHBORS", 1))
        add("邻近", "CONQUEST", defines.get("MINOR_APPROACH_CONQUEST_PROXIMITY_NEIGHBORS", 1))
        add("邻近", "BULLY", HARDCODED["BULLY_PROXIMITY_NEIGHBORS"])
    elif prox == "CLOSE":
        add("较近", "IGNORE", defines.get("MINOR_APPROACH_IGNORE_PROXIMITY_CLOSE", -1))
        add("较近", "PROTECTIVE", defines.get("MINOR_APPROACH_PROTECTIVE_PROXIMITY_CLOSE", 1))
        add("较近", "CONQUEST", defines.get("MINOR_APPROACH_CONQUEST_PROXIMITY_CLOSE", -2))
        add("较近", "BULLY", HARDCODED["BULLY_PROXIMITY_CLOSE"])
    elif prox == "FAR":
        add("较远", "FRIENDLY", defines.get("MINOR_APPROACH_FRIENDLY_PROXIMITY_FAR", 2))
        add("较远", "CONQUEST", defines.get("MINOR_APPROACH_CONQUEST_PROXIMITY_FAR", -4))
    elif prox == "DISTANT":
        add("极远", "FRIENDLY", defines.get("MINOR_APPROACH_FRIENDLY_PROXIMITY_DISTANT", 2))
        add("极远", "CONQUEST", defines.get("MINOR_APPROACH_CONQUEST_PROXIMITY_DISTANT", -10))
        add("极远", "BULLY", HARDCODED["BULLY_PROXIMITY_DISTANT"])

    # 8. 城邦UA 争夺偏置（二选一）
    if cs_contest_bias is not None:
        # 用户CSV：按当前胜利路线查该城邦偏置 X，同时加到 FRIENDLY + PROTECTIVE
        bias = cs_contest_bias.get(minor["type"], {}).get(scenario.grand_strategy, 0)
        if bias:
            add("路线偏置", "FRIENDLY", bias)
            add("路线偏置", "PROTECTIVE", bias)
        match = float(bias)
    else:
        # 原 CSUA 倾向匹配（城邦倾向 × 领袖 flavor 余弦相似度）
        leader_dim = aggregate_flavor(leader["flavors"])
        match = inclination_match(cs_incl, leader_dim)
        if match > 0:
            bonus = match * scenario.match_scale
            add("CSUA倾向匹配→FRIENDLY", "FRIENDLY", bonus)
            add("CSUA倾向匹配→PROTECTIVE", "PROTECTIVE", bonus)

    return w, detail, match


def final_approach(w):
    """取权重最高的 approach（C++ 用 CvWeightedVector.SortItems 取最大）。"""
    return max(APPROACHES, key=lambda a: w[a])


# =====================================================================
# 输出
# =====================================================================
def contest_score(w):
    """争夺分数 = FRIENDLY + PROTECTIVE（拉拢意愿）。"""
    return w["FRIENDLY"] + w["PROTECTIVE"]


APPROACH_CN = {"IGNORE": "无视", "FRIENDLY": "友好", "PROTECTIVE": "保护", "CONQUEST": "征服", "BULLY": "勒索"}


def print_terminal_table(leaders, minors, cs_incl, defines, scenario, cs_contest_bias=None):
    """终端简表：城邦 × 领袖 争夺分数。"""
    minor_list = list(minors.values())
    # 只显示有文明映射的领袖
    leader_list = [l for l in leaders.values() if l["civ"]]

    header = f"{'城邦\\领袖':<14}" + "".join(f"{short(l['civ']):>10}" for l in leader_list)
    print("=" * len(header))
    print(f"场景: 胜利路线={scenario.grand_strategy} 距离={scenario.proximity} 城邦性格={scenario.personality}")
    print("=" * len(header))
    print(header)
    for m in minor_list:
        row = f"{short(m['type']):<14}"
        for l in leader_list:
            w, _, _ = compute_weights(l, m, cs_incl.get(m["type"], {}), defines, scenario, cs_contest_bias)
            row += f"{contest_score(w):>10.1f}"
        print(row)
    print("(单元格 = 争夺分数 = FRIENDLY + PROTECTIVE 权重)")


def print_summary(leaders, minors, cs_incl, defines, scenario, top_n=5, cs_contest_bias=None):
    """终端摘要：每个城邦争夺分数最高的 N 个领袖 + 最终态度。"""
    minor_list = list(minors.values())
    leader_list = [l for l in leaders.values() if l["civ"]]
    print(f"\n=== 各城邦争夺 Top{top_n} 领袖（场景: {scenario.grand_strategy}/{scenario.proximity}/{scenario.personality}）===")
    for m in minor_list:
        scored = []
        for l in leader_list:
            w, _, match = compute_weights(l, m, cs_incl.get(m["type"], {}), defines, scenario, cs_contest_bias)
            scored.append((contest_score(w), short(l["civ"]), APPROACH_CN[final_approach(w)]))
        scored.sort(reverse=True)
        line = "  " + " | ".join(f"{name}:{score:.0f}({appr})" for score, name, appr in scored[:top_n])
        print(f"{short(m['type']):<14}{line}")


def short(s):
    """把 TYPE 字符串缩短用于表格显示。"""
    for prefix in ("CIVILIZATION_", "LEADER_", "MINOR_CIV_"):
        if s.startswith(prefix):
            return s[len(prefix):]
    return s


def generate_html(leaders, minors, cs_incl, defines, strategies, output_path, cs_contest_bias=None):
    """生成自包含 HTML 报告：城邦 × 领袖 争夺分数热力图矩阵。"""
    minor_list = list(minors.values())
    leader_list = [l for l in leaders.values() if l["civ"]]
    leader_list.sort(key=lambda l: l["civ"])

    # 预计算所有组合的分数（每种 strategy 一份）
    data = {}
    for gs in strategies:
        scenario = Scenario(grand_strategy=gs)
        matrix = []
        for m in minor_list:
            for l in leader_list:
                w, detail, match = compute_weights(l, m, cs_incl.get(m["type"], {}), defines, scenario, cs_contest_bias)
                matrix.append({
                    "minor": m["type"], "leader": l["type"],
                    "score": round(contest_score(w), 1),
                    "approach": final_approach(w),
                    "weights": {a: round(w[a], 1) for a in APPROACHES},
                    "match": round(match, 1),
                    "detail": {k: round(v, 1) for k, v in detail.items()},
                })
        data[gs] = matrix

    # 找出分数范围用于配色
    all_scores = [c["score"] for m in data.values() for c in m]
    vmin, vmax = min(all_scores), max(all_scores)

    # 组装 JSON 供前端
    payload = {
        "strategies": strategies,
        "minors": [{"type": m["type"], "short": short(m["type"]), "trait": m["trait"], "uatype": m["uatype"]} for m in minor_list],
        "leaders": [{"type": l["type"], "short": short(l["civ"]), "civ": l["civ"]} for l in leader_list],
        "data": data,
        "vmin": vmin, "vmax": vmax,
    }

    html = HTML_TEMPLATE.replace("__PAYLOAD__", json.dumps(payload, ensure_ascii=False))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>城邦争夺分数矩阵</title>
<style>
  body { font-family: "Segoe UI", "Microsoft YaHei", sans-serif; margin: 20px; background:#1e1e2e; color:#cdd6f4; }
  h1 { font-size: 20px; }
  .controls { margin: 12px 0; }
  .controls label { margin-right: 16px; }
  select { padding: 4px; background:#313244; color:#cdd6f4; border:1px solid #585b70; border-radius:4px; }
  table { border-collapse: collapse; margin-top: 12px; }
  th, td { border: 1px solid #45475a; padding: 6px 9px; text-align: center; font-size: 12px; }
  th { background: #313244; position: sticky; top: 0; }
  td.minor { text-align: left; font-weight: bold; background:#2a2a3d; position: sticky; left:0; }
  .cell { cursor: pointer; }
  .cell:hover { outline: 2px solid #f9e2af; }
  .legend { margin: 8px 0; font-size: 12px; color:#a6adc8; }
  #detail { margin-top: 16px; padding: 12px; background:#252539; border:1px solid #45475a; border-radius:6px; font-size:13px; }
  #detail table { margin-top: 6px; }
  .badge { display:inline-block; padding:1px 6px; border-radius:4px; font-size:11px; margin-left:4px; }
</style>
</head>
<body>
<h1>城邦争夺分数矩阵（复刻 CvDiplomacyAI::GetBestApproachTowardsMinorCiv）</h1>
<div class="controls">
  <label>胜利路线：
    <select id="strategy" onchange="render()"></select>
  </label>
  <span id="stat"></span>
</div>
<div class="legend">单元格颜色 = 争夺分数（FRIENDLY + PROTECTIVE 权重）。点击单元格查看权重分解。</div>
<div id="grid"></div>
<div id="detail"></div>
<script>
const PAYLOAD = __PAYLOAD__;
const APPROACH_LABEL = {IGNORE:"无视", FRIENDLY:"友好", PROTECTIVE:"保护", CONQUEST:"征服", BULLY:"勒索"};
const APPROACH_COLOR = {IGNORE:"#a6adc8", FRIENDLY:"#a6e3a1", PROTECTIVE:"#89b4fa", CONQUEST:"#f38ba8", BULLY:"#fab387"};

const sel = document.getElementById('strategy');
PAYLOAD.strategies.forEach(s => {
  const o = document.createElement('option');
  o.value = s; o.textContent = s; sel.appendChild(o);
});

function color(v) {
  const t = PAYLOAD.vmax === PAYLOAD.vmin ? 0.5 : (v - PAYLOAD.vmin) / (PAYLOAD.vmax - PAYLOAD.vmin);
  // 红(低) -> 黄 -> 绿(高)
  const r = Math.round(243 - 77*t), g = Math.round(139 + 87*t), b = Math.round(168 - 68*t);
  return `rgb(${r},${g},${b})`;
}

function render() {
  const gs = sel.value;
  const rows = PAYLOAD.data[gs];
  const byKey = {};
  rows.forEach(c => byKey[c.minor + '|' + c.leader] = c);
  let html = '<table><thead><tr><th>城邦</th>';
  PAYLOAD.leaders.forEach(l => html += `<th>${l.short}</th>`);
  html += '</tr></thead><tbody>';
  PAYLOAD.minors.forEach(m => {
    html += `<tr><td class="minor">${m.short}</td>`;
    PAYLOAD.leaders.forEach(l => {
      const c = byKey[m.type + '|' + l.type];
      html += `<td class="cell" style="background:${color(c.score)};color:#11111b" onclick="showDetail('${m.type}','${l.type}')" title="点击看权重分解">${c.score.toFixed(1)}<br><span style="font-size:9px;opacity:.7">${APPROACH_LABEL[c.approach]}</span></td>`;
    });
    html += '</tr>';
  });
  html += '</tbody></table>';
  document.getElementById('grid').innerHTML = html;
}

function showDetail(minor, leader) {
  const gs = sel.value;
  const c = PAYLOAD.data[gs].find(x => x.minor === minor && x.leader === leader);
  const mn = PAYLOAD.minors.find(m => m.type === minor).short;
  const ln = PAYLOAD.leaders.find(l => l.type === leader).short;
  let html = `<h3>${mn} × ${ln}（路线 ${gs}）</h3>`;
  html += `<div>争夺分数 = <b>${c.score.toFixed(1)}</b>　路线偏置分 = ${c.match.toFixed(1)}　最终态度 = <b>${APPROACH_LABEL[c.approach]}</b></div>`;
  html += '<table><tr><th>approach</th><th>IGNORE</th><th>FRIENDLY</th><th>PROTECTIVE</th><th>CONQUEST</th><th>BULLY</th></tr>';
  html += '<tr><td>权重</td>';
  ['IGNORE','FRIENDLY','PROTECTIVE','CONQUEST','BULLY'].forEach(a => {
    html += `<td style="color:${APPROACH_COLOR[a]}">${c.weights[a].toFixed(1)}</td>`;
  });
  html += '</tr></table>';
  html += '<div style="margin-top:8px;color:#a6adc8">权重分解：';
  for (const [k, v] of Object.entries(c.detail)) {
    if (v !== 0) html += `<span class="badge" style="background:#313244">${k}: ${v>0?'+':''}${v.toFixed(1)}</span> `;
  }
  html += '</div>';
  document.getElementById('detail').innerHTML = html;
}

render();
</script>
</body>
</html>
"""


# =====================================================================
# 主流程
# =====================================================================
def main():
    default_db = r"C:/Users/pc/Documents/My Games/Sid Meier's Civilization 5/cache/Civ5DebugDatabase.db"
    parser = argparse.ArgumentParser(description="城邦争夺分数计算器")
    parser.add_argument("--db", default=default_db, help="Civ5 数据库路径（默认 Civ5DebugDatabase.db）")
    parser.add_argument("--csv", default=None, help="城邦争夺倾向 CSV（可选，覆盖内置默认）")
    parser.add_argument("--contest-csv", default=None,
                        help="城邦UA四路线争夺偏置 CSV（可选，GBK编码，列: 城邦名,UA描述,征服胜利,文化胜利,科技胜利,外交胜利,总分数）")
    parser.add_argument("--strategy", default="DIPLO",
                        help="胜利路线: DIPLO|CULTURE|CONQUEST|SCIENCE|ALL")
    parser.add_argument("--out", default="cs_contest_report.html", help="HTML 报告输出路径")
    parser.add_argument("--full", action="store_true", help="终端输出完整矩阵（默认只输出摘要）")
    parser.add_argument("--top", type=int, default=5, help="摘要里每城邦显示的领袖数")
    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f"[错误] 找不到数据库: {args.db}")
        print("请用 --db 指定 Civ5DebugDatabase.db 的路径。")
        sys.exit(1)

    print(f"读取数据库: {args.db}")
    defines, leaders, minors = load_db(args.db)

    # 城邦 CSUA 倾向
    cs_incl = dict(DEFAULT_CS_INCLINATION)
    if args.csv:
        cs_incl.update(load_inclination_csv(args.csv))
        print(f"已从 CSV 加载城邦倾向: {args.csv}")
    else:
        print("使用内置城邦倾向默认值（可用 --csv 覆盖）")

    # 城邦UA 四路线争夺偏置（用户 CSV 模式）
    cs_contest_bias = None
    if args.contest_csv:
        cs_contest_bias = load_contest_csv(args.contest_csv)
        print(f"已从 CSV 加载四路线争夺偏置: {args.contest_csv}（{len(cs_contest_bias)} 个城邦）")

        # 合成数据库缺失的城邦（迪拜/甘托克 SP 设计替换了香港/拉萨，数据库中无对应行）
        for typ in cs_contest_bias:
            if typ not in minors:
                minors[typ] = {"type": typ, "trait": "", "uatype": "CSUA", "flavors": {}}

    # 城邦集合：CSV 模式取 CSV 里的城邦，否则取有 CSUA 的城邦
    if cs_contest_bias is not None:
        csua_minors = {k: v for k, v in minors.items() if k in cs_contest_bias}
    else:
        csua_minors = {k: v for k, v in minors.items() if v["uatype"]}
    print(f"城邦(CSUA)数: {len(csua_minors)}，领袖数: {sum(1 for l in leaders.values() if l['civ'])}")

    strategies = ["DIPLO", "CULTURE", "CONQUEST", "SCIENCE"] if args.strategy == "ALL" else [args.strategy]

    # 终端输出（默认 DIPLO 场景）
    scenario = Scenario(grand_strategy=strategies[0])
    if args.full:
        print_terminal_table(leaders, csua_minors, cs_incl, defines, scenario, cs_contest_bias)
    else:
        print_summary(leaders, csua_minors, cs_incl, defines, scenario, args.top, cs_contest_bias)

    # HTML 报告
    out = generate_html(leaders, csua_minors, cs_incl, defines, strategies, args.out, cs_contest_bias)
    print(f"\nHTML 报告已生成: {os.path.abspath(out)}")


if __name__ == "__main__":
    main()
