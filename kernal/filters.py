from django.template.defaultfilters import register
from kernal.models import SerialNo

@register.filter
def IMEIOnly(obj):
    try:
        serial = SerialNo.objects.get(serial_no = obj)
        return obj.replace(serial.inStockRecord.product.name+'-', '')
    except SerialNo.DoesNotExist:
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
