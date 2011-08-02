from django.db import models
from django.forms import ModelForm
from django import forms
from django.forms.extras.widgets import SelectDateWidget
from django.contrib.admin.widgets import AdminDateWidget 
import datetime
from django.contrib.localflavor.us.models import PhoneNumberField
from django.contrib.auth.models import User
from django.contrib import admin
from django.core.files.storage import FileSystemStorage

CHOICES_ITEM = (
    ('Motorola', 'Motorola'),  
    ('Nokia', 'Nokia'),             
    ('Iphone', 'Iphone'),            
)

PAYMENT_STATUS = (
    ('Complete', 'Complete'),  
    ('Incomplete', 'Incomplete'),             
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
    barcode = models.CharField(max_length=100, blank=True)
    name = models.CharField("code",max_length=100)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category)
    brand = models.ForeignKey(Brand)
    type = models.ForeignKey(Type, null = True)
    retail_price = models.DecimalField(max_digits=100,  decimal_places=2)
    cost = models.DecimalField(max_digits=100,  decimal_places=2)
    uom = models.ForeignKey(UOM)
    active = models.BooleanField("actived product", True)
    
    def __unicode__(self):
        return self.name

class Company(models.Model):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    phone_office = models.CharField(max_length=100, blank=True)
    phone_mobile = models.CharField(max_length=100, blank=True)
    fax = models.CharField(max_length=100, blank=True)
    email = models.EmailField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    active = models.BooleanField(True)
    logo = models.ImageField(upload_to='static/images/upload/', max_length=100)
    create_at = models.DateTimeField(auto_now_add = True)    
        
class Supplier(models.Model):
    supplier_code = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    phone_office = models.CharField(max_length=100, blank=True)
    phone_mobile = models.CharField(max_length=100, blank=True)
    fax = models.CharField(max_length=100, blank=True)
    email = models.EmailField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    active = models.BooleanField(True)
    
    def __unicode__(self):
        return self.name

class SupplierAdmin(admin.ModelAdmin):
    list_display=('supplier_code','name', 'contact_person', 'phone_office', 'email', 'active')
    ordering = ['-supplier_code']
    list_per_page = 25
    search_fields = ['supplier_code', 'name', 'contact_person', 'phone_office', 'email']
            
class Customer(models.Model):
    customer_code = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=100, blank=True) 
    fax = models.CharField(max_length=100, blank=True) 
    email = models.EmailField(max_length=100, blank=True)
    term = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(True)

    def __unicode__(self):
        return self.name 

class CustomerAdmin(admin.ModelAdmin):
    list_display=('customer_code','name', 'contact_person', 'phone', 'email', 'active')
    ordering = ['-customer_code']
    list_per_page = 25
    search_fields = ['customer_code', 'name', 'contact_person', 'phone', 'email']
    
class InStockBatch(models.Model):
    supplier = models.ForeignKey(Supplier)
    do_date = models.DateField(auto_now_add = False)
    invoice_no = models.CharField(max_length=100)
    do_no = models.CharField(max_length=100)
    user = models.ForeignKey(User)
    mode = models.CharField(max_length=150) 
    status = models.CharField(max_length=150) 
    create_at = models.DateTimeField(auto_now_add = True)
    
class InStockRecord(models.Model):
    inStockBatch = models.ForeignKey(InStockBatch)
    barcode = models.CharField(max_length=100)
    product = models.ForeignKey(Product)    
    cost = models.DecimalField(max_digits=100,  decimal_places=2)
    quantity = models.DecimalField(max_digits=100,  decimal_places=0)
    create_at = models.DateTimeField(auto_now_add = True)
    type = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    
    def natural_key(self):
        return (self.product.name)    
        
    def __unicode__(self):
        return self.barcode + " " +str(self.cost) + " " + str(self.quantity)

class SerialNo(models.Model):
    inStockRecord = models.ForeignKey(InStockRecord)
    serial_no = models.CharField(max_length=100, primary_key=True)
    active = models.BooleanField("Is Saled", True)
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
        return str(self.create_at) + " " + str(self.active and  "Open" or "Close")         
        
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
    sales_by = models.ForeignKey(User, related_name="sales_by")
    issue_by = models.ForeignKey(User, related_name="issue_by")
    mode = models.CharField(max_length=100)
    def __unicode__(self):
        # return self.customer.name 
        return str(self.pk).zfill(6)

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
    type = models.CharField(max_length=100)
    create_at = models.DateTimeField(auto_now_add = True)

    def __unicode__(self):
        return "barcode: "+self.barcode + " index: " + str(self.sell_index) + " profit: " + str(self.profit)

class Payment(models.Model):
    bill = models.ForeignKey(Bill)
    term = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    status = models.CharField(max_length=100, choices=PAYMENT_STATUS)
    transaction_no = models.CharField(max_length=100, blank = True)
    create_at = models.DateTimeField(auto_now_add = True)

    def __unicode__(self):
        return str(self.bill) + " " + self.type + " " + self.status 

class DisableStock(models.Model):
    inStockRecord = models.ForeignKey(InStockRecord)
    outStockRecord = models.ForeignKey(OutStockRecord)
    type = models.CharField(max_length=100)    
    serialNo = models.ForeignKey(SerialNo, null = True)
    quantity = models.DecimalField(max_digits=100,  decimal_places=0)
    index = models.DecimalField(max_digits=100,  decimal_places=0)
    create_at = models.DateTimeField(auto_now_add = True)

class VoidBill(models.Model):
    bill = models.ForeignKey(Bill)
    reason = models.CharField(max_length=1500)    
    user = models.ForeignKey(User)
    create_at = models.DateTimeField(auto_now_add = True)
    
    
class ConsignmentInDetail(models.Model):
    inStockBatch = models.ForeignKey(InStockBatch)
    create_at = models.DateTimeField(auto_now_add = True)
    inStockRecord = models.ForeignKey(InStockRecord)
    serialNo = models.ForeignKey(SerialNo, null = True)
    quantity = models.DecimalField(max_digits=100,  decimal_places=0)
    balance = models.DecimalField(max_digits=100,  decimal_places=0)
    status = models.CharField(max_length=100)

class ConsignmentOutDetail(models.Model):
    payment = models.ForeignKey(Payment)
    create_at = models.DateTimeField(auto_now_add = True)
    outStockRecord = models.ForeignKey(OutStockRecord)
    serialNo = models.ForeignKey(SerialNo, null = True)
    quantity = models.DecimalField(max_digits=100,  decimal_places=0)
    balance = models.DecimalField(max_digits=100,  decimal_places=0)

class ProductForm(ModelForm):
    class Meta:
        model = Product
        exclude = ('active', 'category', 'brand' , 'type')
        
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
    do_date = forms.DateField(widget=AdminDateWidget)
    do_no = forms.CharField(max_length=150)
    inv_no = forms.CharField(max_length=150)
    
class VoidBillForm(ModelForm):        
    class Meta:
        model = VoidBill
        exclude = ('user','bill',)

class ConsignmentInBalanceForm(forms.Form):        
    supplier = forms.CharField(max_length=150)
    do_date = forms.DateField(widget=AdminDateWidget)
    
class ConsignmentOutStockBalanceForm(forms.Form):        
    customer = forms.CharField(max_length=150)
    do_date = forms.DateField(widget=AdminDateWidget)
    do_no = forms.CharField(max_length=150)
    inv_no = forms.CharField(max_length=150)    

class ReportFilterForm(forms.Form):
    start_date =  forms.DateField(widget=AdminDateWidget)
    end_date =  forms.DateField(widget=AdminDateWidget)    

class CounterAdmin(admin.ModelAdmin):
    list_display=('create_at', 'initail_amount', 'close_amount', 'active', 'user')
    exclude = ('close_amount','active','user',)
    initail_amount = models.DecimalField(max_digits=100,  decimal_places=2)
    close_amount = models.DecimalField(max_digits=100,  decimal_places=2, null=True)
    active = models.BooleanField("counter actived", True)
    user = models.ForeignKey(User)
    create_at = models.DateTimeField(auto_now_add = True)    
    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.close_amount = 0
        obj.active = True
        obj.save()    
    
class BillAdmin(admin.ModelAdmin):
    list_display=('customer', 'create_at', 'sales_by', 'total_price', 'counter')
    ordering = ['-create_at']
    list_per_page = 25
    search_fields = ['customer__name']
    date_hierarchy = 'create_at'

    def queryset(self, request):
        user = None
        if request.session.get('_auth_user_id'):
            user = User.objects.get(pk=request.session.get('_auth_user_id'))    
            if user.is_superuser:
                return Bill.objects.all()        
            
        return Bill.objects.filter(counter__active = True)
         
class PaymentAdmin(admin.ModelAdmin):
    list_display=('pk','bill','create_at', 'term', 'status')
    ordering = ['-create_at']
    list_per_page = 25
    search_fields = ['bill__customer__name', 'term', 'status']
    date_hierarchy = 'create_at'        
    
class ProductAdmin(admin.ModelAdmin):
    list_display=('barcode','name', 'description', 'category', 'brand')
    ordering = ['-name']
    list_per_page = 25
    search_fields = ['name', 'description', 'category__category_name', 'brand__brand_name']
    
    
