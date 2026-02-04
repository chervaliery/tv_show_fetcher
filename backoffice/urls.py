from django.urls import path
from backoffice.admin import admin_site
from backoffice.views import home_view

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', home_view, name='home'),
]
