

from pos.kernal.models import Product
from pos.kernal.models import InStockBatch, InStockRecord
from pos.kernal.models import OutStockRecord
from pos.kernal.models import Product
from pos.kernal.models import Product

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
"""
Below function for ajax use
"""
#def ajaxProductDetailView(request):
   # if request.method == 'GET':

class StockKeeper:
    def __init__(self, product):
        if not product:
            logger.error("StockKeeper build fail!!")
            return 
        logger.info("StockKeeper '%s' build !!", product.name)
        self.product = product

class ProductBuilder:
    def build(self, dict, inStockBatch):
        inventoryDict = __buildProductsDict(dict)
        __buildProducts(inventoryDict, inStockBatch)
        logger.debug("product build")
    def __buildProductsDict(self, dict):
        logger.debug("instock items: %s", sales_item)    
        for key,  value in sales_item:
            if key == "do_no":
                continue
            if key == "inv_no":
                continue            
            if key == "do_date":
                continue
            if key.find("_") == -1:
                continue
            pk = key.split("_")[0]
            attr = key.split("_")[1]
            if pk not in inventoryDict :
                inventoryDict [pk] ={}
            inventoryDict [pk] [attr]= value
        logger.debug("inventory dict: %s", inventoryDict)
        return inventoryDict
    
    def __buildProducts(self, inventoryDict, inStockBatch):
        # build OutStockRecord to save data
        for pk in inventoryDict :
            inStockRecord = InStockRecord()
            inStockRecord.inStockBatch = inStockBatch
            inStockRecord.barcode = pk
            product = Product.objects.get(pk=pk)
            inStockRecord.product = product
            inStockRecord.cost = inventoryDict [pk]['cost'][0]
            inStockRecord.quantity = inventoryDict [pk]['quantity'] [0]
            inStockRecord.save()
            for value in inventoryDict[pk] :
                if 'serial-' in value:
                    serialNO = request.GET.get(pk+"_"+value, '') 
                    if serialNO == '':
                        continue
                    serial = SerialNo()
                    serial.inStockRecord = inStockRecord
                    serial.serial_no = serialNO
                    serial.save()            
        