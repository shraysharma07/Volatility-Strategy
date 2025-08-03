import yfinance as yf
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import yaml
import os

class BacktestError(Exception):
    pass

def load_config(filepath='config.yaml'):
    if not os.path.exists(filepath):
        raise BacktestError(f"Config file '{filepath}' not found.")
    with open(filepath, 'r') as file:
        return yaml.safe_load(file)

def fetch_data(symbol, start_date, end_date):
    df = yf.download(symbol, start=start_date, end=end_date, progress=False, auto_adjust=True)
    if df.empty:
        raise BacktestError(f"No data found for symbol: {symbol}")
    return df['Close']

def run_backtest(config):
    try:
        trade_symbol = str(config['symbols']['trade']).strip()
        vol_symbol = str(config['symbols']['volatility']).strip()
        start_date = str(config['start_date']).strip()
        end_date = str(config['end_date']).strip()
        threshold = float(config['vol_threshold'])
        capital = float(config['initial_capital'])
    except Exception as e:
        raise BacktestError(f"Invalid input parameters: {e}")

    if start_date >= end_date:
        raise BacktestError("Start date must be before end date.")

    prices_trade = fetch_data(trade_symbol, start_date, end_date)
    prices_vol = fetch_data(vol_symbol, start_date, end_date)

    prices = pd.concat([prices_trade, prices_vol], axis=1, keys=[trade_symbol, vol_symbol]).dropna()

    if prices.empty:
        raise BacktestError("No overlapping data between trade and volatility symbols.")

    vol_series = prices[vol_symbol].iloc[:, 0]
    trade_series = prices[trade_symbol].iloc[:, 0]

    position = (vol_series <= threshold).astype(int)
    returns = trade_series.pct_change()

    position_shifted = position.shift(1).fillna(0)
    strat_returns = position_shifted * returns.fillna(0)

    equity_curve = (1 + strat_returns).cumprod() * capital

    if equity_curve.isnull().all() or equity_curve.empty:
        raise BacktestError("Equity curve contains no data after calculation. Check your inputs and data.")

    total_return = (equity_curve.iloc[-1] / capital - 1) * 100
    annualized_return = ((equity_curve.iloc[-1] / capital) ** (252 / len(equity_curve)) - 1) * 100
    max_drawdown = ((equity_curve.cummax() - equity_curve) / equity_curve.cummax()).max() * 100

    stats = {
        "Total Return (%)": f"{total_return:.2f}",
        "Annualized Return (%)": f"{annualized_return:.2f}",
        "Max Drawdown (%)": f"{max_drawdown:.2f}",
        "Volatility Threshold": threshold,
        "Initial Capital": capital,
        "Trade Symbol": trade_symbol,
        "Volatility Symbol": vol_symbol,
        "Date Range": f"{start_date} to {end_date}",
    }

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(equity_curve.index, equity_curve, label="Strategy Equity")
    ax.set_title("Volatility-Based Strategy Equity Curve")
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio Value ($)")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend()

    return {"plot": fig, "stats": stats}
