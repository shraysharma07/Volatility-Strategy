# Volatility-Based Backtesting Strategy

# Requirements 
``` bash 
pip install pandas pandas_datareader yfinance matplotlib
```
- Fetches historical adjusted close prices using `pandas_datareader` and `yfinance`.
- Generates a plot of normalized strategy performance vs. the benchmark using `matplotlib`

# Overview
This project implements a volatility-based trading strategy using historical financial data. The strategy switches between equity and cash based on the VIX and compares performance against a benchmark index.
- Fetches historical adjusted close prices using pandas_datareader and yfinance.

- Applies a volatility filter:

    - VIX > 20: hold cash
    
    - VIX ≤ 20: invest in SPY

- Compares results against a benchmark index (^GSPC).

- Generates a plot of normalized strategy performance vs. the benchmark.

# Usage
Generate a chart that indicates the perfomance of this stategy against a benchmark index (^GSPC):

```bash
python volatility_backtest.py
```


When the strategy line is **above** the benchmark:

- Filter **helped avoid drawdowns or captured gains more efficiently** during that period.

When the strategy line is **below** the benchmark:

- Filter **missed market gains or was too conservative**, staying in cash during upward moves.

The slope of the lines:

- **Steeper slope** -> faster capital growth.

- **Flat slope** -> no growth (in cash) or stagnant performance.

# Further Developing 

Strategy parameters, such as volatility threshold, symbols, and capital, can be altered.

```bash 
  volatility_threshold = 25   # VIX level 
  capital = 50000   # Portfolio size
  symbols = ['QQQ', '^IXIC', '^VIX']   # Ticker symbols to fetch data for
  ``` 
  `start_date` and `end_date` can also be modified to experiment with multiple market cycles 