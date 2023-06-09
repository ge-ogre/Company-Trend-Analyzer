from django.db import models

class Tweet(models.Model):
    tweet_obj = models.TextField()
    sa_score = models.FloatField(default=0)
    ticker = models.TextField()
    username = models.CharField(max_length=255, default='harry') 

class Stock(models.Model):
    ticker = models.TextField()
    positive_tweets = models.IntegerField(default=0)
    negative_tweets = models.IntegerField(default=0)