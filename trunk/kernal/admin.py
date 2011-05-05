from django.contrib import admin
from pos.kernal.models import Product, ProductForm
from pos.kernal.models import InStockRecord, InStockRecordForm
from pos.kernal.models import OutStockRecord, OutStockRecordForm
from pos.kernal.models import Bill, BillForm
from pos.kernal.models import Supplier, SupplierForm
from pos.kernal.models import Customer, CustomerForm
from pos.kernal.models import Category, CategoryForm
from pos.kernal.models import Brand, BrandForm
from pos.kernal.models import Type, TypeForm
from pos.kernal.models import UOM
from pos.kernal.models import InStockBatch
admin.site.register(Product)
admin.site.register(InStockRecord)
admin.site.register(InStockBatch)
admin.site.register(OutStockRecord)
admin.site.register(Bill)
admin.site.register(Supplier)
admin.site.register(Customer)
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Type)
admin.site.register(UOM)


