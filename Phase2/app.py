import io
import base64
from flask import Flask, render_template, request
import matplotlib.pyplot as plt
from backtest_utils import backtest_strategy

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    plot_data = None
    stats = None

    if request.method == 'POST':
        symbols = request.form.get('symbols', '').strip()
        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()
        threshold = request.form.get('threshold', '').strip()
        capital = request.form.get('capital', '').strip()

        if not symbols or not start_date or not end_date or not threshold or not capital:
            error = "Please fill in all fields."
        else:
            symbols_list = [s.strip() for s in symbols.split(',')]
            try:
                threshold = float(threshold)
                capital = float(capital)
            except ValueError:
                error = "Threshold and Capital must be valid numbers."
            
            if not error:
                try:
                    # Run the backtest with the first symbol as trade_symbol for demo
                    trade_symbol = symbols_list[0]

                    result = backtest_strategy(
                        symbols_list,
                        trade_symbol,
                        start_date,
                        end_date,
                        threshold,
                        capital
                    )

                    fig = result['plot']
                    stats = result['stats']

                    # Convert plot to base64 string to embed in HTML
                    img = io.BytesIO()
                    fig.savefig(img, format='png', bbox_inches='tight')
                    plt.close(fig)
                    img.seek(0)
                    plot_data = base64.b64encode(img.getvalue()).decode()

                except Exception as e:
                    error = f"Error during backtest: {str(e)}"

    return render_template('index.html', error=error, plot_data=plot_data, stats=stats)

if __name__ == '__main__':
    app.run(debug=True)
