import sys
sys.path.append('d:\\')
sys.path.append('d:\\pos\\')
import django
from pos.kernal.models import *

file = open('d:\\pos\\STOCK_BALANCE.csv')
lines = file.readlines()
i = 0
for line in lines:
    token = line.split(',')
    product = Product()
    product.name = token[0]
    product.description = token[1]
    product.category = Category.objects.get(pk=1)
    product.brand = Brand.objects.filter(brand_name=token[3].strip())[0]
    product.retail_price = 0
    product.cost = 0
    product.uom = UOM.objects.get(pk=1)
    product.active = True
    product.save()
    i = i + 1    
    print str(i)+ " done"
    
