import sys, os  
p1 = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
p2 = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(p1)
sys.path.append(p2)
sys.stdout = sys.stderr
os.environ['DJANGO_SETTINGS_MODULE'] = 'pos.settings' 
from django.db.models import Q
from pos.kernal.barn import *
import django
from pos.kernal.models import *
import re

import sys    
        
if __name__ == "__main__":
    inStockRecords = InStockRecord.objects.filter(active=True).filter(type="Consignment_IN")
    stock = {}
    for inStockRecord in inStockRecords:
        stock[inStockRecord] = None
    
    outstocks = OutStockRecord.objects.filter(active=True).exclude(inStockRecord__pk = 0).exclude(type = "service")
    for outstock in outstocks:
        print outstock.pk
        if outstock.inStockRecord in stock:
            del stock[outstock.inStockRecord]
            print "Consignment record %s out" % outstock.inStockRecord.pk
    print "======================"
    
    for instock in stock:
        serials = SerialNo.objects.filter(inStockRecord = instock)
        for serial in serials:
            print serial.serial_no