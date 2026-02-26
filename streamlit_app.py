import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Puey Greenroof",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Theme Detection ────────────────────────────────────────────────────────────
_theme_base = st.get_option("theme.base") or "light"
IS_DARK = _theme_base == "dark"

# ─── Theme Tokens ───────────────────────────────────────────────────────────────
if IS_DARK:
    T = dict(
        card_bg="#1A1D24",
        card_border="#2D333B",
        text_primary="#E6EDF3",
        text_secondary="#8B949E",
        text_muted="#6E7681",
        status_dot="#34D399",
        plotly_template="plotly_dark",
        plotly_paper="rgba(0,0,0,0)",
        plotly_plot="rgba(0,0,0,0)",
        plotly_grid="#21262D",
        plotly_font="#8B949E",
        btn_bg="#1A1D24",
        btn_border="#2D333B",
        btn_text="#C9D1D9",
    )
else:
    T = dict(
        card_bg="#FFFFFF",
        card_border="#E8ECF0",
        text_primary="#111827",
        text_secondary="#6B7280",
        text_muted="#9CA3AF",
        status_dot="#34D399",
        plotly_template="plotly_white",
        plotly_paper="rgba(0,0,0,0)",
        plotly_plot="rgba(0,0,0,0)",
        plotly_grid="#F0F1F3",
        plotly_font="#4B5563",
        btn_bg="#F9FAFB",
        btn_border="#D1D5DB",
        btn_text="#374151",
    )

# ─── Custom CSS (theme-aware) ───────────────────────────────────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {{ font-family: 'Inter', sans-serif; }}
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
        font-size: 0.85rem;
    }}

    /* Cards */
    .card {{
        background: {T['card_bg']};
        border: 1px solid {T['card_border']};
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
    }}
    .card-title {{
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: {T['text_secondary']};
        margin-bottom: 0.75rem;
    }}

    /* Section titles (no card) */
    .section-title {{
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: {T['text_secondary']};
        margin-bottom: 0.25rem;
        margin-top: 1rem;
    }}

    /* Sidebar */
    .sidebar-brand {{
        font-size: 1.25rem;
        font-weight: 700;
        color: {T['text_primary']};
        padding: 0.5rem 0 1rem 0;
        border-bottom: 1px solid {T['card_border']};
        margin-bottom: 1rem;
    }}
    .sidebar-section {{
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: {T['text_muted']};
        margin: 1.25rem 0 0.5rem 0;
    }}

    /* Status bar */
    .status-bar {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.75rem;
        color: {T['text_muted']};
        padding: 0.25rem 0 0.75rem 0;
    }}
    .status-dot {{
        width: 6px; height: 6px;
        background: {T['status_dot']};
        border-radius: 50%;
        display: inline-block;
    }}

    /* Hide footer only */
    footer {{ display: none !important; }}
</style>
""", unsafe_allow_html=True)


# ─── Constants ──────────────────────────────────────────────────────────────────
COLORS = {
    'S1':   '#0F4C81',
    'S2':   '#D55E00',
    'K1S1': '#0F4C81',
    'K2S1': '#56B4E9',
    'K1S2': '#D55E00',
    'K2S2': '#E69F00',
}

# Brighter variants for dark mode so traces stay readable
if IS_DARK:
    COLORS.update({
        'S1':   '#4A9FD8',
        'K1S1': '#4A9FD8',
        'K2S1': '#7FC8F8',
        'S2':   '#F28C28',
        'K1S2': '#F28C28',
        'K2S2': '#FFD166',
    })

SHEET_S1 = ("1yoRrYDPAvIBfL3eVFYQ-rxDZAuTNzWq1KxAjBuHBReI", "0")
SHEET_S2 = ("1Tw7w08rW02abAAI6b3brXqlTRBBHGZ3Bf0H4CK2v4_U", "0")

CHART_LAYOUT_DEFAULTS = dict(
    template=T['plotly_template'],
    paper_bgcolor=T['plotly_paper'],
    plot_bgcolor=T['plotly_plot'],
    font=dict(color=T['plotly_font'], size=11, family='Inter'),
    xaxis=dict(showgrid=False),
    yaxis=dict(gridcolor=T['plotly_grid'], tickformat="g"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    margin=dict(t=40, b=50, l=10, r=10),
)


# ─── Helper Functions ───────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_sheet(sheet_id: str, gid: str) -> pd.DataFrame:
    """Fetch a Google Sheet as CSV and return a DataFrame."""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    return pd.read_csv(url)


@st.cache_data
def to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode('utf-8')


def process_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """Convert DS3231 column to Asia/Bangkok local time."""
    df = df.copy()
    df['local_time'] = (
        pd.to_datetime(df['DS3231'], errors='coerce')
        .dt.tz_localize('UTC')
        .dt.tz_convert('Asia/Bangkok')
    )
    df.dropna(subset=['local_time'], inplace=True)
    return df


def hex_to_rgba(color: str, alpha: float) -> str:
    """Convert hex color to rgba string."""
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ─── Auto-refresh ──────────────────────────────────────────────────────────────
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 300:
    st.session_state.last_refresh = time.time()
    st.rerun()


# ─── Sidebar ────────────────────────────────────────────────────────────────────

if st.sidebar.button("↻ Refresh Data", use_container_width=True):
    fetch_sheet.clear()
    st.session_state.last_refresh = time.time()
    st.rerun()

st.sidebar.markdown('<div class="sidebar-section">Date & Time Filters</div>', unsafe_allow_html=True)

col_d, col_t = st.sidebar.columns(2)
with col_d:
    selected_date = st.date_input("Start Date", pd.to_datetime("2026-02-25").date())
with col_t:
    selected_time = st.time_input("Start Time", pd.to_datetime("19:30:00").time())

enable_end = st.sidebar.checkbox("Enable End Date Filter", value=False)
selected_end_date, selected_end_time = None, None
if enable_end:
    col_ed, col_et = st.sidebar.columns(2)
    with col_ed:
        selected_end_date = st.date_input("End Date", pd.to_datetime("2026-02-26").date())
    with col_et:
        selected_end_time = st.time_input("End Time", pd.to_datetime("23:59:00").time())


# ─── Fetch & Process Data ───────────────────────────────────────────────────────
with st.spinner("Loading sensor data…"):
    raw_s1 = fetch_sheet(*SHEET_S1)
    raw_s2 = fetch_sheet(*SHEET_S2)

station1 = process_timestamps(raw_s1)
station2 = process_timestamps(raw_s2)

start_dt = pd.to_datetime(f"{selected_date} {selected_time}").tz_localize('Asia/Bangkok')
filt1 = station1[station1['local_time'] >= start_dt].copy()
filt2 = station2[station2['local_time'] >= start_dt].copy()

if enable_end and selected_end_date and selected_end_time:
    end_dt = pd.to_datetime(f"{selected_end_date} {selected_end_time}").tz_localize('Asia/Bangkok')
    filt1 = filt1[filt1['local_time'] <= end_dt]
    filt2 = filt2[filt2['local_time'] <= end_dt]


# ─── Compute latest datapoint timestamp ────────────────────────────────────────
latest_timestamps = []
if not filt1.empty:
    latest_timestamps.append(filt1['local_time'].max())
if not filt2.empty:
    latest_timestamps.append(filt2['local_time'].max())

if latest_timestamps:
    latest_datapoint = max(latest_timestamps).strftime("%Y-%m-%d %H:%M:%S")
else:
    latest_datapoint = "N/A"


# ─── Sidebar Downloads ─────────────────────────────────────────────────────────
st.sidebar.markdown('<div class="sidebar-section">Export Data</div>', unsafe_allow_html=True)
dl1, dl2 = st.sidebar.columns(2)
if not filt1.empty:
    dl1.download_button("⬇ Station 1", data=to_csv(filt1), file_name='station1.csv', mime='text/csv', use_container_width=True)
if not filt2.empty:
    dl2.download_button("⬇ Station 2", data=to_csv(filt2), file_name='station2.csv', mime='text/csv', use_container_width=True)


# ─── Main Title ─────────────────────────────────────────────────────────────────
st.title("Puey Greenroof Dashboard")

# ─── Status Bar ─────────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="status-bar">'
    f'<span class="status-dot"></span> Last synced: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    f' · Auto-refresh every 5 min'
    f' · {len(filt1)} + {len(filt2)} records'
    f' · Latest datapoint: {latest_datapoint}'
    f'</div>',
    unsafe_allow_html=True,
)


# ─── Plotting Functions ─────────────────────────────────────────────────────────
def create_box_plot(df1: pd.DataFrame, df2: pd.DataFrame) -> go.Figure:
    """
    Create box plots where each box at a given timestamp is computed from the
    10 sub-sensor readings (e.g. KIT1-1 through KIT1-10).

    Result: 4 box plot groups per timestamp:
      - KIT1 · S1  (KIT1-1 … KIT1-10 from Station 1)
      - KIT2 · S1  (KIT2-1 … KIT2-10 from Station 1)
      - KIT1 · S2  (KIT1-1 … KIT1-10 from Station 2)
      - KIT2 · S2  (KIT2-1 … KIT2-10 from Station 2)
    """
    fig = go.Figure()

    kit1_cols = [f'KIT1-{i}' for i in range(1, 11)]
    kit2_cols = [f'KIT2-{i}' for i in range(1, 11)]

    configs = [
        (kit1_cols, df1, 'KIT1 · S1', COLORS['K1S1']),
        (kit2_cols, df1, 'KIT2 · S1', COLORS['K2S1']),
        (kit1_cols, df2, 'KIT1 · S2', COLORS['K1S2']),
        (kit2_cols, df2, 'KIT2 · S2', COLORS['K2S2']),
    ]

    box_vis, line_vis, both_vis = [], [], []

    for sensor_cols, df_src, trace_name, color in configs:
        available = [c for c in sensor_cols if c in df_src.columns]
        if not available or df_src.empty:
            continue

        # Melt the 10 sub-sensor columns into long format so each timestamp
        # has up to 10 values → enough for a real box with Q1, median, Q3
        melted = df_src[['local_time'] + available].melt(
            id_vars='local_time', value_vars=available,
            var_name='sub_sensor', value_name='value'
        ).dropna(subset=['value', 'local_time'])

        if melted.empty:
            continue

        # Pre-compute stats per timestamp for explicit box rendering
        grouped = melted.groupby('local_time')['value']
        stats = grouped.agg(['median', 'count']).reset_index()
        q1 = grouped.quantile(0.25).reset_index(name='q1')
        q3 = grouped.quantile(0.75).reset_index(name='q3')
        stats = stats.merge(q1, on='local_time').merge(q3, on='local_time')
        stats['iqr'] = stats['q3'] - stats['q1']
        stats['lower_fence'] = stats['q1'] - 1.5 * stats['iqr']
        stats['upper_fence'] = stats['q3'] + 1.5 * stats['iqr']
        # Clamp fences to actual observed min/max per timestamp
        bin_mins = grouped.min().reset_index(name='vmin')
        bin_maxs = grouped.max().reset_index(name='vmax')
        stats = stats.merge(bin_mins, on='local_time').merge(bin_maxs, on='local_time')
        stats['lower_fence'] = stats[['lower_fence', 'vmin']].max(axis=1)
        stats['upper_fence'] = stats[['upper_fence', 'vmax']].min(axis=1)

        # ── Box trace with explicit statistics ──
        fig.add_trace(go.Box(
            x=stats['local_time'],
            lowerfence=stats['lower_fence'],
            q1=stats['q1'],
            median=stats['median'],
            q3=stats['q3'],
            upperfence=stats['upper_fence'],
            name=trace_name,
            marker=dict(color=color, size=4),
            line=dict(color=color, width=1.5),
            fillcolor=hex_to_rgba(color, 0.25 if IS_DARK else 0.20),
            whiskerwidth=0.5,
            legendgroup=trace_name,
            showlegend=True,
            visible=False,
        ))

        # ── Line trace (median over time) ──
        fig.add_trace(go.Scatter(
            x=stats['local_time'],
            y=stats['median'],
            mode='lines+markers',
            name=trace_name,
            line=dict(color=color, width=2),
            marker=dict(size=4),
            legendgroup=trace_name,
            showlegend=True,
            visible=True,
        ))

        box_vis.extend([True, False])
        line_vis.extend([False, True])
        both_vis.extend([True, True])

    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        boxmode='group',
        yaxis_title="Sensor Value",
        height=480,
        updatemenus=[dict(
            type="buttons",
            direction="right",
            active=0,
            x=0.0, y=1.13,
            xanchor="left", yanchor="bottom",
            buttons=[
                dict(label="  Lines  ", method="restyle", args=[{"visible": line_vis}]),
                dict(label="  Box Plots  ", method="restyle", args=[{"visible": box_vis}]),
                dict(label="  Both  ", method="restyle", args=[{"visible": both_vis}]),
            ],
            pad=dict(r=8, t=8),
            showactive=True,
            font=dict(size=11, color=T['btn_text']),
            bgcolor=T['btn_bg'],
            bordercolor=T['btn_border'],
            borderwidth=1,
        )],
    )

    return fig


def create_temperature_chart(df1: pd.DataFrame, df2: pd.DataFrame) -> go.Figure:
    """Create a clean temperature comparison line chart."""
    fig = go.Figure()
    temp_col = 'DS18B20 Temperature (°C)'

    for df, name, color in [(df1, 'Station 1', COLORS['S1']), (df2, 'Station 2', COLORS['S2'])]:
        if temp_col not in df.columns:
            continue
        valid = df.dropna(subset=[temp_col, 'local_time'])
        if valid.empty:
            continue
        fig.add_trace(go.Scatter(
            x=valid['local_time'],
            y=valid[temp_col],
            mode='lines',
            name=name,
            line=dict(color=color, width=1.8),
            fill='tozeroy',
            fillcolor=hex_to_rgba(color, 0.08 if IS_DARK else 0.04),
        ))

    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        yaxis_title="Temperature (°C)",
        hovermode="x unified",
        height=380,
    )

    return fig


# ─── Main Content ───────────────────────────────────────────────────────────────
if filt1.empty and filt2.empty:
    st.info("No data available for the selected time range. Try adjusting the filters.")
else:
    st.markdown('<div class="section-title">Water Pressure</div>', unsafe_allow_html=True)
    st.plotly_chart(
        create_box_plot(filt1, filt2),
        use_container_width=True,
        config={'displayModeBar': True},
    )

    st.markdown('<div class="section-title">Temperature</div>', unsafe_allow_html=True)
    st.plotly_chart(
        create_temperature_chart(filt1, filt2),
        use_container_width=True,
        config={'displayModeBar': True},
    )