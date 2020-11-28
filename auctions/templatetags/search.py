from django import template

# Define template custom search
register = template.Library()

@register.filter(name='search')
def search(value, id):
    for v in value:
        if v.id == id:
            return True
    return False