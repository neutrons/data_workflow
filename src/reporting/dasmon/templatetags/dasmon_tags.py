from django import template
register = template.Library()


@register.filter(name='is_number')
def is_number(value):
    try:
        float(value)
        return True
    except:
        return False


@register.filter(name='strip')
def strip(value):
    try:
        return value.strip().replace('_', ' ')
    except:
        return value
