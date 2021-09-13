from django.contrib import admin

from .models import Airport
from .models import Metar
from .models import Answer
from .models import Question
from .models import Report


admin.site.register(Airport)
admin.site.register(Metar)
admin.site.register(Answer)
admin.site.register(Question)
admin.site.register(Report)
