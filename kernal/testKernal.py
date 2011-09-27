# -*- coding:utf-8 -*-
import os
import sys
import unittest
import datetime
from django.contrib.auth.models import User
p1 = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
p2 = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(p1)
sys.path.append(p2)
sys.stdout = sys.stderr
os.environ['DJANGO_SETTINGS_MODULE'] = 'pos.settings' 

import logging
from barn import BarnMouse, BarnOwl
from pos.kernal.models import Product, Category, Brand, Type, UOM, InStockRecord,\
    Bill, StockCost, Counter, OutStockRecord, Payment

logging.basicConfig(
    level = logging.WARN,
    format = '%(asctime)s %(levelname)s %(funcName)s():%(lineno)s %(message)s',
)
# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestBarnMouse(unittest.TestCase):
    def setUp(self):
        logger.debug("TestBarnMouse.Setup")
        unittest.TestCase.setUp(self)
        self.products = self._build_moc_product()
        logger.debug("Build MOC OWL")
        owl = BarnOwl()
        owl.InStock(owl.purchase, self._build_inStockBatch_dict(), self._build_input_dict())
        owl.InStock(owl.purchase, self._build_inStockBatch_dict(), self._build_input_dict_2())
                    
    def tearDown(self):
        logger.debug("TestBarnMouse.TearDown")
        unittest.TestCase.tearDown(self)
        self._remove_moc_product()

    def test_stock_value(self):
        mouse = BarnMouse(self.products[0])
        assert mouse.StockValue() == 10500
        
    def test_instock(self):
        mouse = BarnMouse(self.products[1])
        owl = BarnOwl()
        inStockBatch = owl.__build_instock_batch__(self._build_inStockBatch_dict())
        mouse.InStock(inStockBatch, 3, 3, owl.purchase, ['111'])
        assert InStockRecord.objects.filter(inStockBatch = inStockBatch).count() > 0 
        
    def test_outstock(self):
        mouse = BarnMouse(self.products[0])
        bill = Bill()
        bill.subtotal_price = 100
        bill.discount = 0
        bill.total_price = 100
        bill.tendered_amount = 100
        bill.profit = 50
        bill.change = 0
        bill.create_at = datetime.datetime.today()
        bill.counter = Counter()
        bill.pk = 65535
        bill.mode = "x"
                
        mouse.OutStock(bill, 1, 1000, "Cash Sales", "serial-2")
        stockcost = StockCost.objects.get(product = self.products[0]) 
        assert stockcost.qty == 5 
        
    def test_cost_by_product__(self):
        logger.debug("Test Product Cost")
        mouse = BarnMouse(self.products[0])
        assert mouse.Cost() == 1750
        assert mouse.Cost('NKPPL006') == 1500
        assert mouse.Cost('NKPPL003') == 2000
    
    def test_delete__(self):
        logger.debug("Test DELETE Product instock record")
        mouse = BarnMouse(self.products[0])
        assert mouse.QTY() == 6
        assert mouse.Cost() == 1750
        owl = BarnOwl()
        
        inStockRecords = owl.InStock(owl.purchase, self._build_inStockBatch_dict(), self._build_input_dict())
        for inStockRecord in inStockRecords:
            mouse.Delete("ForTestOnly", InStockRecord, inStockRecord.pk)
        assert mouse.QTY() == 6
        assert mouse.Cost() == 1750
    
    def test_update_cost__(self):
        logger.debug("Test UPDATE Product Cost")
        mouse = BarnMouse(self.products[0])
        assert mouse.Cost() == 1750
        assert mouse.Cost('NKPPL006') == 1500
        owl = BarnOwl()
        inStockRecords = owl.InStock(owl.purchase, self._build_inStockBatch_dict(), self._build_input_dict_emypt_cost())
        for inStockRecord in inStockRecords:
            mouse.UpdateCost(inStockRecord.pk, 1590)
        self.assertAlmostEqual(float(mouse.Cost()), 1696.67)
    
    def test_qty_by_product__(self):
        logger.debug("Test Product QTY")
        mouse = BarnMouse(self.products[0])
        assert mouse.QTY() == 6
        
    def test_effect_counter(self):
        logger.debug("Test Effect Counter")
        c = Counter()
        c.initail_amount = 0
        c.close_amount = -1
        c.active = True
        c.user = User.objects.get(pk = 1)
        c.pk = 9999
        c.create_at = datetime.datetime.today()
        c.save()
        
        owl = BarnOwl()        
        inStockRecords = owl.InStock(owl.purchase, self._build_inStockBatch_dict(), self._build_input_dict())
        
        bill_dict = self._build_bill_dict()
        outStock_dict = self._build_output_dict()
        outStockResult = owl.OutStock(owl.cash , bill_dict, outStock_dict)
        outStockResult = owl.OutStock(owl.cash , bill_dict, outStock_dict)
        outStockResult = owl.OutStock(owl.cash , bill_dict, outStock_dict)
        assert len(outStockResult[2]) == 2

        mouse = BarnMouse(self.products[0])
        for inStockRecord in inStockRecords:
            counters = mouse._effect_counter(inStockRecord)
            assert len(counters) == 1
        c.delete()
        
    def _build_bill_dict(self):
        inputDict  = {}
        inputDict[u'customer'] = u'Cash'
        inputDict[u'salesby'] = 1
        inputDict[u'_auth_user_id'] = 1
        inputDict[u'amountTendered'] = u'300'
        inputDict[u'salesMode'] = u'cash'
        inputDict[u'item'] = u'NK1280PPL'
        inputDict[u'mode'] = u'sale'
        inputDict[u'discount'] = u'0.00'
        inputDict[u'total'] = u'300'
        inputDict[u'subTotal'] = u'300'
        inputDict[u'change'] = u'0'
        inputDict[u'transactionNo'] = u''
        return inputDict
    
    def _build_output_dict(self):
        inputDict  = {}
        inputDict[u'65535'] = {}
        inputDict[u'65535'] [u'imei'] = u'serial-0'
        inputDict[u'65535'] [u'pk'] = 65535
        inputDict[u'65535'] [u'price'] = 300    
        inputDict[u'65535'] [u'quantity'] = 1            
        
        inputDict[u'65536'] = {}
        inputDict[u'65536'] [u'imei'] = u'serial-1'
        inputDict[u'65536'] [u'pk'] = 65536
        inputDict[u'65536'] [u'price'] = 300    
        inputDict[u'65536'] [u'quantity'] = 1            
                    
        return inputDict    
    
    def _build_moc_product(self):
        logger.debug("Build MOC product")
        products = []
        product = Product()
        category = Category.objects.get(pk=1)
        brand = Brand.objects.get(pk=1)
        type = Type.objects.get(pk=1)
        uom = UOM.objects.get(pk=1)
        product.pk = 65535
        product.barcode = "testBarn " + str(65535)
        product.name = "testBarn " + str(65535)
        product.description = "testBarn " + str(65535)
        product.retail_price = 0
        product.cost = 0
        product.uom = uom
        product.category = category
        product.brand = brand
        product.type = type
        product.active=True
        product.save()
        logger.debug("Product: '%s' build", product.pk)
        products.append(product)

        product = Product()
        category = Category.objects.get(pk=1)
        brand = Brand.objects.get(pk=1)
        type = Type.objects.get(pk=1)
        uom = UOM.objects.get(pk=1)
        product.pk = 65536
        product.barcode = "testBarn " + str(65536)
        product.name = "testBarn " + str(65536)
        product.description = "testBarn " + str(65536)
        product.retail_price = 0
        product.cost = 0
        product.uom = uom
        product.category = category
        product.brand = brand
        product.type = type
        product.active=True
        product.save()
        logger.debug("Product: '%s' build", product.pk)
        products.append(product)
        return products

    def _remove_moc_product(self):
        logger.debug("clean databases:")
        for product in self.products:
            inStockRecords = InStockRecord.objects.filter(product = product)
            for inStockRecord in inStockRecords:
                logger.debug("delete instockRecord: '%s'", inStockRecord.pk)
                inStockRecord.delete()
            outStockRecords = OutStockRecord.objects.filter(product = product)
            for outStockRecord in outStockRecords:
                logger.debug("delete outStockRecord: '%s'", outStockRecord.pk)
                outStockRecord.delete()                
            logger.debug("delete product: '%s'", product.name)
            product.delete()

    def _build_inStockBatch_dict(self):
        inputDict  = {}
        inputDict[u'do_date'] = u'2011-06-22'
        inputDict[u'do_no'] = u'BC1655'
        inputDict[u'inv_no'] = u'BC1654'
        inputDict[u'salesMode'] = u'cash'
        inputDict[u'item'] = u'NK1280PPL'
        inputDict[u'mode'] = u'purchase'
        inputDict[u'supplier'] = u'Super-Link Station [M) Sdn Bhd'
        inputDict[u'_auth_user_id'] = 1
        return inputDict
        
    def _build_input_dict(self):
        inputDict  = {}
        inputDict[u'65535'] = {}
        inputDict[u'65535'] [u'serial-2'] = u'NK1280PPL003'
        inputDict[u'65535'] [u'serial-1'] = u'NK1280PPL002'
        inputDict[u'65535'] [u'serial-0'] = u'NK1280PPL001'    
        inputDict[u'65535'] [u'cost'] = u'2000'    
        inputDict[u'65535'] [u'quantity'] = u'3'            
        
        inputDict[u'65536'] = {}
        inputDict[u'65536'] [u'serial-2'] = u'NKPPL003'
        inputDict[u'65536'] [u'serial-1'] = u'NKPPL002'
        inputDict[u'65536'] [u'serial-0']= u'NKPPL001'    
        inputDict[u'65536'] [u'cost'] = u'2000'    
        inputDict[u'65536'] [u'quantity'] = u'3'                    
        return inputDict

    def _build_input_dict_2(self):
        inputDict  = {}
        inputDict[u'65535'] = {}
        inputDict[u'65535'] [u'serial-2']=u'NK1280PPL008'
        inputDict[u'65535'] [u'serial-1']=u'NK1280PPL007'
        inputDict[u'65535'] [u'serial-0']=u'NK1280PPL006'    
        inputDict[u'65535'] [u'cost'] = u'1500'    
        inputDict[u'65535'] [u'quantity'] = u'3'            
        
        inputDict[u'65536'] = {}
        inputDict[u'65536'] [u'serial-2'] = u'NKPPL008'
        inputDict[u'65536'] [u'serial-1'] = u'NKPPL007'
        inputDict[u'65536'] [u'serial-0'] = u'NKPPL006'    
        inputDict[u'65536'] [u'cost'] = u'1500'
        inputDict[u'65536'] [u'quantity'] = u'3'                    
        return inputDict
    
    def _build_input_dict_emypt_cost(self):
        inputDict  = {}
        inputDict[u'65535'] = {}
        inputDict[u'65535'] [u'serial-2'] = u'NK1280PPL003'
        inputDict[u'65535'] [u'serial-1'] = u'NK1280PPL002'
        inputDict[u'65535'] [u'serial-0'] = u'NK1280PPL001'    
        inputDict[u'65535'] [u'cost'] = u''    
        inputDict[u'65535'] [u'quantity'] = u'3'            
        
        inputDict[u'65536'] = {}
        inputDict[u'65536'] [u'serial-2'] = u'NKPPL003'
        inputDict[u'65536'] [u'serial-1'] = u'NKPPL002'
        inputDict[u'65536'] [u'serial-0']= u'NKPPL001'    
        inputDict[u'65536'] [u'cost'] = u''    
        inputDict[u'65536'] [u'quantity'] = u'3'                    
        return inputDict
            
class TestBarnOwl(unittest.TestCase):    
    def setUp(self):
        logger.debug("TestBarnOwl.Setup")
        unittest.TestCase.setUp(self)
        self.products = self._build_moc_product()
        logger.debug("Build MOC OWL")
        owl = BarnOwl()
        owl.InStock(owl.purchase, self._build_inStockBatch_dict(), self._build_input_dict())        
        
    def tearDown(self):
        logger.debug("TestBarnOwl.TearDown")
        unittest.TestCase.tearDown(self)
        self._remove_moc_product()
        
    def test__filter_serial_by_product__(self):
        owl = BarnOwl()        
        dict = self._build_input_dict()
        serials = owl.__filter_serial_by_product__(dict[u'65535'])        
        assert len(serials) == 3
        
    def testInStock(self):
        owl = BarnOwl()        
        inStockResult = owl.InStock(owl.purchase, self._build_inStockBatch_dict(), self._build_input_dict())        
        assert len(inStockResult) == 2
        
    def testOutStock(self):
        c = Counter()
        c.initail_amount = 0
        c.close_amount = -1
        c.active = True
        c.user = User.objects.get(pk = 1)
        c.pk = 9999
        c.create_at = datetime.datetime.today()
        c.save()
        
        owl = BarnOwl()        
        bill_dict = self._build_bill_dict()
        outStock_dict = self._build_output_dict()
        outStockResult = owl.OutStock(owl.cash , bill_dict, outStock_dict)
        assert len(outStockResult[2]) == 2
        c.delete()
        
    def testStockValue(self):
        owl = BarnOwl()
        assert owl.StockValue(self.products[0]) == 6000

    def testCost(self):
        owl = BarnOwl()
        assert owl.Cost(self.products[0]) == 2000
    
    def testQty(self):
        owl = BarnOwl()
        assert owl.QTY(self.products[0]) == 3
    
    def _test_delete_bill(self):
        c = Counter()
        c.initail_amount = 0
        c.close_amount = -1
        c.active = True
        c.user = User.objects.get(pk = 1)
        c.pk = 9999
        c.create_at = datetime.datetime.today()
        c.save()
        
        owl = BarnOwl()        
        bill_dict = self._build_bill_dict()
        outStock_dict = self._build_output_dict()
        outStockResult = owl.OutStock(owl.cash , bill_dict, outStock_dict)
        assert len(outStockResult) == 2
        owl.DeleteBill(outStockResult[0].bill.pk, "for Testing")
        assert Bill.objects.get(pk = outStockResult[0].bill.pk).active == False
        payments = Payment.objects.filter(bill = outStockResult[0].bill)
        for payment in payments: 
            assert payment.active == False
        outStockRecords = OutStockRecord.objects.filter(bill = outStockResult[0].bill)
        for outStockRecord in outStockRecords:
            assert outStockRecord.active == False
        c.delete()        
    
    def test_delete_instock_batch(self):
        owl = BarnOwl()        
        inStockResult = owl.InStock(owl.purchase, self._build_inStockBatch_dict(), self._build_input_dict())        
        assert len(inStockResult) == 2        
        for inStockRecord in inStockResult:
            owl.DeleteInStockBatch(inStockRecord.inStockBatch.pk, "for test")
        assert inStockResult[0].inStockBatch.active == False
            
    def _build_moc_product(self):
        logger.debug("Build MOC product")
        products = []
        product = Product()
        category = Category.objects.get(pk=1)
        brand = Brand.objects.get(pk=1)
        type = Type.objects.get(pk=1)
        uom = UOM.objects.get(pk=1)
        product.pk = 65535
        product.barcode = "testBarn"
        product.name = "testBarn"
        product.description = "testBarn"
        product.retail_price = 0
        product.cost = 0
        product.uom = uom
        product.category = category
        product.brand = brand
        product.type = type
        product.active=True
        product.save()
        logger.debug("Product: '%s' build", product.pk)
        products.append(product)

        product = Product()
        category = Category.objects.get(pk=1)
        brand = Brand.objects.get(pk=1)
        type = Type.objects.get(pk=1)
        uom = UOM.objects.get(pk=1)
        product.pk = 65536
        product.barcode = "testBarn"
        product.name = "testBarn"
        product.description = "testBarn"
        product.retail_price = 0
        product.cost = 0
        product.uom = uom
        product.category = category
        product.brand = brand
        product.type = type
        product.active=True
        product.save()
        logger.debug("Product: '%s' build", product.pk)
        products.append(product)
        return products

    def _remove_moc_product(self):
        logger.debug("clean databases:")
        products = Product.objects.filter(barcode = "testBarn")
        for product in products:
            inStockRecords = InStockRecord.objects.filter(product = product)
            for inStockRecord in inStockRecords:
                logger.debug("delete inStockRecord: '%s'", inStockRecord.pk)
                inStockRecord.delete()
            outStockRecords = OutStockRecord.objects.filter(product = product)
            for outStockRecord in outStockRecords:
                logger.debug("delete outStockRecord: '%s'", outStockRecord.pk)
                outStockRecord.delete()
            logger.debug("delete product: '%s'", product.name)
            product.delete()
        
    def _build_inStockBatch_dict(self):
        inputDict  = {}
        inputDict[u'do_date'] = u'2011-06-22'
        inputDict[u'do_no'] = u'BC1655'
        inputDict[u'inv_no'] = u'BC1654'
        inputDict[u'salesMode'] = u'cash'
        inputDict[u'item'] = u'NK1280PPL'
        inputDict[u'mode'] = u'purchase'
        inputDict[u'supplier'] = u'Super-Link Station [M) Sdn Bhd'
        inputDict[u'_auth_user_id'] = 1
        return inputDict
    
    def _build_input_dict(self):
        inputDict  = {}
        inputDict[u'65535'] = {}
        inputDict[u'65535'] [u'serial-2'] = u'NK1280PPL003'
        inputDict[u'65535'] [u'serial-1'] = u'NK1280PPL002'
        inputDict[u'65535'] [u'serial-0'] = u'NK1280PPL001'    
        inputDict[u'65535'] [u'cost'] = u'2000'    
        inputDict[u'65535'] [u'quantity'] = u'3'            
        
        inputDict[u'65536'] = {}
        inputDict[u'65536'] [u'serial-2'] = u'NK1280PPL003'
        inputDict[u'65536'] [u'serial-1'] = u'NK1280PPL002'
        inputDict[u'65536'] [u'serial-0'] = u'NK1280PPL001'    
        inputDict[u'65536'] [u'cost'] = u'2000'    
        inputDict[u'65536'] [u'quantity'] = u'3'                    
        return inputDict

    def _build_bill_dict(self):
        inputDict  = {}
        inputDict[u'customer'] = u'Cash'
        inputDict[u'salesby'] = 1
        inputDict[u'_auth_user_id'] = 1
        inputDict[u'amountTendered'] = u'300'
        inputDict[u'salesMode'] = u'cash'
        inputDict[u'item'] = u'NK1280PPL'
        inputDict[u'mode'] = u'sale'
        inputDict[u'discount'] = u'0.00'
        inputDict[u'total'] = u'300'
        inputDict[u'subTotal'] = u'300'
        inputDict[u'change'] = u'0'
        inputDict[u'transactionNo'] = u''
        return inputDict
    
    def _build_output_dict(self):
        inputDict  = {}
        inputDict[u'65535'] = {}
        inputDict[u'65535'] [u'imei'] = u'serial-0'
        inputDict[u'65535'] [u'pk'] = 65535
        inputDict[u'65535'] [u'price'] = 300    
        inputDict[u'65535'] [u'quantity'] = 1            
        
        inputDict[u'65536'] = {}
        inputDict[u'65536'] [u'imei'] = u'serial-1'
        inputDict[u'65536'] [u'pk'] = 65536
        inputDict[u'65536'] [u'price'] = 300    
        inputDict[u'65536'] [u'quantity'] = 1            
                    
        return inputDict
        
if __name__=="__main__":
    unittest.main()    
    