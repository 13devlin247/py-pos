from pos.kernal.models import Product, ProductForm 
from pos.kernal.models import Invoice
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

"""
Below function for ajax use
"""
#def ajaxProductDetailView(request):
   # if request.method == 'GET':

def ReportDaily(request):
    invoices = Invoice.objects.all()
    profitTable = {}
    
    for invoice in invoices:
        outStockRecords = OutStockRecord.objects.filter(invoice=invoice)
        total_proift = 0
        for outStockRecord in outStockRecords:
            total_proift = total_proift + outStockRecord.profit
        profitTable[invoice.pk] = total_proift
    return render_to_response('report_dailySales.html',{'invoices': invoices, 'profitTable':profitTable })
        
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
            if key == "po_no":
                continue
            barcode = key.split("_")[0]
            attr = key.split("_")[1]
            if barcode not in inventoryDict :
                inventoryDict [barcode] ={}
            inventoryDict [barcode] [attr]= value
        
        po_no = request.GET['po_no']
        inStockBatch = InStockBatch()
        
        # build OutStockRecord to save data
        for barcode in inventoryDict :
            inStockRecord = InStockRecord()
            inStockRecord.inStockBatch = inStockBatch
            inStockRecord.barcode = barcode
            inStockRecord.po_no = po_no
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
            barcode = key.split("_")[0]
            attr = key.split("_")[1]
            if barcode not in salesDict:
                salesDict[barcode] ={}
            salesDict[barcode] [attr]= value
        
        customerName = request.GET['customer']
        customer = Customer.objects.filter(name=customerName)[0]
        invoice = Invoice()
        invoice.total_price = request.GET['subTotal']
        invoice.tendered_amount = request.GET['amount_tendered']
        invoice.customer = customer
        invoice.fulfill_payment = False
        invoice.save()
        
        # build OutStockRecord to save data
        for barcode in salesDict:
            outStockRecord = OutStockRecord()
            outStockRecord.invoice = invoice
            outStockRecord.barcode = barcode
            outStockRecord.unit_sell_price = salesDict[barcode]['price'][0]
            outStockRecord.quantity = salesDict[barcode]['quantity'] [0]

            sales_index = 0
            #find last time sell record
            lastOutStockRecordSet = OutStockRecord.objects.filter(barcode=barcode)
            if lastOutStockRecordSet.count() != 0:
                lastOutStockRecord = lastOutStockRecordSet.order_by('-create_at')[0]
                sales_index = lastOutStockRecord.sell_index
            
            inStockObject = InStockRecord.objects.filter(barcode=barcode)[0]
            outStockRecord.profit = float(outStockRecord.unit_sell_price) - float(inStockObject.cost)
            sales_index = sales_index + int(outStockRecord.quantity) 
            outStockRecord.sell_index = sales_index
            
            outStockRecord.save()
        return HttpResponseRedirect('/sales/bill/'+str(invoice.pk))        

def QueryBill(request, invoiceID):    
    invoice = Invoice.objects.get(pk=invoiceID)
    outStockRecordset = OutStockRecord.objects.filter(invoice=invoice)
    return render_to_response('bill.html',{'invoice': invoice, 'outStockRecordset':outStockRecordset })
        
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
    messages.info(request, "check product: " + `barcode` + "  inventory")
   
    inStockRecordSet = InStockRecord.objects.filter(barcode=barcode)
    if inStockRecordSet.count() == 0:
        messages.debug(request, "inStockRecordSet not found")
        return HttpResponse(0, mimetype="application/json")    

    outStockRecordSet = OutStockRecord.objects.filter(barcode=barcode)
    
    if outStockRecordSet.count() != 0:
        outStockRecord = outStockRecordSet.order_by('-create_at')[0]
        if outStockRecord is None:
            messages.debug(request, "outStockRecord not found")        
        
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
                product.disable = True
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

