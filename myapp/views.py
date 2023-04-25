from django.shortcuts import redirect, render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from data_mining import settings
from .models import Tweet, Stock
#from .models import Stock
from .twitter_stock import *
import threading
from .tickerValidation import *
import plotly.express as px
from . getStockTable import *

# Create your views here.
def home(request):
    return render(request, "myapp/index.html")


def sentiment_analysis(request, ticker):
    if isValidTicker(ticker):
        #check if stream thread is running
        list_of_threads = threading.enumerate()
        streaming = False
        for thread in list_of_threads:
            if thread.name == "stream_thread":
                streaming = True
                break

        if not streaming:
            stream_thread = threading.Thread(target=fetch_and_stream_tweets, name="stream_thread", args=(ticker, "AAAAAAAAAAAAAAAAAAAAADpLZgEAAAAA58cu%2Bxrb8qCNT57oA%2FNYwbjNWvs%3DgdnlVLtp4RgYXXpMbBSYSlmp69CfrW81pH4mCg6zwLTe1VLmWF"))
            stream_thread.start()

            time.sleep(5)
            stock = Stock.objects.get(ticker=ticker)
            
            #create piechart
            graph = create_graph(stock)
            stockTable = get_stock_info(ticker)
            return {
                'pos': stock.positive_tweets,
                'neg': stock.negative_tweets,
                'ticker': ticker,
                'graph':graph,
                'stockTable': stockTable,
                }
        else:
            stock = Stock.objects.get(ticker=ticker)
            #create piechart
            graph = create_graph(stock)
            stockTable = get_stock_info(ticker)
            return {
                'pos': stock.positive_tweets,
                'neg': stock.negative_tweets,
                'ticker': ticker,
                'graph':graph,
                'stockTable': stockTable,
                }
    # invalid ticker
    else:
        messages.error(request, 'True')
        redirect('home')
        return None
    
def fetch_stock_chart_data(ticker):
    api_key = 'HDF291TIVVGY7UDU'  # Replace with your API key

    # Fetch stock data from Alpha Vantage
    base_url = "https://www.alphavantage.co/query?"
    function = "TIME_SERIES_INTRADAY"
    interval = "5min"  # Set the time interval for data points, e.g. 5min, 15min, 30min, etc.
    outputsize = "compact"  # Change to 'full' for more data points
    datatype = "json"

    url = f"{base_url}function={function}&symbol={ticker}&interval={interval}&apikey={api_key}&outputsize={outputsize}&datatype={datatype}"
    response = requests.get(url)
    data = json.loads(response.text)

    # Prepare data for the chart
    timeseries = data[f'Time Series ({interval})']
    dates = []
    prices = []
    for date, price_info in timeseries.items():
        dates.append(date)
        prices.append(float(price_info['4. close']))

    return {'dates': dates[::-1], 'prices': prices[::-1], 'ticker': ticker}

def cta(request):
    context = {}

    if request.method == 'POST':
        ticker = request.POST['ticker']
        sentiment_data = sentiment_analysis(request, ticker)
        if sentiment_data is not None:
            context.update(sentiment_data)

        stock_chart_data = fetch_stock_chart_data(ticker)
        context.update(stock_chart_data)

        return render(request, 'myapp/cta.html', context)
    
    # handle other types of requests besides POST
    else:
        # AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            ticker = request.GET.get('ticker')
            stock = Stock.objects.get(ticker=ticker)
            graph = create_graph(stock)
            return JsonResponse({'graph': graph})
        else:
            return render(request, 'myapp/cta.html')
    
def create_graph(stock):
    data= {"sentiment": ["positive", "negative"]
    , "count": [stock.positive_tweets, stock.negative_tweets]}
    fig = px.pie(data, values="count", names="sentiment")
    graph = fig.to_html(full_html=False)
    return graph