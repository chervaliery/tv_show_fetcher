from django.http import HttpResponse

from backoffice.models import *
from backoffice.utils import fetch_show, get_show

# Create your views here.


def home(request):
    return HttpResponse("Bonjour monde!")
