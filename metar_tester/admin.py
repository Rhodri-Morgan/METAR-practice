from django.contrib import admin

from .models import Airport
from .models import Report


admin.site.register(Airport)
admin.site.register(Report)
