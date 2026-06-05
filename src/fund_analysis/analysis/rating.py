import re

import pandas as pd


def rank_score(values: list, reverse: bool = True) -> list[int]:
    """在给定列表中排名，返回 1~5 分（第1名5分，第2名4分，第3名3分，第4名2分，第5+名1分）"""
    sorted_vals = sorted(values, reverse=reverse)
    rank_map = {}
    for i, v in enumerate(sorted_vals):
        if v not in rank_map:
            rank_map[v] = i + 1
    scores = []
    for v in values:
        r = rank_map[v]
        if r == 1:
            scores.append(5)
        elif r == 2:
            scores.append(4)
        elif r == 3:
            scores.append(3)
        elif r == 4:
            scores.append(2)
        else:
            scores.append(1)
    return scores


def parse_scale(scale_str: str) -> float:
    """解析净资产规模字符串 → 亿元数值"""
    m = re.search(r"([\d.]+)亿元", scale_str)
    return float(m.group(1)) if m else 0


def parse_fee(value: str) -> float:
    """解析单个费率字符串 → 百分比数值"""
    m = re.search(r"([\d.]+)%", value)
    return float(m.group(1)) if m else 0


def parse_total_fee(mgmt_str: str, trustee_str: str) -> float:
    """解析管理费率+托管费率 → 合计百分比"""
    return parse_fee(mgmt_str) + parse_fee(trustee_str)


def parse_est_date(est_str: str) -> str:
    """提取成立日期"""
    if " / " in est_str:
        return est_str.split(" / ")[0].strip()
    return est_str


def score_premium(premium: float, mean: float, std: float) -> int:
    """溢价偏离度评分：越靠近折价越高"""
    lower = max(mean - std, 0)
    upper = min(mean + std, mean * 1.5)
    if premium <= mean - 2 * std:
        return 5
    elif premium < lower:
        return 4
    elif premium <= upper:
        return 3
    elif premium <= mean + 2 * std:
        return 2
    else:
        return 1


WEIGHTS = {"规模": 0.25, "成立时间": 0.15, "费率": 0.20, "溢价偏离": 0.40}


def calculate_rating(scale_score: int, age_score: int, fee_score: int, premium_score: int) -> float:
    total = (scale_score * WEIGHTS["规模"] +
             age_score * WEIGHTS["成立时间"] +
             fee_score * WEIGHTS["费率"] +
             premium_score * WEIGHTS["溢价偏离"])
    return round(total, 2)
