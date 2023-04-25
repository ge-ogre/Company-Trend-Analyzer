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

# Create your views here.
def home(request):
    return render(request, "myapp/index.html")

def cta(request):
    if request.method == 'POST':
        ticker = request.POST.get('ticker')
        if isValidTicker(ticker):
            #stock url for live stock data
            stockUrl=f"https://finance.yahoo.com/chart/{ticker}/#eyJpbnRlcnZhbCI6NSwicGVyaW9kaWNpdHkiOjEsInRpbWVVbml0IjoibWludXRlIiwiY2FuZGxlV2lkdGgiOjc3LjUsImZsaXBwZWQiOmZhbHNlLCJ2b2x1bWVVbmRlcmxheSI6dHJ1ZSwiYWRqIjp0cnVlLCJjcm9zc2hhaXIiOnRydWUsImNoYXJ0VHlwZSI6ImxpbmUiLCJleHRlbmRlZCI6ZmFsc2UsIm1hcmtldFNlc3Npb25zIjp7fSwiYWdncmVnYXRpb25UeXBlIjoib2hsYyIsImNoYXJ0U2NhbGUiOiJsaW5lYXIiLCJwYW5lbHMiOnsiY2hhcnQiOnsicGVyY2VudCI6MSwiZGlzcGxheSI6IkFBUEwiLCJjaGFydE5hbWUiOiJjaGFydCIsImluZGV4IjowLCJ5QXhpcyI6eyJuYW1lIjoiY2hhcnQiLCJwb3NpdGlvbiI6bnVsbH0sInlheGlzTEhTIjpbXSwieWF4aXNSSFMiOlsiY2hhcnQiLCLigIx2b2wgdW5kcuKAjCJdfX0sInNldFNwYW4iOm51bGwsImxpbmVXaWR0aCI6Miwic3RyaXBlZEJhY2tncm91bmQiOnRydWUsImV2ZW50cyI6dHJ1ZSwiY29sb3IiOiIjMDA4MWYyIiwic3RyaXBlZEJhY2tncm91ZCI6dHJ1ZSwicmFuZ2UiOm51bGwsInN5bWJvbHMiOlt7InN5bWJvbCI6IkFBUEwiLCJzeW1ib2xPYmplY3QiOnsic3ltYm9sIjoiQUFQTCIsInF1b3RlVHlwZSI6IkVRVUlUWSIsImV4Y2hhbmdlVGltZVpvbmUiOiJBbWVyaWNhL05ld19Zb3JrIn0sInBlcmlvZGljaXR5IjoxLCJpbnRlcnZhbCI6NSwidGltZVVuaXQiOiJtaW51dGUiLCJzZXRTcGFuIjpudWxsfV0sImV2ZW50TWFwIjp7ImNvcnBvcmF0ZSI6eyJkaXZzIjp0cnVlLCJzcGxpdHMiOnRydWV9LCJzaWdEZXYiOnt9fSwiY3VzdG9tUmFuZ2UiOm51bGwsInN0dWRpZXMiOnsi4oCMdm9sIHVuZHLigIwiOnsidHlwZSI6InZvbCB1bmRyIiwiaW5wdXRzIjp7ImlkIjoi4oCMdm9sIHVuZHLigIwiLCJkaXNwbGF5Ijoi4oCMdm9sIHVuZHLigIwifSwib3V0cHV0cyI6eyJVcCBWb2x1bWUiOiIjMDBiMDYxIiwiRG93biBWb2x1bWUiOiIjZmYzMzNhIn0sInBhbmVsIjoiY2hhcnQiLCJwYXJhbWV0ZXJzIjp7IndpZHRoRmFjdG9yIjowLjQ1LCJjaGFydE5hbWUiOiJjaGFydCIsInBhbmVsTmFtZSI6ImNoYXJ0In19fX0-"
            
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
                return render(request, 'myapp/cta.html', {
                    'pos': stock.positive_tweets,
                    'neg': stock.negative_tweets,
                    'ticker': ticker,
                    'graph':graph,
                    'stockUrl':stockUrl,
                    }
                )
            else:
                stock = Stock.objects.get(ticker=ticker)
                #create piechart
                graph = create_graph(stock)
                return render(request, 'myapp/cta.html', {
                    'pos': stock.positive_tweets,
                    'neg': stock.negative_tweets,
                    'ticker': ticker,
                    'graph':graph,
                    'stockUrl':stockUrl,
                
                    }
                )
        # invalid ticker
        else:
            messages.error(request,'True')
            return redirect('home')
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