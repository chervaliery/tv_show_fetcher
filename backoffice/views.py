from django.http import HttpResponse

from models import *
from utils import fetch_show, get_show

# Create your views here.


def home(request):
    return HttpResponse("Bonjour monde!")
