"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.utils import unittest
from pos.kernal.views import countInventory
from pos.kernal.models import InStockRecord, OutStockRecord
from pos.kernal.models import Product
from pos.kernal.models import Category
from pos.kernal.models import Brand
from pos.kernal.models import Type
from pos.kernal.models import UOM

from django.core import serializers
class post_kernal_views_countInventory_Test(unittest.TestCase):
    def setUp(self):
        self.inStockRecordSet = [] 
        self.inStockRecordSet.append(InStockRecord(barcode='65535', cost=15, quantity=10))
        self.inStockRecordSet.append(InStockRecord(barcode='65535', cost=15, quantity=10))
        self.inStockRecordSet.append(InStockRecord(barcode='65535', cost=15, quantity=10))
        self.outStockRecord = OutStockRecord(sell_index=15)
        
    def test_normal_usecase(self):
        self.assertEqual(countInventory(self.inStockRecordSet, self.outStockRecord), 15)

    def test_empty_paramter_usecase(self):
        self.assertEqual(countInventory(None, None), 0)
        
    def test_empty_sale_usecase(self):
        self.assertEqual(countInventory(self.inStockRecordSet, None), 30)

    def test_bound_sale_usecase(self):
        outStockRecord = OutStockRecord(sell_index=30)
        self.assertEqual(countInventory(self.inStockRecordSet, outStockRecord), 0)

class post_kernal_find_SalesIdx_(unittest.TestCase):
    def setUp(self):
        c = Category()
        c.category_name = 'testCategory'
        c.save()
        
        b = Brand()
        b.category = c
        b.brand_name = 'testBrand'
        b.save()
        
        t = Type()
        t.brand = b
        t.type_name = 'testType'
        t.save()

        u = UOM()
        u.name = 'unit'
        u.save() 
        
        self.product = Product()
        self.product.pk = 99999
        self.product.barcode = "test123"
        self.product.name = "test123"
        self.product.description = "test123"
        self.product.category = c
        self.product.brand = b
        self.product.type = t
        self.product.retail_price = 150
        self.product.cost = 100
        self.product.uom = u
        self.product.active = True
        self.product.save()
        print("Mock Product saved!")
        
           
        inStockRecord = InStockRecord()
        inStockRecord
        
        self.inStockRecordSet = [] 
        self.inStockRecordSet.append(InStockRecord(barcode='65535', cost=15, quantity=10))
        self.inStockRecordSet.append(InStockRecord(barcode='65535', cost=15, quantity=10))
        self.inStockRecordSet.append(InStockRecord(barcode='65535', cost=15, quantity=10))
        self.outStockRecord = OutStockRecord(sell_index=15)
        
    def test_serializer(self):
        data = serializers.serialize("json",  self.inStockRecordSet)
        self.assertEqual(data, 0)
