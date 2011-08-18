from datetime import date, datetime
from django.contrib.auth.models import User
from pos.kernal.models import InStockRecord, OutStockRecord, StockCost, Product, Supplier, Customer, InStockBatch, SerialNo,\
    Bill, Payment, Category, Brand, UOM, ConsignmentOutDetail, Counter
import logging
from django.db.models.query_utils import Q



logging.basicConfig(
    level = logging.WARN,
    format = '%(asctime)s %(levelname)s %(module)s.%(funcName)s():%(lineno)s %(message)s',
)
# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class SerialRequiredException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class SerialRejectException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)    

class CounterNotReadyException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class BarnMouse:
    def __init__(self, product):
        logger.debug("BarnMose '%s' build", product.name)
        self.product = product
        self.is_serialable = self._check_serial() # mouse.is_serialable == None that mean this is initial product, still dont know is serial product or not
        self.foc_product = self._check_foc_product()
        try:
            stockCost = StockCost.objects.get(product = product)
        except StockCost.DoesNotExist:
            self._recalc_cost()

    def _check_foc_product(self):
        if "-foc-product" in self.product.name:
            logger.debug("'%s' is FOC Product", self.product.name)
            return True
        return False
        
    def _check_serial(self):
        serials = SerialNo.objects.filter(inStockRecord__product = self.product)
        if serials.count() > 0:
            logger.debug("Product: '%s' is serial product" , self.product.name)
            return True
        elif InStockRecord.objects.filter(Q(product = self.product)&Q(active = True)).count() == 0:
            return None
        logger.debug("Product: '%s' is NOT serial product", self.product.name)
        return False

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

        inStockRecords = InStockRecord.objects.filter(product = product).filter(active = True)
        outStockRecords = OutStockRecord.objects.filter(product = product).filter(active = True)
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
        avg_cost = 0
        if qty != 0:
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

    def __lock_serial_no__(self, imei):
        serial_no = None
        try:
            serial_no = SerialNo.objects.get(serial_no = imei)
            serial_no.active = False
            serial_no.save()
            logger.debug("product found by imei : %s ", imei)
        except SerialNo.DoesNotExist:
            logger.debug("no imei no '%s'. found", imei)
        return serial_no    
    
    def _count_sales_index(self):
        startIDX = 0
        endIDX = 0
        
        disableList = []
        
        inStockRecords = InStockRecord.objects.filter(product = self.product).filter(active = True)
        if inStockRecords.count() > 0:
            inStockRecords = inStockRecords.order_by("create_at")
            startIDX = inStockRecords[0].startIDX
            endIDX = inStockRecords[len(inStockRecords-1)].startIDX + inStockRecords[len(inStockRecords-1)].quantity
        
        outStockRecords = OutStockRecord.objects.filter(product = self.product).filter(active = True)
        for outStockRecord in outStockRecords:
            sales_idx = outStockRecord.sell_index
            qty =  outStockRecord.quantity
#            for i in [sales_idx: sales_idx + qty]:
#                disableList.append(i)
        return 0
    
    def OutStock(self, bill, qty, price, reason, serials):
        outStockRecord = OutStockRecord()
        outStockRecord.bill = bill
        outStockRecord.product = self.product
        serial_no = self.__lock_serial_no__(serials)
        outStockRecord.serial_no = serial_no
        outStockRecord.unit_sell_price = price
        outStockRecord.quantity = qty
        outStockRecord.amount = price * qty 
        outStockRecord.sell_index = 0;
        outStockRecord.profit = 0;
        outStockRecord.cost = -1;
        outStockRecord.type = reason
        outStockRecord.active = True
        outStockRecord.save()
        logger.info("Product: '%s' OutStockRecord build: '%s' , bill pk: '%s', qty: '%s', price: '%s', reason: '%s', serials: '%s' ", self.product.name, outStockRecord.pk, bill.pk, qty, price, reason, serials)
        
        stockCost = StockCost.objects.get(product = self.product)
        stockCost.qty = stockCost.qty - qty 
        stockCost.save()
        return outStockRecord
    
    def InStock(self, inStockBatch, qty, cost, reason, serials):
        if cost == "":
            logger.debug("Cost not define, use avg cost") 
            cost = self.Cost()
            
        index = 1
        inStockRecords = InStockRecord.objects.filter(product = self.product)
        if inStockRecords.count() > 0:
            instockrecord = inStockRecords.order_by("-startIDX")[0] 
            index = instockrecord.startIDX + instockrecord.quantity 
        
        inStockRecord = InStockRecord()
        inStockRecord.inStockBatch = inStockBatch
        inStockRecord.product = self.product
        inStockRecord.cost = cost
        inStockRecord.quantity = qty
        inStockRecord.status = reason
        inStockRecord.active = True
        inStockRecord.startIDX = index
        inStockRecord.save()
        
        if serials:
            logger.debug("Product: '%s' build serial numbers", self.product)
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
    
    def _effect_counter(self, inStockRecord):
        logger.debug("look up effect count with inStockRecord: '%s'", inStockRecord.pk)
        counters = {}
        startIDX = inStockRecord.startIDX
        endIDX = int(inStockRecord.startIDX) + int(inStockRecord.quantity)
        outStockRecords = OutStockRecord.objects.filter(Q(product = self.product)&Q(sell_index__lte = endIDX))
        logger.debug("outStockRecords found: '%s' item", len(outStockRecords))
        for outStockRecord in outStockRecords:
            outStockRecord_endIndex = outStockRecord.sell_index + outStockRecord.quantity
            logger.debug("outStockRecord_endIndex: '%s' , outStockRecord.sell_index: '%s', outStockRecord.quantity: '%s'", outStockRecord_endIndex, outStockRecord.sell_index, outStockRecord.quantity)
            if outStockRecord_endIndex < startIDX:
                continue
            counter = outStockRecord.bill.counter
            counters[counter] = counter
            logger.debug("Counter: '%s' add", counter)
        return counters
    
    def Delete(self, reason, Models, pk):
        try:
            logger.debug("Delete '%s', pk:'%s', reason:'%s'", Models, pk, reason)
            model = Models.objects.get(pk = pk)
            model.active = False
            model.reason = reason
            model.save()
            if Models == InStockRecord:
                logger.debug("InStockRecord '%s' has been delete, recalc cost", pk)
                self._recalc_cost()
        except model.DoesNotExist:
            logger.error("Delete '%s', pk:'%', reason:'%s' Fail, Does Not Exist",Models, pk, reason)




class BarnOwl:
    def __init__(self):
        # instock
        self.purchase = "purchase"
        
        # outstock
        self.cash = "Cash Sales"
        self.invoice =  "Invoice"
        self.adjust = "adjust"
        self.consignment = "Consignment"
        self.Consignment_in_balance = "Consignment_in_balance"
        self.Consignment_out_sales = "Consignment_out_sales"

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

    def __build_FOC_product__(self, product_name):    
        category = None
        brand = None
        uom = None
        categorys = Category.objects.filter(category_name = "FOC")
        if categorys.count() == 0:
            category = Category()
            category.category_name = "FOC"
            category.save()
        else:
            category = categorys[0]
        brands = Brand.objects.filter(brand_name = "FOC")
        if brands.count() == 0:
            brand = Brand()
            brand.category = category
            brand.brand_name = "FOC"
            brand.save()
        else:
            brand = brands[0]
        uoms = UOM.objects.filter(name="FOC")
        if uoms.count() == 0:
            uom = UOM()
            uom.name = "FOC"
            uom.save()
        else:
            uom = uoms[0]        
        product = Product()
        product.barcode = "FOC"
        product.name = product_name
        product.description = product_name
        product.category =  category
        product.brand =  brand
        product.retail_price = 0
        product.cost = 0
        product.uom = uom
        product.active = False
        product.save()
        return product    

    def _query_product(self, product_key):
        logger.debug("query product by: '%s'", product_key)
        product = None
        if "-foc-product" in product_key:
            logger.debug("Foc product !! : %s ", product_key)    
            products = Product.objects.filter(name=product_key)
            if products.count() == 0:
                logger.debug("Foc product NOT found in DB !! : %s , create it", product_key)    
                product =  self.__build_FOC_product__(product_key)
            else:
                product = products[0]
        else:
            serial_no = None
            try:
                serial_no = SerialNo.objects.get(serial_no = product_key)
                product = serial_no.inStockRecord.product
                logger.debug("product found by imei : %s ", product_key)
            except SerialNo.DoesNotExist:
                logger.debug("no imei no '%s'. found", product_key)
                product = Product.objects.get(pk = product_key)
        return product
    

    def _is_serial_no(self, serial_key):
        try:
            serial_no = SerialNo.objects.get(serial_no = serial_key)
            return serial_no.serial_no
        except SerialNo.DoesNotExist:
            return None
    
    
    def __build_outstock_record__(self, bill, payment, dict , reason):
        outStockRecords = []
        # build OutStockRecord to save data
        for barcode in dict:
            logger.debug("build OutStockRecord by: '%s'", barcode)
            product = self._query_product(barcode)
            qty = int(dict[barcode]['quantity'])
            unit_sell_price = float(dict[barcode]['price'])
            imei = dict[barcode].get('imei', 'None')
            serial = self._is_serial_no(imei)
            mouse = BarnMouse(product)
            outStockRecord = mouse.OutStock(bill, qty, unit_sell_price, reason, serial)
            outStockRecords.append(outStockRecord)
            """
            if payment.type == "Consignment":
                consignmentOut = ConsignmentOutDetail()
                consignmentOut.payment = payment
                consignmentOut.outStockRecord = outStockRecord
                consignmentOut.serialNo = serial
                consignmentOut.quantity = outStockRecord.quantity
                consignmentOut.balance = 0
                consignmentOut.save()
                logger.debug("build Prodict '%s' OutStockRecord '%s' consignment detail.", outStockRecord.product.name, outStockRecord.pk )
            """                
        return outStockRecords
    
    
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
            
            if mouse.is_serialable != None:  
                if mouse.is_serialable:
                    if not serials:
                        logger.error("Product: '%s' is serial product, please the input serial no.", product.name)
                        raise SerialRequiredException(product.name) 
                else:
                    if serials:
                        logger.error("Product: '%s' is NOT serial product, please DONT input serial no.", product.name)
                        raise SerialRejectException(product.name)
            
            inStockRecord = mouse.InStock(inStockBatch, qty, cost, reason, serials)
            inStockRecords.append(inStockRecord)
        return inStockRecords
    
    def __query_customer__(self, customerName):
        customerList = Customer.objects.filter(name=customerName)
        customer = None
        if customerList.count() == 0:
            logger.debug("Customer '%s' not found, auto create cusomer info.")
            customer = Customer()
            customer.customer_code = customerName
            customer.name = customerName
            customer.save()
            logger.debug("Customer build success: %s", customer)
        customer = Customer.objects.filter(name=customerName)[0]
        logger.debug("Customer found: %s", customer)
        return customer    

    def __build_bill__(self, dict, customer, counter):
        bill = Bill()
        bill.mode = dict.get('mode', 'sale')
        bill.subtotal_price = dict.get('subTotal', '0')
        bill.discount = dict.get('discount', '0')
        bill.total_price = dict.get('total', '0')
        bill.tendered_amount = dict.get('amountTendered', '0')
        bill.change = dict.get('change', '0')
        bill.customer = customer
        bill.profit = 0
        bill.counter = counter
        bill.sales_by = User.objects.get(pk=int(dict.get('salesby','-1')))
        bill.issue_by = User.objects.get(pk=dict.get('_auth_user_id'))
        bill.fulfill_payment = False
        bill.active = True
        bill.save()
        logging.info("Bill '%s' create, customer: '%s', counter: '%s '", bill.pk, customer, counter)
        return bill
    
    def __build_payment__(self, dict, bill, customer):    
        payment = Payment()
        payment.active = True
        payment.bill = bill
        salesMode = dict.get('salesMode', '')
        logger.debug("SalesMode: %s", salesMode)
        if salesMode == "cash":
            payment.term = "Cash"
            payment.type = "Cash Sales"
            payment.status = "Complete"
        elif salesMode == "invoice":
            payment.term = customer.term
            payment.type = "Invoice"
            payment.status = "Incomplete"    
        elif salesMode == "adjust":
            payment.term = "adjust"
            payment.type = "adjust"
            payment.status = "Complete"            
        elif salesMode == "Consignment":
            payment.term = "Consignment"
            payment.type = "Consignment"
            payment.status = "Incomplete"    
        elif salesMode == "Consignment_in_balance":
            payment.term = "Consignment_in_balance"
            payment.type = "Consignment_in_balance"
            payment.status = "Incomplete"    
        elif salesMode == "Consignment_out_sales":
            payment.term = "Consignment_out_sales"
            payment.type = "Consignment_out_sales"
            payment.status = "Complete"         
        else:
            logger.error("salesMode out of expect: %s ", salesMode)
        logger.debug("build '%s' payment", salesMode)                
        transactionNo = dict.get('transactionNo', '')
        if transactionNo != '': 
            logger.info("paid by creadit card")
            payment.term = "CreaditCard"
            payment.transaction_no = transactionNo
        logger.debug("payment success builded")
        payment.save()    
        return payment    
    
    """
        __convert_sales_URL_2_dict__(): 
        
        Input Data array
            [
            // Bill data
             (u'customer', [u'Cash']), 
             (u'salesby', [u'1']), 
             (u'amountTendered', [u'300']), 
             (u'salesMode', [u'cash']), 
             (u'item', [u'EXT5001']), 
             (u'mode', [u'sale']), 
             (u'discount', [u'0.00']), 
             (u'total', [u'300']), 
             (u'subTotal', [u'300']), 
             (u'change', [u'0'])
            // Payment data
             (u'transactionNo', [u'']), 
            // OutStockRecord data
             (u'EXT5001_pk', [u'35']), 
             (u'EXT5001_quantity', [u'1']), 
             (u'EXT5001_imei', [u'EXT5001']), 
             (u'EXT5001_price', [u'300']), 
            ]
            
        Output Data Dict
            {
             u'EXT5001': {
                             u'imei': [u'EXT5001'], 
                             u'pk': [u'35'], 
                             u'price': [u'300'], 
                             u'quantity': [u'1']
                         }
             }    
    """
    def __convert_sales_URL_2_dict__(self, request):
        salesDict = {}
        sales_item = request.GET.lists()
        logger.debug("instock items url parameters: %s", sales_item)    
        for key,  value in sales_item:
            if '_' not in key:
                continue
            pk = key.split("_")[0]
            attr = key.split("_")[1]
            if pk not in salesDict:
                salesDict[pk] ={}
            salesDict[pk] [attr]= value
        return salesDict
    
    
    def __build_bill_batch__(self, dict):
        counter = None
        counters = Counter.objects.filter(active=True)
        if counters.count() != 0:
            counter = counters.order_by('-create_at')[0]
        else:
            logger.warn("Can not found 'OPEN' Counter, direct to open page")
            raise CounterNotReadyException("Counter Not Found")
        # process Request parameter
        customer_name = dict.get("customer")
        customer = self.__query_customer__(customer_name)
        bill = self.__build_bill__(dict, customer, counter)
        payment = self.__build_payment__(dict, bill, customer)
        return [bill, payment]
            
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
        inStockBatch.active = True
        inStockBatch.save();
        logger.debug("InStockBatch: '%s' build", inStockBatch.pk)
        return inStockBatch    
    
    def InStock(self, reason, inStockBatch_dict, in_stock_batch_dict):
        logger.debug("Reason: '%s', dict: %s", reason, in_stock_batch_dict)
        inStockBatch = self.__build_instock_batch__(inStockBatch_dict)
        try:
            inStockRecords = self.__build_instock_records__(inStockBatch, in_stock_batch_dict, reason)
        except SerialRequiredException as srException:
            self.DeleteInStockBatch(inStockBatch.pk, "InStockRecord build fail, serial no required")
            raise srException 
        except SerialRejectException as srException:
            self.DeleteInStockBatch(inStockBatch.pk, "InStockRecord build fail, serial NOT Required, please remove it")
            raise srException 
        logger.debug("InStockBatch '%s' build", inStockBatch.pk)
        return inStockRecords
    
    def OutStock(self, reason, bill_dict, out_stock_batch_dict):
        logger.debug("Reason: '%s', dict: %s", reason, out_stock_batch_dict)
        result = self.__build_bill_batch__(bill_dict)
        bill = result[0]
        payment = result[1]
        outStockRecords = self.__build_outstock_record__(bill, payment, out_stock_batch_dict , reason)
        return [bill, payment, outStockRecords]
        
    def Cost(self, product, serial=None):
        mouse = BarnMouse(product)
        return mouse.Cost(serial)
        
    def QTY(self, product):
        mouse = BarnMouse(product)
        return mouse.QTY()
    
    def StockValue(self, product):
        mouse = BarnMouse(product)
        return mouse.StockValue()

    def DeleteBill(self, bill_pk, reason):
        if not reason:
            logger.error("Delete have fulfill reason")
            return 
        try:
            logger.info("Delete Bill: '%s', reason: '%s'", bill_pk, reason)
            bill = Bill.objects.get(pk = bill_pk)
            bill.active = False
            bill.reason = reason
            bill.save()
            
            payments = Payment.objects.filter(bill = bill)
            for payment in payments:
                logger.info("Delete Payment: '%s', reason: '%s'", payment.pk, reason)
                payment.active = False
                payment.reason = reason
                payment.save()
                
            outStockRecords = OutStockRecord.objects.filter(bill = bill)
            for outStockRecord in outStockRecords:
                product = outStockRecord.product
                mouse = BarnMouse(product)
                mouse.Delete(reason, OutStockRecord, outStockRecord.pk)
        except Bill.DoesNotExist:
            logger.error("Delete Error")
            
    def DeleteInStockBatch(self, inStockBatch_pk, reason):
        if not reason:
            logger.error("Delete have fulfill reason")
            return 
        try:
            inStockBatch = InStockBatch.objects.get(pk = inStockBatch_pk)
            inStockBatch.active = False
            inStockBatch.reason = reason
            inStockBatch.save()
            logger.info("Delete InStockBatch '%s' ", inStockBatch.pk)
            inStockRecords = InStockRecord.objects.filter(inStockBatch = inStockBatch)
            for inStockRecord in inStockRecords:
                product = inStockRecord.product
                mouse = BarnMouse(product)
                mouse.Delete(reason, InStockRecord, inStockRecord.pk)
        except InStockBatch.DoesNotExist:
            logger.error("Delete Error")

class Hermes:
    def _counter_check(self):
        counters = Counter.objects.filter(active = True)
        if counters.count() > 0:
            return False
        return True
    
    def __init__(self):
        self.is_all_close = self._counter_check()
        
    def _update_outStockRecord_set(self, bill):
        outStockRecordSet = bill.outstockrecord_set.all()
        totalProfit = 0
        for outStockRecord in outStockRecordSet:
            if outStockRecord.serial_no != None:
                product = outStockRecord.serial_no.inStockRecord.product
                totalCost = outStockRecord.serial_no.inStockRecord.cost
                outStockRecord.sell_index = -1
                outStockRecord.serial_no.active = False
                outStockRecord.serial_no.save()
                logger.info("Get price by SerialNo: %s ",totalCost);
            else:
                product = outStockRecord.product
                sales_index = __find_SalesIdx__(product)
                totalCost = __find_cost__(sales_index, outStockRecord)
                outStockRecord.sell_index = __count_sales_index__(product, sales_index, outStockRecord.quantity) 
                logger.info("Get cost by FIFO, sales index: %s ,quantity: %s, sell_index: %s",sales_index , outStockRecord.quantity, outStockRecord.sell_index);
            outStockRecord.profit = outStockRecord.amount - totalCost
            outStockRecord.cost = totalCost
            outStockRecord.save()
            totalProfit = totalProfit + outStockRecord.profit
            logger.info("OutStockRecord: %s profit: %s, product: %s, sales index: %s" , outStockRecord.pk , outStockRecord.profit, outStockRecord.product.name, outStockRecord.sell_index)
        bill.profit = totalProfit
        logger.info("Bill: %s total profit: %s" , bill.pk , bill.profit)
        bill.save()

    def _CounterCalc(self, counterID):
        counter = Counter.objects.get(pk=counterID)
        bills = Bill.objects.filter(counter=counter)
        totalAmount = counter.initail_amount
        for bill in bills:
            totalAmount = totalAmount + bill.total_price
            logger.info("Calc Bill: %s, %s" , bill.pk, bill.create_at)
            self._update_outStockRecord_set(bill)
        counter.close_amount = totalAmount
        counter.active = False
        counter.save()
        logger.debug("Counter '%s', '%s' update", counter.pk, counter.create_at)    

    def ReCalc(self, date):
        new_date = str(datetime.today()).split(" ")[0] + " 23:59:59"
        logger.debug("create_at__range=(%s,%s)", date, new_date)
        counters = Counter.objects.filter(create_at__range=(date, new_date)).order_by('create_at')
        logger.debug("%s Counters waiting update", counters.count())
        for counter in counters:
            counter.active = True
            counter.save()
            self._CounterCalc(counter.pk)
        
    def Profit(self, product):
        return False
    

