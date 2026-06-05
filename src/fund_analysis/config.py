import os

import matplotlib as mpl

PROJECT_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)
CACHE_DIR = os.path.join(PROJECT_ROOT, "fund_cache")

INDEX_NAMES = {
    ".NDX": "纳斯达克100",
    ".INX": "标普500",
    ".IXIC": "纳斯达克综合",
    ".DJI": "道琼斯",
}


def setup_matplotlib(backend: str | None = None):
    if backend:
        mpl.use(backend)
    mpl.rcParams["font.sans-serif"] = [
        "Noto Sans CJK JP", "Noto Sans CJK SC", "Noto Sans CJK",
        "Songti SC", "Heiti TC", "PingFang HK",
        "WenQuanYi Micro Hei", "SimHei", "Microsoft YaHei",
        "Arial Unicode MS",
    ]
    mpl.rcParams["axes.unicode_minus"] = False
