from django.contrib import admin
from pos.kernal.models import Product,  InStockRecord, OutStockRecord, Profit, ProductForm, InStockRecordForm, OutStockRecordForm, ProfitForm

admin.site.register(Product)
admin.site.register(InStockRecord)
admin.site.register(OutStockRecord)
admin.site.register(Profit)

