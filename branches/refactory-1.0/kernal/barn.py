from datetime import date, datetime
from django.contrib.auth.models import User
from pos.kernal.models import InStockRecord, OutStockRecord, StockCost, Product, Supplier, Customer, InStockBatch, SerialNo
import logging


logging.basicConfig(
    level = logging.WARN,
    format = '%(asctime)s %(levelname)s %(module)s.%(funcName)s():%(lineno)s %(message)s',
)
# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class BarnMouse:
    def __init__(self, product):
        logger.debug("BarnMose '%s' build", product.name)
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

    def _query_last_record_datetime(self, models):
        result = models.objects.filter(product = self.product)
        if result.count() > 0:
            return result.order_by("-create_at")[0].create_at
        return None

    def Cost(self, serial=None):
        if serial:
            try:
                serial = SerialNo.objects.get(serial_no=serial)
                cost = serial.inStockRecord.cost
                logger.debug("product:'%s', Serial no: '%s' cost: '%s'", self.product, serial, cost)
                return cost
            except SerialNo.DoesNotExist:
                cost = StockCost.objects.get(product=self.product).avg_cost
                logger.debug("product:'%s', Serial no: '%s' NOT found, return avg cost: '%s' ", self.product, serial, cost)
                return cost
        cost = 0
        try:
            logger.debug("look up Product: '%s' stockCost", self.product.pk)
            query = StockCost.objects.get(product=self.product)
            cost = query.avg_cost
        except StockCost.DoesNotExist:
            logger.warn("Product: '%s' not found on StockCount table, return avg cost: 0")
            return 0
        logger.debug("product:'%s', avg cost: '%s' ", self.product, cost)
        return cost
    
    def _recalc_cost(self):
        startDate = str(date.min)+" 00:00:00"
        endDate = str(date.max)+" 23:59:59"
        starttime = datetime.strptime(startDate, '%Y-%m-%d %H:%M:%S')
        endtime = datetime.strptime(endDate, '%Y-%m-%d %H:%M:%S')    
        inventory_summary = self.__count_inventory_stock__(starttime, endtime, self.product)
        qty = inventory_summary[5]
        cost = inventory_summary[6]
        avg_cost = cost / qty
        on_hand_value = qty * avg_cost
        logger.debug("Product: '%s' avarage cost: '%s'",self.product.name, avg_cost)
        
        stockCosts = StockCost.objects.filter(product = self.product)
        stockCost = None
        if stockCosts.count() == 0:
            logger.debug("Create StockCosts: '%s'", self.product.name)
            stockCost = StockCost()
        else:
            logger.debug("update StockCosts '%s'", self.product.name)
            stockCost = stockCosts[0] 
        stockCost.on_hand_value = on_hand_value
        stockCost.product = self.product
        stockCost.qty = qty
        stockCost.avg_cost = avg_cost
        stockCost.instock_create_at = self._query_last_record_datetime(InStockRecord)
        stockCost.outstock_create_at = self._query_last_record_datetime(OutStockRecord)
        stockCost.save()
    
    def InStock(self, inStockBatch, qty, cost, reason, serials):
        if cost == "":
            logger.debug("Cost not define, use avg cost") 
            cost = self.Cost()
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
        
        logger.debug("Product '%s' instock build success, cost: '%s', quantity:'%s' ", self.product.name, inStockRecord.cost, inStockRecord.quantity)
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
    
    def StockValue(self):
        try:
            logger.debug("look up Product: '%s' stockCost", self.product.pk)
            query = StockCost.objects.get(product=self.product)
            cost = query.on_hand_value
        except StockCost.DoesNotExist:
            logger.warn("Product: '%s' not found on StockCount table, return avg cost: 0")
            return 0
        logger.debug("Product: '%s' On hand value: '%s'", self.product, cost)
        return cost

    
    def QTY(self):
        try:
            logger.debug("look up Product: '%s' QTY", self.product.pk)
            query = StockCost.objects.get(product=self.product)
            qty = query.qty
        except StockCost.DoesNotExist:
            logger.warn("Product: '%s' not found on StockCount table, return QTY: 0")
            return 0
        logger.debug("Product: '%s' QTY: '%s'", self.product, qty)
        return qty

    
    def UpdateCost(self, pk, cost):
        try:
            instance = InStockRecord.objects.get(pk = pk)
            instance.cost = cost
            instance.save()
            logger.debug("instance '%s' , Cost: '%s' update SUCCESS", pk, cost)
            self._recalc_cost()
        except InStockRecord.DoesNotExist:
            logger.warn("instance '%s' , Cost: '%s' does NOT update correctly", pk, cost)

    
    def Delete(self, reason, InStockRecord, pk):
        
        pass
    
    

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
            cost = inventoryDict [pk]['cost']
            qty = inventoryDict [pk]['quantity']
            mouse = BarnMouse(product)
            serials = self.__filter_serial_by_product__(inventoryDict[pk])
            inStockRecord = mouse.InStock(inStockBatch, qty, cost, reason, serials)
            inStockRecords.append(inStockRecord)
            logger.debug("filter serial no by product: '%s'",  product.name)
        return inStockRecords
        
    def __build_instock_batch__(self, dict):
        mode = dict.get('mode', 'purchase')
        today = date.today()
        do_date = dict.get('do_date', today.strftime("%d/%m/%y"))
        supplier_name = dict.get('supplier', "")
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
        inStockBatch.user = User.objects.get(pk=dict.get('_auth_user_id'))
        inStockBatch.do_date = do_date
        inStockBatch.invoice_no = dict.get('inv_no', "-")
        inStockBatch.do_no = dict.get('do_no', "-")
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
        
#    def __build_outstock_record__(self.request, bill, payment, dict , type):
#        outStockRecords = []
#        # build OutStockRecord to save data
#        for barcode in dict:
#            logger.debug("build OutStockRecord by: '%s'", barcode)
#            outStockRecord = OutStockRecord()
#            outStockRecord.bill = bill
#            outStockRecord.barcode = barcode
#            logger.info("looking for pk : %s " % barcode)
#            if "-foc-product" in barcode:
#                logger.info("Foc product !! : %s " % barcode)    
#                products = Product.objects.filter(name=barcode)
#                if products.count() == 0:
#                    logger.info("Foc product NOT found in DB !! : %s , create it" % barcode)    
#                    outStockRecord.product =  __build_FOC_product__(barcode)
#                else:
#                    outStockRecord.product = products[0]
#            else:
#                serial_no = __lock_serial_no__(request, barcode)
#                outStockRecord.serial_no = serial_no
#                if serial_no:
#                    logger.info("product found by imei : %s " % barcode)
#                    outStockRecord.product = serial_no.inStockRecord.product
#                else:
#                    logger.info("product found by pk : %s " % barcode)
#                    outStockRecord.product = Product.objects.get(pk=barcode)
#            outStockRecord.unit_sell_price = dict[barcode]['price'][0]
#            outStockRecord.quantity = dict[barcode]['quantity'] [0]
#            outStockRecord.amount = str(float(dict[barcode]['price'][0]) * float(dict[barcode]['quantity'] [0])) 
#            outStockRecord.sell_index = 0;
#            outStockRecord.profit = 0;
#            outStockRecord.cost = -1;
#            outStockRecord.type = type
#            outStockRecord.save()
#            outStockRecords.append(OutStockRecord.objects.get(pk=outStockRecord.pk))
#            if payment.type == "Consignment":
#                consignmentOut = ConsignmentOutDetail()
#                consignmentOut.payment = payment
#                consignmentOut.outStockRecord = outStockRecord
#                consignmentOut.serialNo = serial_no
#                consignmentOut.quantity = outStockRecord.quantity
#                consignmentOut.balance = 0
#                consignmentOut.save()
#                logger.debug("build Prodict '%s' OutStockRecord '%s' consignment detail.", outStockRecord.product.name, outStockRecord.pk )
#            return outStockRecords
#        
    def OutStock(self, reason, out_stock_batch_dict):
        logger.debug("Reason: '%s', dict: %s", reason, out_stock_batch_dict)
#        bill = self.__build_instock_batch__(out_stock_batch_dict)
#        outStockRecords = self.__build_instock_records__(bill, out_stock_batch_dict, reason)
#        logger.debug("InStockBatch '%s' build", outStockRecords.pk)
#        return outStockRecords
        pass
        
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
    
