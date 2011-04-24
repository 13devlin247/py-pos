from django.db import models
from django.forms import ModelForm

CHOICES_ITEM = (
    ('Motorola', 'Motorola'),  
    ('Nokia', 'Nokia'),             
    ('Iphone', 'Iphone'),            
)

class Product(models.Model):
    barcode = models.CharField(max_length=100)
    barcode = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=100,  choices=CHOICES_ITEM)
    category = models.CharField(max_length=100,  choices=CHOICES_ITEM)
    type = models.CharField(max_length=100,  choices=CHOICES_ITEM)
    disable = models.BooleanField(False)
    
    def __unicode__(self):
        return self.name
        
class InStockRecord(models.Model):
    barcode = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=100,  decimal_places=2)
    quantity = models.DecimalField(max_digits=100,  decimal_places=0)
    create_at = models.DateTimeField(auto_now_add = True)

class OutStockRecord(models.Model):
    barcode = models.CharField(max_length=100)
    unit_sell_price = models.DecimalField(max_digits=100,  decimal_places=2)
    quantity = models.DecimalField(max_digits=100,  decimal_places=0)
    create_at = models.DateTimeField(auto_now_add = True)

class Profit(models.Model):
    out_stock_record = models.OneToOneField(OutStockRecord)
    sell_index = models.IntegerField()
    profit = models.DecimalField(max_digits=100,  decimal_places=2)
    create_at = models.DateTimeField(auto_now_add = True)
    
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

class ProfitForm(ModelForm):
    class Meta:
        model = Profit
        

