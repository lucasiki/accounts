from django import template

register = template.Library()

@register.filter()
def get_key(value, arg):
    if arg in value.__dict__:
        return value.__dict__[arg]
    else:
        return ''