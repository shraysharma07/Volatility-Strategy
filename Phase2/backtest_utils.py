import yfinance as yf
import pandas as pd
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
