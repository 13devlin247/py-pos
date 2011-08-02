import logging
from datetime import date
from datetime import datetime
from pos.kernal.models import *

logging.basicConfig(
    level = logging.WARN,
    format = '%(asctime)s %(levelname)s %(funcName)s():%(lineno)s %(message)s',
)
# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class BarnOwl:
    def __init__(self):
        self.purchase = "purchase"
    """
    output 
    {
     u'111': {
                 u'serial-2': [u'NK1280PPL003'], 
                 u'serial-1': [u'NK1280PPL002'], 
                 u'serial-0': [u'NK1280PPL001'], 
                 u'cost': [u'2000'], 
                 u'quantity': [u'3']
             }, 
     u'110': {
                 u'serial-0': [u'NK1208001'], 
                 u'serial-2': [u'NK1208003'], 
                 u'serial-1': [u'NK1208002'], 
                 u'cost': [u'1000'], 
                 u'quantity': [u'3']
             }
     }
    """
    
    def __build_instock_batch__(self, request):
        mode = request.get('mode', 'purchase')
        today = date.today()
        do_date = request.get('do_date', today.strftime("%d/%m/%y"))
        supplier_name = request.get('supplier', "")
        supplier = None
        try:
            supplier = Supplier.objects.filter(name=supplier_name)[0:1].get()
        except Supplier.DoesNotExist:
            try:
                customer = Customer.objects.filter(name=supplier_name)[0:1].get()
                supplier = Supplier()
                supplier.name = customer.name
                supplier.supplier_code = customer.customer_code
                supplier.contact_person = customer.contact_person
                supplier.phone_office = customer.phone
                supplier.phone_mobile = customer.phone
                supplier.fax = customer.fax
                supplier.email = customer.email
                supplier.address = customer.address
                supplier.active = True            
                supplier.save()            
                logger.warn("Supplier '%s' found, auto create supplier", supplier_name)                
            except Customer.DoesNotExist:
                logger.warn("Supplier '%s' not found in Customer, auto create supplier", supplier_name)    
                supplier = Supplier()
                supplier.name = supplier_name
                supplier.supplier_code = supplier_name
                supplier.contact_person = supplier_name
                supplier.save()
        inStockBatch = InStockBatch()
        inStockBatch.mode = mode
        inStockBatch.supplier = supplier
        inStockBatch.user = User.objects.get(pk=request.get('_auth_user_id'))
        inStockBatch.do_date = do_date
        inStockBatch.invoice_no = request.get('inv_no', "-")
        inStockBatch.do_no = request.get('do_no', "-")
        inStockBatch.status = 'Incomplete'
        inStockBatch.save();
        logger.debug("InStockBatch: '%s' build", inStockBatch.pk)
        return inStockBatch    
    
    def InStock(self, reason, in_stock_batch_dict):
        logger.debug("Reason: '%s', dict: %s", reason, in_stock_batch_dict)
        inStockBatch = self.__build_instock_batch__(in_stock_batch_dict)
        logger.debug("InStockBatch '%s' build", inStockBatch.pk)
        return []
        
    def OutStock(self, reason, out_stock_batch_dict):
        return False
        
    def Cost(self, reason, out_stock_batch_dict):
        return False
        
    def Qty(self, reason, start, end):
        return 0

    def Catch(self, reason, start, end):
        return 0        

class Hermes:
    def Cost(self, product):
        return False
        
    def Profit(self, product):
        return False
    
