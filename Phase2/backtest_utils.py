import yfinance as yf
import pandas as pd
<<<<<<< HEAD
import matplotlib.pyplot as plt

def backtest_strategy(symbols, trade_symbol, start_date, end_date, threshold, capital):
    # Download price data for all symbols
    data = {}
    for sym in symbols:
        df = yf.download(sym, start=start_date, end=end_date, progress=False, auto_adjust=True)
        if df.empty:
            raise ValueError(f"No data found for symbol: {sym}")
        data[sym] = df['Close']
    
    # Check necessary symbols exist
    if trade_symbol not in data:
        raise ValueError(f"Trade symbol '{trade_symbol}' data missing")
    
    # Assume the volatility symbol is the other symbol (e.g., ^VIX)
    vol_symbols = [s for s in symbols if s != trade_symbol]
    if not vol_symbols:
        raise ValueError("At least two symbols required: trade symbol and volatility symbol")
    vol_symbol = vol_symbols[0]
    
    # Align data by date, drop NA rows
    prices = pd.DataFrame({sym: data[sym] for sym in symbols}).dropna()
    
    # Extract series
    trade_prices = prices[trade_symbol]
    vol_prices = prices[vol_symbol]
    
    # Create position: 1 if volatility <= threshold, else 0 (cash)
    position = (vol_prices <= threshold).astype(int)
    
    # Calculate daily returns for trade symbol
    returns = trade_prices.pct_change().fillna(0)
    
    # Strategy returns: position * returns
    strat_returns = position.shift(1).fillna(0) * returns  # Use yesterday's position
    
    # Calculate equity curve
    equity_curve = (1 + strat_returns).cumprod() * capital
    
    # Summary stats
    total_return = (equity_curve.iloc[-1] / capital - 1) * 100
    annualized_return = ((equity_curve.iloc[-1] / capital) ** (252/len(equity_curve)) - 1) * 100
    max_drawdown = ((equity_curve.cummax() - equity_curve) / equity_curve.cummax()).max() * 100
    
=======
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

>>>>>>> 770f2ce (Update Flask backtest app with fixes and UI improvements)
    stats = {
        "Total Return (%)": f"{total_return:.2f}",
        "Annualized Return (%)": f"{annualized_return:.2f}",
        "Max Drawdown (%)": f"{max_drawdown:.2f}",
        "Volatility Threshold": threshold,
        "Initial Capital": capital,
        "Trade Symbol": trade_symbol,
        "Volatility Symbol": vol_symbol,
        "Date Range": f"{start_date} to {end_date}",
<<<<<<< HEAD
    }
    
    # Plot equity curve
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(equity_curve.index, equity_curve, label="Strategy Equity")
    ax.set_title("Volatility-Based Strategy Equity Curve")
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio Value ($)")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend()
    
    return {
        "plot": fig,
        "stats": stats
    }
=======
    }

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(equity_curve.index, equity_curve, label="Strategy Equity")
    ax.set_title("Volatility-Based Strategy Equity Curve")
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio Value ($)")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend()

    return {"plot": fig, "stats": stats}
>>>>>>> 770f2ce (Update Flask backtest app with fixes and UI improvements)
