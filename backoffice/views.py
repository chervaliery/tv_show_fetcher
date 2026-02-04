from django.http import HttpResponse

# Create your views here.


def home_view(request):
    return HttpResponse("Bonjour monde!")
