# -*- coding:utf-8 -*-
import os, sys
p1 = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
p2 = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(p1)
sys.path.append(p2)
sys.stdout = sys.stderr
os.environ['DJANGO_SETTINGS_MODULE'] = 'pos.settings' 


import unittest
import django
from store import ProductBuilder
from store import StockKeeper
from pos.kernal.models import Product
# import the logging library
import logging

logging.basicConfig(
    level = logging.WARN,
    format = '%(asctime)s %(levelname)s %(funcName)s():%(lineno)s %(message)s',
)
# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestProductBuilder(unittest.TestCase):
    def testBuild(self):
        productMeta = [(u'10_quantity', [u'2']), (u'10_serial-1', [u'3']), (u'do_date', [u'2011-06-19']), (u'7_serial-0', [u'1']), (u'10_serial-0', [u'2']), (u'7_quantity', [u'1']), (u'do_no', [u'1']), (u'inv_no', [u'2']), (u'item', [u'CNB98WHTMALAY']), (u'7_cost', [u'1']), (u'mode', [u'receive']), (u'10_cost', [u'2']), (u'supplier', [u'Super-Link Station (M) Sdn Bhd'])]
        builder = ProductBuilder()
        products = builder.build(productMeta)
        assert len(products) == 2

class TestStockKeeper(unittest.TestCase):
    def testSingleTon(self):
        product = Product()
        keeperA = StockKeeper(product)
        keeperB = StockKeeper(product)
        assert keeperA == keeperB

    def setUp(self):
        product = Product()
        self.keeper = StockKeeper(product)
        pass
    
    def testInstock(self):
        k = self.keeper
        k.instock()

        
if __name__=="__main__":
    unittest.main()