from django.template.defaultfilters import register

@register.filter
def IMEIOnly(obj):
    return obj.split("-")[1]

@register.filter
def classname(obj, arg=None):
    classname = obj.__class__.__name__.lower()
    if arg:
        if arg.lower() == classname:
            return True
        else:
            return False
    else:
        return classname
