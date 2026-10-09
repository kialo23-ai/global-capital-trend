# app.py
# 全球资金趋势 · Streamlit 版本（日度更新）
# 依赖: streamlit, yfinance, pandas, numpy, plotly

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, date, timedelta

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


# ============================================================
# 资产配置
# ============================================================
ASSETS = [
    {
        "id": "dxy", "name": "美元指数", "ticker": "DXY",
        "symbols": ["DX-Y.NYB", "DX=F"], "unit": "", "decimals": 2,
        "color": "#5b8def", "scale": 1.0, "group": "汇率",
    },
    {
        "id": "gold", "name": "黄金", "ticker": "XAU",
        "symbols": ["GC=F", "XAUUSD=X"], "unit": "美元/盎司", "decimals": 0,
        "color": "#ffc043", "scale": 1.0, "group": "贵金属",
    },
    {
        "id": "brent", "name": "布伦特原油", "ticker": "BRENT",
        "symbols": ["BZ=F", "CL=F"], "unit": "美元/桶", "decimals": 2,
        "color": "#8b8fa3", "scale": 1.0, "group": "能源",
    },
    {
        "id": "copper", "name": "LME铜", "ticker": "COPPER",
        "symbols": ["HG=F"], "unit": "美元/吨", "decimals": 0,
        "color": "#e8853a", "scale": 2204.62, "group": "工业金属",
        # COMEX铜(美元/磅) × 2204.62 ≈ 美元/吨
    },
    {
        "id": "spx", "name": "标普500", "ticker": "SPX",
        "symbols": ["^GSPC"], "unit": "", "decimals": 0,
        "color": "#4ea8de", "scale": 1.0, "group": "股指",
    },
    {
        "id": "ndx", "name": "纳斯达克", "ticker": "IXIC",
        "symbols": ["^IXIC"], "unit": "", "decimals": 0,
        "color": "#7c6af0", "scale": 1.0, "group": "股指",
    },
    {
        "id": "ust10y", "name": "美债10年期", "ticker": "US10Y",
        "symbols": ["^TNX"], "unit": "%", "decimals": 3,
        "color": "#ef5777", "scale": 1.0, "group": "利率",
    },
    {
        "id": "vix", "name": "VIX恐慌指数", "ticker": "VIX",
        "symbols": ["^VIX"], "unit": "", "decimals": 2,
        "color": "#f7b731", "scale": 1.0, "group": "波动率",
    },
    {
        "id": "btc", "name": "比特币", "ticker": "BTC",
        "symbols": ["BTC-USD"], "unit": "美元", "decimals": 0,
        "color": "#f7931a", "scale": 1.0, "group": "加密",
    },
    {
        "id": "cny", "name": "美元兑人民币", "ticker": "USDCNY",
        "symbols": ["CNY=X"], "unit": "", "decimals": 4,
        "color": "#26c6a8", "scale": 1.0, "group": "汇率",
    },
]

ASSET_MAP = {a["id"]: a for a in ASSETS}

# 说明文案
NOTES = {
    "dxy":  "美元指数衡量美元对一篮子主要货币的强弱。指数下行代表美元贬值，通常利多黄金、大宗商品与新兴市场资产。",
    "gold": "COMEX 黄金期货主力合约，以美元/盎司计价。避险属性与抗通胀属性使其成为资金流向的重要观察指标。",
    "brent": "布伦特原油期货，全球原油定价基准。价格受地缘政治、OPEC+ 产量政策与全球需求预期共同驱动。",
    "copper": "COMEX 铜期货折算为美元/吨，与 LME 铜走势高度一致。铜被称为「铜博士」，对全球制造业景气度极为敏感。",
    "spx":  "标普500指数，美国大盘股基准。是观察全球风险偏好与美股资金流向的核心指标。",
    "ndx":  "纳斯达克综合指数，以科技股为主。对利率变化与 AI 产业叙事高度敏感，波动大于标普500。",
    "ust10y": "美国10年期国债收益率（^TNX）。作为全球资产定价的「利率锚」，上行通常压制成长股与黄金，利多美元。",
    "vix":  "CBOE 波动率指数，衡量标普500未来30天的隐含波动率。通常与股市负相关，是市场恐慌情绪的「温度计」。",
    "btc":  "比特币现货价格（美元），7×24 小时交易。近年机构资金通过现货 ETF 大量参与，已成为风险偏好的领先指标之一。",
    "cny":  "美元兑人民币在岸汇率。数值下行代表人民币升值，数值上行代表人民币贬值。",
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
# 数据获取
# ============================================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_series(symbols: tuple, start_str: str, end_str: str, scale: float):
    """按顺序尝试多个 symbol，返回收盘价 Series。"""
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

            # 去除时区
            try:
                s.index = pd.to_datetime(s.index).tz_localize(None)
            except Exception:
                s.index = pd.to_datetime(s.index)

            s = s.astype(float) * float(scale)

            # ^TNX 异常防护：若数值 > 20，说明是放大 10 倍，需还原
            if s.iloc[-1] > 20 and "TNX" in sym.upper():
                s = s / 10.0

            return s

        except Exception:
            continue

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
        s = fetch_series(tuple(a["symbols"]), start_str, end_str, a["scale"])
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
    xaxis=dict(gridcolor="#1a2334", zeroline=False,
               showspikes=True, spikecolor="#3a4459", spikethickness=1),
    yaxis=dict(gridcolor="#1a2334", zeroline=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                bgcolor="rgba(0,0,0,0)"),
)


def detail_chart(series: pd.Series, meta: dict):
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
    fig.update_layout(
        **PLOT_BASE,
        height=340,
        showlegend=False,
        yaxis=dict(gridcolor="#1a2334", zeroline=False,
                   range=[float(series.min()) - pad, float(series.max()) + pad]),
        xaxis=dict(gridcolor="#1a2334", zeroline=False,
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
                   showspikes=True, spikecolor="#3a4459", spikethickness=1),
    )
    return fig


def compare_chart(data_map, selected):
    fig = go.Figure()
    for aid in selected:
        a = ASSET_MAP[aid]
        s = data_map[aid].dropna()
        if len(s) < 2:
            continue
        norm = s / s.iloc[0] * 100.0
        fig.add_trace(go.Scatter(
            x=norm.index, y=norm.values,
            mode="lines", name=a["name"],
            line=dict(color=a["color"], width=1.8),
            hovertemplate=f"<b>{a['name']}</b> %{{y:.1f}}<extra></extra>",
        ))

    fig.add_hline(y=100, line_dash="dot", line_color="#3a4459", line_width=1)
    fig.update_layout(**PLOT_BASE, height=430)
    fig.update_yaxes(title_text="基期 = 100", title_font=dict(size=11, color="#4a5670"))
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
            "分组": a["group"],
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
    st.markdown("**对比图标的**")
    compare_ids = st.multiselect(
        "归一化对比",
        options=selected_ids if selected_ids else default_ids,
        default=(selected_ids or default_ids)[:6],
        format_func=lambda x: ASSET_MAP[x]["name"],
        label_visibility="collapsed",
    )

    st.divider()
    if st.button("🔄 强制刷新数据", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption("缓存有效期 1 小时，点按钮可立即重新拉取。")

if not selected_ids:
    st.warning("请在左侧至少选择一个资产。")
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
# 卡片网格
# ============================================================
cards_html = []
for aid, s in data_map.items():
    a = ASSET_MAP[aid]
    s = s.dropna()
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

    # 为了 sparkline 性能，最多取 260 个点
    spark_vals = s.values[-260:] if len(s) > 260 else s.values
    spark = sparkline_svg(spark_vals, a["color"], uid=f'c{aid}')

    cards_html.append(
        f'<div class="card" style="--c:{a["color"]}">'
        f'<div class="c-head"><span class="c-dot"></span>'
        f'<span class="c-name">{a["name"]}</span>'
        f'<span class="c-tick">{a["ticker"]}</span></div>'
        f'<div class="c-val">{val_str}{unit_html}</div>'
        f'<div class="c-chg {cls}"><span class="arrow">{arrow}</span>{abs(chg):.2f}%'
        f'<span style="color:#48546e;font-weight:400;font-size:10px">区间</span></div>'
        f'{spark}'
        f'</div>'
    )

if cards_html:
    st.markdown('<div class="grid">' + "".join(cards_html) + "</div>", unsafe_allow_html=True)

st.write("")

# ============================================================
# 标签页
# ============================================================
tab1, tab2, tab3 = st.tabs(["📊 归一化对比", "🔍 单标的详情", "📋 数据总表"])

# ---------- Tab 1 ----------
with tab1:
    valid_compare = [i for i in compare_ids if i in data_map]
    if len(valid_compare) < 1:
        st.info("请在左侧选择至少一个对比标的。")
    else:
        st.caption("所有标的起点归一化为 100，方便横向比较相对强弱。")
        st.plotly_chart(
            compare_chart(data_map, valid_compare),
            use_container_width=True,
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
            use_container_width=True,
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
            use_container_width=True,
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
                "分组": st.column_config.TextColumn(width="small"),
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
# 页脚
# ============================================================
st.divider()
st.caption(
    "数据来源：Yahoo Finance（通过 yfinance 获取），缓存有效期 1 小时。"
    "本页面仅用于趋势观察，所有数据为公开市场信息的整理，不构成任何投资建议。"
)    div[data-testid="stMetricValue"] { font-size: 1.3rem !important; font-weight: 700; }
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

st.markdown("""
<div class="main-title">
    <h1>🌐 全球资本趋势</h1>
    <p>Global Capital Trend · 数据自动刷新</p>
</div>
""", unsafe_allow_html=True)

# ==================== FRED 初始化 ====================
try:
    FRED_API_KEY = st.secrets["FRED_API_KEY"]
except Exception:
    FRED_API_KEY = ""

@st.cache_resource
def get_fred_client():
    return Fred(api_key=FRED_API_KEY)

fred = get_fred_client()

# ==================== 数据获取函数 ====================

@st.cache_data(ttl=3600)
def get_fred_latest(series_id):
    """获取 FRED 序列的最新值和前值"""
    try:
        data = fred.get_series(series_id)
        data = data.dropna()
        if len(data) >= 2:
            return float(data.iloc[-1]), float(data.iloc[-2])
        return None, None
    except Exception as e:
        return None, None

@st.cache_data(ttl=600)
def get_yf_latest(ticker):
    """获取 yfinance 的最新收盘价和前一日收盘价"""
    try:
        data = yf.Ticker(ticker).history(period="5d")
        if len(data) >= 2:
            return float(data['Close'].iloc[-1]), float(data['Close'].iloc[-2])
        return None, None
    except Exception:
        return None, None

def calc_delta(current, previous):
    """计算变化率"""
    if current is None or previous is None or previous == 0:
        return 0.0
    return (current - previous) / previous

# ==================== 指标配置 ====================
# 每个指标: (大类图标, 名称, 数据源类型, 标识符, 单位, 信号方向)
# 信号方向: "normal" 涨=流入; "inverse" 涨=撤离(如收益率)
INDICATORS = [
    # --- 股 ---
    ("📈", "标普500", "yf", "^GSPC", "点", "normal"),
    ("📈", "纳斯达克", "yf", "^IXIC", "点", "normal"),
    ("📈", "道琼斯", "yf", "^DJI", "点", "normal"),
    ("📈", "罗素2000", "yf", "^RUT", "点", "normal"),
    ("📈", "费城半导体", "yf", "^SOX", "点", "normal"),
    ("📈", "德国DAX", "yf", "^GDAXI", "点", "normal"),
    ("📈", "英国富时100", "yf", "^FTSE", "点", "normal"),
    ("📈", "法国CAC40", "yf", "^FCHI", "点", "normal"),
    ("📈", "日经225", "yf", "^N225", "点", "normal"),
    ("📈", "韩国KOSPI", "yf", "^KS11", "点", "normal"),
    ("📈", "澳洲标普200", "yf", "^AXJO", "点", "normal"),
    ("📈", "印度Nifty50", "yf", "^NSEI", "点", "normal"),
    ("📈", "巴西IBOVESPA", "yf", "^BVSP", "点", "normal"),
    ("📈", "恒生指数", "yf", "^HSI", "点", "normal"),
    ("📈", "恒生科技", "yf", "^HSTECH", "点", "normal"),
    ("📈", "上证指数", "yf", "000001.SS", "点", "normal"),
    ("📈", "沪深300", "yf", "000300.SS", "点", "normal"),

    # --- 债 ---
    ("📊", "美债2年期", "fred", "DGS2", "%", "inverse"),
    ("📊", "美债10年期", "fred", "DGS10", "%", "inverse"),
    ("📊", "美债30年期", "fred", "DGS30", "%", "inverse"),
    ("📊", "10Y-2Y利差", "fred", "T10Y2Y", "%", "normal"),
    ("📊", "投资级债利差", "fred", "BAMLC0A0CM", "%", "inverse"),
    ("📊", "高收益债利差", "fred", "BAMLH0A0HYM2", "%", "inverse"),

    # --- 汇 ---
    ("💱", "美元指数DXY", "yf", "DX-Y.NYB", "点", "normal"),
    ("💱", "美元广义指数", "fred", "DTWEXBGS", "指数", "normal"),
    ("💱", "欧元/美元", "yf", "EURUSD=X", "汇率", "normal"),
    ("💱", "美元/日元", "yf", "JPY=X", "汇率", "normal"),
    ("💱", "英镑/美元", "yf", "GBPUSD=X", "汇率", "normal"),
    ("💱", "美元/人民币", "yf", "CNY=X", "汇率", "normal"),

    # --- 商品 ---
    ("🛢", "WTI原油", "yf", "CL=F", "美元/桶", "normal"),
    ("🛢", "布伦特原油", "yf", "BZ=F", "美元/桶", "normal"),
    ("🥇", "COMEX黄金", "yf", "GC=F", "美元/盎司", "normal"),
    ("🥈", "COMEX白银", "yf", "SI=F", "美元/盎司", "normal"),
    ("🔩", "COMEX铜", "yf", "HG=F", "美元/磅", "normal"),
    ("🌾", "CBOT大豆", "yf", "ZS=F", "美分/蒲式耳", "normal"),
    ("🌾", "CBOT玉米", "yf", "ZC=F", "美分/蒲式耳", "normal"),

    # --- 加密 ---
    ("💎", "比特币", "yf", "BTC-USD", "美元", "normal"),
    ("💎", "以太坊", "yf", "ETH-USD", "美元", "normal"),

    # --- 资本流 ---
    ("🌊", "美联储总资产", "fred", "WALCL", "百万美元", "normal"),
    ("🚢", "全球供应链压力", "fred", "GSCPI", "指数", "normal"),
]

# ==================== 渲染看板 ====================

categories = {
    "📈": "股 · 股票资金流",
    "📊": "债 · 债券资金流",
    "💱": "汇 · 外汇资金流",
    "🛢": "商品 · 能源",
    "🥇": "商品 · 贵金属",
    "🥈": "商品 · 贵金属",
    "🔩": "商品 · 工业金属",
    "🌾": "商品 · 农产品",
    "💎": "加密资产",
    "🌊": "资本流 · 美元流动性",
    "🚢": "贸易流 · 实体联通",
}

# 每个指标的流入方向
FLOW_DIRECTION = {
    "标普500": "price_up", "纳斯达克": "price_up", "道琼斯": "price_up",
    "罗素2000": "price_up", "费城半导体": "price_up", "德国DAX": "price_up",
    "英国富时100": "price_up", "法国CAC40": "price_up", "日经225": "price_up",
    "韩国KOSPI": "price_up", "澳洲标普200": "price_up", "印度Nifty50": "price_up",
    "巴西IBOVESPA": "price_up", "恒生指数": "price_up", "恒生科技": "price_up",
    "上证指数": "price_up", "沪深300": "price_up",

    "美债2年期": "price_down", "美债10年期": "price_down", "美债30年期": "price_down",
    "10Y-2Y利差": "price_up", "投资级债利差": "price_down", "高收益债利差": "price_down",

    "美元指数DXY": "dollar_up", "美元广义指数": "dollar_up",
    "欧元/美元": "price_up", "美元/日元": "price_up",
    "英镑/美元": "price_up", "美元/人民币": "price_up",

    "WTI原油": "price_up", "布伦特原油": "price_up",
    "COMEX黄金": "price_up", "COMEX白银": "price_up", "COMEX铜": "price_up",
    "CBOT大豆": "price_up", "CBOT玉米": "price_up",

    "比特币": "price_up", "以太坊": "price_up",

    "美联储总资产": "price_up", "全球供应链压力": "price_down",
}

def render_card(icon, name, value_str, unit, delta_pct, is_inflow, use_china=True):
    """渲染单个卡片。use_china=True 时红涨绿跌，否则绿涨红跌。"""
    if use_china:
        color = "#cf222e" if is_inflow else "#1a7f37"
        bg = "#fff0f0" if is_inflow else "#f0fff4"
    else:
        color = "#1a7f37" if is_inflow else "#cf222e"
        bg = "#f0fff4" if is_inflow else "#fff0f0"

    arrow = "↑" if is_inflow else "↓"
    signal_text = "流入" if is_inflow else "撤离"

    html = f"""
    <div style="
        background: {bg};
        border-left: 4px solid {color};
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    ">
        <div style="font-size: 0.8rem; color: #555; margin-bottom: 3px;">
            {icon} {name}
        </div>
        <div style="font-size: 1.05rem; font-weight: 700; color: #222; margin-bottom: 3px;">
            {value_str} <span style="font-size: 0.75rem; color: #888;">{unit}</span>
        </div>
        <div style="font-size: 0.8rem; color: {color}; font-weight: 600;">
            {arrow} {signal_text} ({delta_pct:+.2%})
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ==================== 配色方案切换 ====================
color_scheme = st.sidebar.radio(
    "配色方案",
    ["中国配色（红涨绿跌）", "国际配色（绿涨红跌）"],
    index=0
)
use_china = color_scheme.startswith("中国")

# ==================== 第一步：收集所有数据，按流入/撤离分类 ====================
data_by_flow = {"outflow": {}, "inflow": {}}

for cat_icon in ["📈", "📊", "💱", "🛢", "🥇", "🥈", "🔩", "🌾", "💎", "🌊", "🚢"]:
    items = [ind for ind in INDICATORS if ind[0] == cat_icon]
    if not items:
        continue

    data_by_flow["outflow"][cat_icon] = []
    data_by_flow["inflow"][cat_icon] = []

    for (icon, name, source, ticker, unit, direction) in items:
        if source == "fred":
            current, previous = get_fred_latest(ticker)
        else:
            current, previous = get_yf_latest(ticker)

        if current is None or previous is None:
            data_by_flow["outflow"][cat_icon].append((icon, name, "—", unit, 0.0, False))
            continue

        delta_pct = calc_delta(current, previous)
        flow = FLOW_DIRECTION.get(name, "price_up")

        if flow == "price_up":
            is_inflow = delta_pct > 0
        elif flow == "price_down":
            is_inflow = delta_pct < 0
        elif flow == "dollar_up":
            is_inflow = delta_pct > 0
        else:
            is_inflow = delta_pct > 0

        if current >= 1_000_000:
            value_str = f"{current:,.0f}"
        elif current >= 100:
            value_str = f"{current:,.2f}"
        elif current >= 1:
            value_str = f"{current:.4f}"
        else:
            value_str = f"{current:.6f}"

        if is_inflow:
            data_by_flow["inflow"][cat_icon].append((icon, name, value_str, unit, delta_pct, True))
        else:
            data_by_flow["outflow"][cat_icon].append((icon, name, value_str, unit, delta_pct, False))

# ==================== 第二步：渲染两个大板块 ====================

def render_section(flow_key, title, use_china):
    """渲染一个大板块：标题 + 内部按大类分组"""
    total = sum(len(cards) for cards in data_by_flow[flow_key].values())

    # 根据配色方案和板块决定标题颜色
    if flow_key == "outflow":
        arrow_char = "←"
        if use_china:
            title_color = "#1a7f37"   # 中国配色：撤离=绿色
        else:
            title_color = "#cf222e"   # 国际配色：撤离=红色
    else:  # inflow
        arrow_char = "→"
        if use_china:
            title_color = "#cf222e"   # 中国配色：流入=红色
        else:
            title_color = "#1a7f37"   # 国际配色：流入=绿色

    st.markdown(f"""
    <div style="
        background: {title_color};
        color: white;
        padding: 12px 20px;
        border-radius: 10px;
        margin: 20px 0 16px 0;
        font-size: 1.2rem;
        font-weight: 700;
    ">
        {arrow_char} {title} · 共 {total} 项
    </div>
    """, unsafe_allow_html=True)

    for cat_icon in ["📈", "📊", "💱", "🛢", "🥇", "🥈", "🔩", "🌾", "💎", "🌊", "🚢"]:
        cards = data_by_flow[flow_key].get(cat_icon, [])
        if not cards:
            continue

        cat_name = categories.get(cat_icon, cat_icon)
        st.markdown(f"**{cat_icon} {cat_name}**")

        cols = st.columns(4)
        for i, (icon, name, value_str, unit, delta_pct, is_inflow) in enumerate(cards):
            with cols[i % 4]:
                render_card(icon, name, value_str, unit, delta_pct, is_inflow, use_china)

        st.markdown("")

# 渲染撤离板块
render_section("outflow", "撤离 / Outflow", use_china)

# 渲染流入板块
render_section("inflow", "流入 / Inflow", use_china)

st.caption(f"数据自动刷新 · 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
