from django.contrib import admin
from pos.kernal.models import Product, ProductAdmin
from pos.kernal.models import InStockRecord, InStockRecordForm
from pos.kernal.models import OutStockRecord, OutStockRecordForm
from pos.kernal.models import Bill, BillForm, BillAdmin
from pos.kernal.models import Payment, PaymentAdmin
from pos.kernal.models import Supplier, SupplierAdmin
from pos.kernal.models import Customer, CustomerAdmin
from pos.kernal.models import Category, CategoryForm
from pos.kernal.models import Brand, BrandForm
from pos.kernal.models import UOM
from pos.kernal.models import InStockBatch
from pos.kernal.models import SerialNo
from pos.kernal.models import Category
from pos.kernal.models import Brand
from pos.kernal.models import Type, TypeForm
from pos.kernal.models import Counter
from pos.kernal.models import CounterAdmin
from pos.kernal.models import Company
from pos.kernal.models import Algo
from pos.kernal.models import Deposit

admin.site.register(Product, ProductAdmin)
admin.site.register(InStockRecord)
admin.site.register(InStockBatch)
admin.site.register(OutStockRecord)
admin.site.register(Bill, BillAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(UOM)
admin.site.register(SerialNo)
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Type)
admin.site.register(Counter, CounterAdmin)
admin.site.register(Company)
admin.site.register(Algo)
admin.site.register(Deposit)


