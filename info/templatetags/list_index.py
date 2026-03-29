from django import template

register = template.Library()

@register.filter
def index(value, arg):
    """
    Returns the item at the given index in a list or queryset.
    """
    try:
        return value[int(arg)]
    except (IndexError, ValueError, TypeError):
        return None
