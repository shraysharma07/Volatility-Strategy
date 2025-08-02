import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime
from typing import List, Optional, Dict
import warnings

# --- SET MATPLOTLIB BACKEND TO 'Agg' BEFORE ANY pyplot IMPORT ---
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend for server environments
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import seaborn as sns  # For styling

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress specific warnings for clean logs
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# Check if yfinance is available
try:
    import yfinance as yf
    has_yfinance = True
except ImportError:
    has_yfinance = False
    logger.warning("yfinance not available")

class DataValidationError(Exception):
    pass

class InsufficientDataError(Exception):
    pass

def safe_data_access(df: pd.DataFrame, column: str, index: int, default_value: float = np.nan) -> float:
    try:
        if column not in df.columns:
            logger.warning(f"Column '{column}' not found.")
            return default_value
        if index < 0 or index >= len(df):
            logger.warning(f"Index {index} out of bounds.")
            return default_value
        value = df[column].iloc[index]
        return value if pd.notna(value) else default_value
    except Exception as e:
        logger.warning(f"Safe access error: {e}")
        return default_value

def fetch_yfinance_data(symbol: str, start_date: str, end_date: str) -> Optional[pd.Series]:
    if not has_yfinance:
        return None
    try:
        # Use yf.download instead of Ticker.history for reliability
        df_yf = yf.download(symbol, start=start_date, end=end_date, progress=False, auto_adjust=True)
        if df_yf.empty:
            return None
        return df_yf['Close'].dropna()
    except Exception as e:
        logger.debug(f"yfinance error for {symbol}: {e}")
        return None

def fetch_pandas_data(symbol: str, start_date: str, end_date: str) -> Optional[pd.Series]:
    import pandas_datareader.data as web
    try:
        data = web.DataReader(symbol, 'yahoo', start_date, end_date)
        if data.empty or 'Adj Close' not in data.columns:
            return None
        return data['Adj Close'].dropna()
    except Exception as e:
        logger.debug(f"pandas_datareader error for {symbol}: {e}")
        return None

def load_equities_web(symbols: List[str], start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    # Validate date inputs
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        min_start = datetime(2010, 1, 1)
        if start_dt < min_start:
            start_date = min_start.strftime('%Y-%m-%d')
            logger.info(f"Adjusted start date to {start_date}")
    except ValueError as e:
        raise DataValidationError(f"Invalid date format: {e}")

    # Replace problematic tickers with proxies
    fixed_symbols = []
    for sym in symbols:
        s = sym.strip().upper()
        if s == '^GSPC':
            logger.info("Replacing ^GSPC with SPY for data fetching.")
            fixed_symbols.append('SPY')
        elif s == '^VIX':
            logger.info("Replacing ^VIX with VIXY for data fetching.")
            fixed_symbols.append('VIXY')
        else:
            fixed_symbols.append(s)

    successful_data: Dict[str, pd.Series] = {}
    failed_symbols: List[str] = []

    logger.info(f"Fetching data for symbols: {fixed_symbols} from {start_date} to {end_date}")

    for symbol in fixed_symbols:
        success = False
        for source_name, fetch_func in [('yfinance', fetch_yfinance_data), ('pandas_datareader', fetch_pandas_data)]:
            try:
                data = fetch_func(symbol, start_date, end_date)
                if data is not None and len(data) > 10:
                    successful_data[symbol] = data
                    logger.info(f"✅ {symbol}: {len(data)} points from {source_name}")
                    success = True
                    break
            except Exception as e:
                logger.debug(f"Error fetching {symbol} via {source_name}: {e}")
        if not success:
            failed_symbols.append(symbol)
            logger.error(f"Failed to fetch data for {symbol}")

    if not successful_data:
        raise InsufficientDataError(f"No data loaded for symbols: {failed_symbols}")

    if len(successful_data) < len(fixed_symbols):
        logger.warning(f"Partial data loaded: {len(successful_data)}/{len(fixed_symbols)}")

    # Align on common dates, drop NaNs
    try:
        aligned_df = pd.concat(successful_data.values(), axis=1, join='inner')
        aligned_df.columns = list(successful_data.keys())
        aligned_df = aligned_df.dropna()
        if len(aligned_df) < 10:
            raise InsufficientDataError("Not enough overlapping data after alignment.")
        logger.info(f"Final dataset shape: {aligned_df.shape}")
        return aligned_df
    except Exception as e:
        raise DataValidationError(f"Data alignment error: {e}")

def backtest_strategy(prices: pd.DataFrame, symbol_trade: str, symbol_volatility: str,
                      volatility_threshold: float, capital: float, symbol_benchmark: str) -> pd.DataFrame:
    required_symbols = [symbol_trade, symbol_volatility, symbol_benchmark]
    missing = [s for s in required_symbols if s not in prices.columns]
    if missing:
        raise DataValidationError(f"Missing symbols: {missing}")
    if len(prices) < 2:
        raise InsufficientDataError("At least 2 data points required.")

    strategy_values = [capital]
    benchmark_values = [capital]
    trade_signals = []
    volatility_readings = []

    for i in range(1, len(prices)):
        current_vol = safe_data_access(prices, symbol_volatility, i, np.nan)
        prev_trade = safe_data_access(prices, symbol_trade, i - 1, np.nan)
        curr_trade = safe_data_access(prices, symbol_trade, i, np.nan)
        prev_bench = safe_data_access(prices, symbol_benchmark, i - 1, np.nan)
        curr_bench = safe_data_access(prices, symbol_benchmark, i, np.nan)

        if any(pd.isna(x) for x in [prev_trade, curr_trade, prev_bench, curr_bench]):
            strategy_values.append(strategy_values[-1])
            benchmark_values.append(benchmark_values[-1])
            continue

        if prev_trade <= 0 or prev_bench <= 0:
            strategy_values.append(strategy_values[-1])
            benchmark_values.append(benchmark_values[-1])
            continue

        trade_return = curr_trade / prev_trade
        bench_return = curr_bench / prev_bench

        if pd.notna(current_vol) and current_vol <= volatility_threshold:
            new_strategy_val = strategy_values[-1] * trade_return
            trade_signals.append(1)
        else:
            new_strategy_val = strategy_values[-1]  # cash
            trade_signals.append(0)

        volatility_readings.append(current_vol if pd.notna(current_vol) else 0)
        new_bench_val = benchmark_values[-1] * bench_return

        strategy_values.append(new_strategy_val)
        benchmark_values.append(new_bench_val)

    results_df = pd.DataFrame({
        'Strategy': strategy_values,
        'Benchmark': benchmark_values
    }, index=prices.index)

    if trade_signals:
        exposure = np.mean(trade_signals) * 100
        avg_vol = np.mean([v for v in volatility_readings if v > 0])
        logger.info(f"Market exposure: {exposure:.1f}%, Average volatility: {avg_vol:.1f}")

    return results_df

def plot_results(results_df: pd.DataFrame, filename: str = 'plot.png') -> None:
    if results_df.empty or len(results_df) < 2:
        raise DataValidationError("Insufficient data for plot.")

    required_cols = ['Strategy', 'Benchmark']
    missing = [c for c in required_cols if c not in results_df.columns]
    if missing:
        raise DataValidationError(f"Missing columns for plot: {missing}")

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(16, 10), dpi=100)
    fig.patch.set_facecolor('white')

    colors = {
        'strategy': '#2563eb',
        'benchmark': '#dc2626',
        'grid': '#e5e7eb',
        'text': '#1f2937'
    }

    ax.plot(results_df.index, results_df['Strategy'], label='Volatility Strategy', linewidth=3, color=colors['strategy'], alpha=0.9, zorder=3)
    ax.plot(results_df.index, results_df['Benchmark'], label='Benchmark', linewidth=3, color=colors['benchmark'], alpha=0.9, zorder=3)

    ax.set_title('Volatility Strategy vs Benchmark Performance', fontsize=24, fontweight='bold', color=colors['text'], pad=30, fontfamily='Arial')
    ax.set_xlabel('Date', fontsize=16, fontweight='600', color=colors['text'], fontfamily='Arial')
    ax.set_ylabel('Portfolio Value ($)', fontsize=16, fontweight='600', color=colors['text'], fontfamily='Arial')

    legend = ax.legend(fontsize=14, loc='upper left', frameon=True, fancybox=True, shadow=True, framealpha=0.95, facecolor='white', edgecolor=colors['grid'])
    for text in legend.get_texts():
        text.set_fontfamily('Arial')
        text.set_fontweight('600')

    ax.grid(True, alpha=0.4, linestyle='-', linewidth=0.8, color=colors['grid'], zorder=1)
    ax.set_axisbelow(True)

    def currency_formatter(x, _):
        if x >= 1e6:
            return f'${x/1e6:.1f}M'
        elif x >= 1e3:
            return f'${x/1e3:.0f}K'
        else:
            return f'${x:.0f}'

    ax.yaxis.set_major_formatter(FuncFormatter(currency_formatter))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    ax.set_facecolor('#fafafa')
    ax.tick_params(axis='both', which='major', labelsize=12, colors=colors['text'], width=1.2)

    try:
        strat_return = (results_df['Strategy'].iloc[-1] / results_df['Strategy'].iloc[0] - 1) * 100
        bench_return = (results_df['Benchmark'].iloc[-1] / results_df['Benchmark'].iloc[0] - 1) * 100
        outperf = strat_return - bench_return

        stats_text = f'Strategy Return: {strat_return:.1f}%\nBenchmark Return: {bench_return:.1f}%\nOutperformance: {outperf:+.1f}%'
        props = dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor=colors['grid'])
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=11,
                verticalalignment='top', bbox=props, fontfamily='Arial', color=colors['text'])
    except Exception as e:
        logger.warning(f"Could not add stats text: {e}")

    plt.tight_layout(pad=3.0)

    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    os.makedirs(static_dir, exist_ok=True)

    filepath = os.path.join(static_dir, filename)
    plt.savefig(filepath, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none', format='png', pad_inches=0.2)
    plt.close(fig)
    plt.close('all')
    logger.info(f"Plot saved to {filepath}")
