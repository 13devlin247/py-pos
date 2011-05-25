from django.db import models
from django.forms import ModelForm
from django import forms
from django.forms.extras.widgets import SelectDateWidget
from django.contrib.admin.widgets import AdminDateWidget 
import datetime
from django.contrib.localflavor.us.models import PhoneNumberField
from django.contrib.auth.models import User
from django.contrib import admin

CHOICES_ITEM = (
    ('Motorola', 'Motorola'),  
    ('Nokia', 'Nokia'),             
    ('Iphone', 'Iphone'),            
)

class Category(models.Model):
    category_name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.category_name
        
class Brand(models.Model):
    category = models.ForeignKey(Category)
    brand_name = models.CharField(max_length=100)
    
    def __unicode__(self):
        return self.brand_name

class Type(models.Model):
    brand = models.ForeignKey(Brand)
    type_name = models.CharField(max_length=100)
    
    def __unicode__(self):
        return self.type_name

class UOM(models.Model):        
    name = models.CharField(max_length=100) 

    def __unicode__(self):
        return self.name    

class Product(models.Model):
    barcode = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category)
    brand = models.ForeignKey(Brand)
    type = models.ForeignKey(Type)
    retail_price = models.DecimalField(max_digits=100,  decimal_places=2)
    cost = models.DecimalField(max_digits=100,  decimal_places=2)
    uom = models.ForeignKey(UOM)
    active = models.BooleanField("actived product", True)
    
    def __unicode__(self):
        return self.name
        
class Supplier(models.Model):
    supplier_code = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    phone_office = models.CharField(max_length=100, blank=True)
    phone_mobile = models.CharField(max_length=100, blank=True)
    fax = models.CharField(max_length=100, blank=True)
    email = models.EmailField(max_length=100, blank=True)
    #remark = models.TextField(blank=True)
    address = models.TextField(blank=True)
    active = models.BooleanField(True)
    
    def __unicode__(self):
        return self.name
        
class Customer(models.Model):
    customer_code = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    contact_person = models.CharField(max_length=100)
    phone = models.CharField(max_length=100, blank=True) 
    fax = models.CharField(max_length=100, blank=True) 
    email = models.EmailField(max_length=100, blank=True)
    term = models.CharField(max_length=100)
    active = models.BooleanField(True)

    def __unicode__(self):
        return self.name 
    
class InStockBatch(models.Model):
    supplier = models.ForeignKey(Supplier)
    do_date = models.DateField(auto_now_add = False)
    invoice_no = models.CharField(max_length=100)
    do_no = models.CharField(max_length=100)
    user = models.ForeignKey(User)
    create_at = models.DateTimeField(auto_now_add = True)
    
class InStockRecord(models.Model):
    inStockBatch = models.ForeignKey(InStockBatch)
    barcode = models.CharField(max_length=100)
    product = models.ForeignKey(Product)    
    cost = models.DecimalField(max_digits=100,  decimal_places=2)
    quantity = models.DecimalField(max_digits=100,  decimal_places=0)
    create_at = models.DateTimeField(auto_now_add = True)
    
    def natural_key(self):
        return (self.product.name)    
        
    def __unicode__(self):
        return self.barcode + " " +str(self.cost) + " " + str(self.quantity)

class SerialNo(models.Model):
    inStockRecord = models.ForeignKey(InStockRecord)
    serial_no = models.CharField(max_length=100, primary_key=True)
    create_at = models.DateTimeField(auto_now_add = True)
    
    def __unicode__(self):
        return str(self.inStockRecord.product.name) + " " +str(self.serial_no) 

class Counter(models.Model):
    initail_amount = models.DecimalField(max_digits=100,  decimal_places=2)
    close_amount = models.DecimalField(max_digits=100,  decimal_places=2, null=True)
    active = models.BooleanField("counter actived", True)
    user = models.ForeignKey(User)
    create_at = models.DateTimeField(auto_now_add = True)

    def __unicode__(self):
        return str(self.create_at) + " " + str(self.initail_amount) + " " + self.user.username         
        

class Bill(models.Model):
    subtotal_price = models.DecimalField(max_digits=100,  decimal_places=2)
    discount = models.DecimalField(max_digits=100,  decimal_places=2)
    total_price = models.DecimalField(max_digits=100,  decimal_places=2)
    tendered_amount = models.DecimalField(max_digits=100,  decimal_places=2)
    profit = models.DecimalField(max_digits=100,  decimal_places=2)
    change = models.DecimalField(max_digits=100,  decimal_places=2)
    customer = models.ForeignKey(Customer)
    create_at = models.DateTimeField(auto_now_add = True)
    counter = models.ForeignKey(Counter)
    user = models.ForeignKey(User)
    def __unicode__(self):
        return " $" + str(self.total_price) + " "+str(self.create_at) + " Cashier: " + self.user.username 

class Payment(models.Model):
    bill = models.ForeignKey(Bill)
    term = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    transaction_no = models.CharField(max_length=100, blank = True)
    create_at = models.DateTimeField(auto_now_add = True)

    def __unicode__(self):
        return str(self.bill) + " " + self.type + " " + self.status 
        
class OutStockRecord(models.Model):
    bill = models.ForeignKey(Bill)
    barcode = models.CharField(max_length=100)
    product = models.ForeignKey(Product) 
    unit_sell_price = models.DecimalField(max_digits=100,  decimal_places=2)
    cost = models.DecimalField(max_digits=100,  decimal_places=2)
    quantity = models.DecimalField(max_digits=100,  decimal_places=0)
    amount = models.DecimalField(max_digits=100,  decimal_places=2) 
    sell_index = models.IntegerField(blank=True)
    serial_no = models.ForeignKey(SerialNo, blank=True,  null=True)
    profit = models.DecimalField(max_digits=100,  decimal_places=2, blank=True)
    create_at = models.DateTimeField(auto_now_add = True)

    def __unicode__(self):
        return "barcode: "+self.barcode + " index: " + str(self.sell_index) + " profit: " + str(self.profit)

class ProductForm(ModelForm):
    class Meta:
        model = Product
        exclude = ('active', )
        
class InStockRecordForm(ModelForm):
    class Meta:
        model = InStockRecord

class OutStockRecordForm(ModelForm):
    class Meta:
        model = OutStockRecord

class BillForm(ModelForm):
    class Meta:
        model = Bill

class SupplierForm(ModelForm):
    class Meta:
        model = Supplier

class CustomerForm(ModelForm):
    class Meta:
        model = Customer

        
class CategoryForm(ModelForm):
    class Meta:
        model = Category        

class BrandForm(ModelForm):
    class Meta:
        model = Brand

class TypeForm(ModelForm):
    class Meta:
        model = Type
        
class InStockBatchForm(forms.Form):        
    supplier = forms.CharField(max_length=150)
    do_date =  forms.DateField(widget=AdminDateWidget)
    do_no =  forms.CharField(max_length=150)
    inv_no =  forms.CharField(max_length=150)

class ReportFilterForm(forms.Form):
    start_date =  forms.DateField(widget=AdminDateWidget)
    end_date =  forms.DateField(widget=AdminDateWidget)    


