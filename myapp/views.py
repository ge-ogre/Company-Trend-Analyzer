from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from data_mining import settings

# Create your views here.
def home(request):
    return render(request, "myapp/index.html")