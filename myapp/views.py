from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from data_mining import settings
from .models import Tweet
from .twitter_stock import *
import threading

# Create your views here.
def home(request):
    return render(request, "myapp/index.html")

def cta(request):
    if request.method == 'POST':
        ticker = request.POST.get('ticker')
        if threading.active_count() <= 3:

            stream_thread = threading.Thread(target=fetch_and_stream_tweets, args=(ticker, "AAAAAAAAAAAAAAAAAAAAADpLZgEAAAAA58cu%2Bxrb8qCNT57oA%2FNYwbjNWvs%3DgdnlVLtp4RgYXXpMbBSYSlmp69CfrW81pH4mCg6zwLTe1VLmWF"))
            stream_thread.start()

            time.sleep(5)
            stock = Stock.objects.get(ticker=ticker)

            return render(request, 'myapp/cta.html', {
                'pos': stock.positive_tweets,
                'neg': stock.negative_tweets,
                'ticker': ticker
                }
            )
        else:
            stock = Stock.objects.get(ticker=ticker)
            return render(request, 'myapp/cta.html', {
                'pos': stock.positive_tweets,
                'neg': stock.negative_tweets,
                'ticker': ticker
                }
            )
    
    else:
        return render(request, 'myapp/cta.html')
    
def create_tweet(request):
    pass
