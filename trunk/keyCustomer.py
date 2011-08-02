import sys
sys.path.append('d:\\')
sys.path.append('d:\\pos\\')
import django
from pos.kernal.models import *

file = open('d:\\pos\\customer.csv')
lines = file.readlines()
i = 0
for line in lines:
    token = line.split(',')
    customer = Customer()
    customer.customer_code = token[0]
    customer.name = token[1]
    customer.contact_person = token[2]
    customer.phone = token[3]
    customer.fax = token[4]
    customer.address = token[5].replace('"', ' ') + token[6].replace('"', ' ') + token[7].replace('"', ' ') + token[8].replace('"', ' ')
    customer.email = ""
    customer.term = ""
    customer.active = True
    customer.save()
    i += 1
    print str(i)+ " done"
    
