import requests
import re
import json
import time
import datetime
import sys
from requests.structures import CaseInsensitiveDict
from .models import Tweet, Stock
import nltk
from nltk.stem import WordNetLemmatizer
nltk.download('wordnet')
from nltk.corpus import sentiwordnet as swn
nltk.download('sentiwordnet')


def get_sentiment_analysis_score(tweet_text):
    tt = nltk.TweetTokenizer()
    tokens = tt.tokenize(tweet_text)
    lemmatizer = WordNetLemmatizer()
    sentiments = []
    for token in range(len(tokens)):
        lemma = lemmatizer.lemmatize(tokens[token])
        synsets = list(swn.senti_synsets(lemma))
        sentiments.append([])
        if synsets:
            for synset in range(len(synsets)):
                sentiment_score = synsets[synset].pos_score() - synsets[synset].neg_score()
                sentiments[token].append(sentiment_score)
        else:
            # if the token is not in SentiWordNet, ignore it
            pass
    
    # Calculate the total sentiment score for the tweet
    total_sentiment = 0
    num_tokens_with_sentiment = 0
    for token_sentiments in sentiments:
        if token_sentiments:
            total_sentiment += sum(token_sentiments)
            num_tokens_with_sentiment += 1

    # Calculate the average sentiment score for the tweet
    if num_tokens_with_sentiment > 0:
        avg_sentiment = total_sentiment / num_tokens_with_sentiment
        return avg_sentiment
    else:
        return 0

def get_initial_tweets(stock_ticker, bearer_token):
    query = f"\"{stock_ticker}\" lang:en"
    ticker_regex = re.compile(r'\$[A-Za-z]+')
    filtered_tweets = []
    next_token = None

    while len(filtered_tweets) < 100:
        url = f"https://api.twitter.com/2/tweets/search/recent?query={query}&max_results=100&tweet.fields=created_at,public_metrics,author_id&expansions=author_id&user.fields=username"
        if next_token:
            url += f"&next_token={next_token}"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {bearer_token}"
        }

        resp = requests.get(url, headers=headers)

        if resp.status_code == 429:
            print("Rate limited, waiting 15 minutes")
            time.sleep(15 * 60)
            continue

        if resp.status_code != 200:
            print(f"Error {resp.status_code}: {resp.text}")
            raise ValueError("Failed to fetch tweets")

        data = resp.json()
        all_tweets = data["data"]
        users = data["includes"]["users"]

        author_id_to_username = {user["id"]: user["username"] for user in users}

        next_token = data.get("meta", {}).get("next_token", None)

        # Filter tweets containing only the input stock ticker
        current_filtered_tweets = [
            tweet for tweet in all_tweets
            if len(ticker_regex.findall(tweet['text'])) == 1 and f"${stock_ticker}" in tweet['text']
        ]

        for tweet in current_filtered_tweets:
            tweet["username"] = author_id_to_username[tweet["author_id"]]

        filtered_tweets.extend(current_filtered_tweets)

        # Stop fetching if there are no more tweets available
        if not next_token:
            break

    # Return only the first 100 filtered tweets
    filtered_tweets_json = [
        {k: tweet[k] for k in ['author_id', 'text', 'created_at', 'public_metrics', 'username'] if k in tweet}
        for tweet in filtered_tweets[:100]
    ]

    return filtered_tweets_json


def create_filtered_stream_rule(stock_ticker, bearer_token):
    url = "https://api.twitter.com/2/tweets/search/stream/rules"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token}"
    }
    rule_value = f"{stock_ticker} lang:en"
    rule = {"add": [{"value": rule_value, "tag": f"Stock: {stock_ticker}"}]}

    resp = requests.post(url, headers=headers, json=rule)

    if resp.status_code != 201:
        print(f"Error {resp.status_code}: {resp.text}")
        raise ValueError("Failed to create stream rule")

def delete_all_stream_rules(bearer_token):
    url = "https://api.twitter.com/2/tweets/search/stream/rules"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {bearer_token}"
    }
    resp = requests.get(url, headers=headers)
    rules = resp.json()

    if rules.get("data"):
        ids = [rule["id"] for rule in rules["data"]]
        delete_payload = {"delete": {"ids": ids}}
        resp = requests.post(url, headers=headers, json=delete_payload)

        if resp.status_code != 200:
            print(f"Error {resp.status_code}: {resp.text}")
            raise ValueError("Failed to delete stream rules")
        
def map_author_id_to_username(includes):
    author_id_to_username = {}
    if includes:
        for user in includes.get("users", []):
            author_id_to_username[user["id"]] = user["username"]
    return author_id_to_username


def stream_filtered_tweets(stock_ticker, bearer_token):
    stock = Stock.objects.get(ticker=stock_ticker)
    url = "https://api.twitter.com/2/tweets/search/stream"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {bearer_token}"
    }
    params = {
    "tweet.fields": "created_at,public_metrics,author_id",
    "expansions": "author_id",
    "user.fields": "username"
    }

    ticker_regex = re.compile(r'\$[A-Za-z]+')

    response = requests.get(url, headers=headers, params=params, stream=True)

    if response.status_code == 429:
        print(f"Error {response.status_code}: {response.text}")
        print("Rate limited, waiting 15 minutes")
        time.sleep(1000000)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        raise ValueError("Failed to fetch tweets")

    for line in response.iter_lines():
        if line:
            tweet_data = json.loads(line)
            tweet = tweet_data.get("data")
            includes = tweet_data.get("includes", {})

            if tweet:
                author_id_to_username = map_author_id_to_username(includes)
                if len(ticker_regex.findall(tweet['text'])) == 1 and f"${stock_ticker}" in tweet['text']:
                    filtered_tweet = {k: tweet[k] for k in ['author_id', 'text', 'created_at', 'public_metrics'] if k in tweet}
                    filtered_tweet["username"] = author_id_to_username.get(filtered_tweet["author_id"], "")

                    new_tweet = Tweet.objects.create(
                    tweet_obj=json.dumps(tweet),  # Save the tweet as a JSON string
                    sa_score=get_sentiment_analysis_score(filtered_tweet["text"]),
                    ticker=stock_ticker,
                    username=filtered_tweet["username"]
                    )
                    new_tweet.save()
                    stock.positive_tweets += 1 if new_tweet.sa_score > 0 else 0
                    stock.negative_tweets += 1 if new_tweet.sa_score < 0 else 0
                    stock.save()
                    print("New tweet")


def fetch_and_stream_tweets(stock_ticker, bearer_token):
    if not Stock.objects.filter(ticker=stock_ticker).exists():
        new_stock = Stock.objects.create(ticker=stock_ticker)
        new_stock.save()
    stock = Stock.objects.get(ticker=stock_ticker)
    initial_tweets = get_initial_tweets(stock_ticker, bearer_token)
    print(f"Initial tweets about {stock_ticker}:")
    for tweet in initial_tweets:
        new_tweet = Tweet.objects.create(
            tweet_obj=json.dumps(tweet),  # Save the tweet as a JSON string
            sa_score=get_sentiment_analysis_score(tweet["text"]),
            ticker=stock_ticker,
            username=tweet["username"]
        )
        new_tweet.save()
        stock.positive_tweets += 1 if new_tweet.sa_score > 0 else 0
        stock.negative_tweets += 1 if new_tweet.sa_score < 0 else 0
        stock.save()

    delete_all_stream_rules(bearer_token)
    create_filtered_stream_rule(stock_ticker, bearer_token)

    print(f"\nStreaming live tweets about {stock_ticker}:")
    
    try:
        stream_filtered_tweets(stock_ticker, bearer_token)
    except KeyboardInterrupt:
        print("\nStream stopped.")

def main(stock_ticker, bearer_token):
    fetch_and_stream_tweets(stock_ticker, bearer_token)

if __name__ == "__main__":
    bearer_token = "AAAAAAAAAAAAAAAAAAAAADpLZgEAAAAA58cu%2Bxrb8qCNT57oA%2FNYwbjNWvs%3DgdnlVLtp4RgYXXpMbBSYSlmp69CfrW81pH4mCg6zwLTe1VLmWF"
    stock_ticker = "AAPL"
    main(stock_ticker, bearer_token)
