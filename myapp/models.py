from django.db import models

class Tweet(models.Model):
    tweet_obj= models.TextField()
    sa_score= models.FloatField(default=0)



