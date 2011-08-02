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

class BarnMouse:
    def __init__(self, product):
        self.product = product
        self.is_serialable = self._check_serial()
     
    def _check_serial(self):
        serials = SerialNo.objects.filter(inStockRecord__product = self.product)
        if serials.count() > 0:
            logger.debug("Product: '%s' is serial product" , self.product.name)
            return True
        logger.debug("Product: '%s' is NOT serial product", self.product.name)
        return False
    
    def InStock(self, inStockBatch, qty, cost, reason):
        inStockRecord = InStockRecord()
        inStockRecord.inStockBatch = inStockBatch
        inStockRecord.product = self.product
        inStockRecord.cost = cost
        inStockRecord.quantity = qty
        inStockRecord.status = reason
        inStockRecord.save()
        
        if self.is_serialable:
            self.__build_serial_no__()
            
        logger.debug("instock '%s' build success, cost: '%s', quantity:'%s' ", self.product.name, inStockRecord.cost, inStockRecord.quantity)
        return inStockRecord
        
    def __build_serial_no__(self, request, inStockRecords, dict):   
        logger.debug("build Serial Numbs ")
        serials = []
        for inStockRecord in inStockRecords:
            product = inStockRecord.product
            for value in dict[str(product.pk)] :
                if 'serial-' in value:
                    serialNO = request.GET.get(str(product.pk)+"_"+value, '') 
                    if serialNO == '':
                        continue
                    # look up from serial no table
                    try:
                        serial = SerialNo.objects.get(serial_no = serialNO)
                        serial.inStockRecord = inStockRecord
                        serial.active = True
                        serial.save()
                        serials.append(serial)
                        logger.debug("Serial no: %s found, unlock it", serialNO)
                    except SerialNo.DoesNotExist:
                        serial = SerialNo()
                        serial.inStockRecord = inStockRecord
                        serial.serial_no = serialNO
                        serial.active = True
                        serial.save()  
                        serials.append(serial)
                        logger.debug("build serial no: '%s' for product: '%s'", serialNO, product.name)
        return serials  
    
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
    def __filter_serial_by_product__(self, productDict):
        serials = []
        for item in productDict:
            if item.startswith("serial-"):
                serials.append(productDict[item])
        logger.debug("serials count: '%s' ", len(serials))
        return serials
    
    def __build_instock_records__(self, inStockBatch, inventoryDict, reason):
        logger.debug("build InStock records")
        inStockRecords = []
        # build OutStockRecord to save data
        for pk in inventoryDict :
            product = None
            try:
                product = Product.objects.get(pk=pk)
            except Product.DoesNotExist:
                logger.error("Product primary key: '%s' not found, this round fail, continue. ", pk)
                continue
            except ValueError:
                logger.error("Product primary key: '%s' not valid, this round fail, continue. ", pk)
                continue        
            cost = float(inventoryDict [pk]['cost'][0])
            qty = int(inventoryDict [pk]['quantity'] [0])
            mouse = BarnMouse(product)
            inStockRecord = mouse.InStock(inStockBatch, qty, cost, reason)
            inStockRecords.append(inStockRecord)
            logger.debug("filter serial no by product: '%s'",  product.name)
            serials = self.__filter_serial_by_product__(inventoryDict[pk])
        return inStockRecords
        
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
        self.__build_instock_records__(inStockBatch, in_stock_batch_dict, reason)
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
    
