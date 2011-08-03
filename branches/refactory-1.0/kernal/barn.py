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
        return True

    def __count_product_stock__(self, starttime, endtime, stockRecords, product):
        summary = [0, 0, 0, 0] #  statistic less than starttime, statistic fall in time, total statistic, cost
        for stockRecord in stockRecords:
            if stockRecord.create_at < starttime:
                summary[0] = summary[0] + stockRecord.quantity
            elif stockRecord.create_at > starttime and stockRecord.create_at < endtime:
                summary[1] = summary[1] + stockRecord.quantity
            summary[2] = summary[2] + stockRecord.quantity    
            if hasattr(stockRecord, 'unit_sell_price'): # that mean this is OutStockRecord
                summary[3] = summary[3] +  stockRecord.cost
            else: # that mean this is InStockRecord
                summary[3] = summary[3] + ( stockRecord.cost * stockRecord.quantity) 
        logger.debug("Product '%s' quantity count by %s ~ %s, result: %s, %s, %s, %s", product.name, starttime, endtime, summary[0], summary[1], summary[2], summary[3] )
        return summary 
         
    def __count_inventory_stock__(self, starttime, endtime, product):
        result = []
        inStockSummary = []
        outStockSummary = []
        inStockRecords = InStockRecord.objects.filter(product = product)
        outStockRecords = OutStockRecord.objects.filter(product = product)
        inStockSummary = self.__count_product_stock__(starttime, endtime, inStockRecords, product)
        outStockSummary = self.__count_product_stock__(starttime, endtime, outStockRecords, product)
        # count old stock record
        old_inStock = inStockSummary[0]
        old_outStock = outStockSummary[0]
        old_Stock = old_inStock - old_outStock
        # logger.debug("the product '%s' stock before '%s', InStock: '%s', OutStock:'%s', Balance: '%s'", product.name, starttime, old_inStock, old_outStock, old_Stock)
        # count current stock record
        current_inStock = inStockSummary[1]
        current_outStock = outStockSummary[1]
        current_Stock = current_inStock - current_outStock    
        #logger.debug("the product '%s' stock fall in: '%s' ~ '%s', InStock: '%s', OutStock:'%s', Balance: '%s'", product.name, starttime, endtime, current_inStock, current_outStock, current_Stock)
        # count all stock record
        total_inStock = inStockSummary[2]
        total_outStock = outStockSummary[2]
        total_Stock = total_inStock - total_outStock    
        #logger.debug("the product '%s' total stock, InStock: '%s', OutStock:'%s', Balance: '%s'", product.name, total_inStock, total_outStock, total_Stock)
        # count all stock cost
        cost_inStock = inStockSummary[3]
        cost_outStock = outStockSummary[3]
        cost_Stock = cost_inStock - cost_outStock    
        #cost_Stock = round(cost_Stock, 2)
        logger.debug("the product '%s' cost stock, InStock: '%s', OutStock:'%s', Balance: '%s'", product.name, cost_inStock, cost_outStock, cost_Stock)
        result.append(product.name)
        result.append(product.description)
        result.append(old_Stock)
        result.append(current_inStock)
        result.append(current_outStock)
        result.append(total_Stock)
        result.append(cost_Stock)
        logger.debug("Product: '%s' count: '%s' ", product.name, result)
        return result

    def _get_cost(self):
    
    def _recalc_cost(self):
        startDate = str(date.min)+" 00:00:00"
        endDate = str(date.max)+" 23:59:59"
        starttime = datetime.datetime.strptime(startDate, '%Y-%m-%d %H:%M:%S')
        endtime = datetime.datetime.strptime(endDate, '%Y-%m-%d %H:%M:%S')    
        inventory_summary = self.__count_inventory_stock__(starttime, endtime, self.product)
        qty = inventory_summary[5]
        cost = inventory_summary[6]
        avg_cost = float(cost)/float(qty)
        logger.debug("Product: '%s' avarage cost: '%s'",self.product.name, avg_cost)
        stockCost = StockCost()
        stockCost.product = self.product
        stockCost.avg_cost = avg_cost
        stockCost.save()
        
    
    def InStock(self, inStockBatch, qty, cost, reason, serials):
        inStockRecord = InStockRecord()
        inStockRecord.inStockBatch = inStockBatch
        inStockRecord.product = self.product
        inStockRecord.cost = cost
        inStockRecord.quantity = qty
        inStockRecord.status = reason
        inStockRecord.save()
        
        if self.is_serialable:
            if not serials:
                logger.error("Product: '%s' is serial product, please the input serial no.")
                return 
            self.__build_serial_no__(inStockRecord, serials)
        
        self._recalc_cost()
        
        logger.debug("instock '%s' build success, cost: '%s', quantity:'%s' ", self.product.name, inStockRecord.cost, inStockRecord.quantity)
        return inStockRecord
        
    def __build_serial_no__(self, inStockRecord, serials):   
        logger.debug("build Serial Numbs ")
        for serialNo in serials:
            try:
               serial = SerialNo.objects.get(serial_no = serialNo)
               logger.debug("Serial no: %s found, unlock it", serialNo)
            except SerialNo.DoesNotExist:
               serial = SerialNo()
               logger.debug("build serial no: '%s' for product: '%s'", serialNo, inStockRecord.product.name)    
            serial.inStockRecord = inStockRecord
            serial.active = True
            serial.serial_no = serialNo
            serial.save()  
               
   
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
        for pk in inventoryDict:
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
            serials = self.__filter_serial_by_product__(inventoryDict[pk])
            inStockRecord = mouse.InStock(inStockBatch, qty, cost, reason, serials)
            inStockRecords.append(inStockRecord)
            logger.debug("filter serial no by product: '%s'",  product.name)
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
        inStockRecords = self.__build_instock_records__(inStockBatch, in_stock_batch_dict, reason)
        logger.debug("InStockBatch '%s' build", inStockBatch.pk)
        return inStockRecords
        
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
    
