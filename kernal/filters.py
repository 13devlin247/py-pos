from django.template.defaultfilters import register

@register.filter
def IMEIOnly(obj):
    if '-' in obj:
        return obj.split("-")[1]
    else:
        return obj

@register.filter
def FOCHidden(obj):
    return obj.replace("-foc-product", '')

@register.filter
def Get(obj, idx):
    return obj[idx]

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
