import pandas as pd
import pandas_datareader.data as web
from datetime import datetime
import matplotlib.pyplot as plt

try:
    import yfinance as yf
    has_yfinance = True
except ImportError:
    has_yfinance = False
    print("yfinance not installed; fallback will not be available.")

def load_equities_web(symbols, start_date, end_date=None):
    if end_date is None:
        end_date = datetime.today().strftime('%Y-%m-%d')
    
    all_data = {}
    for symbol in symbols:
        df = None
        try:
            df = web.DataReader(symbol, 'yahoo', start_date, end_date)
            if 'Adj Close' in df.columns:
                all_data[symbol] = df['Adj Close']
                continue
        except:
            pass
        if df is None and has_yfinance:
            try:
                df_yf = yf.download(symbol, start=start_date, end=end_date, progress=False)
                if 'Adj Close' in df_yf.columns:
                    all_data[symbol] = df_yf['Adj Close']
            except:
                pass
    if not all_data:
        raise ValueError("No valid data fetched for any symbols.")
    prices = pd.concat(all_data.values(), axis=1)
    prices.columns = list(all_data.keys())
    return prices

def backtest_strategy(prices, symbol_trade, symbol_volatility, volatility_threshold, capital, symbol_benchmark):
    strategy_value = [capital]
    benchmark_value = [capital]
    for i in range(1, len(prices)):
        try:
            today_vol = prices[symbol_volatility].iloc[i]
            yesterday_trade = prices[symbol_trade].iloc[i-1]
            today_trade = prices[symbol_trade].iloc[i]
            yesterday_bench = prices[symbol_benchmark].iloc[i-1]
            today_bench = prices[symbol_benchmark].iloc[i]
            trade_return = today_trade / yesterday_trade
            bench_return = today_bench / yesterday_bench
            if today_vol <= volatility_threshold:
                new_strategy_val = strategy_value[-1] * trade_return
            else:
                new_strategy_val = strategy_value[-1]
            new_bench_val = benchmark_value[-1] * bench_return
            strategy_value.append(new_strategy_val)
            benchmark_value.append(new_bench_val)
        except:
            strategy_value.append(strategy_value[-1])
            benchmark_value.append(benchmark_value[-1])
    results = pd.DataFrame({
        'Strategy': strategy_value,
        'Benchmark': benchmark_value
    }, index=prices.index)
    return results

def plot_results(results_df):
    results_df.plot(title='Volatility Strategy vs Benchmark', ylabel='Portfolio Value ($)', figsize=(10,6))
    plt.tight_layout()
    plt.savefig("static/plot.png")
    plt.close()

def summarize_results(results_df):
    strat_final = results_df['Strategy'].iloc[-1]
    bench_final = results_df['Benchmark'].iloc[-1]
    strat_return = (strat_final / results_df['Strategy'].iloc[0] - 1) * 100
    bench_return = (bench_final / results_df['Benchmark'].iloc[0] - 1) * 100
    return {
        "Strategy Final Value": f"${strat_final:,.2f}",
        "Benchmark Final Value": f"${bench_final:,.2f}",
        "Strategy Total Return": f"{strat_return:.2f}%",
        "Benchmark Total Return": f"{bench_return:.2f}%"
    }
