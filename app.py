# app.py
# 全球资金趋势 · Streamlit 版本（日度更新）
# 依赖: streamlit, yfinance, pandas, numpy, plotly, fred

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from fredapi import Fred

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="全球资金趋势",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 强制展开侧边栏（必须在最前面，避免 st.stop() 时丢失）
# ============================================================
st.markdown("""
<style>
section[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    transform: none !important;
    margin-left: 0 !important;
    left: 0 !important;
    width: 21rem !important;
    min-width: 21rem !important;
    max-width: 21rem !important;
    opacity: 1 !important;
    position: relative !important;
    z-index: 999999 !important;
}
section[data-testid="stSidebar"] > div {
    width: 21rem !important;
    display: block !important;
}
[data-testid="stAppViewContainer"] > .main,
.main .block-container {
    margin-left: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 全局样式
# ============================================================
st.markdown("""<style>
.block-container{padding-top:1.2rem;padding-bottom:2rem;max-width:1320px}
#MainMenu,footer,header{visibility:hidden}

/* ---------- 卡片网格 ---------- */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(196px,1fr));gap:12px;margin:4px 0 6px}
.card{position:relative;overflow:hidden;border-radius:14px;
  background:linear-gradient(180deg,#131a29,#0f1421);
  border:1px solid #1d2740;padding:13px 13px 4px;transition:.2s}
.card:hover{border-color:#2b3a5c;transform:translateY(-2px);
  box-shadow:0 8px 24px -10px rgba(0,0,0,.8)}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--c);opacity:.85}
.c-head{display:flex;align-items:center;gap:6px;margin-bottom:7px}
.c-dot{width:7px;height:7px;border-radius:50%;background:var(--c);flex:none;box-shadow:0 0 8px var(--c)}
.c-name{font-size:12.5px;font-weight:600;color:#c3cee2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.c-tick{margin-left:auto;font-size:9.5px;color:#48546e;font-weight:600;letter-spacing:.5px;flex:none}
.c-val{font-size:21px;font-weight:700;letter-spacing:-.4px;font-variant-numeric:tabular-nums;
  line-height:1.15;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.c-unit{font-size:10.5px;color:#48546e;font-weight:500;margin-left:2px}
.c-chg{font-size:11.5px;font-weight:600;margin-top:3px;font-variant-numeric:tabular-nums;
  display:flex;align-items:center;gap:4px}
.c-chg.up{color:#00d68f}.c-chg.down{color:#ff4d6a}
.c-chg .arrow{font-size:9px}
.spark{display:block;width:100%;height:50px;margin-top:2px}

/* ---------- 指标条 ---------- */
.statbar{display:flex;gap:18px;flex-wrap:wrap;font-size:12px;color:#68758f;margin:2px 0 14px}
.statbar b{font-weight:700;font-size:13px;font-variant-numeric:tabular-nums}
.statbar .u{color:#00d68f}.statbar .d{color:#ff4d6a}

/* ---------- Streamlit 组件微调 ---------- */
div[data-testid="stMetricValue"]{font-size:20px;font-weight:700}
div[data-testid="stMetricLabel"]{font-size:11px;color:#68758f}
.stTabs [data-baseweb="tab-list"]{gap:6px}
.stTabs [data-baseweb="tab"]{padding:6px 14px;font-size:13px}

</style>""", unsafe_allow_html=True)

st.caption("👉 侧边栏（左上角箭头可展开）可选择资产、时间范围和对比模式。")

# ============================================================
# 分类定义
# ============================================================
CATEGORIES = {
    "股":       {"icon": "📈", "color": "#2563eb", "bg": "#eff6ff"},
    "债":       {"icon": "📊", "color": "#7c3aed", "bg": "#f5f3ff"},
    "汇":       {"icon": "💱", "color": "#0891b2", "bg": "#ecfeff"},
    "能源":     {"icon": "🛢", "color": "#dc2626", "bg": "#fef2f2"},
    "贵金属":   {"icon": "🥇", "color": "#d97706", "bg": "#fffbeb"},
    "工业金属": {"icon": "🔩", "color": "#92400e", "bg": "#fef3c7"},
    "加密":     {"icon": "💎", "color": "#db2777", "bg": "#fdf2f8"},
    "贸易流":   {"icon": "🚢", "color": "#059669", "bg": "#ecfdf5"},
}

CATEGORY_ORDER = ["股", "债", "汇", "能源", "贵金属", "工业金属", "加密", "贸易流"]

# ============================================================
# 资产配置
# ============================================================
ASSETS = [
    # ---------------- 股 ----------------
    {"id": "spx",  "name": "标普500",    "ticker": "SPX",    "cat": "股",
     "source": "yf", "symbols": ["^GSPC"], "unit": "点", "decimals": 0,
     "color": "#4ea8de", "scale": 1.0},
    {"id": "ndx",  "name": "纳斯达克",   "ticker": "IXIC",   "cat": "股",
     "source": "yf", "symbols": ["^IXIC"], "unit": "点", "decimals": 0,
     "color": "#7c6af0", "scale": 1.0},
    {"id": "dji",  "name": "道琼斯",     "ticker": "DJI",    "cat": "股",
     "source": "yf", "symbols": ["^DJI"], "unit": "点", "decimals": 0,
     "color": "#3b82f6", "scale": 1.0},
    {"id": "rut",  "name": "罗素2000",   "ticker": "RUT",    "cat": "股",
     "source": "yf", "symbols": ["^RUT"], "unit": "点", "decimals": 0,
     "color": "#60a5fa", "scale": 1.0},
    {"id": "sox",  "name": "费城半导体", "ticker": "SOX",    "cat": "股",
     "source": "yf", "symbols": ["^SOX"], "unit": "点", "decimals": 0,
     "color": "#8b5cf6", "scale": 1.0},
    {"id": "dax",  "name": "德国DAX",    "ticker": "DAX",    "cat": "股",
     "source": "yf", "symbols": ["^GDAXI"], "unit": "点", "decimals": 0,
     "color": "#06b6d4", "scale": 1.0},
    {"id": "ftse", "name": "英国富时100","ticker": "FTSE",   "cat": "股",
     "source": "yf", "symbols": ["^FTSE"], "unit": "点", "decimals": 0,
     "color": "#0ea5e9", "scale": 1.0},
    {"id": "cac",  "name": "法国CAC40",  "ticker": "CAC",    "cat": "股",
     "source": "yf", "symbols": ["^FCHI"], "unit": "点", "decimals": 0,
     "color": "#38bdf8", "scale": 1.0},
    {"id": "n225", "name": "日经225",    "ticker": "N225",   "cat": "股",
     "source": "yf", "symbols": ["^N225"], "unit": "点", "decimals": 0,
     "color": "#f43f5e", "scale": 1.0},
    {"id": "kospi","name": "韩国KOSPI",  "ticker": "KOSPI",  "cat": "股",
     "source": "yf", "symbols": ["^KS11"], "unit": "点", "decimals": 0,
     "color": "#ec4899", "scale": 1.0},
    {"id": "axjo", "name": "澳洲标普200","ticker": "AXJO",   "cat": "股",
     "source": "yf", "symbols": ["^AXJO"], "unit": "点", "decimals": 0,
     "color": "#f97316", "scale": 1.0},
    {"id": "nsei", "name": "印度Nifty50","ticker": "NIFTY",  "cat": "股",
     "source": "yf", "symbols": ["^NSEI"], "unit": "点", "decimals": 0,
     "color": "#fb923c", "scale": 1.0},
    {"id": "bvsp", "name": "巴西IBOVESPA","ticker": "BVSP",  "cat": "股",
     "source": "yf", "symbols": ["^BVSP"], "unit": "点", "decimals": 0,
     "color": "#16a34a", "scale": 1.0},
    {"id": "hsi",  "name": "恒生指数",   "ticker": "HSI",    "cat": "股",
     "source": "yf", "symbols": ["^HSI"], "unit": "点", "decimals": 0,
     "color": "#22c55e", "scale": 1.0},
     {"id": "hstech", "name": "恒生科技", "ticker": "HSTECH", "cat": "股",
     "source": "yf", "symbols": ["HSTECH.HK", "3067.HK", "KTEC"], "unit": "点", "decimals": 2,
     "color": "#06b6d4", "scale": 1.0},
    {"id": "sse",  "name": "上证指数",   "ticker": "SSE",    "cat": "股",
     "source": "yf", "symbols": ["000001.SS"], "unit": "点", "decimals": 2,
     "color": "#ef4444", "scale": 1.0},
    {"id": "csi300","name": "沪深300",   "ticker": "CSI300", "cat": "股",
     "source": "yf", "symbols": ["000300.SS"], "unit": "点", "decimals": 2,
     "color": "#dc2626", "scale": 1.0},
    {"id": "chinext", "name": "创业板指",   "ticker": "CHINEXT", "cat": "股",
     "source": "yf", "symbols": ["159915.SZ", "399006.SHE"], "unit": "点", "decimals": 2,
     "color": "#14b8a6", "scale": 1.0},

    # ---------------- 债 ----------------
    {"id": "ust2y", "name": "美债2年期", "ticker": "US2Y",   "cat": "债",
     "source": "fred", "symbols": ["DGS2"], "unit": "%", "decimals": 3,
     "color": "#a78bfa", "scale": 1.0},
    {"id": "ust10y","name": "美债10年期","ticker": "US10Y",  "cat": "债",
     "source": "fred", "symbols": ["DGS10"], "unit": "%", "decimals": 3,
     "color": "#8b5cf6", "scale": 1.0},
    {"id": "ust30y","name": "美债30年期","ticker": "US30Y",  "cat": "债",
     "source": "fred", "symbols": ["DGS30"], "unit": "%", "decimals": 3,
     "color": "#7c3aed", "scale": 1.0},

    # ---------------- 汇 ----------------
    {"id": "dxy",  "name": "美元指数DXY","ticker": "DXY",    "cat": "汇",
     "source": "yf", "symbols": ["DX-Y.NYB", "DX=F"], "unit": "点", "decimals": 2,
     "color": "#5b8def", "scale": 1.0},
    {"id": "dtwexbgs","name": "美元广义指数","ticker": "DTWEXBGS","cat": "汇",
     "source": "fred", "symbols": ["DTWEXBGS"], "unit": "指数", "decimals": 2,
     "color": "#60a5fa", "scale": 1.0},
    {"id": "eurusd","name": "欧元/美元", "ticker": "EURUSD", "cat": "汇",
     "source": "yf", "symbols": ["EURUSD=X"], "unit": "汇率", "decimals": 4,
     "color": "#0891b2", "scale": 1.0},
    {"id": "usdjpy","name": "美元/日元", "ticker": "USDJPY", "cat": "汇",
     "source": "yf", "symbols": ["JPY=X"], "unit": "汇率", "decimals": 2,
     "color": "#06b6d4", "scale": 1.0},
    {"id": "gbpusd","name": "英镑/美元", "ticker": "GBPUSD", "cat": "汇",
     "source": "yf", "symbols": ["GBPUSD=X"], "unit": "汇率", "decimals": 4,
     "color": "#14b8a6", "scale": 1.0},
    {"id": "usdcny","name": "美元/人民币","ticker": "USDCNY","cat": "汇",
     "source": "yf", "symbols": ["CNY=X"], "unit": "汇率", "decimals": 4,
     "color": "#26c6a8", "scale": 1.0},

    # ---------------- 能源 ----------------
    {"id": "wti",  "name": "WTI原油",    "ticker": "WTI",    "cat": "能源",
     "source": "yf", "symbols": ["CL=F"], "unit": "美元/桶", "decimals": 2,
     "color": "#ef4444", "scale": 1.0},
    {"id": "brent","name": "布伦特原油", "ticker": "BRENT",  "cat": "能源",
     "source": "yf", "symbols": ["BZ=F"], "unit": "美元/桶", "decimals": 2,
     "color": "#dc2626", "scale": 1.0},

    # ---------------- 贵金属 ----------------
    {"id": "gold", "name": "COMEX黄金",  "ticker": "XAU",    "cat": "贵金属",
     "source": "yf", "symbols": ["GC=F", "XAUUSD=X"], "unit": "美元/盎司", "decimals": 0,
     "color": "#ffc043", "scale": 1.0},
    {"id": "silver","name": "COMEX白银", "ticker": "XAG",    "cat": "贵金属",
     "source": "yf", "symbols": ["SI=F"], "unit": "美元/盎司", "decimals": 2,
     "color": "#a8a29e", "scale": 1.0},

    # ---------------- 工业金属 ----------------
    {"id": "copper","name": "COMEX铜",   "ticker": "COPPER", "cat": "工业金属",
     "source": "yf", "symbols": ["HG=F"], "unit": "美元/磅", "decimals": 3,
     "color": "#e8853a", "scale": 1.0},

    # ---------------- 加密 ----------------
    {"id": "btc",  "name": "比特币",     "ticker": "BTC",    "cat": "加密",
     "source": "yf", "symbols": ["BTC-USD"], "unit": "美元", "decimals": 0,
     "color": "#f7931a", "scale": 1.0},
    {"id": "eth",  "name": "以太坊",     "ticker": "ETH",    "cat": "加密",
     "source": "yf", "symbols": ["ETH-USD"], "unit": "美元", "decimals": 0,
     "color": "#627eea", "scale": 1.0},

    # ---------------- 贸易流 ----------------
    {"id": "gscpi","name": "全球供应链压力","ticker": "GSCPI","cat": "贸易流",
     "source": "fred", "symbols": ["GSCPI"], "unit": "指数", "decimals": 3,
     "color": "#059669", "scale": 1.0},
]

ASSET_MAP = {a["id"]: a for a in ASSETS}

# 说明文案
NOTES = {
    # 股
    "spx":  "标普500指数，美国大盘股基准，观察全球风险偏好的核心指标。",
    "ndx":  "纳斯达克综合指数，科技股为主，对利率与 AI 产业叙事高度敏感。",
    "dji":  "道琼斯工业平均指数，30 只蓝筹股价格加权，传统工业与金融权重较高。",
    "rut":  "罗素2000指数，美国小盘股代表，对本土经济与信贷环境更敏感。",
    "sox":  "费城半导体指数，全球半导体产业风向标，AI 算力需求的核心映射。",
    "dax":  "德国DAX指数，欧洲最大经济体蓝筹基准，制造业出口导向明显。",
    "ftse": "英国富时100指数，伦敦交易所蓝筹基准，能源与金融权重较高。",
    "cac":  "法国CAC40指数，巴黎交易所蓝筹基准，奢侈品与工业占比高。",
    "n225": "日经225指数，东京交易所蓝筹基准，日元汇率与出口景气度关联紧密。",
    "kospi":"韩国KOSPI指数，三星、SK海力士等半导体权重高，全球科技周期温度计。",
    "axjo": "澳洲标普200指数，悉尼交易所蓝筹基准，矿业与金融权重较高。",
    "nsei": "印度Nifty50指数，印度大盘基准，新兴市场资金流入的重要观测标的。",
    "bvsp": "巴西IBOVESPA指数，拉美最大股票市场，大宗商品与汇率联动明显。",
    "hsi":  "恒生指数，香港交易所蓝筹基准，中资与外资资金交锋的前沿。",
    "hstech":"恒生科技指数，港股科技龙头集合，中概股资金流向的核心指标。",
    "sse":  "上证综合指数，上海交易所全部股票加权，A股资金面的基础指标。",
    "csi300":"沪深300指数，A股大盘蓝筹基准，境内机构与外资的主要配置对象。",
    "chinext": "创业板指（399006.SZ），由创业板中市值大、流动性好的100只股票组成，反映创业板市场运行情况[reference:4]。",

    # 债
    "ust2y":  "美国2年期国债收益率（FRED: DGS2）。对美联储政策路径最敏感。",
    "ust10y": "美国10年期国债收益率（FRED: DGS10）。全球资产定价的「利率锚」。",
    "ust30y": "美国30年期国债收益率（FRED: DGS30）。反映长期通胀预期与期限溢价。",

    # 汇
    "dxy":    "美元指数，衡量美元对一篮子主要货币的强弱。",
    "dtwexbgs":"美元广义贸易加权指数（FRED: DTWEXBGS），覆盖范围比 DXY 更广。",
    "eurusd": "欧元兑美元汇率，全球交易量最大的货币对。",
    "usdjpy": "美元兑日元汇率，套息交易与日元避险属性的核心观察指标。",
    "gbpusd":"英镑兑美元汇率，英欧资金流向的重要参考。",
    "usdcny":"美元兑人民币在岸汇率。数值下行代表人民币升值。",

    # 能源
    "wti":  "WTI 西德州中质原油期货，北美原油定价基准。",
    "brent":"布伦特原油期货，全球原油定价基准，受地缘政治与 OPEC+ 政策驱动。",

    # 贵金属
    "gold": "COMEX 黄金期货主力合约，避险与抗通胀属性的核心资产。",
    "silver":"COMEX 白银期货，兼具贵金属与工业金属双重属性。",

    # 工业金属
    "copper":"COMEX 铜期货主力合约，被称为「铜博士」，对全球制造业景气度敏感。",

    # 加密
    "btc":  "比特币现货价格（美元），24×7 交易，机构资金参与度持续提升。",
    "eth":  "以太坊现货价格（美元），加密市场第二大资产。",

    # 贸易流
    "gscpi":"纽约联储全球供应链压力指数（FRED: GSCPI）。数值越高表示供应链越紧张。",
}

RANGE_OPTIONS = {
    "近1个月": 30,
    "近3个月": 90,
    "近6个月": 180,
    "近1年": 365,
    "近2年": 730,
    "近5年": 1825,
}


# ============================================================
# FRED 客户端（延迟初始化）
# ============================================================
@st.cache_resource(show_spinner=False)
def get_fred_client():
    try:
        key = st.secrets.get("FRED_API_KEY", "")
    except Exception:
        key = ""
    if not key:
        return None
    try:
        return Fred(api_key=key)
    except Exception:
        return None


# ============================================================
# 数据获取
# ============================================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_yf_series(symbols: tuple, start_str: str, end_str: str, scale: float):
    """yfinance 拉取收盘价，按顺序尝试多个 symbol。"""
    import yfinance as yf

    for sym in symbols:
        try:
            df = yf.Ticker(sym).history(start=start_str, end=end_str, auto_adjust=False)
            if df is None or df.empty:
                continue

            col = "Close" if "Close" in df.columns else ("Adj Close" if "Adj Close" in df.columns else None)
            if col is None:
                continue

            s = df[col].dropna()
            if s.empty or len(s) < 2:
                continue

            try:
                s.index = pd.to_datetime(s.index).tz_localize(None)
            except Exception:
                s.index = pd.to_datetime(s.index)

            s = s.astype(float) * float(scale)

            if s.iloc[-1] > 20 and "TNX" in sym.upper():
                s = s / 10.0

            return s

        except Exception:
            continue

    return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fred_series(series_id: str, start_str: str, end_str: str):
    """FRED 拉取时间序列。未配置 FRED_API_KEY 时返回 None。"""
    fred = get_fred_client()
    if fred is None:
        return None
    try:
        s = fred.get_series(series_id, observation_start=start_str, observation_end=end_str)
        if s is None:
            return None
        s = s.dropna()
        if s.empty or len(s) < 2:
            return None
        s.index = pd.to_datetime(s.index).tz_localize(None)
        return s.astype(float)
    except Exception:
        return None


def load_all(asset_ids, start: date, end: date):
    """批量拉取，返回 {id: Series}。"""
    start_str = start.isoformat()
    end_str = (end + timedelta(days=1)).isoformat()

    out = {}
    for aid in asset_ids:
        a = ASSET_MAP.get(aid)
        if not a:
            continue

        if a.get("source") == "fred":
            s = fetch_fred_series(a["symbols"][0], start_str, end_str)
        else:
            s = fetch_yf_series(tuple(a["symbols"]), start_str, end_str, a.get("scale", 1.0))

        if s is not None:
            out[aid] = s
    return out


# ============================================================
# 绘图工具
# ============================================================
def sparkline_svg(values, color, w=200, h=50, pad=5, uid="s"):
    if values is None or len(values) < 2:
        return ""
    arr = np.asarray(values, dtype=float)
    vmin, vmax = float(arr.min()), float(arr.max())
    rng = (vmax - vmin) or 1.0
    n = len(arr)
    xs = pad + (np.arange(n) / (n - 1)) * (w - pad * 2)
    ys = pad + (1 - (arr - vmin) / rng) * (h - pad * 2)

    line = "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in zip(xs, ys))
    area = line + f" L {xs[-1]:.2f} {h} L {xs[0]:.2f} {h} Z"

    return (
        f'<svg class="spark" viewBox="0 0 {w} {h}" preserveAspectRatio="none">'
        f'<defs><linearGradient id="g{uid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0.28"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/>'
        f'</linearGradient></defs>'
        f'<path d="{area}" fill="url(#g{uid})"/>'
        f'<path d="{line}" fill="none" stroke="{color}" stroke-width="1.6" '
        f'stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/>'
        f'<circle cx="{xs[-1]:.2f}" cy="{ys[-1]:.2f}" r="1.7" fill="{color}"/>'
        f'</svg>'
    )


PLOT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(
        color="#8b99b5", size=11,
        family="-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif",
    ),
    margin=dict(l=8, r=8, t=34, b=8),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                bgcolor="rgba(0,0,0,0)"),
)


def detail_chart(series, meta):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=series.index, y=series.values,
        mode="lines",
        line=dict(color=meta["color"], width=2),
        name=meta["name"],
        hovertemplate="%{x|%Y-%m-%d}<br><b>%{y:,.4~f}</b><extra></extra>",
    ))

    # 区间高低点标注
    imax, imin = int(np.argmax(series.values)), int(np.argmin(series.values))
    fig.add_trace(go.Scatter(
        x=[series.index[imax]], y=[series.values[imax]],
        mode="markers+text", text=["高"], textposition="top center",
        textfont=dict(color="#ffc043", size=10),
        marker=dict(color="#ffc043", size=8, line=dict(color="#0d1220", width=1.5)),
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=[series.index[imin]], y=[series.values[imin]],
        mode="markers+text", text=["低"], textposition="bottom center",
        textfont=dict(color="#8b99b5", size=10),
        marker=dict(color="#8b99b5", size=8, line=dict(color="#0d1220", width=1.5)),
        showlegend=False, hoverinfo="skip",
    ))

    pad = (float(series.max()) - float(series.min())) * 0.10 or 1

    # 布局：只传 PLOT_BASE 里的通用配置
    fig.update_layout(
        **PLOT_BASE,
        height=340,
        showlegend=False,
    )

    # 坐标轴单独设置
    fig.update_yaxes(
        gridcolor="#1a2334",
        zeroline=False,
        range=[float(series.min()) - pad, float(series.max()) + pad],
    )
    fig.update_xaxes(
        gridcolor="#1a2334",
        zeroline=False,
        showspikes=True, spikecolor="#3a4459", spikethickness=1,
        rangeselector=dict(
            buttons=[
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=3, label="3M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(step="all", label="全部"),
            ],
            bgcolor="#141b2b", activecolor="#25314d",
            font=dict(color="#8b99b5", size=11),
            x=0, y=1.16, xanchor="left",
        ),
    )
    return fig


def compare_chart(data_map, selected, normalize=True):
    fig = go.Figure()

    for aid in selected:
        a = ASSET_MAP[aid]
        s = data_map[aid].dropna()
        if len(s) < 2:
            continue

        if normalize:
            y = s / s.iloc[0] * 100.0
            name = a["name"]
            hovertemplate = f"<b>{a['name']}</b> %{{y:.1f}}<extra></extra>"
        else:
            y = s
            name = f'{a["name"]} ({a["unit"]})' if a["unit"] else a["name"]
            unit_str = a["unit"] or ""
            hovertemplate = f"<b>{a['name']}</b> %{{y:,.4f}} {unit_str}<extra></extra>"

        fig.add_trace(go.Scatter(
            x=y.index, y=y.values,
            mode="lines", name=name,
            line=dict(color=a["color"], width=1.8),
            hovertemplate=hovertemplate,
        ))

    if normalize:
        fig.add_hline(y=100, line_dash="dot", line_color="#3a4459", line_width=1)

    fig.update_layout(**PLOT_BASE, height=430)

    if normalize:
        fig.update_yaxes(title_text="基期 = 100", title_font=dict(size=11, color="#4a5670"))
    else:
        fig.update_yaxes(title_text="原始点位", title_font=dict(size=11, color="#4a5670"))

    return fig

# ============================================================
# 汇总计算
# ============================================================
def pct_change(s, periods):
    if len(s) <= periods:
        return np.nan
    prev = float(s.iloc[-1 - periods])
    if prev == 0:
        return np.nan
    return (float(s.iloc[-1]) - prev) / prev * 100.0


def build_summary(data_map):
    rows = []
    for aid, s in data_map.items():
        a = ASSET_MAP[aid]
        s = s.dropna()
        if len(s) < 2:
            continue
        rows.append({
            "资产": f'{a["name"]}',
            "代码": a["ticker"],
            "最新": float(s.iloc[-1]),
            "日涨跌%": pct_change(s, 1),
            "周涨跌%": pct_change(s, 5),
            "月涨跌%": pct_change(s, 21),
            "区间涨跌%": pct_change(s, len(s) - 1),
            "区间高": float(s.max()),
            "区间低": float(s.min()),
            "分类": a["cat"],
            "_id": aid,
        })
    return pd.DataFrame(rows)


# ============================================================
# 侧边栏
# ============================================================
with st.sidebar:
    st.markdown("### 🌐 全球资金流向")
    st.caption("日度更新 · 数据源 Yahoo Finance")
    st.divider()

    range_label = st.selectbox("时间范围", list(RANGE_OPTIONS.keys()), index=3)
    days = RANGE_OPTIONS[range_label]

    st.divider()
    st.markdown("**选择资产**")
    default_ids = [a["id"] for a in ASSETS]
    selected_ids = st.multiselect(
        "配置表标的",
        options=default_ids,
        default=default_ids,
        format_func=lambda x: ASSET_MAP[x]["name"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**对比模式**")
    compare_mode = st.radio(
        "对比模式",
        ["归一化（起点=100）", "绝对点位"],
        index=0,
        label_visibility="collapsed",
    )
    normalize = compare_mode.startswith("归一化")
    
    st.divider()
    st.markdown("**涨跌配色**")
    color_scheme = st.radio(
        "涨跌配色",
        ["中国配色（红涨绿跌）", "国际配色（绿涨红跌）"],
        index=0,
        label_visibility="collapsed",
    )
    use_china = color_scheme.startswith("中国")

    st.divider()
    if st.button("🔄 强制刷新数据", width="stretch"):
        st.cache_data.clear()
        st.rerun()

    st.caption("缓存有效期 1 小时，点按钮可立即重新拉取。")

# ============================================================
# 涨跌配色 CSS（必须在卡片渲染之前注入）
# ============================================================

    if use_china:
        up_color = "#ff4d6a"      # 中国配色：涨 = 红
        down_color = "#00d68f"    # 中国配色：跌 = 绿
    else:
        up_color = "#00d68f"      # 国际配色：涨 = 绿
        down_color = "#ff4d6a"    # 国际配色：跌 = 红

    st.markdown(f"""
    <style>
    .c-chg.up   {{ color: {up_color} !important; }}
    .c-chg.down {{ color: {down_color} !important; }}
    .statbar .u {{ color: {up_color} !important; }}
    .statbar .d {{ color: {down_color} !important; }}
    </style>
    """, unsafe_allow_html=True)

if not selected_ids:
    st.info("👉 请在左侧侧边栏中选择至少一个资产。")
    st.stop()

# ============================================================
# 拉取数据
# ============================================================
end_date = date.today()
start_date = end_date - timedelta(days=days)

with st.spinner("正在拉取行情数据…"):
    data_map = load_all(selected_ids, start_date, end_date)

if not data_map:
    st.error("未能获取任何数据。请检查网络连接，或点击侧边栏「强制刷新数据」重试。")
    st.stop()

now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
st.markdown(
    f'<div style="display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:10px">'
    f'<span style="font-size:19px;font-weight:700;letter-spacing:.3px">全球资金流向配置表</span>'
    f'<span style="font-size:11.5px;color:#48546e">数据更新于 {now_str} · 区间 {start_date} ~ {end_date}</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# ============================================================
# 顶部统计条
# ============================================================
chg_list = []
for aid, s in data_map.items():
    c = pct_change(s.dropna(), len(s.dropna()) - 1)
    if not np.isnan(c):
        chg_list.append((aid, c))

if chg_list:
    ups = sum(1 for _, c in chg_list if c > 0)
    downs = len(chg_list) - ups
    best_id, best_c = max(chg_list, key=lambda x: x[1])
    worst_id, worst_c = min(chg_list, key=lambda x: x[1])

    st.markdown(
        f'<div class="statbar">'
        f'<span>区间上涨 <b class="u">{ups}</b> / 下跌 <b class="d">{downs}</b></span>'
        f'<span>最强 <b class="u">{ASSET_MAP[best_id]["name"]} {best_c:+.2f}%</b></span>'
        f'<span>最弱 <b class="d">{ASSET_MAP[worst_id]["name"]} {worst_c:+.2f}%</b></span>'
        f'<span>覆盖资产 <b>{len(data_map)}</b> 个</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ============================================================
# 卡片网格：按分类分组，每类一种颜色
# ============================================================
for cat in CATEGORY_ORDER:
    cat_assets = [a for a in ASSETS if a["cat"] == cat and a["id"] in data_map]
    if not cat_assets:
        continue

    info = CATEGORIES[cat]

    # 分类标题条
    st.markdown(
        f'<div style="background:{info["color"]};color:#fff;'
        f'padding:9px 16px;border-radius:8px;margin:22px 0 12px 0;'
        f'font-size:14px;font-weight:700;letter-spacing:.3px">'
        f'{info["icon"]} {cat} · {len(cat_assets)} 项'
        f'</div>',
        unsafe_allow_html=True,
    )

    # 分类内卡片
    cards = []
    for a in cat_assets:
        s = data_map[a["id"]].dropna()
        if len(s) < 2:
            continue

        last = float(s.iloc[-1])
        first = float(s.iloc[0])
        chg = (last - first) / first * 100 if first else 0.0
        up = chg >= 0

        dec = a["decimals"]
        val_str = f"{last:,.{dec}f}"
        unit_html = f'<span class="c-unit">{a["unit"]}</span>' if a["unit"] else ""
        arrow = "▲" if up else "▼"
        cls = "up" if up else "down"

        spark_vals = s.values[-260:] if len(s) > 260 else s.values
        # 卡片内的曲线用分类色，视觉上更统一
        spark = sparkline_svg(spark_vals, info["color"], uid=f'c{a["id"]}')

        cards.append(
            f'<div class="card" style="--c:{info["color"]}">'
            f'<div class="c-head"><span class="c-dot"></span>'
            f'<span class="c-name">{a["name"]}</span>'
            f'<span class="c-tick">{a["ticker"]}</span></div>'
            f'<div class="c-val">{val_str}{unit_html}</div>'
            f'<div class="c-chg {cls}"><span class="arrow">{arrow}</span>{abs(chg):.2f}%'
            f'<span style="color:#48546e;font-weight:400;font-size:10px">区间</span></div>'
            f'{spark}'
            f'</div>'
        )

    if cards:
        st.markdown('<div class="grid">' + "".join(cards) + "</div>", unsafe_allow_html=True)

st.write("")

# ============================================================
# 标签页
# ============================================================
tab1, tab2, tab3 = st.tabs(["📊 归一化对比", "🔍 单标的详情", "📋 数据总表"])

# ---------- Tab 1 ----------
with tab1:
    valid_compare = [i for i in selected_ids if i in data_map]
    if len(valid_compare) < 1:
        st.info("请在左侧选择至少一个资产。")
    else:
        if normalize:
            st.caption("所有标的起点归一化为 100，方便横向比较相对强弱。")
        else:
            st.caption(
                "显示选中资产的原始点位。不同数量级差异较大的资产（如 SPX 与 VIX）"
                "可能难以在同一纵轴上分辨，建议按需勾选或切换回归一化模式。"
            )
        st.plotly_chart(
            compare_chart(data_map, valid_compare, normalize),
            width="stretch",
            config={"displayModeBar": False},
        )

# ---------- Tab 2 ----------
with tab2:
    detail_ids = [i for i in selected_ids if i in data_map]
    if not detail_ids:
        st.info("暂无可用数据。")
    else:
        pick = st.selectbox(
            "选择标的",
            options=detail_ids,
            format_func=lambda x: f'{ASSET_MAP[x]["name"]}（{ASSET_MAP[x]["ticker"]}）',
            key="detail_pick",
        )

        s = data_map[pick].dropna()
        a = ASSET_MAP[pick]

        c1, c2, c3, c4, c5 = st.columns(5)
        last = float(s.iloc[-1])
        d1 = pct_change(s, 1)
        w1 = pct_change(s, 5)
        m1 = pct_change(s, 21)
        rng = pct_change(s, len(s) - 1)

        c1.metric("最新", f'{last:,.{a["decimals"]}f}')
        c2.metric("日涨跌", "—" if np.isnan(d1) else f"{d1:+.2f}%")
        c3.metric("周涨跌", "—" if np.isnan(w1) else f"{w1:+.2f}%")
        c4.metric("月涨跌", "—" if np.isnan(m1) else f"{m1:+.2f}%")
        c5.metric("区间涨跌", "—" if np.isnan(rng) else f"{rng:+.2f}%")

        st.plotly_chart(
            detail_chart(s, a),
            width=True,
            config={"displayModeBar": False},
        )

        st.info(NOTES.get(pick, ""))

        # 单标的 CSV 下载
        dl = s.rename("收盘价").to_frame()
        dl.index.name = "日期"
        st.download_button(
            "⬇️ 下载该标的日度数据 (CSV)",
            data=dl.to_csv().encode("utf-8-sig"),
            file_name=f'{a["id"]}_daily.csv',
            mime="text/csv",
        )

# ---------- Tab 3 ----------
with tab3:
    df = build_summary(data_map)
    if df.empty:
        st.info("暂无数据。")
    else:
        show = df.drop(columns=["_id"]).copy()

        st.dataframe(
            show,
            width=True,
            hide_index=True,
            column_config={
                "资产": st.column_config.TextColumn(width="medium"),
                "代码": st.column_config.TextColumn(width="small"),
                "最新": st.column_config.NumberColumn(format="%.4f"),
                "日涨跌%": st.column_config.NumberColumn(format="%.2f%%"),
                "周涨跌%": st.column_config.NumberColumn(format="%.2f%%"),
                "月涨跌%": st.column_config.NumberColumn(format="%.2f%%"),
                "区间涨跌%": st.column_config.NumberColumn(format="%.2f%%"),
                "区间高": st.column_config.NumberColumn(format="%.4f"),
                "区间低": st.column_config.NumberColumn(format="%.4f"),
                "分类": st.column_config.TextColumn(width="small"),
            },
        )

        # 合并全部日度数据导出
        merged = pd.DataFrame()
        for aid, s in data_map.items():
            merged[ASSET_MAP[aid]["name"]] = s
        merged.index.name = "日期"
        merged = merged.sort_index()

        st.download_button(
            "⬇️ 下载全部标的日度数据 (CSV)",
            data=merged.to_csv().encode("utf-8-sig"),
            file_name=f"global_flow_{end_date}.csv",
            mime="text/csv",
        )

# ============================================================
# 全局样式
# ============================================================
st.markdown("""
<style>
div[data-testid="stMetricValue"] { font-size: 1.3rem !important; font-weight: 700; }
div[data-testid="stMetricDelta"] { font-size: 0.85rem !important; }
@media (max-width: 600px) {
    div[data-testid="stMetricValue"] { font-size: 1.1rem !important; }
    div[data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
}
.main-title {
    background: linear-gradient(90deg, #1F4E78, #2E75B6);
    color: white;
    padding: 20px 24px;
    border-radius: 12px;
    margin-bottom: 20px;
}
.main-title h1 { margin: 0; font-size: 1.6rem; }
.main-title p { margin: 6px 0 0 0; font-size: 0.85rem; opacity: 0.85; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 页脚信息
# ============================================================
st.divider()
st.caption(
    "数据来源：Yahoo Finance（通过 yfinance 获取），缓存有效期 1 小时。"
    "本页面仅用于趋势观察，所有数据为公开市场信息的整理，不构成任何投资建议。"
)
