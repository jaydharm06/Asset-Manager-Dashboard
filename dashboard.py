import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as godgdd
from datetime import date, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Portfolio Dashboard", layout="wide")
st.title("📊 Asset Management Performance Dashboard")

TRADING_DAYS = 252

# --- SIDEBAR CONTROLS ---
st.sidebar.header("Portfolio Configuration")

DEFAULT_TICKERS = {
    'AAPL': 'Technology', 'MSFT': 'Technology',
    'JPM': 'Financials', 'BAC': 'Financials',
    'JNJ': 'Healthcare', 'UNH': 'Healthcare',
    'XOM': 'Energy', 'CVX': 'Energy',
    'PG': 'Consumer Staples', 'KO': 'Consumer Staples'
}

selected_tickers = st.sidebar.multiselect(
    "Choose portfolio holdings",
    options=list(DEFAULT_TICKERS.keys()),
    default=list(DEFAULT_TICKERS.keys())
)

benchmark = st.sidebar.selectbox(
    "Benchmark",
    options=["SPY", "QQQ", "DIA", "IWM"],
    index=0
)

col_start, col_end = st.sidebar.columns(2)
with col_start:
    start_date = st.date_input("Start date", value=date(2023, 1, 1), max_value=date.today())
with col_end:
    end_date = st.date_input("End date", value=date.today(), max_value=date.today())

risk_free_rate = st.sidebar.number_input(
    "Annual risk-free rate (%)", min_value=0.0, max_value=15.0, value=4.0, step=0.25
) / 100

st.sidebar.divider()
st.sidebar.subheader("Weights (%)")
st.sidebar.caption("Weights are normalised to sum to 100% automatically.")

# --- WEIGHT SLIDERS ---
if not selected_tickers:
    st.warning("Select at least one ticker in the sidebar to build a portfolio.")
    st.stop()

raw_weights = {}
default_weight = round(100 / len(selected_tickers), 2)
for ticker in selected_tickers:
    raw_weights[ticker] = st.sidebar.slider(
        ticker, min_value=0.0, max_value=100.0, value=default_weight, step=1.0
    )

weight_sum = sum(raw_weights.values())
if weight_sum == 0:
    st.error("Total weight cannot be zero. Adjust the sliders in the sidebar.")
    st.stop()

# Normalise so weights always sum to 100%, regardless of slider inputs
normalised_weights = {t: w / weight_sum for t, w in raw_weights.items()}

st.sidebar.caption(f"Raw total: {weight_sum:.0f}% → normalised to 100%")

# --- DATA INGESTION (Cached for speed) ---
@st.cache_data(show_spinner="Downloading market data...")
def load_data(tickers, benchmark, start, end):
    """
    Downloads adjusted close prices and returns daily percentage returns
    for the selected tickers plus the benchmark.

    NOTE ON METHODOLOGY: portfolio returns below assume DAILY rebalancing
    to fixed target weights. This is a simplifying assumption common in
    illustrative dashboards -- a real portfolio would drift between
    rebalance dates, so realised returns would differ slightly from this
    model. Flagging this explicitly for transparency.
    """
    all_tickers = list(set(tickers + [benchmark]))
    try:
        data = yf.download(all_tickers, start=start, end=end, progress=False)['Close']
    except Exception as e:
        raise RuntimeError(f"Failed to download data from Yahoo Finance: {e}")

    if data.empty:
        raise RuntimeError("No data returned. Check tickers or date range.")

    # yfinance can return a Series if only one ticker is present
    if isinstance(data, pd.Series):
        data = data.to_frame()

    missing = [t for t in all_tickers if t not in data.columns]
    if missing:
        raise RuntimeError(f"No data found for: {', '.join(missing)}. They may be delisted or mistyped.")

    data = data.dropna(how="all")
    returns = data.pct_change().dropna()

    if returns.empty or len(returns) < 2:
        raise RuntimeError("Not enough data points in the selected date range to compute returns.")

    return returns, all_tickers


def build_portfolio_returns(returns, tickers, weights_dict):
    port_returns = returns[tickers]
    weights = np.array([weights_dict[t] for t in tickers])
    combined = returns.copy()
    combined['Portfolio'] = port_returns.dot(weights)
    return combined[['Portfolio', benchmark]]


# --- LOAD DATA WITH ERROR HANDLING ---
try:
    raw_returns, all_tickers = load_data(selected_tickers, benchmark, start_date, end_date)
    returns = build_portfolio_returns(raw_returns, selected_tickers, normalised_weights)
except RuntimeError as e:
    st.error(f"⚠️ {e}")
    st.stop()
except Exception as e:
    st.error(f"⚠️ Unexpected error while loading data: {e}")
    st.stop()

# --- CALCULATE CUMULATIVE RETURNS ---
cum_returns = (1 + returns).cumprod()

# --- CALCULATE PERFORMANCE METRICS ---
total_days = len(returns)

# Annualized Return
ann_return = (cum_returns.iloc[-1] ** (TRADING_DAYS / total_days)) - 1

# Annualized Volatility
ann_vol = returns.std() * np.sqrt(TRADING_DAYS)

# Sharpe Ratio: (annualised return - risk-free rate) / annualised volatility
sharpe_ratio = (ann_return - risk_free_rate) / ann_vol

# Sortino Ratio: like Sharpe, but only penalises downside volatility
downside_returns = returns.copy()
downside_returns[downside_returns > 0] = 0
downside_vol = downside_returns.std() * np.sqrt(TRADING_DAYS)
sortino_ratio = (ann_return - risk_free_rate) / downside_vol.replace(0, np.nan)

# Maximum Drawdown
rolling_max = cum_returns.cummax()
drawdown = (cum_returns / rolling_max) - 1
max_drawdown = drawdown.min()

# Beta and correlation vs benchmark
covariance = returns['Portfolio'].cov(returns[benchmark])
benchmark_variance = returns[benchmark].var()
beta = covariance / benchmark_variance
correlation = returns['Portfolio'].corr(returns[benchmark])

# --- DISPLAY METRICS IN DASHBOARD ---
st.subheader("Performance Scorecard")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Annualized Return",
        f"{ann_return['Portfolio']:.2%}",
        delta=f"{(ann_return['Portfolio'] - ann_return[benchmark]):.2%} vs {benchmark}"
    )
with col2:
    st.metric("Annualized Volatility", f"{ann_vol['Portfolio']:.2%}")
with col3:
    st.metric("Max Drawdown", f"{max_drawdown['Portfolio']:.2%}")
with col4:
    st.metric("Sharpe Ratio", f"{sharpe_ratio['Portfolio']:.2f}")

col5, col6, col7 = st.columns(3)
with col5:
    st.metric("Sortino Ratio", f"{sortino_ratio['Portfolio']:.2f}")
with col6:
    st.metric(f"Beta vs {benchmark}", f"{beta:.2f}")
with col7:
    st.metric(f"Correlation vs {benchmark}", f"{correlation:.2f}")

st.caption(
    "Sharpe/Sortino use an annual risk-free rate of "
    f"{risk_free_rate:.2%} (adjustable in the sidebar). "
    "Portfolio returns assume daily rebalancing to target weights."
)

st.divider()

# --- CUMULATIVE GROWTH CHART ---
st.subheader("Cumulative Growth of $1")

fig = px.line(
    cum_returns,
    labels={'value': 'Cumulative Return', 'Date': 'Date', 'variable': 'Series'},
    title=f"Portfolio vs. {benchmark} Cumulative Returns"
)
fig.update_layout(hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# --- ROLLING VOLATILITY & ROLLING SHARPE ---
st.subheader("Rolling Risk Metrics (63-day window)")

ROLL_WINDOW = 63  # roughly one trading quarter

rolling_vol = returns.rolling(ROLL_WINDOW).std() * np.sqrt(TRADING_DAYS)
rolling_mean_ann = returns.rolling(ROLL_WINDOW).mean() * TRADING_DAYS
rolling_sharpe = (rolling_mean_ann - risk_free_rate) / rolling_vol

roll_col1, roll_col2 = st.columns(2)

with roll_col1:
    fig_vol = px.line(
        rolling_vol.dropna(),
        labels={'value': 'Annualised Volatility', 'Date': 'Date', 'variable': 'Series'},
        title="Rolling Annualised Volatility"
    )
    fig_vol.update_layout(hovermode="x unified", yaxis_tickformat=".1%")
    st.plotly_chart(fig_vol, use_container_width=True)

with roll_col2:
    fig_sharpe = px.line(
        rolling_sharpe.dropna(),
        labels={'value': 'Sharpe Ratio', 'Date': 'Date', 'variable': 'Series'},
        title="Rolling Sharpe Ratio"
    )
    fig_sharpe.update_layout(hovermode="x unified")
    st.plotly_chart(fig_sharpe, use_container_width=True)

# --- DRAWDOWN CHART ---
st.subheader("Drawdown Over Time")
fig_dd = px.area(
    drawdown,
    labels={'value': 'Drawdown', 'Date': 'Date', 'variable': 'Series'},
    title=f"Portfolio vs. {benchmark} Drawdown"
)
fig_dd.update_layout(hovermode="x unified", yaxis_tickformat=".0%")
st.plotly_chart(fig_dd, use_container_width=True)

st.divider()

# --- PORTFOLIO COMPOSITION ---
st.subheader("Portfolio Composition")
weights_df = pd.DataFrame({
    "Ticker": list(normalised_weights.keys()),
    "Weight": list(normalised_weights.values())
})
fig_pie = px.pie(weights_df, names="Ticker", values="Weight", title="Target Portfolio Weights")
st.plotly_chart(fig_pie, use_container_width=True)

# --- RAW DATA ---
with st.expander("View Raw Daily Returns"):
    st.dataframe(returns)

with st.expander("View Normalised Weights"):
    st.dataframe(weights_df.style.format({"Weight": "{:.2%}"}))