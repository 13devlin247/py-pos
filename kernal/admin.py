from django.contrib import admin
from pos.kernal.models import Product,  InStockRecord, OutStockRecord, Invoice,  ProductForm, InStockRecordForm, OutStockRecordForm,  InvoiceForm

admin.site.register(Product)
admin.site.register(InStockRecord)
admin.site.register(OutStockRecord)
admin.site.register(Invoice)


