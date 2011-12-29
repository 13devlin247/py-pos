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


class Stocker:
    qty = 0
    cost = 0
    
    def change(self, record, verbose = False):
        if "InStockRecord" == record.__class__.__name__:
            # print "%s %s %s" % (record.pk, self.qty, record.quantity)
            if record.quantity == 0:
                print "FUCK: %s" % record.pk
            if (float(self.qty) + float(record.quantity) == 0):
                self.cost = 0
            else:
                self.cost = ((self.cost * self.qty) + (float(record.cost) * float(record.quantity))) / (float(self.qty) + float(record.quantity))
            self.cost = round(self.cost, 2)
            self.qty += int(record.quantity)
            if verbose:
                print "+%(InQTY)s(%(InCost)s) \t=\t %(StockQty)s(%(StockCost)s)" % {"create_at": "", "StockCost": self.cost, "StockQty": self.qty, "InQTY": record.quantity, "InCost": record.cost, "OutQTY": 0, "OutCost":0}
        else:
            self.qty -= int(record.quantity)
            if self.qty == 0:
                self.cost = 0
            
            if verbose:
                print "-%(OutQTY)s(%(OutCost)s) \t=\t %(StockQty)s(%(StockCost)s)" % {"create_at": "", "StockCost": self.cost, "StockQty": self.qty, "InQTY": 0, "InCost": 0, "OutQTY": record.quantity, "OutCost":(record.cost/record.quantity)}
        return (self.cost, self.qty)

def _query_outstock_cost(record):
    if record.quantity == 0:
        return (0, 0)    
    outStock_cost = round(float(record.cost)/float(record.quantity), 2)
    return (outStock_cost, record.quantity)    
        
def trace_product(product, verbose=False):
    inStocks = InStockRecord.objects.filter(product = product).filter(active=True).order_by("create_at")
    outstocks = OutStockRecord.objects.filter(product = product).filter(active=True).order_by("create_at")
    
    all = []
    all.extend(inStocks)
    all.extend(outstocks)
    all_sorted = sorted(all, key=lambda record: record.create_at)

    s = Stocker()
    cost = 0
    qty = 0
    for record in all_sorted:
        last_cost = cost
        last_qty = qty
        cost, qty = s.change(record, verbose)
        if "OutStockRecord" == record.__class__.__name__:
            out_cost, out_qty = _query_outstock_cost(record)
            if record.serial_no:
                last_cost = float(SerialNoMapping.objects.filter(serial_no = record.serial_no).latest("create_at").inStockRecord.cost)
            
            if out_cost != last_cost:
                if record.bill.mode == "service":
                    continue
                if record.serial_no:
                    print "serial"
                if record.quantity == 0:
                    print "================ %s product: %s %s record: %s wrong cost:%s , right cost:%s==================== " % (record.bill.mode, record.product.pk, record.product.name, record.pk, 0, last_cost)
                else:
                    print "================ %s product: %s %s record: %s wrong cost:%s , right cost:%s==================== " % (record.bill.mode, record.product.pk, record.product.name, record.pk, (record.cost/record.quantity), last_cost)
                record.cost = last_cost * int(record.quantity)
                record.save()


        
if __name__ == "__main__":
    products = []
    verbose = False
    if len(sys.argv) != 2:
        products = Product.objects.all()
    else:
        products = [Product.objects.get(pk=int(sys.argv[1]))]
        verbose = True
    for product in products:
        trace_product(product, verbose)