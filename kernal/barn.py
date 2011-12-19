from datetime import date, datetime
from django.contrib.auth.models import User
from pos.kernal.models import InStockRecord, OutStockRecord, StockCost, Product, Supplier, Customer, InStockBatch, SerialNo, Bill, Payment, Category, Brand, UOM, ConsignmentOutDetail, Counter,\
    ConsignmentInDetail, ConsignmentInDetailBalanceHistory, Algo, Deposit,\
    ExtraCost, SerialNoMapping
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
    
class OutofStockException(Exception):
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
    def _calc_last_index(self):
        if self.foc_product:
            return 
        inStockRecords = InStockRecord.objects.filter(product = self.product).filter(active = True).order_by("create_at")
        if inStockRecords.count() == 0:
            logger.debug(" '%s' not instock record found ", self.product.name)
            return 
 
        logger.debug("calc last instock record and sell index for product '%s'", self.product.name)
        outStockRecords = OutStockRecord.objects.filter(product = self.product).filter(active = True).order_by("-create_at")
        if outStockRecords.count() == 0:
            logger.debug("Product: '%s' not any out stock record, initial it", self.product.name)
            self.sell_index = 0;
            inStockRecords = InStockRecord.objects.filter(product = self.product).filter(active = True).order_by("create_at")
            if inStockRecords.count() != 0:
                self.last_inStockRecord = inStockRecords[0]
        else:
            self.sell_index = outStockRecords[0].sell_index + outStockRecords[0].quantity 
            pre_inStockRecord = outStockRecords[0].inStockRecord
            if  self.sell_index > (pre_inStockRecord.startIDX + pre_inStockRecord.quantity):
                inStockRecors = InStockRecord.objects.filter(product = self.product).filter(create_at__gt = pre_inStockRecord.create_at)
                if inStockRecors.count() == 0:
                    logger.debug("sell_index: '%s' > pre_instockrecord: '%s', next inStockRecord NOT FOUND, return pre_inStockRecord", self.sell_index, pre_inStockRecord.pk)
                    self.last_inStockRecord = pre_inStockRecord
                else:
                    logger.debug("sell_index: '%s' > pre_instockrecord: '%s', next inStockRecord FOUND, return next inStockRecord", self.sell_index, pre_inStockRecord.pk)
                    self.last_inStockRecord = inStockRecors[0]
            else:
                logger.debug("sell_index: '%s' fall in pre_instockrecord: '%s', return pre_inStockRecord", self.sell_index, pre_inStockRecord.pk)
                self.last_inStockRecord = pre_inStockRecord

    def _check_consignment(self):
        inStockRecords = InStockRecord.objects.filter(product = self.product).filter(active = True)
        if inStockRecords.count() == 0:
            logger.debug("Product: '%s' not initial yet, cant to check if consignment or not", self.product)
            return None
        for inStockRecord in inStockRecords:
            batch = inStockRecord.inStockBatch
            if batch.mode == Hermes.CONSIGNMENT_IN:
                return True
            else:
                return False
    
    def __init__(self, product):
        logger.debug("BarnMose Build, product: '%s'", product.name)
        self.product = product
        self.is_serialable = self._check_serial() # mouse.is_serialable == None that mean this is initial product, still dont know is serial product or not
        self.is_consignment_product = self._check_consignment()
        self.foc_product = self._check_foc_product()
        try:
            stockCost = StockCost.objects.get(product = product)
        except StockCost.DoesNotExist:
            self._recalc_cost()
        self.last_inStockRecord = None
        self.sell_index = 0
        self._calc_last_index()

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
            logger.debug("Product: '%s' are NOT initial yet" , self.product.name)
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
                summary[3] = summary[3] +  (stockRecord.inStockRecord.cost * stockRecord.quantity)
            else: # that mean this is InStockRecord
                summary[3] = summary[3] + ( stockRecord.cost * stockRecord.quantity) 
        logger.debug("Product '%s' '%s' quantity count by %s ~ %s, result: B4_QTY:%s, NOW_QTY:%s, QTY:%s, COST:%s", product.name, stockRecords, starttime, endtime, summary[0], summary[1], summary[2], summary[3] )
        return summary 
         
    def Count_inventory_stock(self, starttime, endtime, product):
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
        if total_Stock == 0:
            result.append(0)
        else:
            avg_cost = float(cost_Stock)/float(total_Stock)
            result.append(avg_cost)
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
                serial = SerialNo.objects.get(serial_no=serial.serial_no)
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
    
    def _recalc_sell_index(self, outStockRecord):
        logger.debug("Re-Calc Sell Index since '%s'", outStockRecord.pk)
        pass

    def _recalc_cost(self):
        startDate = str(date.min)+" 00:00:00"
        endDate = str(date.max)+" 23:59:59"
        starttime = datetime.strptime(startDate, '%Y-%m-%d %H:%M:%S')
        endtime = datetime.strptime(endDate, '%Y-%m-%d %H:%M:%S')
        inventory_summary = self.Count_inventory_stock(starttime, endtime, self.product)
        qty = inventory_summary[5]
        cost = inventory_summary[6]
        avg_cost = 0
        if qty != 0:
            avg_cost = cost / qty
        on_hand_value = qty * avg_cost
        logger.debug("Product: '%s' avarage cost: (%s/%s) = %s",self.product.name, cost, qty, avg_cost)
        
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

    def __lock_serial_no__(self, imei, qty):
        serial_no = None
        try:
            serial_no = SerialNo.objects.get(serial_no = imei)
            if (serial_no.balance + qty) > serial_no.quantity:
                raise OutofStockException("Requered: '%s' qty: '%s', stock:'%s' ", serial_no, qty, serial_no.balance)   
            serial_no.balance = serial_no.balance + qty 
            if serial_no.balance == serial_no.quantity:
                logger.debug("Serial '%s' sold out", serial_no.serial_no)
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
    
    def _query_inStockRecord(self, serial_no):
        if serial_no:
            return serial_no.inStockRecord
        return self.last_inStockRecord

    def OutStock(self, bill, qty, price, reason, serials):
        outStockRecord = OutStockRecord()
        outStockRecord.bill = bill
        outStockRecord.product = self.product
        serial_no = self.__lock_serial_no__(serials, qty)
        outStockRecord.inStockRecord = self._query_inStockRecord(serial_no)
        outStockRecord.serial_no = serial_no
        outStockRecord.unit_sell_price = price
        outStockRecord.quantity = qty
        outStockRecord.amount = price * qty 
        outStockRecord.sell_index = 0;
        outStockRecord.cost = self.Cost(serial_no) * qty;
        outStockRecord.profit = float(outStockRecord.amount) - float(outStockRecord.cost);
        outStockRecord.type = reason
        outStockRecord.active = True
        outStockRecord.save()
        logger.info("Product: '%s' OutStockRecord build: '%s' , bill pk: '%s', qty: '%s', price: '%s', reason: '%s', serials: '%s' ", self.product.name, outStockRecord.pk, bill.pk, qty, price, reason, serials)
        
        self._recalc_cost()
        #stockCost = StockCost.objects.get(product = self.product)
        #stockCost.qty = stockCost.qty - qty 
        #stockCost.save()
        return outStockRecord
    
    def InStock(self, inStockBatch, qty, cost, reason, serials):
        if cost == "":
            logger.debug("Cost not define, use avg cost") 
            cost = self.Cost()
            
        index = 1
        inStockRecords = InStockRecord.objects.filter(product = self.product)
        if inStockRecords.count() > 0:
            instockrecord = inStockRecords.order_by("-startIDX")[0] 
            index = int(instockrecord.startIDX) + int(instockrecord.quantity) 
        
        inStockRecord = InStockRecord()
        inStockRecord.inStockBatch = inStockBatch
        inStockRecord.product = self.product
        inStockRecord.cost = cost
        inStockRecord.quantity = qty
        inStockRecord.type = reason
        inStockRecord.status = "Complete"
        inStockRecord.active = True
        inStockRecord.startIDX = index
        inStockRecord.save()
        
        if serials:
            logger.debug("Product: '%s' build serial numbers", self.product)
            self.__build_serial_no__(inStockRecord, serials)
            
        self._recalc_cost()
        
        logger.debug("Product '%s' instock build success, cost: '%s', quantity:'%s' ", self.product.name, inStockRecord.cost, inStockRecord.quantity)
        return inStockRecord
        
    def _serial_validation(self, qty, serials):
        qty = int(qty)
        serialSet = set(serials)
        if len(serialSet) == qty:
            return 1
        elif len(serialSet) == 1:
            return qty
        else:
            return -1
        
    def __build_serial_no__(self, inStockRecord, serials):   
        logger.debug("build Serial Numbs ")
        qty = self._serial_validation(inStockRecord.quantity, serials)
        if qty == -1:
            logger.error("SERIAL Error")
            return
        for serialNo in set(serials):
            if serialNo == '':
                continue
            serialNo = inStockRecord.product.name +"-"+ serialNo
            logger.debug("combine serial no: '%s'", serialNo)
            try:
                serial = SerialNo.objects.get(serial_no = serialNo)
                serial.quantity = int(serial.quantity) + qty
                serial.serial_no = serialNo
                serial.active = True
                serial.save()
                mapping = SerialNoMapping()
                mapping.inStockRecord = inStockRecord
                mapping.serial_no = serial
                mapping.save()                
                logger.debug("Serial no: %s found, unlock it, current qty: '%s'", serialNo, serial.quantity)
            except SerialNo.DoesNotExist:
                serial = SerialNo()
                logger.debug("build serial no: '%s' for product: '%s'", serialNo, inStockRecord.product.name)    
                serial.inStockRecord = inStockRecord
                serial.active = True
                serial.quantity = qty
                serial.balance =  0
                serial.serial_no = serialNo
                serial.save()
                mapping = SerialNoMapping()
                mapping.inStockRecord = inStockRecord
                mapping.serial_no = serial
                mapping.save()
                
    
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

    
    def QTY(self, serial=None):
        try:
            if serial:
                serial = SerialNo.objects.get(serial_no=serial)
                qty = serial.quantity - serial.balance
                logger.debug("Product: '%s' serial:'%s' QTY: '%s'", self.product, serial, qty)
                return qty
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
            
            outStockRecords = OutStockRecord.objects.filter(inStockRecord = instance)
            for outStockRecord in outStockRecords:
                outStockRecord.cost = cost * int(outStockRecord.quantity)
                outStockRecord.save()
                logger.debug('update outStockRecord %s, cost: %s', outStockRecord.pk, outStockRecord.cost)
            logger.debug("instance '%s' , Cost: '%s' update SUCCESS", pk, instance.cost)
            self._recalc_cost()
        except InStockRecord.DoesNotExist:
            logger.warn("instance '%s' , Cost: '%s' does NOT update correctly", pk, cost)
    
    def UpdateProfit(self, outStockRecord):
        logger.debug("Update profit, OutStockRecord: '%s'", outStockRecord.pk)
        totalCost = self.Cost(outStockRecord.serial_no) * outStockRecord.quantity 
        outStockRecord.profit = outStockRecord.amount - totalCost
        outStockRecord.cost = totalCost
        outStockRecord.save()

    
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
                serials = SerialNo.objects.filter(inStockRecord = model)
                for serial in serials:
                    serial.quantity -= model.quantity
                    if serial.balance > serial.quantity:
                        serial.balance = serial.quantity
                    if serial.quantity == 0:
                        serial.avtive = False
                    serial.save()   
                serialmappings = SerialNoMapping.objects.filter(inStockRecord = model)
                for serialmapping in serialmappings:
                    serialmapping.avtive = False
                    serialmapping.reason = 'Delete InStockRecord'
            else:
                logger.debug("OutStockRecord '%s' has been delete, recalc sell index", pk)
                self._recalc_sell_index(model)
            self._recalc_cost()
        except Models.DoesNotExist:
            logger.error("Delete '%s', pk:'%', reason:'%s' Fail, Does Not Exist",Models, pk, reason)

class Rats(BarnMouse):
    def Cost(self, serial=None):
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

class MickyMouse(BarnMouse):
    def _check_foc_product(self):
        if "-foc-product" in self.product.name:
            logger.debug("'%s' is FOC Product", self.product.name)
            return True
        return False
        

    def _recalc_cost(self):
        inStockRecords = InStockRecord.objects.filter(product = self.product)
        if inStockRecords.count() > 0:
            return inStockRecords.order_by(("-create_at"))[0].cost
        logger.debug("Product: '%s' cost not found", self.product)
        return 0
    
    
    def __init__(self, product):
        logger.debug("MickyMouse Build, product: '%s'", product.name)
        self.product = product
        self.cost = self._recalc_cost()
        self.is_serialable = False
        self.is_consignment_product = False
        self.foc_product = self._check_foc_product()
        self.last_inStockRecord = None
        self.sell_index = 0
        
    def InStock(self, inStockBatch, qty, cost, reason, serials):
        if cost == "":
            logger.debug("Cost not define, use avg cost") 
            cost = self.Cost()
        inStockRecord = InStockRecord()
        inStockRecord.inStockBatch = inStockBatch
        inStockRecord.product = self.product
        inStockRecord.cost = float(self.product.retail_price) * (1 - float(cost))
        inStockRecord.quantity = 0
        inStockRecord.status = reason
        inStockRecord.active = True
        inStockRecord.startIDX = -1
        inStockRecord.save()
        self.cost = cost
        logger.debug("Product '%s' instock build success, cost: '%s', quantity:'%s' ", self.product.name, inStockRecord.cost, inStockRecord.quantity)
        return inStockRecord
        
    def OutStock(self, bill, qty, price, reason, serials):
        outStockRecord = OutStockRecord()
        outStockRecord.bill = bill
        outStockRecord.product = self.product
        outStockRecord.inStockRecord = self._query_inStockRecord(None)
        outStockRecord.serial_no = None
        outStockRecord.unit_sell_price = price
        outStockRecord.quantity = qty
        outStockRecord.amount = price * qty 
        outStockRecord.sell_index = 0;
        outStockRecord.cost = self.cost * qty;
        outStockRecord.profit = float(outStockRecord.amount) - float(outStockRecord.cost);
        outStockRecord.type = reason
        outStockRecord.active = True
        outStockRecord.save()
        logger.info("Product: '%s' OutStockRecord build: '%s' , bill pk: '%s', qty: '%s', price: '%s', reason: '%s', serials: '%s', amout:'%s', cost:'%s', profit: '%s' ", self.product.name, outStockRecord.pk, bill.pk, qty, price, reason, serials, float(outStockRecord.amount), float(outStockRecord.cost), outStockRecord.profit)
        return outStockRecord
    
    def StockValue(self):
        return 0
    
    def QTY(self, serial = None):
        return 99999
    
    def Cost(self, serial=None):
        return self.cost
    
    
    def UpdateCost(self, pk, cost):
        return 0
    
    def UpdateProfit(self, outStockRecord):
        return 0
    
    def Delete(self, reason, Models, pk):
        try:
            logger.debug("Delete '%s', pk:'%s', reason:'%s'", Models, pk, reason)
            model = Models.objects.get(pk = pk)
            model.active = False
            model.reason = reason
            model.save()
            if Models == InStockRecord:
                logger.debug("InStockRecord '%s' has been delete, recalc cost", pk)
                self.cost = self._recalc_cost()
        except model.DoesNotExist:
            logger.error("Delete '%s', pk:'%', reason:'%s' Fail, Does Not Exist",Models, pk, reason)

class ServiceMouse(MickyMouse):
    def OutStock(self, bill, qty, price, reason, serials, cost):
        outStockRecord = OutStockRecord()
        outStockRecord.bill = bill
        outStockRecord.product = self.product
        outStockRecord.inStockRecord = None
        outStockRecord.serial_no = serials
        outStockRecord.unit_sell_price = price
        outStockRecord.quantity = qty
        outStockRecord.amount = price * qty 
        outStockRecord.sell_index = 0;
        outStockRecord.cost = cost * qty;
        outStockRecord.profit = float(outStockRecord.amount) - float(outStockRecord.cost);
        outStockRecord.type = reason
        outStockRecord.active = True
        outStockRecord.save()
        logger.info("Product: '%s' OutStockRecord build: '%s' , bill pk: '%s', qty: '%s', price: '%s', reason: '%s', serials: '%s', amout:'%s', cost:'%s', profit: '%s' ", self.product.name, outStockRecord.pk, bill.pk, qty, price, reason, serials, float(outStockRecord.amount), float(outStockRecord.cost), outStockRecord.profit)
        return outStockRecord


class BarnOwl:
        # instock
    purchase = "purchase"
    pawning= "pawning"
    tradein= "trade-in"
    transfer= "transfer"
    # outstock
    cash = "Cash Sales"
    invoice =  "Invoice"
    adjust = "adjust"
    consignment = "Consignment"
    Consignment_in_balance = "Consignment_in_balance"
    Consignment_out_sales = "Consignment_out_sales"
    
    def __init__(self):
        pass
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
                serial = productDict[item]
                if serial == '':
                    continue
                logger.debug("Serial: '%s' add to serial list", productDict[item])
                serials.append(serial)
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
        product.algo = Algo.objects.get(name = Algo.AVERAGE_COST)
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
    
    
    def _build_product_dict(self, dict):
        product_dict = {}
        # build OutStockRecord to save data
        for barcode in dict:
            pk = self._is_serial_no(dict[barcode].get('imei', 'None'))
            if not pk:
                pk = dict[barcode]["pk"]
            if barcode not in product_dict:
                product_dict[barcode] = {}
            product_dict[barcode]['product'] = self._query_product(pk)
            product_dict[barcode]['qty'] = int(dict[barcode]['quantity'])
            product_dict[barcode]['unit_sell_price'] = float(dict[barcode]['price'])
            product_dict[barcode]['extracost'] = float(dict[barcode].get('extracost', '0.0'))
            try:
                product_dict[barcode]['cost'] = float(dict[barcode]['cost'])
            except Exception:
                logger.error("COST not found")
                pass
            product_dict[barcode]['serial'] = self._is_serial_no(dict[barcode].get('imei', 'None'))
        logger.debug("product dict build: '%s'", product_dict)
        return product_dict  

    def __build_outstock_record__(self, bill, payment, dict , reason):
        product_dict = self._build_product_dict(dict)
        outStockRecords = []
        if reason == "service":
            for product_dict in product_dict.itervalues():
                logger.debug("build Service OutStockRecord by: '%s'", product_dict)
                product = product_dict["product"]
                qty = int(product_dict["qty"])
                cost = int(product_dict["cost"])
                unit_sell_price = float(product_dict["unit_sell_price"])
                serial = product_dict["serial"]
                mouse = ServiceMouse(product)
                outStockRecord = mouse.OutStock(bill, qty, unit_sell_price, reason, serial, cost)
                outStockRecords.append(outStockRecord)
            return outStockRecords
        # build OutStockRecord to save data
        for product_dict in product_dict.itervalues():
            logger.debug("build OutStockRecord by: '%s'", product_dict)
            product = product_dict["product"]
            qty = int(product_dict["qty"])
            unit_sell_price = float(product_dict["unit_sell_price"])
            serial = product_dict["serial"]
            if product.algo.name == Algo.PERCENTAGE:
                logger.debug("Build outstockrecord by algo: '%s'", product.algo.name)
                mouse = MickyMouse(product)
            elif product.algo.name == Algo.NO_SERIAL:
                logger.debug("Build outstockrecord by algo: '%s'", product.algo.name)            
                mouse = Rats(product)                
            else:
                logger.debug("Build outstockrecord by algo: '%s'", product.algo.name)            
                mouse = BarnMouse(product)
            outStockRecord = mouse.OutStock(bill, qty, unit_sell_price, reason, serial)
            outStockRecords.append(outStockRecord)
        return outStockRecords

    
    
    def __build_instock_records__(self, inStockBatch, inventoryDict, reason):
        logger.debug("build InStock records")
        inStockRecords = []
        # build OutStockRecord to save data
        for pk in inventoryDict:
            product = None
            try:
                product = Product.objects.get(pk=pk.split('RANDOM')[0])
            except Product.DoesNotExist:
                logger.error("Product primary key: '%s' not found, this round fail, continue. ", pk)
                continue
            except ValueError:
                logger.error("Product primary key: '%s' not valid, this round fail, continue. ", pk)
                continue        
            cost = inventoryDict [pk]['cost']
            qty = inventoryDict [pk]['quantity']
            mouse = None
            if product.algo.name == Algo.PERCENTAGE:
                logger.debug("Build instockrecord by algo: '%s'", product.algo.name)
                mouse = MickyMouse(product)
            else:
                logger.debug("Build instockrecord by algo: '%s'", product.algo.name)
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
    
    def __build_bill__(self, dict, customer, counter):
        bill = Bill()
        bill.mode = dict.get('mode', 'sale')
        bill.subtotal_price = dict.get('subTotal', '0')
        bill.discount = dict.get('discount', '0')
        bill.deposit_price = dict.get('deposit', '0')
        deposit_id = dict.get('depositField', '')
        if deposit_id != '':
            bill.deposit = Deposit.objects.get(pk=int(deposit_id))
        bill.total_price = dict.get('total', '0')
        bill.tendered_amount = dict.get('amountTendered', '0')
        bill.change = dict.get('change', '0')
        bill.customer = customer
        bill.refbill = dict.get('refbill', '')
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
        payment_dict = {}
        payment_dict['cash_term'] = 'Cash'
        payment_dict['cash_type'] = 'Cash Sales'
        payment_dict['cash_status'] = 'Complete'
        
        payment_dict['invoice_term'] = customer.term
        payment_dict['invoice_type'] = 'Invoice'
        payment_dict['invoice_status'] = 'Incomplete'
        
        payment_dict['transfer_term'] = 'Transfer'
        payment_dict['transfer_type'] = 'Transfer'
        payment_dict['transfer_status'] = 'Complete'
        
        payment_dict['adjust_term'] = 'adjust'
        payment_dict['adjust_type'] = 'Adjust'
        payment_dict['adjust_status'] = 'Complete'        
        
        payment_dict['Consignment_IN_Return_term'] = 'Consignment IN Return'
        payment_dict['Consignment_IN_Return_type'] = 'Consignment_IN_Return'
        payment_dict['Consignment_IN_Return_status'] = 'Complete'

        payment_dict['Consignment_OUT_term'] = 'Consignment OUT'
        payment_dict['Consignment_OUT_type'] = 'Consignment_OUT'
        payment_dict['Consignment_OUT_status'] = 'Incomplete'

        payment_dict['service_term'] = 'Service'
        payment_dict['service_type'] = 'Service'
        payment_dict['service_status'] = 'Complete'

        payment_dict['pawning_term'] = 'Service'
        payment_dict['pawning_type'] = 'Service'
        payment_dict['pawning_status'] = 'Complete'

        payment = Payment()
        payment.active = True
        payment.bill = bill
        mode = dict.get('mode', '')
        logger.debug("Mode: %s", mode)
        payment.term = payment_dict[mode+"_term"]
        payment.type = payment_dict[mode+"_type"]
        payment.status = payment_dict[mode+"_status"]
                        
        transactionNo = dict.get('transactionNo', '')
        if transactionNo != '': 
            logger.info("paid by creadit card")
            payment.term = "CreaditCard"
            payment.transaction_no = transactionNo
        logger.debug("payment success builded. Term:'%s', Type:'%s', Status:'%s'", payment.term, payment.type, payment.status)
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
        thanatos = Thanatos()
        customer = None
        if dict.get("mode", '') == Hermes.CONSIGNMENT_IN_RETURN or dict.get("mode", '') == Hermes.CONSIGNMENT:
            customer = thanatos.Customer(dict.get("supplier"))
        else:
            customer = thanatos.Customer(dict.get("customer"))
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
        inStockBatch.refBill_no = dict.get('refBill_no', "-")
        if mode == self.pawning or mode == Hermes.CONSIGNMENT_IN:
            inStockBatch.status = 'Incomplete'
        else:
            inStockBatch.status = 'Complete'
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
        return [inStockBatch, inStockRecords]

    def _summary_profit(self, outStockRecords):
        total_profit = 0
        for outStockRecord in outStockRecords:
            total_profit += float(outStockRecord.profit)
        return total_profit
    
    def _summary_extra_cost(self, bill):
        total_cost = 0
        costs = ExtraCost.objects.filter(bill = bill)
        for cost in costs:
            total_cost += float(cost.price)
        return total_cost
    
    def OutStock(self, reason, bill_dict, out_stock_batch_dict):
        logger.debug("Reason: '%s', dict: %s", reason, out_stock_batch_dict)
        result = self.__build_bill_batch__(bill_dict)
        bill = result[0]
        payment = result[1]
        outStockRecords = self.__build_outstock_record__(bill, payment, out_stock_batch_dict , reason)
        if bill.mode == 'pawning':
            for outStockRecord in outStockRecords:
                inStockBatch = outStockRecord.serial_no.inStockRecord.inStockBatch
                inStockBatch.status = "Complete"
                inStockBatch.save()
        
        bill.profit = self._summary_profit(outStockRecords) - self._summary_extra_cost(bill) 
        logger.debug("Bill: '%s' profit: '%s'", bill.pk, bill.profit)
        bill.save()
        return [bill, payment, outStockRecords]
    
    def RecalcBill(self, billID):
        logger.debug("Recalc bill: '%s'", billID)
        bill = Bill.objects.get(pk=billID)
        outStockRecords = OutStockRecord.objects.filter(bill = bill)
        bill.profit = self._summary_profit(outStockRecords) + float(bill.deposit_price) - self._summary_extra_cost(bill) 
        logger.debug("Bill: '%s' profit: '%s'", bill.pk, bill.profit)
        bill.save()        
        return bill
    
    def Cost(self, product, serial=None):
        mouse = None
        if product.algo.name == Algo.PERCENTAGE:
            mouse = MickyMouse(product)
        elif product.algo.name == Algo.NO_SERIAL:
            mouse = BarnMouse(product)
            logger.debug("Product: '%s' algo is NO_SERIAL, return avg cost", product.name)
            return mouse.Cost(None)    
        else:
            mouse = BarnMouse(product)
        return mouse.Cost(serial)
        
    def QTY(self, product):
        mouse = None
        if product.algo.name == Algo.PERCENTAGE:
            mouse = MickyMouse(product)
        else:
            mouse = BarnMouse(product)
        return mouse.QTY()
    
    def StockValue(self, product):
        mouse = None
        if product.algo.name == Algo.PERCENTAGE:
            mouse = MickyMouse(product)
        else:
            mouse = BarnMouse(product)
        return mouse.StockValue()
    
    def DeleteInStockBatch(self, batch_id, reason):
        if not reason:
            logger.error("Delete have fulfill reason")
            return        
        try:
            logger.info("Delete InStockBatch: '%s', reason: '%s'", batch_id, reason)
            inStockBatch = InStockBatch.objects.get(pk = batch_id)
            inStockBatch.active = False
            inStockBatch.reason = reason
            inStockBatch.save()
            
            inStockRecords = InStockRecord.objects.filter(inStockBatch = inStockBatch)
            for inStockRecord in inStockRecords:
                product = inStockRecord.product
                mouse = None
                if product.algo.name == Algo.PERCENTAGE:
                    mouse = MickyMouse(product)
                else:
                    mouse = BarnMouse(product)
                mouse.Delete(reason, InStockRecord, inStockRecord.pk)
                serials = SerialNo.objects.filter(inStockRecord = inStockRecord)
                for serial in serials:
                    self.unlock_serial_num(serial, inStockRecord.quantity)
            return inStockBatch 
        except inStockBatch.DoesNotExist:
            logger.error("Delete Error")
    
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
                mouse = None
                if product.algo.name == Algo.PERCENTAGE:
                    mouse = MickyMouse(product)
                else:
                    mouse = BarnMouse(product)
                mouse.Delete(reason, OutStockRecord, outStockRecord.pk)
                self.unlock_serial_num(outStockRecord.serial_no, outStockRecord.quantity)
        except Bill.DoesNotExist:
            logger.error("Delete Error")

    def unlock_serial_num(self, serial, qty):
        if not serial:
            return 
        logger.debug("unlock serial no: %s, qty: %s", serial.serial_no, qty)
        serial.active = True
        serial.balance -= qty
        serial.save()

class Hermes:
    CONSIGNMENT = "Consignment"
    CONSIGNMENT_OUT = "Consignment_OUT"
    CONSIGNMENT_OUT_RETURN  = "Consignment_OUT_RETURN"
    CONSIGNMENT_OUT_SALE  = "Consignment_OUT_SALE"
    CONSIGNMENT_IN = "Consignment_IN"
    CONSIGNMENT_IN_RETURN = "Consignment_IN_Return"
    CONSIGNMENT_IN_STATUS_INCOMPLETE = "Incomplete"
    CONSIGNMENT_IN_STATUS_COMPLETE = "Complete"
    CONSIGNMENT_IN_STATUS_FOCUS = "focusing"
    
    def _counter_check(self):
        counters = Counter.objects.filter(active = True)
        if counters.count() > 0:
            return False
        return True
    
    def __init__(self):
        self.is_all_close = self._counter_check()
        
    def _recalc_bill_profit(self, bill):
        outStockRecordSet = bill.outstockrecord_set.all()
        totalProfit = 0
        for outStockRecord in outStockRecordSet:
            mouse = None
            if outStockRecord.product.algo.name == Algo.PERCENTAGE:
                mouse = MickyMouse(outStockRecord.product)
            else:
                mouse = BarnMouse(outStockRecord.product)
            mouse.UpdateProfit(outStockRecord)
            totalProfit = totalProfit + outStockRecord.profit
            logger.info("OutStockRecord: %s profit: %s, product: %s, sales index: %s" , outStockRecord.pk , outStockRecord.profit, outStockRecord.product.name, outStockRecord.sell_index)
        bill.profit = totalProfit
        logger.info("Bill: %s total profit: %s" , bill.pk , bill.profit)
        bill.save()

    def CounterAmount(self, counterID):
        return self._calcCounterTotalAmountByPK(counterID, recalc_bill_profit = False)

    def _calcCounterTotalAmountByPK(self, counterID, recalc_bill_profit = False):
        counter = Counter.objects.get(pk=counterID)
        bills = Bill.objects.filter(counter=counter).filter(active=True)
        totalAmount = counter.initail_amount
        for bill in bills:
            logger.info("Calc Bill: %s, %s" , bill.pk, bill.create_at)
            if recalc_bill_profit:
                logger.debug("ReCalc Bill '%s' outStockRecord profit", bill.pk)
                self._recalc_bill_profit(bill)
            totalAmount = totalAmount + bill.total_price
        
        date = counter.create_at.strftime("%Y-%m-%d") + " 00:00:00"
        new_date = counter.create_at.strftime("%Y-%m-%d") + " 23:59:59"
        logger.debug("create_at__range=(%s,%s)", date, new_date)
        inStockRecords = InStockRecord.objects.filter(create_at__range=(date, new_date)).filter(active=1).filter(Q(type=BarnOwl.pawning)|Q(type=BarnOwl.tradein))
        total_cost = 0
        for inStockRecord in inStockRecords:
            total_cost += inStockRecord.cost 
        
        return totalAmount - total_cost             

    def ReCalcCounterByPK(self, counterID, recalc_bill_profit = False):
        counter = Counter.objects.get(pk=counterID)
        totalAmount = self._calcCounterTotalAmountByPK(counter.pk, recalc_bill_profit)
        counter.close_amount = totalAmount
        counter.active = False
        counter.save()
        logger.debug("Counter '%s', '%s' update", counter.pk, counter.create_at)    

    def ReCalcCounters(self, date):
        date = str(date).split(" ")[0] + " 00:00:00"
        new_date = str(datetime.today()).split(" ")[0] + " 23:59:59"
        logger.debug("create_at__range=(%s,%s)", date, new_date)
        counters = Counter.objects.filter(create_at__range=(date, new_date)).order_by('create_at')
        logger.debug("%s Counters waiting update", counters.count())
        for counter in counters:
            counter.active = True
            counter.save()
            logger.debug("Counter '%s': '%s' reopen for re-calc.", counter.pk, counter.create_at)
            self.ReCalcCounterByPK(counter.pk, recalc_bill_profit=True)

    def ConsignmentOut(self, payment, outStockRecords):
            if payment.type != self.CONSIGNMENT_OUT:
                logger.debug("Payment: '%s' Not Consignment Bill. Payment type = '%s', return ", payment.pk, payment.type)
                return
            for outStockRecord in outStockRecords:
                consignmentOut = ConsignmentOutDetail()
                consignmentOut.payment = payment
                consignmentOut.outStockRecord = outStockRecord
                consignmentOut.serialNo = outStockRecord.serial_no
                consignmentOut.quantity = outStockRecord.quantity
                consignmentOut.balance = 0
                consignmentOut.active = True
                consignmentOut.save()
                logger.debug("build Prodict '%s' OutStockRecord '%s' consignment detail.", outStockRecord.product.name, outStockRecord.pk )
        
    def Profit(self, product):
        return False

    def _try_close_consignmentout_bill(self, payment):
        if payment.active == False:
            logger.debug("payment: '%s' already close", payment.pk)
            return str(payment.pk)
        consignmentOutDetails = ConsignmentOutDetail.objects.filter(payment = payment)
        for consignmentOutDetail in consignmentOutDetails:
            if consignmentOutDetail.active == True:
                logger.debug("Payment: '%s' can not close yet, consignment out detail '%s' still active", payment.pk, consignmentOutDetail.pk, )
                return False
        logger.debug("Payment: '%s' '%s' complete", payment.pk, payment.type)
        payment.status = 'Complete'
        payment.save()
        return payment.bill.pk


    def ConsignmentOutSale(self, payment, bill_dict, out_stock_batch_dict):
        customer = payment.bill.customer
        owl = BarnOwl()
        product_dict = owl._build_product_dict(out_stock_batch_dict)
        
        for id, map in product_dict.items():
            product = map['product']
            serial = None
            if 'serial' in map and map['serial']:
                serial = SerialNo.objects.get(serial_no = map.get('serial', ''))
            qty= map['qty']
            self._ConsignmentOutSale_detail(payment, product, qty, customer, serial = serial)
        return self._try_close_consignmentout_bill(payment)
        
    def _ConsignmentOutSale_detail(self, payment, product, qty, customer, serial = None):
        if serial:
            consignmentOutDetails = ConsignmentOutDetail.objects.filter(Q(payment = payment)&
                                                                        Q(outStockRecord__product = product)&
                                                                        Q(serialNo = serial)&
                                                                        Q(outStockRecord__bill__customer=customer)).order_by('create_at')
            for consignmentOutDetail in consignmentOutDetails:
                consignmentOutDetail.balance += qty
                if consignmentOutDetail.quantity == consignmentOutDetail.balance:
                    consignmentOutDetail.active = False
                    consignmentOutDetail.reason = "Complete"
                    logger.debug("Consignment Out Sales: '%s' close", consignmentOutDetail.pk)
                consignmentOutDetail.save()                
            return
        
        consignmentOutDetails = ConsignmentOutDetail.objects.filter(Q(payment = payment)&
                                                                    Q(outStockRecord__product = product)&
                                                                    Q(outStockRecord__bill__customer=customer)).order_by('create_at')
        logger.debug("Filter ConsignmentOutDetail, result:'%s'", len(consignmentOutDetails))
        
        self._balance_consignment_out_detail(consignmentOutDetails, qty)
                
    def _balance_consignment_out_detail(self, consignmentOutDetails, qty):
        counter = qty
        for consignmentOutDetail in consignmentOutDetails:
            consignmentQty = consignmentOutDetail.quantity - consignmentOutDetail.balance
            if counter <= consignmentQty:
                consignmentOutDetail.balance += counter
                if consignmentOutDetail.quantity == consignmentOutDetail.balance:
                    consignmentOutDetail.active = False
                    consignmentOutDetail.reason = "Complete"
                    logger.debug("Consignment Out Sales: '%s' close", consignmentOutDetail.pk)
                consignmentOutDetail.save()
                logger.debug("Consignment Out Sales balance done.")
            else:
                counter -= consignmentQty
                consignmentOutDetail.balance += consignmentQty
                consignmentOutDetail.active = False
                consignmentOutDetail.reason = "Complete"                
                consignmentOutDetail.save()
                logger.debug("Consignment Out Sales: '%s' close, balance not done. still have '%s' need to balance", consignmentOutDetail.pk, counter)
            self._try_close_consignmentout_bill(consignmentOutDetail.payment)

    def _rollback_consignment_out_detail(self, consignmentOutDetails, qty):
        counter = qty
        for consignmentOutDetail in consignmentOutDetails:
            consignmentQty = consignmentOutDetail.balance
            if counter <= consignmentQty:
                consignmentOutDetail.balance -= counter
                if consignmentOutDetail.quantity != consignmentOutDetail.balance:
                    consignmentOutDetail.active = True
                    consignmentOutDetail.reason = "InComplete"
                consignmentOutDetail.save()
                logger.debug("delete Consignment Out Sales balance done.")
            else:
                counter -= consignmentQty
                consignmentOutDetail.balance = 0
                consignmentOutDetail.active = True
                consignmentOutDetail.reason = "InComplete"                
                consignmentOutDetail.save()
                logger.debug("Delete Consignment Out Sales: '%s' close, balance not done. still have '%s' need to balance", consignmentOutDetail.pk, counter)
            isCanClose = self._try_close_consignmentout_bill(consignmentOutDetail.payment)
            if isCanClose == False:
                consignmentOutDetail.payment.avtive = True
                consignmentOutDetail.payment.status = 'InComplete'
                consignmentOutDetail.payment.save()

    
    def _mining_serials_by_instockrecord(self, inStockRecord):
        serials = set()
        serialNoMappings = SerialNoMapping.objects.filter(inStockRecord = inStockRecord)
        for serialNoMapping in serialNoMappings:
            serials.add(serialNoMapping.serial_no)
        return serials

    def DeleteConsignmentOutReturn(self, inStockBatch):
        if inStockBatch.mode == self.CONSIGNMENT_OUT_RETURN:
            logger.debug("Consignment out return found, Delete consignemnt out balance.")
            supplier = inStockBatch.supplier
            inStockRecords = InStockRecord.objects.filter(inStockBatch = inStockBatch)
            for inStockRecord in inStockRecords:
                product = inStockRecord.product
                qty = inStockRecord.quantity
                serials = self._mining_serials_by_instockrecord(inStockRecord)
                if serials:
                    for serialNo in serials:
                        consignmentOutDetails = ConsignmentOutDetail.objects.filter(Q(payment__bill__customer__name = supplier.name)&Q(serialNo = serialNo)).order_by('-create_at')
                        self._balance_consignment_out_detail(consignmentOutDetails, qty)
                else:
                    consignmentOutDetails = ConsignmentOutDetail.objects.filter(Q(payment__bill__customer__name = supplier.name)&Q(outStockRecord__product = product)).order_by('-create_at')
                    self._balance_consignment_out_detail(consignmentOutDetails, qty)
        else:
            logger.debug("InStock mode: %s", inStockBatch.mode)
    
    def ConsignmentOutReturn(self, inStockBatch):
        if inStockBatch.mode == self.CONSIGNMENT_OUT_RETURN:
            logger.debug("Consignment out return found, consignemnt out balance.")
            supplier = inStockBatch.supplier
            inStockRecords = InStockRecord.objects.filter(inStockBatch = inStockBatch)
            for inStockRecord in inStockRecords:
                product = inStockRecord.product
                qty = inStockRecord.quantity
                serials = self._mining_serials_by_instockrecord(inStockRecord)
                if serials:
                    for serialNo in serials:
                        consignmentOutDetails = ConsignmentOutDetail.objects.filter(Q(payment__bill__customer__name = supplier.name)&Q(serialNo = serialNo)).order_by('create_at')
                        self._balance_consignment_out_detail(consignmentOutDetails, qty)
                else:
                    consignmentOutDetails = ConsignmentOutDetail.objects.filter(Q(payment__bill__customer__name = supplier.name)&Q(outStockRecord__product = product)).order_by('create_at')
                    self._balance_consignment_out_detail(consignmentOutDetails, qty)
        else:
            logger.debug("InStock mode: %s", inStockBatch.mode)

    def DeleteConsignmentIn(self, inStockBatch, reason):
        if inStockBatch.mode == self.CONSIGNMENT_IN:
            logger.debug("Consignment IN batch found, delete consignemnt details.")
            consignmentInDetails = ConsignmentInDetail.objects.filter(inStockBatch = inStockBatch)
            for consignmentInDetail in consignmentInDetails:
                consignmentInDetail.active = False
                consignmentInDetail.reason = reason
                consignmentInDetail.save()
                logger.debug("ConsignmentInDetail deleted. id: '%s' , reason: '%s'", consignmentInDetail.pk, reason)
        else:
            logger.debug("InStock mode: %s", inStockBatch.mode)
    
    def ConsignmentIn(self, inStockBatch):
        if inStockBatch.mode == self.CONSIGNMENT_IN:
            logger.debug("Consignment IN batch found, build consignemnt details.")
            inStockRecords = InStockRecord.objects.filter(inStockBatch = inStockBatch)
            for inStockRecord in inStockRecords:
                consignmentInDetail = ConsignmentInDetail()
                consignmentInDetail.inStockBatch = inStockRecord.inStockBatch
                consignmentInDetail.inStockRecord = inStockRecord
                consignmentInDetail.quantity = inStockRecord.quantity
                consignmentInDetail.balance = 0
                consignmentInDetail.active = True
                consignmentInDetail.status = Hermes.CONSIGNMENT_IN_STATUS_INCOMPLETE
                consignmentInDetail.save()        
                logger.debug("Consignment IN record build! '%s'", consignmentInDetail.pk)
        else:
            logger.debug("InStock mode: %s", inStockBatch.mode)

    def _query_consignment_in_detail_set(self, outStockRecord, supplier = None):
        logger.debug("Query consignment in details, outStockRecord: '%s', supplier: '%s'", outStockRecord.pk, supplier)
        mouse = None
        if outStockRecord.product.algo.name == Algo.PERCENTAGE:
            mouse = MickyMouse(outStockRecord.product)
        else: 
            mouse = BarnMouse(outStockRecord.product)
        if not mouse.is_consignment_product:
            logger.warn("Product: '%s' was not consignment product", outStockRecord.product.pk)
            return []
        if mouse.is_serialable:
            logger.debug("Query ConsignmentInDetail by SerialNo: '%s'", outStockRecord.serial_no)
            return ConsignmentInDetail.objects.filter(inStockRecord = outStockRecord.serial_no.inStockRecord).order_by("create_at")
        else:
            logger.debug("Query ConsignmentInDetail by FIFO")
            query = None
            if supplier:
                logger.debug("Query supplier:'%s' Product: '%s', ConsignmentInDetails", supplier, outStockRecord.product)
                query = Q(inStockBatch__supplier = supplier)&Q(inStockRecord__product = outStockRecord.product)&Q(active=True)
            else:
                logger.debug("Query Product: '%s', ConsignmentInDetails", outStockRecord.product)
                query = Q(inStockRecord__product = outStockRecord.product)&Q(active=True)
            return ConsignmentInDetail.objects.filter(query).order_by("create_at")
    
    def _close_Consignment(self, consignmentInDetail):
        if consignmentInDetail.balance == consignmentInDetail.quantity:
            logger.debug("Consignment IN Record '%s' balanced. ", consignmentInDetail.pk)
            consignmentInDetail.status = self.CONSIGNMENT_IN_STATUS_COMPLETE
            consignmentInDetail.active = False
            

    def _balance_consignment_in(self, outStockRecord, consignmentInDetails):
        total_sold_qty = outStockRecord.quantity
        logger.debug("total_sold_qty: '%s', consignmentInDetails: '%s'", total_sold_qty, len(consignmentInDetails))
        for consignmentInDetail in consignmentInDetails:
            consignmentQty = consignmentInDetail.quantity - consignmentInDetail.balance
            if consignmentQty == 0:
                return
            consignmentInDetailBalanceHistory = ConsignmentInDetailBalanceHistory()
            consignmentInDetailBalanceHistory.consignmentInDetail = consignmentInDetail
            consignmentInDetailBalanceHistory.outStockRecord = outStockRecord
            consignmentInDetailBalanceHistory.active = 1
            consignmentInDetailBalanceHistory.save()
            logger.debug("consignmentInDetailBalanceHistory build, id:'%s'", consignmentInDetailBalanceHistory.pk)
            logger.debug("total_sold_qty: '%s', consignmentQty: '%s'", total_sold_qty, consignmentQty)
            if total_sold_qty <= consignmentQty:
                logger.debug("ConsignmentInDetails: '%s' balance qty: '%s'", consignmentInDetail.pk, consignmentQty)
                consignmentInDetail.balance = consignmentInDetail.balance + total_sold_qty
                self._close_Consignment(consignmentInDetail)
                consignmentInDetail.save()
                logger.debug("last Consignment IN Record balance, '%s'", consignmentInDetail.pk)
                break
            else:
                consignmentInDetail.balance = consignmentInDetail.balance + consignmentQty
                self._close_Consignment(consignmentInDetail)
                consignmentInDetail.save()
                total_sold_qty = total_sold_qty - consignmentQty
                logger.debug("Consignment IN Record: '%s' NOT last Consignment IN Record, next...,", consignmentInDetail.pk)
                logger.debug("ConsignmentInDetails: '%s' balance qty: '%s'", consignmentInDetail.pk, consignmentInDetail.balance)
        
        
    def BalanceConsignmentIN(self, outStockRecords, supplier = None):
        
        logger.debug("BalanceConsignmentIN, outStockRecords: '%s'", len(outStockRecords))
        for outStockRecord in outStockRecords:
            consignment_in_detail_set = self._query_consignment_in_detail_set(outStockRecord, supplier)
            self._balance_consignment_in(outStockRecord, consignment_in_detail_set)


    
    def DeleteConsignmentInBalance(self, bill, reason):
        logger.debug("delete Consignment In Balance, Bill ID:'%s', reason: '%s' ", bill.pk, reason)
        outStockRecords = OutStockRecord.objects.filter(bill = bill)
        for outStockRecord in outStockRecords:
            if outStockRecord.product.algo.name == Algo.PERCENTAGE:
                mouse = MickyMouse(outStockRecord.product)
            else:
                mouse = BarnMouse(outStockRecord.product)
            mouse.Delete(reason, OutStockRecord, outStockRecord.pk)
            self.unlock_serial_num(outStockRecord.serial_no, outStockRecord.quantity)
            ConsignmentInDetailBalanceHistorys = ConsignmentInDetailBalanceHistory.objects.filter(outStockRecord = outStockRecord)
            total_consignment_qty = 0
            for ConsignmentInDetailBalanceHistory in ConsignmentInDetailBalanceHistorys:
                total_consignment_qty += ConsignmentInDetailBalanceHistory.consignmentInDetail.balance
                ConsignmentInDetailBalanceHistory.active = False
                ConsignmentInDetailBalanceHistory.reason = reason
                ConsignmentInDetailBalanceHistory.save()
            
    def unlock_serial_num(self, serial, qty):
        if not serial:
            return 
        logger.debug("unlock serial no: %s, qty: %s", serial.serial_no, qty)
        serial.active = True
        serial.balance -= qty
        serial.save()
                
class Thanatos:
    def Customer(self, name):
        customerList = Customer.objects.filter(name=name)
        customer = None
        if customerList.count() == 0:
            logger.debug("Customer '%s' not found, auto create cusomer info.", name)
            customer = Customer()
            customer.customer_code = name
            customer.name = name
            customer.save()
            logger.debug("Customer build success: %s", customer)
        else:
            customer = customerList[0]
        logger.debug("Customer: '%s' found", customer.name)
        return customer
        
    def Supplier(self, name):
        supplierList = Supplier.objects.filter(name=name)
        supplier = None
        if supplierList.count() == 0:
            logger.debug("Supplier '%s' not found, auto create supplier info.")
            supplier = Supplier()
            supplier.customer_code = name
            supplier.name = name
            supplier.save()
            logger.debug("Supplier build success: %s", supplier)
        else:
            supplier = supplierList[0]
        logger.debug("Supplier: '%s' found", supplier.name)
        return supplier    
        