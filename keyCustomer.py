import sys, os
p1 = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
p2 = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(p1)
sys.path.append(p2)
sys.stdout = sys.stderr
os.environ['DJANGO_SETTINGS_MODULE'] = 'pos.settings' 

import django
from pos.kernal.models import *

file = open('D:\\django_project\\product_pos\\kernal_customer.csv')
lines = file.readlines()
i = 0
for line in lines:
    token = line.split('|')
    customer = Customer()
    customer.customer_code = token[0]
    customer.name = token[1]
    customer.contact_person = token[3]
    customer.phone = token[4]
    customer.fax = token[5]
    customer.address = token[2]
    customer.email = ""
    customer.term = ""
    customer.active = True
    customer.save()
    i += 1
    print str(i)+ " done"
    
