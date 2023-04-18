import requests
import csv
import re
import json
from requests.structures import CaseInsensitiveDict

"""
This function takes in a stock ticker and a bearer token as parameters 
and uses the Twitter API to search for recent tweets containing the stock ticker. 
It returns the first 100 filtered tweets which contain the stock ticker, 
and various metadata such as the creation date, author ID, and public metrics.
"""
def get_initial_tweets(stock_ticker, bearer_token):
    query = f"\"{stock_ticker}\" lang:en"
    ticker_regex = re.compile(r'\$[A-Za-z]+')
    filtered_tweets = []
    next_token = None

    while len(filtered_tweets) < 100:
        url = f"https://api.twitter.com/2/tweets/search/recent?query={query}&max_results=100&tweet.fields=created_at,public_metrics,author_id"
        if next_token:
            url += f"&next_token={next_token}"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {bearer_token}"
        }

        resp = requests.get(url, headers=headers)

        if resp.status_code != 200:
            print(f"Error {resp.status_code}: {resp.text}")
            raise ValueError("Failed to fetch tweets")

        data = resp.json()
        all_tweets = data["data"]
        next_token = data.get("meta", {}).get("next_token", None)

        # Filter tweets containing only the input stock ticker
        current_filtered_tweets = [
            tweet for tweet in all_tweets
            if len(ticker_regex.findall(tweet['text'])) == 1 and f"${stock_ticker}" in tweet['text']
        ]
        filtered_tweets.extend(current_filtered_tweets)

        # Stop fetching if there are no more tweets available
        if not next_token:
            break

    # Return only the first 100 filtered tweets
    return filtered_tweets[:100]

"""
This function takes in a stock ticker and a bearer token as parameters 
and creates a filtered stream rule for the given stock ticker using the Twitter API. 
The rule is used to filter real-time tweets from the Twitter API stream that contain the given stock ticker. 
"""
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

"""
This function takes in a bearer token as a parameter 
and deletes all filtered stream rules that have been created using the Twitter API.
"""
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
        
"""
This function takes in a stock ticker, a bearer token, and an output filename as parameters.
It opens a connection to the Twitter API stream 
and filters real-time tweets based on the filtered stream rule for the given stock ticker.
It then writes the filtered tweets to a CSV file with the specified output filename.
"""
def stream_filtered_tweets(stock_ticker, bearer_token, output_filename):
    url = "https://api.twitter.com/2/tweets/search/stream"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {bearer_token}"
    }

    params = {"tweet.fields": "created_at,public_metrics,author_id"}
    ticker_regex = re.compile(r'\$[A-Za-z]+')

    with open(output_filename, mode='a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['author_id', 'text', 'created_at', 'public_metrics']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        response = requests.get(url, headers=headers, params=params, stream=True)

        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
            raise ValueError("Failed to fetch tweets")

        for line in response.iter_lines():
            if line:
                tweet_data = json.loads(line)
                tweet = tweet_data.get("data")
                if tweet:
                    if len(ticker_regex.findall(tweet['text'])) == 1 and f"${stock_ticker}" in tweet['text']:
                        filtered_tweet = {k: tweet[k] for k in fieldnames if k in tweet}
                        writer.writerow(filtered_tweet)
                        csvfile.flush()

"""
This function takes in a list of tweets and a filename as parameters 
and writes the tweets to a CSV file with the specified filename. 
The CSV file contains the metadata for each tweet, such as the author ID, text, creation date, and public metrics.
"""
def write_tweets_to_csv(tweets, filename):
    with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['author_id', 'text', 'created_at', 'public_metrics']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for tweet in tweets:
            filtered_tweet = {k: tweet[k] for k in fieldnames if k in tweet}
            writer.writerow(filtered_tweet)


"""
This function takes in a stock ticker and a bearer token as parameters 
and uses the previous five functions to fetch and stream tweets containing the stock ticker 
from the Twitter API. It first fetches the initial 100 tweets using the get_initial_tweets function 
and writes them to a CSV file. It then deletes any existing stream rules using 
the delete_all_stream_rules function and creates a new filtered stream rule 
for the given stock ticker using the create_filtered_stream_rule function. 
Finally, it uses the stream_filtered_tweets function to continuously stream real-time tweets containing
the given stock ticker and write them to the same CSV file.
"""
def fetch_and_stream_tweets(stock_ticker, bearer_token):
    tweets = get_initial_tweets(stock_ticker, bearer_token)
    output_filename = f"{stock_ticker}_tweets.csv"
    write_tweets_to_csv(tweets, output_filename)
    print(f"Initial tweets about {stock_ticker} have been saved to {output_filename}")

    delete_all_stream_rules(bearer_token)
    create_filtered_stream_rule(stock_ticker, bearer_token)

    try:
        stream_filtered_tweets(stock_ticker, bearer_token, output_filename)
    except KeyboardInterrupt:
        print("\nStream stopped.")

# if __name__ == "__main__":
#     bearer_token = "AAAAAAAAAAAAAAAAAAAAADpLZgEAAAAA58cu%2Bxrb8qCNT57oA%2FNYwbjNWvs%3DgdnlVLtp4RgYXXpMbBSYSlmp69CfrW81pH4mCg6zwLTe1VLmWF"
#     stock_ticker = input("Enter the stock ticker of the company: ")
#     fetch_and_stream_tweets(stock_ticker, bearer_token)
