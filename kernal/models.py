from django.db import models
from django.forms import ModelForm

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


class Product(models.Model):
    barcode = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=100,  choices=CHOICES_ITEM)
    category = models.CharField(max_length=100,  choices=CHOICES_ITEM)
    type = models.CharField(max_length=100,  choices=CHOICES_ITEM)
    cost = models.DecimalField(max_digits=100,  decimal_places=2)
    price = models.DecimalField(max_digits=100,  decimal_places=2)
    disable = models.BooleanField(False)
    
    def __unicode__(self):
        return self.name
        
class Supplier(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=500, blank=True)
    email = models.EmailField(max_length=100, blank=True)
    phone = models.CharField(max_length=100, blank=True)
        
    def __unicode__(self):
        return self.name + " phone: "+ self.phone
        
class Customer(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=500, blank=True)
    email = models.EmailField(max_length=100, blank=True)
    phone = models.CharField(max_length=100, blank=True)
 
    def __unicode__(self):
        return self.name 
    
class InStockBatch(models.Model):
    supplier = models.ForeignKey(Supplier)
    do_date = models.DateTimeField(auto_now_add = False)
    invoice_no = models.CharField(max_length=100)
    do_no = models.CharField(max_length=100)
    create_at = models.DateTimeField(auto_now_add = True)
        
        
class InStockRecord(models.Model):
    po_no = models.CharField(max_length=100)
    barcode = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=100,  decimal_places=2)
    quantity = models.DecimalField(max_digits=100,  decimal_places=0)
    create_at = models.DateTimeField(auto_now_add = True)
    
    def __unicode__(self):
        return self.barcode + " " +str(self.cost) + " " + str(self.quantity)
        
class Invoice(models.Model):
    total_price = models.DecimalField(max_digits=100,  decimal_places=2)
    tendered_amount = models.DecimalField(max_digits=100,  decimal_places=2)
    fulfill_payment = models.BooleanField(False)
    customer = models.ForeignKey(Customer)
    create_at = models.DateTimeField(auto_now_add = True)
    def __unicode__(self):
        return " $" + str(self.total_price) + " "+str(self.create_at) 
        
class OutStockRecord(models.Model):
    invoice = models.ForeignKey(Invoice)
    barcode = models.CharField(max_length=100)
    unit_sell_price = models.DecimalField(max_digits=100,  decimal_places=2)
    quantity = models.DecimalField(max_digits=100,  decimal_places=0)
    sell_index = models.IntegerField()
    profit = models.DecimalField(max_digits=100,  decimal_places=2)
    create_at = models.DateTimeField(auto_now_add = True)

    def __unicode__(self):
        return "barcode: "+self.barcode + " index: " + str(self.sell_index) + " profit: " + str(self.profit)

class ProductForm(ModelForm):
    class Meta:
        model = Product
        exclude = ('disable', )
        
class InStockRecordForm(ModelForm):
    class Meta:
        model = InStockRecord

class OutStockRecordForm(ModelForm):
    class Meta:
        model = OutStockRecord

class InvoiceForm(ModelForm):
    class Meta:
        model = Invoice

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