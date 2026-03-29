from django import template

register = template.Library()

@register.filter
def percentage(value, total):
    if total == 0:
        return '0%'
    return f'{(value / total) * 100}%'
