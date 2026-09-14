# Quantitative Portfolio Performance & Risk Dashboard

## Executive Summary
A live, interactive asset management dashboard engineered to track custom multi-asset portfolio performance against major equity benchmarks (e.g., S&P 500, QQQ). This tool automates the daily reporting workflow by ingesting live market data, computing institutional-grade risk metrics, and visualizing benchmark-relative active risk to inform allocation decisions.

## Key Features
* **Dynamic Asset Allocation:** Real-time weight normalization engine allowing users to adjust portfolio composition via interactive sliders.
* **Benchmark-Relative Tracking:** Side-by-side performance comparison against major market indices.
* **Rolling Risk Analytics:** 63-day trailing evaluations of market volatility and risk-adjusted returns to visualize trend stability.
* **Automated Data Pipeline:** Fault-tolerant, cached data ingestion via the Yahoo Finance API.

---

## Quantitative Methodology

### 1. Portfolio Composition & Returns

**Portfolio Weights**
* **Plain English:** The exact percentage of total capital allocated to each specific asset. The system normalizes these inputs so they always sum to 100%.
* **The Math:** Let $w_i$ be the weight of asset $i$ and $n$ be the total number of assets. 
  $$\sum_{i=1}^{n} w_i = 1$$

**Daily Portfolio Return**
* **Plain English:** The daily percentage change of the entire portfolio, calculated by multiplying each stock's daily return by its portfolio weight.
* **The Math:** For daily returns $r_i$, the total portfolio return $R_p$ is: 
  $$R_p = \sum_{i=1}^{n} w_i r_i$$

**Cumulative Return**
* **Plain English:** The total compound growth of a $1 investment from the inception date, assuming daily profit reinvestment.
* **The Math:** Over $T$ days, the cumulative return $C_T$ is: 
  $$C_T = \prod_{t=1}^{T} (1 + R_t) - 1$$

### 2. Risk & Performance Metrics

**Annualized Return**
* **Plain English:** The geometric average percentage the portfolio grew each year, standardized to 252 trading days.
* **The Math:** 
  $$R_{ann} = (1 + C_T)^{\frac{252}{T}} - 1$$

**Annualized Volatility**
* **Plain English:** The dispersion of returns. Higher volatility indicates wider daily price fluctuations and higher risk.
* **The Math:** Scaling daily standard deviation $\sigma_{daily}$ to an annual figure: 
  $$\sigma_{ann} = \sigma_{daily} \sqrt{252}$$

**Maximum Drawdown**
* **Plain English:** The single largest percentage drop from a historical peak to a subsequent trough, representing the worst-case historical loss.
* **The Math:** Let $V_t$ be the portfolio value at time $t$, and $P_t$ be the peak value observed up to time $t$. 
  $$MDD = \min \left( \frac{V_t}{P_t} - 1 \right)$$

### 3. Risk-Adjusted Analytics

**Sharpe Ratio**
* **Plain English:** Measures the excess return generated per unit of total risk (volatility) endured, relative to a risk-free benchmark.
* **The Math:** Where $R_f$ is the risk-free rate and $\sigma_p$ is portfolio volatility: 
  $$S = \frac{R_{ann} - R_f}{\sigma_{ann}}$$

**Sortino Ratio**
* **Plain English:** An asymmetric risk metric that penalizes the portfolio only for downward price drops, ignoring upward volatility.
* **The Math:** Replacing total volatility with downside deviation $\sigma_d$: 
  $$S_R = \frac{R_{ann} - R_f}{\sigma_d}$$

**Beta ($\beta$)**
* **Plain English:** The portfolio's sensitivity to broader market movements. A Beta of 1.0 indicates perfect correlation with the benchmark; 1.5 indicates 50% greater volatility.
* **The Math:** The covariance of portfolio and benchmark returns divided by the benchmark's variance: 
  $$\beta = \frac{Cov(R_p, R_b)}{Var(R_b)}$$

---

## Technical Architecture
* **Frontend:** `Streamlit` (Interactive UI state management, caching)
* **Data Processing:** `Pandas`, `NumPy` (Vectorized time-series manipulation, rolling window calculations)
* **Visualisation:** `Plotly Express` (Unified hover-state rendering, interactive web charting)
* **Data Source:** `yfinance` (Live market data ingestion with automated error handling)