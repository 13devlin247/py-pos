import sys
import os
p1 = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
p2 = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(p1)
sys.path.append(p2)
sys.stdout = sys.stderr
os.environ['DJANGO_SETTINGS_MODULE'] = 'pos.settings' 
import django
from pos.kernal.models import *

file = open('D:\\django_project\\product_pos\\kernal_product.csv')
lines = file.readlines()
i = 0
for line in lines:
    token = line.split('|')
    product = Product()
    product.pk = token[0]
    product.name = token[2]
    product.description = token[3]
    category = Category.objects.get(pk=int(token[4]))
    product.category = category
    brand = Brand.objects.get(pk=int(token[5]))
    product.brand = brand
    product.retail_price = 0
    product.cost = 0
    product.algo = Algo.objects.get(pk=1)
    product.uom = UOM.objects.get(pk=1)
    product.active = True
    product.save()
    i = i + 1    
    print str(i)+ " done"
    
