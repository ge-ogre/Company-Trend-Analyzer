import requests
import json


def isValidTicker(ticker):
    api_key = 'ch0orjhr01qhadkoggcgch0orjhr01qhadkoggd0'
    url = f'https://finnhub.io/api/v1/stock/symbol?exchange=US&token={api_key}'
    response = requests.get(url)
    data = json.loads(response.text)
    symbols = [item['symbol'] for item in data]
    if ticker in symbols:
        return True
    else:
        return False
