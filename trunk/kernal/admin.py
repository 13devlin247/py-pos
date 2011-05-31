from django.contrib import admin
from pos.kernal.models import Product, ProductForm
from pos.kernal.models import InStockRecord, InStockRecordForm
from pos.kernal.models import OutStockRecord, OutStockRecordForm
from pos.kernal.models import Bill, BillForm, BillAdmin
from pos.kernal.models import Payment, PaymentAdmin
from pos.kernal.models import Supplier, SupplierForm
from pos.kernal.models import Customer, CustomerForm
from pos.kernal.models import Category, CategoryForm
from pos.kernal.models import Brand, BrandForm
from pos.kernal.models import UOM
from pos.kernal.models import InStockBatch
from pos.kernal.models import SerialNo
from pos.kernal.models import Category
from pos.kernal.models import Brand
from pos.kernal.models import Type, TypeForm
from pos.kernal.models import Counter
from pos.kernal.models import Company

admin.site.register(Product)
admin.site.register(InStockRecord)
admin.site.register(InStockBatch)
admin.site.register(OutStockRecord)
admin.site.register(Bill, BillAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Supplier)
admin.site.register(Customer)
admin.site.register(UOM)
admin.site.register(SerialNo)
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Type)
admin.site.register(Counter)
admin.site.register(Company)

