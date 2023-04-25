from django.contrib import admin
from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.home, name ="home"),
    path('cta', views.cta, name ="cta"),
    path('update_sentiment/', views.update_sentiment, name='update_sentiment'),

]