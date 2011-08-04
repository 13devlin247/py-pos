# -*- coding:utf-8 -*-
import os
import sys
import unittest
p1 = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
p2 = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(p1)
sys.path.append(p2)
sys.stdout = sys.stderr
os.environ['DJANGO_SETTINGS_MODULE'] = 'pos.settings' 
import logging
from barn import BarnMouse, BarnOwl
from kernal.models import Product, Category, Brand, Type, UOM

logging.basicConfig(
    level = logging.WARN,
    format = '%(asctime)s %(levelname)s %(funcName)s():%(lineno)s %(message)s',
)
# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestBarnMouse(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)
        owl = BarnOwl()
        owl.InStock("purchase", )
                    
    def test_cost_by_product__(self):
        mouse = BarnMouse()
        
        pass
    def _build_moc_product(self):
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


    def _remove_moc_product(self):
        logger.debug("clean databases:")
        products = Product.objects.filter(barcode = "testBarn")
        for product in products:
            logger.debug("delete product: '%s'", product.name)
            product.delete()
        
    def _build_input_dict(self):
        inputDict  = {}
        inputDict[u'do_date'] = u'2011-06-22'
        inputDict[u'do_no'] = u'BC1655'
        inputDict[u'inv_no'] = u'BC1654'
        inputDict[u'salesMode'] = u'cash'
        inputDict[u'item'] = u'NK1280PPL'
        inputDict[u'mode'] = u'purchase'
        inputDict[u'supplier'] = u'Super-Link Station [M) Sdn Bhd'
        inputDict[u'_auth_user_id'] = 1
        
        
        """
        Supplier
        Customer
        Mode
        User
        DO_Date
        Invoice_NO
        DO_NO
        Status
        """
        inputDict[u'65535'] = {}
        inputDict[u'65535'] [u'serial-2'] = []
        inputDict[u'65535'] [u'serial-2'].append(u'NK1280PPL003')
        inputDict[u'65535'] [u'serial-1'] = []
        inputDict[u'65535'] [u'serial-1'].append(u'NK1280PPL002')
        inputDict[u'65535'] [u'serial-0'] = []
        inputDict[u'65535'] [u'serial-0'].append(u'NK1280PPL001')    
        inputDict[u'65535'] [u'cost'] = []
        inputDict[u'65535'] [u'cost'].append(u'2000')    
        inputDict[u'65535'] [u'quantity'] = []
        inputDict[u'65535'] [u'quantity'].append(u'3')            
        
        inputDict[u'65536'] = {}
        inputDict[u'65536'] [u'serial-2'] = []
        inputDict[u'65536'] [u'serial-2'].append(u'NK1280PPL003')
        inputDict[u'65536'] [u'serial-1'] = []
        inputDict[u'65536'] [u'serial-1'].append(u'NK1280PPL002')
        inputDict[u'65536'] [u'serial-0'] = []
        inputDict[u'65536'] [u'serial-0'].append(u'NK1280PPL001')    
        inputDict[u'65536'] [u'cost'] = []
        inputDict[u'65536'] [u'cost'].append(u'2000')    
        inputDict[u'65536'] [u'quantity'] = []
        inputDict[u'65536'] [u'quantity'].append(u'3')                    
        return inputDict
        
class TestBarnOwl(unittest.TestCase):    
    def test__filter_serial_by_product__(self):
        owl = BarnOwl()        
        dict = self._build_input_dict()
        serials = owl.__filter_serial_by_product__(dict[u'111'])        
        assert len(serials) == 3
        
    def testInStock(self):
        owl = BarnOwl()        
        dict = self._build_input_dict()
        inStockResult = owl.InStock(owl.purchase , dict)        
        assert len(inStockResult) == 2
        
    def testOutStock(self):
        pass
        
    def testStockCount(self):
        pass

    def _build_input_dict(self):
        inputDict  = {}
        inputDict[u'do_date'] = u'2011-06-22'
        inputDict[u'do_no'] = u'BC1655'
        inputDict[u'inv_no'] = u'BC1654'
        inputDict[u'salesMode'] = u'cash'
        inputDict[u'item'] = u'NK1280PPL'
        inputDict[u'mode'] = u'purchase'
        inputDict[u'supplier'] = u'Super-Link Station [M) Sdn Bhd'
        inputDict[u'_auth_user_id'] = 1
        
        
        """
        Supplier
        Customer
        Mode
        User
        DO_Date
        Invoice_NO
        DO_NO
        Status
        """
        inputDict[u'111'] = {}
        inputDict[u'111'] [u'serial-2'] = []
        inputDict[u'111'] [u'serial-2'].append(u'NK1280PPL003')
        inputDict[u'111'] [u'serial-1'] = []
        inputDict[u'111'] [u'serial-1'].append(u'NK1280PPL002')
        inputDict[u'111'] [u'serial-0'] = []
        inputDict[u'111'] [u'serial-0'].append(u'NK1280PPL001')    
        inputDict[u'111'] [u'cost'] = []
        inputDict[u'111'] [u'cost'].append(u'2000')    
        inputDict[u'111'] [u'quantity'] = []
        inputDict[u'111'] [u'quantity'].append(u'3')            
        
        inputDict[u'110'] = {}
        inputDict[u'110'] [u'serial-2'] = []
        inputDict[u'110'] [u'serial-2'].append(u'NK1280PPL003')
        inputDict[u'110'] [u'serial-1'] = []
        inputDict[u'110'] [u'serial-1'].append(u'NK1280PPL002')
        inputDict[u'110'] [u'serial-0'] = []
        inputDict[u'110'] [u'serial-0'].append(u'NK1280PPL001')    
        inputDict[u'110'] [u'cost'] = []
        inputDict[u'110'] [u'cost'].append(u'2000')    
        inputDict[u'110'] [u'quantity'] = []
        inputDict[u'110'] [u'quantity'].append(u'3')                    
        return inputDict
        
if __name__=="__main__":
    unittest.main()    
    