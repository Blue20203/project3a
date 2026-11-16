import csv
import os
from datetime import datetime

import pygal
import requests
from flask import Flask, render_template, request

app = Flask(__name__)
API_KEY = os.environ.get("API_KEY", "YOUR_API_KEY")

FUNCTIONS = {
    "1": ("TIME_SERIES_INTRADAY", "Time Series (60min)"),
    "2": ("TIME_SERIES_DAILY", "Time Series (Daily)"),
    "3": ("TIME_SERIES_WEEKLY", "Weekly Time Series"),
    "4": ("TIME_SERIES_MONTHLY", "Monthly Time Series"),
}


def load_symbols():
    with open("stocks.csv", newline="") as f:
        return [row["Symbol"] for row in csv.DictReader(f)]


def get_data(symbol, series):
    function, key = FUNCTIONS[series]
    params = {"function": function, "symbol": symbol, "apikey": API_KEY, "outputsize": "full"}
    if series == "1":
        params["interval"] = "60min"
    data = requests.get("https://www.alphavantage.co/query", params=params).json()
    return data.get(key)


def make_chart(symbol, chart_type, data, start, end):
    dates = sorted(d for d in data if start <= d[:10] <= end)
    chart = pygal.Bar() if chart_type == "1" else pygal.Line()
    chart.title = f"Stock Data for {symbol}: {start} to {end}"
    chart.x_labels = dates
    chart.x_label_rotation = 45
    for label, field in [("Open", "1. open"), ("High", "2. high"), ("Low", "3. low"), ("Close", "4. close")]:
        chart.add(label, [float(data[d][field]) for d in dates])
    return chart.render_data_uri()


@app.route("/", methods=["GET", "POST"])
def index():
    symbols = load_symbols()
    chart = None
    error = None

    if request.method == "POST":
        symbol = request.form["symbol"]
        chart_type = request.form["chart_type"]
        series = request.form["time_series"]
        start = request.form["start_date"]
        end = request.form["end_date"]

        if not all([symbol, chart_type, series, start, end]):
            error = "Please fill out every field."
        elif datetime.strptime(end, "%Y-%m-%d") < datetime.strptime(start, "%Y-%m-%d"):
            error = "End date cannot be before the start date."
        else:
            data = get_data(symbol, series)
            if not data:
                error = "Could not get data from Alpha Vantage. Check your API key or try again."
            else:
                chart = make_chart(symbol, chart_type, data, start, end)

    return render_template("index.html", symbols=symbols, chart=chart, error=error)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
