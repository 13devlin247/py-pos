from pos.kernal.models import Product, ProductForm 
from pos.kernal.models import Bill
from pos.kernal.models import InStockBatch, InStockRecord, InStockRecordForm
from pos.kernal.models import OutStockRecord, OutStockRecordForm
from pos.kernal.models import Supplier, SupplierForm
from pos.kernal.models import Customer, CustomerForm 
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.views.generic import list_detail, date_based, create_update
from django.contrib import messages
from django.core import serializers
from django.db.models import Count
from datetime import date

# import the logging library
import logging

logging.basicConfig(
    level = logging.DEBUG,
    format = '%(asctime)s %(levelname)s %(message)s',
)
# Get an instance of a logger
logger = logging.getLogger(__name__)

"""
Below function for ajax use
"""
#def ajaxProductDetailView(request):
   # if request.method == 'GET':

def ReportDaily(request):
    bills = Bill.objects.all()
    profitTable = {}
    
    for bill in bills:
        outStockRecords = OutStockRecord.objects.filter(bill=bill)
        total_proift = 0
        for outStockRecord in outStockRecords:
            total_proift = total_proift + outStockRecord.profit
        profitTable[bill.pk] = total_proift
    return render_to_response('report_dailySales.html',{'bills': bills, 'profitTable':profitTable })
        
def printData(request):
    txt = ""
    salesDict = {}
    if request.method == 'GET':
        # process Request parameter
        sales_item = request.GET.lists()
        for key,  value in sales_item:
            if key == "amount_tendered":
                continue
            if key == "subTotal":
                continue            
            barcode = key.split("_")[0]
            attr = key.split("_")[1]
            if barcode not in salesDict:
                salesDict[barcode] ={}
            salesDict[barcode] [attr]= value
        
       
        # build OutStockRecord to save data
        for barcode in salesDict:
            sales_index = 0
            #find last time sell record
            lastOutStockRecordSet = OutStockRecord.objects.filter(barcode=barcode)
            if lastOutStockRecordSet.count() != 0:
                lastOutStockRecord = lastOutStockRecordSet.order_by('-create_at')[0]
                sales_index = lastOutStockRecord.sell_index
            
            
        return HttpResponse("sales index: "+str(sales_index)+" , outStockRecord.quantity: " + salesDict[barcode]['quantity'] [0] + ", new saleIndex: " + str((sales_index+int(salesDict[barcode]['quantity'] [0]))), mimetype="text/plain")     

def InventoryConfirm(request):
    inventoryDict = {}
    if request.method == 'GET':
        # process Request parameter
        
        sales_item = request.GET.lists()
        
        for key,  value in sales_item:
            if key == "do_no":
                continue
            if key == "inv_no":
                continue            
            if key == "do_date":
                continue
            if key == "supplier":
                continue                
            if key.find("_") == -1:
                continue
            barcode = key.split("_")[0]
            attr = key.split("_")[1]
            logger.error('barcode: ' + key)
            if barcode not in inventoryDict :
                inventoryDict [barcode] ={}
            inventoryDict [barcode] [attr]= value
        supplier_name = request.GET.get('supplier', "")
        supplier = None
        try:
            supplier = Supplier.objects.filter(name=supplier_name)[0:1].get()
        except Supplier.DoesNotExist:
            supplier = None # supplier not found
            
        inStockBatch = InStockBatch()
        inStockBatch.supplier = supplier
        today = date.today()
        inStockBatch.do_date = request.GET.get('do_date', today.strftime("%d/%m/%y"))
        inStockBatch.invoice_no = request.GET.get('inv_no', "-")
        inStockBatch.do_no = request.GET.get('do_no', "-")
        inStockBatch.save();
        
        # build OutStockRecord to save data
        for barcode in inventoryDict :
            inStockRecord = InStockRecord()
            inStockRecord.inStockBatch = inStockBatch
            inStockRecord.barcode = barcode
            product = Product.objects.filter(barcode=barcode)[0]
            inStockRecord.product = product
            inStockRecord.cost = inventoryDict [barcode]['cost'][0]
            inStockRecord.quantity = inventoryDict [barcode]['quantity'] [0]
            inStockRecord.save()
        return HttpResponseRedirect('/inventory/result/')

def SalesConfirm(request):
    salesDict = {}
    if request.method == 'GET':
        # process Request parameter
        sales_item = request.GET.lists()
        for key,  value in sales_item:
            if key == "amount_tendered":
                continue
            if key == "subTotal":
                continue            
            if key == "customer":
                continue                  
            if key == "discount":
                continue            
            if key == "total":
                continue              
            if key == "change":
                continue                        
            barcode = key.split("_")[0]
            attr = key.split("_")[1]
            if barcode not in salesDict:
                salesDict[barcode] ={}
            salesDict[barcode] [attr]= value
        
        customerName = request.GET.get('customer', 'Cash')
        customer = Customer.objects.filter(name=customerName)[0]
        bill = Bill()
        bill.subtotal_price = request.GET.get('subTotal', '0')
        bill.discount = request.GET.get('discount', '0')
        bill.total_price = request.GET.get('total', '0')
        bill.tendered_amount = request.GET.get('amount_tendered', '0')
        bill.change = request.GET.get('change', '0')
        bill.customer = customer
        bill.fulfill_payment = False
        bill.save()
        
        # build OutStockRecord to save data
        for barcode in salesDict:
            outStockRecord = OutStockRecord()
            outStockRecord.bill = bill
            outStockRecord.barcode = barcode
            product = Product.objects.filter(barcode=barcode)[0]
            outStockRecord.product = product            
            
            outStockRecord.unit_sell_price = salesDict[barcode]['price'][0]
            outStockRecord.quantity = salesDict[barcode]['quantity'] [0]
            outStockRecord.amount = str(float(salesDict[barcode]['price'][0]) * float(salesDict[barcode]['quantity'] [0])) 
            sales_index = 0
            #find last time sell record
            lastOutStockRecordSet = OutStockRecord.objects.filter(barcode=barcode)
            if lastOutStockRecordSet.count() != 0:
                lastOutStockRecord = lastOutStockRecordSet.order_by('-create_at')[0]
                sales_index = lastOutStockRecord.sell_index
            
            inStockRecordSet = InStockRecord.objects.filter(barcode=barcode)
            inStockObject = None
            if inStockRecordSet.count() != 0:
                inStockObject = InStockRecord.objects.filter(barcode=barcode)[0]
            if inStockObject:
                outStockRecord.profit = str(float(outStockRecord.unit_sell_price) - float(inStockObject.cost)) # str() for convert to decimal prepare
                sales_index = sales_index + int(outStockRecord.quantity) 
            else:
                outStockRecord.profit = '0.0'
            
            outStockRecord.sell_index = sales_index
            outStockRecord.save()
        return HttpResponseRedirect('/sales/bill/'+str(bill.pk))        

def QueryBill(request, billID):    
    bill = Bill.objects.get(pk=billID)
    outStockRecordset = OutStockRecord.objects.filter(bill=bill)
    return render_to_response('bill.html',{'bill': bill, 'outStockRecordset':outStockRecordset })
        
def ProductInfo(request, barcode):
    messages.info(request, "check product: " + `barcode` + " info")
   
    productSet = Product.objects.filter(barcode=barcode)
    if not productSet:
        return HttpResponse("[{\"error\":true}]", mimetype="text/plain")    
    json = serializers.serialize("json",  productSet)
    #json =                                                                               "[{\"inventoryCount\":"+str(inventoryCount)+"}]"
    return HttpResponse(json, mimetype="application/json")
    
def ProductInventory(request, barcode):
    outStockRecord = None
    logging.info(request, "check product: " + `barcode` + "  inventory")
   
    inStockRecordSet = InStockRecord.objects.filter(barcode=barcode)
    if inStockRecordSet.count() == 0:
        logging.debug(request, "inStockRecordSet not found")
        return HttpResponse(0, mimetype="application/json")    

    outStockRecordSet = OutStockRecord.objects.filter(barcode=barcode)
    
    if outStockRecordSet.count() != 0:
        outStockRecord = outStockRecordSet.order_by('-create_at')[0]
        if outStockRecord is None:
            logging.debug(request, "outStockRecord not found")        
        
    inventoryCount = countInventory(inStockRecordSet, outStockRecord)
    json = "[{\"inventory\":"+str(inventoryCount)+"}]"
    return HttpResponse(json, mimetype="application/json")    

""" 
below function for save form object to databases
"""
def CustomerSave(request, customerID=None):
    customer = None
    if customerID is not None:
        customer = Customer.objects.get(pk=customerID)
    if request.method == 'GET':
        form = CustomerForm(request.GET, instance=customer)
            
        if form.is_valid():
            customer = form.save(commit = True)
            customer.save()
            return HttpResponseRedirect('/customer/search/')
        else:
            return HttpResponseRedirect('/customer/create/')
            
def SupplierSave(request, supplierID=None):
    supplier = None
    if supplierID is not None:
        supplier = Supplier.objects.get(pk=supplierID)
    if request.method == 'GET':
        form = SupplierForm(request.GET, instance=supplier)
            
        if form.is_valid():
            supplier = form.save(commit = True)
            supplier.save()
            return HttpResponseRedirect('/supplier/search/')
        else:
            return HttpResponseRedirect('/supplier/create/')


def ProductSave(request, productID=None):
    product = None
    if productID is not None:
        product = Product.objects.get(pk=productID)
    if request.method == 'GET':
        form = ProductForm(request.GET, instance=product)
            
        if form.is_valid():
            product = form.save(commit = True)
            product.save()
            return HttpResponseRedirect('/product/search/')
        else:
            return HttpResponseRedirect('/product/create/')

def ProductUpdateView(request, productID):
    product = Product.objects.get(pk=productID)
    form = ProductForm(instance=product)
    return render_to_response('product_form.html',{'form': form, 'submit_form':'/product/save/'+productID, 'form_title': 'Update Product'})


def ProductDelete(request):
    if request.method == 'GET':
        delete_products = request.GET.getlist('delete_product[]')
    
        for barcode in delete_products:
            products = Product.objects.filter(barcode=barcode)
            for product in products:
                product.active = False
                product.save()
    return HttpResponseRedirect('/product/search/')        


def InStockRecordSave(request):
    if request.method == 'GET':
        form = InStockRecordForm(request.GET)
        if form.is_valid():
            inStockRecord = form.save(commit = True)
            inStockRecord.save()
            return HttpResponseRedirect('/in_stock_record/search/')
        else:
            return HttpResponseRedirect('/in_stock_record/create/')


def OutStockRecordSave(request):
    if request.method == 'GET':
        form = OutStockRecordForm(request.GET)
        if form.is_valid():
            outStockRecord = form.save(commit = True)
            outStockRecord.save()
            return HttpResponseRedirect('/out_stock_record/search/')
        else:
            return HttpResponseRedirect('/out_stock_record/create/')

def countInventory(inStockRecordSet, outStockRecord):
    count = 0;
    sellCount = 0
    if inStockRecordSet is None:
        messages.info(request,"")
        return 0;
        
    if outStockRecord is not None:
        sellCount = outStockRecord.sell_index
        
    for inStockRecord in inStockRecordSet:
        count = count + inStockRecord.quantity
    count = count - sellCount
    return count

