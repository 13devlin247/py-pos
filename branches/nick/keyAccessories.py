import sys
sys.path.append('d:\\')
sys.path.append('d:\\pos\\')
import django
from pos.kernal.models import *

file = open('d:\\pos\\STOCK_BALANCE_accessories.csv')
lines = file.readlines()
i = 0
for line in lines:
    token = line.split(',')
    product = Product()
    product.name = token[1]
    product.description = token[2]
    category = None
    categorys = Category.objects.filter(category_name=token[0]) # fixme 
    if categorys.count() == 0:
        category = Category()
        category.category_name = token[0]
        category.save()
    else:
        category = categorys[0]
    product.category =  category
    
    brand = None
    brands = Brand.objects.filter(category=category).filter(brand_name=token[3].strip())
    if brands.count() == 0:
        brand = Brand()
        brand.category = category
        brand.brand_name = token[3].strip()
        brand.save()
    else:
        brand = brands[0]
        
    product.brand = brand
    product.retail_price = 0
    product.cost = 0
    product.uom = UOM.objects.get(pk=1)
    product.active = True
    product.save()
    i = i + 1    
    print str(i)+ " done"
    
