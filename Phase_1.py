import pandas as pd
import pandas_datareader.data as web
from datetime import datetime
import matplotlib.pyplot as plt
import logging

# Add logging and yaml configuration

# Attempt to import yfinance for fallback data fetching
try:
    import yfinance as yf
    has_yfinance = True
except ImportError:
    has_yfinance = False
    print("yfinance not installed; fallback will not be available.")

# === Part 1: Load Equities Data ===
def load_equities_web(symbols, start_date, end_date=None):
    """
    Fetch historical adjusted closing prices for a list of stock symbols.
    Tries pandas_datareader first, falls back to yfinance if necessary.

    Args:
        symbols (list of str): Ticker symbols to fetch data for.
        start_date (str): Start date for data in 'YYYY-MM-DD' format.
        end_date (str, optional): End date for data; defaults to today if None.

    Returns:
        pd.DataFrame: DataFrame with dates as index and symbols as columns (Adj Close prices).
    """
    if end_date is None:
        # Default end date is today
        end_date = datetime.today().strftime('%Y-%m-%d')
    
    all_data = {}  # Dictionary to hold each symbol's price series

    for symbol in symbols:
        df = None  # Placeholder for fetched data

        # Attempt data fetching using pandas_datareader
        try:
            df = web.DataReader(symbol, 'yahoo', start_date, end_date)
            if df.empty:
                print(f"pandas_datareader fetched empty data for {symbol}")
                df = None
            # Check if 'Adj Close' column exists and has data
            elif 'Adj Close' in df.columns and not df['Adj Close'].empty:
                all_data[symbol] = df['Adj Close'].copy()
                print(f"Fetched {symbol} using pandas_datareader.")
                continue  # Move to next symbol after success
            else:
                print(f"pandas_datareader data for {symbol} missing 'Adj Close' or empty")
                df = None
        except Exception as e:
            # Print error if pandas_datareader fails
            print(f"pandas_datareader failed for {symbol}: {e}")
            df = None
        
        # If pandas_datareader fails or no valid data, try yfinance fallback if available
        if df is None and has_yfinance:
            try:
                # Download data with yfinance (auto_adjust=False to keep original columns)
                df_yf = yf.download(symbol, start=start_date, end=end_date, progress=False, auto_adjust=False)
                if df_yf.empty:
                    print(f"yfinance fetched empty data for {symbol}")
                    continue
                
                # Print columns returned by yfinance for debugging
                print(f"yfinance columns for {symbol}: {df_yf.columns.tolist()}")
                
                # Prefer 'Adj Close' if available, otherwise use 'Close'
                if 'Adj Close' in df_yf.columns and not df_yf['Adj Close'].empty:
                    all_data[symbol] = df_yf['Adj Close'].copy()
                    print(f"Fetched {symbol} using yfinance 'Adj Close'.")
                elif 'Close' in df_yf.columns and not df_yf['Close'].empty:
                    all_data[symbol] = df_yf['Close'].copy()
                    print(f"Fetched {symbol} using yfinance 'Close'.")
                else:
                    print(f"yfinance data for {symbol} missing both 'Adj Close' and 'Close'.")
            except Exception as e_yf:
                # Print error if yfinance also fails
                print(f"yfinance also failed for {symbol}: {e_yf}")
        elif df is None and not has_yfinance:
            print(f"No fallback available for {symbol} because yfinance not installed.")
    
    # If no valid data fetched for any symbol, raise error
    if not all_data:
        raise ValueError("No valid data fetched for any symbols.")
    
    # Concatenate all series into a single DataFrame aligned by date
    prices = pd.concat(all_data.values(), axis=1)
    prices.columns = list(all_data.keys())  # Set column names to symbols
    
    return prices

# === Part 2: Backtest Strategy ===
def backtest_strategy(prices, symbol_trade, symbol_volatility, volatility_threshold, capital, symbol_benchmark):
    """
    Run a simple volatility-based trading strategy:
    - Invest in symbol_trade when volatility <= threshold
    - Stay in cash when volatility > threshold
    Compare to always invested benchmark symbol.

    Args:
        prices (pd.DataFrame): DataFrame with Adj Close prices indexed by date.
        symbol_trade (str): Symbol to trade based on volatility.
        symbol_volatility (str): Symbol used to measure volatility (e.g. VIX).
        volatility_threshold (float): Threshold below which to invest.
        capital (float): Initial capital.
        symbol_benchmark (str): Benchmark symbol for comparison.

    Returns:
        pd.DataFrame: DataFrame with columns 'Strategy' and 'Benchmark' tracking portfolio value over time.
    """
    strategy_value = [capital]  # Track strategy portfolio value starting at initial capital
    benchmark_value = [capital]  # Track benchmark portfolio value starting at initial capital
    
    # Loop over each trading day starting from second day (index 1)
    for i in range(1, len(prices)):
        try:
            today_vol = prices[symbol_volatility].iloc[i]
            yesterday_trade = prices[symbol_trade].iloc[i-1]
            today_trade = prices[symbol_trade].iloc[i]
            yesterday_bench = prices[symbol_benchmark].iloc[i-1]
            today_bench = prices[symbol_benchmark].iloc[i]

            # Calculate daily returns
            trade_return = today_trade / yesterday_trade
            bench_return = today_bench / yesterday_bench

            # If volatility low enough, update strategy value with trade return, else stay flat
            if today_vol <= volatility_threshold:
                new_strategy_val = strategy_value[-1] * trade_return
            else:
                new_strategy_val = strategy_value[-1]

            # Benchmark always invested, update with benchmark return
            new_bench_val = benchmark_value[-1] * bench_return

            # Append today's portfolio values
            strategy_value.append(new_strategy_val)
            benchmark_value.append(new_bench_val)
        except Exception as e:
            # On any error, print and hold values flat (no change)
            print(f"Error on {prices.index[i]}: {e}")
            strategy_value.append(strategy_value[-1])
            benchmark_value.append(benchmark_value[-1])

    # Create DataFrame of results indexed by date
    results = pd.DataFrame({
        'Strategy': strategy_value,
        'Benchmark': benchmark_value
    }, index=prices.index)

    return results

# === Main Execution ===
if __name__ == "__main__":
    # Define symbols to fetch: SPY (S&P 500 ETF), ^GSPC (S&P 500 index), ^VIX (volatility index)
    symbols = ['SPY', '^GSPC', '^VIX']
    start_date = '2000-01-01'  # Fetch data starting from Jan 1, 2000

    # Fetch historical prices with fallback logic
    prices_df = load_equities_web(symbols, start_date)
    print("Sample of fetched prices data:")
    print(prices_df.tail())  # Show last few rows of fetched price data

    capital = 10000  # Initial capital for backtesting
    volatility_threshold = 20  # Threshold on volatility index to decide trading

    # Run backtest: trade SPY based on VIX volatility, benchmark is always invested in S&P 500 (^GSPC)
    results_df = backtest_strategy(prices_df, 'SPY', '^VIX', volatility_threshold, capital, '^GSPC')
    print("Sample of backtest results:")
    print(results_df.tail())  # Show last few rows of strategy and benchmark portfolio values

    # Plot results: portfolio value over time
    results_df.plot(title='Volatility-Based Strategy vs Benchmark',
                    ylabel='Portfolio Value ($)',
                    figsize=(10,6))
    plt.show()
