from flask import Flask, render_template, request
from backtest_utils import load_equities_web, backtest_strategy, plot_results, summarize_results
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    plot_path = None
    metrics = None

    if request.method == 'POST':
        try:
            # Get form inputs
            symbols = request.form['symbols'].split(',')
            symbols = [s.strip() for s in symbols if s.strip()]
            trade_symbol = request.form['trade_symbol'].strip()
            volatility_symbol = request.form['volatility_symbol'].strip()
            benchmark_symbol = request.form['benchmark_symbol'].strip()
            start_date = request.form['start_date'].strip()
            end_date = request.form.get('end_date', '').strip() or None
            volatility_threshold = float(request.form.get('volatility_threshold', 20))
            capital = float(request.form.get('capital', 10000))

            # Load prices
            prices = load_equities_web(symbols, start_date, end_date)

            # Run backtest
            results_df = backtest_strategy(prices, trade_symbol, volatility_symbol, volatility_threshold, capital, benchmark_symbol)

            # Plot results and save image in static folder
            plot_results(results_df)
            plot_path = os.path.join('static', 'plot.png')

            # Summarize results
            metrics = summarize_results(results_df)

        except Exception as e:
            error = str(e)

    return render_template('index.html', error=error, plot_path=plot_path, metrics=metrics)

if __name__ == '__main__':
    app.run(debug=True)
