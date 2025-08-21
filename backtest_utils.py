from flask import Flask, request, render_template, send_file
import io
import matplotlib.pyplot as plt

application = Flask(__name__)

class BacktestError(Exception):
    pass

def run_backtest(config):
    import matplotlib.pyplot as plt
    import numpy as np
    
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.linspace(0, 100, 100)
    y = np.cumsum(np.random.randn(100)) + 100
    ax.plot(x, y, label='Portfolio Value')
    ax.set_xlabel('Days')
    ax.set_ylabel('Value ($)')
    ax.set_title('Backtest Results')
    ax.legend()
    
    stats = {
        'total_return': '15.2%',
        'max_drawdown': '-8.1%',
        'sharpe_ratio': '1.34',
        'trades': 45
    }
    
    return {
        'stats': stats,
        'plot': fig
    }

@application.route('/', methods=['GET', 'POST'])
def index():
    stats = None
    error = None
    plot_url = None

    if request.method == 'POST':
        try:
            trade_symbol = request.form.get('trade_symbol', '').strip()
            vol_symbol = request.form.get('vol_symbol', '').strip()
            start_date = request.form.get('start_date', '').strip()
            end_date = request.form.get('end_date', '').strip()
            vol_threshold = float(request.form.get('vol_threshold', 0))
            initial_capital = float(request.form.get('initial_capital', 0))

            if not all([trade_symbol, vol_symbol, start_date, end_date]):
                raise BacktestError("Please fill in all fields.")

            config = {
                "symbols": {
                    "trade": trade_symbol,
                    "volatility": vol_symbol
                },
                "start_date": start_date,
                "end_date": end_date,
                "vol_threshold": vol_threshold,
                "initial_capital": initial_capital
            }

            result = run_backtest(config)
            stats = result['stats']

            buf = io.BytesIO()
            result['plot'].savefig(buf, format='png')
            buf.seek(0)
            plot_url = '/plot.png'
            plt.close(result['plot'])
            application.config['PLOT_IMAGE'] = buf

        except BacktestError as be:
            error = str(be)
        except Exception as e:
            error = f"Unexpected error: {e}"

    return render_template('index.html', stats=stats, error=error, plot_url=plot_url)

@application.route('/plot.png')
def plot_png():
    buf = application.config.get('PLOT_IMAGE')
    if buf:
        return send_file(buf, mimetype='image/png')
    return "No plot available."

if __name__ == '__main__':
    application.run(debug=True)
