from django.contrib import admin
from django.urls import path, include

from clearcolour import urls as clearcolour_urls


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(clearcolour_urls)),
]
