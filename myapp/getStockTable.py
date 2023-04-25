import requests
import json
from prettytable import PrettyTable
import re

# Replace YOUR_API_KEY with your actual Alpha Vantage API key
API_KEY = "HDF291TIVVGY7UDU"

def get_stock_info(stock_symbol):
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock_symbol}&apikey={API_KEY}"
    response = requests.get(url)
    data = json.loads(response.text)

    # Retrieve relevant information from the API response
    symbol = data["Global Quote"]["01. symbol"]
    price = round(float(data["Global Quote"]["05. price"]), 2)
    change_percent = data["Global Quote"]["10. change percent"]
    volume = data["Global Quote"]["06. volume"]
    latest_trading_day = data["Global Quote"]["07. latest trading day"]

    # Print stock information in a pretty table
    table = PrettyTable()
    table.field_names = ["Symbol", "Price", "Change Percent", "Volume", "Latest Trading Day"]
    table.add_row([symbol, price, change_percent, volume, latest_trading_day])
   

    # Generate HTML table with proper formatting and CSS styling
    html_table = table.get_html_string()
    html_table = html_table.replace("<table>", '<table style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif;">')
    html_table = html_table.replace("<thead>", '<thead style="background-color: #ddd; font-weight: bold;">')
    html_table = html_table.replace("<th>", '<th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">')
    html_table = html_table.replace("<tr>", '<tr style="border-bottom: 1px solid #ddd;">')
    html_table = html_table.replace("<td>", '<td style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">')

    return html_table