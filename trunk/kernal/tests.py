"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.utils import unittest
from pos.kernal.views import countInventory
from pos.kernal.models import InStockRecord, Profit

class post_kernal_views_countInventory_Test(unittest.TestCase):
    def setUp(self):
        self.inStockRecordSet = [] 
        self.inStockRecordSet.append(InStockRecord(barcode='65535', cost=15, quantity=10))
        self.inStockRecordSet.append(InStockRecord(barcode='65535', cost=15, quantity=10))
        self.inStockRecordSet.append(InStockRecord(barcode='65535', cost=15, quantity=10))
        self.profit = Profit(sell_index=15)

    def test_normal_usecase(self):
        self.assertEqual(countInventory(self.inStockRecordSet, self.profit), 15)

    def test_empty_paramter_usecase(self):
        self.assertEqual(countInventory(None, None), 0)
        
    def test_empty_sale_usecase(self):
        self.assertEqual(countInventory(self.inStockRecordSet, None), 30)

    def test_bound_sale_usecase(self):
        profit = Profit(sell_index=30)
        self.assertEqual(countInventory(self.inStockRecordSet, profit), 0)
        