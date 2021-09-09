from django.template import Library


register = Library()
@register.filter
def index(indexable, i):
    return indexable[i]
