from pos.kernal.models import Product, ProductForm 
from pos.kernal.models import Bill
from pos.kernal.models import InStockBatch, InStockRecord, InStockRecordForm
from pos.kernal.models import OutStockRecord, OutStockRecordForm
from pos.kernal.models import Supplier, SupplierForm
from pos.kernal.models import Customer, CustomerForm
from pos.kernal.models import Payment 
from pos.kernal.models import SerialNo
from pos.kernal.models import Counter
from pos.kernal.models import Company
from pos.kernal.models import Category
from pos.kernal.models import Brand
from pos.kernal.models import Type
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.views.generic import list_detail, date_based, create_update
from django.contrib import messages
from django.core import serializers
from django.db.models import Count
from datetime import date
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import permission_required
from datetime import date
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# import the logging library
import logging

logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s %(levelname)s %(message)s',
)
# Get an instance of a logger
logger = logging.getLogger(__name__)

"""
Below function for ajax use
"""
#def ajaxProductDetailView(request):
   # if request.method == 'GET':



def InventoryReturnReport(request):
    startDate = request.GET.get('start_date','')
    endDate = request.GET.get('end_date','')
    if startDate == '' or endDate == '':
        startDate = str(date.min)
        endDate = str(date.max)
    startDate = startDate+" 00:00:00"
    endDate = endDate+" 23:59:59"
    inStockBatchs = InStockBatch.objects.filter(mode='return').filter(create_at__range=(startDate,endDate)).order_by('-create_at')
    return render_to_response('inventory_return_list.html',{'inStockBatchs': inStockBatchs, 'dateRange': str(startDate)+" to "+str(endDate)}, )
   
   
def SalesReturnReport(request):
    startDate = request.GET.get('start_date','')
    endDate = request.GET.get('end_date','')
    if startDate == '' or endDate == '':
        startDate = str(date.min)
        endDate = str(date.max)
    startDate = startDate+" 00:00:00"
    endDate = endDate+" 23:59:59"
    bills = Bill.objects.filter(mode='return').filter(create_at__range=(startDate,endDate)).order_by('-create_at')
    return render_to_response('sales_return_list.html',{'bills': bills, 'dateRange': str(startDate)+" to "+str(endDate)}, )
   
def CashSalesReport(request):
    startDate = request.GET.get('start_date','')
    endDate = request.GET.get('end_date','')
    if startDate == '' or endDate == '':
        startDate = str(date.min)
        endDate = str(date.max)
    startDate = startDate+" 00:00:00"
    endDate = endDate+" 23:59:59"
    payments = Payment.objects.all().filter(create_at__range=(startDate,endDate)).filter(type='Cash Sales').order_by('-create_at')
    return render_to_response('cash_sales_list.html',{'payments': payments, 'dateRange': str(startDate)+" to "+str(endDate)}, )

   
def InvoiceReport(request):
    startDate = request.GET.get('start_date','')
    endDate = request.GET.get('end_date','')
    if startDate == '' or endDate == '':
        startDate = str(date.min)
        endDate = str(date.max)
    startDate = startDate+" 00:00:00"
    endDate = endDate+" 23:59:59"
    payments = Payment.objects.all().filter(create_at__range=(startDate,endDate)).filter(type='Invoice').order_by('-create_at')
    return render_to_response('do_list.html',{'payments': payments, 'dateRange': str(startDate)+" to "+str(endDate)}, )
           
   
def ReportDaily(request):
    startDate = request.GET.get('start_date','')
    endDate = request.GET.get('end_date','')
    if startDate == '' or endDate == '':
        startDate = str(date.min)
        endDate = str(date.max)
    startDate = startDate+" 00:00:00"
    endDate = endDate+" 23:59:59"

    bills = Bill.objects.all().filter(create_at__range=(startDate,endDate))
    profitTable = {}
    
    for bill in bills:
        outStockRecords = OutStockRecord.objects.filter(bill=bill)
        total_proift = 0
        for outStockRecord in outStockRecords:
            total_proift = total_proift + outStockRecord.profit
        profitTable[bill.pk] = total_proift
    return render_to_response('report_dailySales.html',{'bills': bills, 'profitTable':profitTable, 'dateRange': str(startDate)+" to "+str(endDate)}, )
        
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
            pk = key.split("_")[0]
            attr = key.split("_")[1]
            if pk not in inventoryDict :
                inventoryDict [pk] ={}
            inventoryDict [pk] [attr]= value
        supplier_name = request.GET.get('supplier', "")
        supplier = None
        try:
            supplier = Supplier.objects.filter(name=supplier_name)[0:1].get()
        except Supplier.DoesNotExist:
            supplier = None # supplier not found
        
        mode = request.GET.get('mode', 'receive')
        
        inStockBatch = InStockBatch()
        inStockBatch.mode = mode
        inStockBatch.supplier = supplier
        inStockBatch.user = User.objects.get(pk=request.session.get('_auth_user_id'))
        today = date.today()
        inStockBatch.do_date = request.GET.get('do_date', today.strftime("%d/%m/%y"))
        inStockBatch.invoice_no = request.GET.get('inv_no', "-")
        inStockBatch.do_no = request.GET.get('do_no', "-")
        inStockBatch.save();
        
        # build OutStockRecord to save data
        for pk in inventoryDict :
            inStockRecord = InStockRecord()
            inStockRecord.inStockBatch = inStockBatch
            inStockRecord.barcode = pk
            product = Product.objects.get(pk=pk)
            inStockRecord.product = product
            inStockRecord.cost = inventoryDict [pk]['cost'][0]
            inStockRecord.quantity = inventoryDict [pk]['quantity'] [0]
            inStockRecord.save()
            for value in inventoryDict[pk] :
                if 'serial-' in value:
                    serialNO = request.GET.get(pk+"_"+value, '') 
                    if serialNO == '':
                        continue
                    serial = SerialNo()
                    serial.inStockRecord = inStockRecord
                    serial.serial_no = serialNO
                    serial.save()            
        return HttpResponseRedirect('/inventory/result/'+str(inStockBatch.pk))

def SalesConfirm(request):
    salesDict = {}
    if request.method == 'GET':
        # check Counter 
        counter = None
        counter = Counter.objects.filter(active=True).order_by('-create_at')
        if counter.count() == 0:
            return HttpResponseRedirect('/admin/kernal/counter/add/')    
            
        # process Request parameter
        sales_item = request.GET.lists()
        for key,  value in sales_item:
            if '_' not in key:
                continue

            barcode = key.split("_")[0]
            attr = key.split("_")[1]
            if barcode not in salesDict:
                salesDict[barcode] ={}
            salesDict[barcode] [attr]= value
        
        customerName = request.GET.get('customer', 'Cash')
        customer = Customer.objects.filter(name=customerName)[0]
        mode = request.GET.get('mode', 'sale')
        bill = Bill()
        bill.mode = mode
        bill.subtotal_price = request.GET.get('subTotal', '0')
        bill.discount = request.GET.get('discount', '0')
        bill.total_price = request.GET.get('total', '0')
        bill.tendered_amount = request.GET.get('amountTendered', '0')
        bill.change = request.GET.get('change', '0')
        bill.customer = customer
        bill.profit = 0
        bill.counter = counter[0]
        bill.user = User.objects.get(pk=request.session.get('_auth_user_id'))
        bill.fulfill_payment = False
        bill.save()
        
        payment = Payment()
        payment.bill = bill
        salesMode = request.GET.get('salesMode', '')
        if salesMode == 'cash':
            payment.term = "Cash"
            payment.type = "Cash Sales"
            payment.status = "Complete"
        else:
            payment.term = customer.term
            payment.type = "Invoice"
            payment.status = "Incomplete"        
            
        transactionNo = request.GET.get('transactionNo', '')
        if transactionNo != '': 
            logging.info("paid by creadit card")
            payment.term = "CreaditCard"
            payment.transaction_no = transactionNo
        payment.save()
        
        # build OutStockRecord to save data
        for barcode in salesDict:
            outStockRecord = OutStockRecord()
            outStockRecord.bill = bill
            outStockRecord.barcode = barcode
            logging.info("looking for pk : %s " % barcode)
            if "-foc-product" in barcode:
                logging.info("Foc product found !! : %s " % barcode)    
                
            try:
                imei = request.GET.get(barcode+'_imei', 'None')
                serial_no = SerialNo.objects.get(serial_no = imei)
                outStockRecord.serial_no = serial_no
                product = serial_no.inStockRecord.product
                outStockRecord.product = product            
                
                logging.info("product found by imei : %s " % barcode)
            except SerialNo.DoesNotExist:
                product = Product.objects.get(pk=barcode)
                outStockRecord.product = product            
                logging.info("no imei no. found ")
                logging.info("product found by pk : %s " % barcode)
                
            outStockRecord.unit_sell_price = salesDict[barcode]['price'][0]
            outStockRecord.quantity = salesDict[barcode]['quantity'] [0]
            outStockRecord.amount = str(float(salesDict[barcode]['price'][0]) * float(salesDict[barcode]['quantity'] [0])) 
            outStockRecord.sell_index = 0;
            outStockRecord.profit = 0;
            outStockRecord.cost = -1;
            outStockRecord.save()
        return HttpResponseRedirect('/sales/bill/'+str(bill.pk))        
        
def QueryBill(request, displayPage, billID):    
    list_per_page = 25
    if displayPage == 'bill':
        list_per_page = 10
        
    bill = Bill.objects.get(pk=billID)
    resultSet = OutStockRecord.objects.filter(bill=bill)
    paginator = Paginator(resultSet, list_per_page) # Show 25 contacts per page    
    page = request.GET.get('page','1')
    try:
        outStockRecordset = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        outStockRecordset = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        outStockRecordset = paginator.page(paginator.num_pages)    
    company = Company.objects.all()[0]
    return render_to_response(displayPage+".html",{'bill': bill, 'outStockRecordset':outStockRecordset, 'company': company})
        
def QueryInventory(request, inStockBatchID):    
    inStockBatch = InStockBatch.objects.get(pk=inStockBatchID)
    return render_to_response('inventory_result.html',{'inStockBatch': inStockBatch,  'instockrecordSet': inStockBatch.instockrecord_set.all()})
        
        
def SupplierList(request):
    prefix = request.GET.get('q', "")
    logging.debug("get ajax autocomplete query q: " + prefix)
    supplierList = Supplier.objects.filter(Q(name__contains=prefix))
    list = ''
    for supplier in supplierList:
        list = list + supplier.name + "\n"
    return HttpResponse(list, mimetype="text/plain")
    
def ProductList(request):    
    q = request.GET.get('q', "")
    logging.debug("get ajax autocomplete query q: " + q)
    prefixs = q.split(",")
    productList = Product.objects.all()
    for prefix in prefixs:
        productList = productList.filter(Q(barcode__contains=prefix)|Q(name__contains=prefix))
    list = ''
    if productList:
        for product in productList:
            list = list + product.name+ "\n"
        
    serialNoSet = SerialNo.objects.filter(Q(serial_no__contains=prefix))
    if serialNoSet.count() > 0:
        for serialno in serialNoSet:
            list = list + serialno.serial_no + "\n"    
    
    return HttpResponse(list, mimetype="text/plain")
    
def CustomerList(request):
    prefix = request.GET.get('q', "")
    logging.debug("get ajax autocomplete query q: " + prefix)
    customerList = Customer.objects.filter(Q(name__contains=prefix)|Q(phone__contains=prefix))
    list = ''
    for customer in customerList :
        list = list + customer.name + "\n"
    return HttpResponse(list, mimetype="text/plain")    

def CategoryInfo(request):
    categorys = Category.objects.all()
    brands = Brand.objects.all()
    types = Type.objects.all()
    
    categorys_str = serializers.serialize("json",  categorys).replace("[","").replace("]","")
    brands_str = serializers.serialize("json",  brands).replace("[","").replace("]","")
    types_str = serializers.serialize("json",  types).replace("[","").replace("]","")
    json = "["+categorys_str+", "+brands_str+", "+types_str+"]"
#    json = "["+categorys_str+", "+brands_str+"]"
    return HttpResponse(json, mimetype="application/json")
    
def ProductInfo(request, query):
    logging.info("check product: %s info" % query)

    # serialNoSet = SerialNo.objects.filter(Q(serial_no__contains=query))
    try:
        serialNo = SerialNo.objects.get(serial_no=query)
        
        if serialNo:
            logging.info("SerialNo Found !! %s " % str(serialNo.serial_no))
            product = serialNo.inStockRecord.product
            product.cost = serialNo.inStockRecord.cost
            serial_no = serialNo.serial_no
            productSet = []
            productSet.append(product)
            json = serializers.serialize("json",  productSet)
            #newJson = json.replace("\"pk\": "+str(product.pk),"\"pk\": " + "\""+serial_no+"\"")
            newJson = json.replace("\"pk\"","\"imei\": " + "\""+serial_no+"\", \"pk\"")
            logging.info("Json: %s" % newJson)
            return HttpResponse(newJson, mimetype="application/json")    
        
    except SerialNo.DoesNotExist:
        logging.info("SerialNo Not Found !! %s, try search product barcode and name " % query)
        
    productSet = Product.objects.filter((Q(barcode__contains=query)|Q(name__contains=query)))
    if not productSet:
        return HttpResponse("[]", mimetype="application/json")    
    json = serializers.serialize("json",  productSet)
    return HttpResponse(json, mimetype="application/json")
    
def ProductInventory(request, pk):
    outStockRecord = None
    logging.info("check product: %s  inventory" % pk)
   
    inStockRecordSet = InStockRecord.objects.filter(product__pk=pk)
    if inStockRecordSet.count() == 0:
        logging.debug(request, "inStockRecordSet not found")
        return HttpResponse(0, mimetype="application/json")    

    outStockRecordSet = OutStockRecord.objects.filter(product__pk=pk)
    
    if outStockRecordSet.count() != 0:
        outStockRecord = outStockRecordSet.order_by('-create_at')[0]
        if outStockRecord is None:
            logging.debug(request, "outStockRecord not found")        
        
    inventoryCount = countInventory(inStockRecordSet, outStockRecord)
    json = "[{\"inventory\":"+str(inventoryCount)+"}]"
    return HttpResponse(json, mimetype="application/json")    

def CustomerInfo(request, query):
    logging.info(request, "check customer: " + query)
   
    customerSet = Customer.objects.filter((Q(name__contains=query)))
    if customerSet.count() == 0:
        logging.debug(request, "customerSet not found")
        return HttpResponse(0, mimetype="application/json")    

    json = serializers.serialize("json",  customerSet)
    return HttpResponse(json, mimetype="application/json")        
    
def SupplierInfo(request, query):
    logging.info(request, "check supplier: " + query)
   
    supplierSet = Supplier.objects.filter((Q(name__contains=query)))
    if supplierSet.count() == 0:
        logging.debug(request, "supplierSet not found")
        return HttpResponse(0, mimetype="application/json")    

    json = serializers.serialize("json",  supplierSet)
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
            product = form.save(commit = False)
            
            category_pk = request.GET.get('category','-1')
            brand_pk = request.GET.get('brand','-1')
            type_pk = request.GET.get('type','-1')
            try:
                category = Category.objects.get(pk=int(category_pk))
                brand = Brand.objects.get(pk=int(brand_pk))
                type = Type.objects.get(pk=int(type_pk))
            except Category.DoesNotExist:
                return HttpResponseRedirect('/product/search/')    
            except brand.DoesNotExist:
                return HttpResponseRedirect('/product/search/')    
            except type.DoesNotExist:
                return HttpResponseRedirect('/product/search/')                    
                
            product.category = category
            product.brand = brand
            product.type = type
            
            product.active=True
            product.save()
            return HttpResponseRedirect('/product/search/')
        else:
            return HttpResponseRedirect('/product/search/')

def ProductUpdateView(request, productID):
    product = Product.objects.get(pk=productID)
    form = ProductForm(instance=product)
    barcode = product.barcode
    return render_to_response('product_form.html',{'form': form, 'submit_form':'/product/save/'+productID, 'form_title': 'Update Product', 'barcode': barcode})

def PrintBarcode(request, barcode):    
    return render_to_response('printBarcode.html',{'barcode': barcode})
    
    
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
        logging.debug('inStockRecordSet is None')
        return 0;
        
    if outStockRecord is not None:
        sellCount = outStockRecord.sell_index
        
    for inStockRecord in inStockRecordSet:
        count = count + inStockRecord.quantity
    count = count - sellCount
    return count

@permission_required('kernal.change_counter', login_url='/accounts/login/')
def CounterUpdate(request):
    counterID =  request.GET.get('counterID', "")
    
    # count close amount
    counter = Counter.objects.get(pk=counterID)
    bills = Bill.objects.filter(counter=counter)
    totalAmount = counter.initail_amount
    for bill in bills:
        totalAmount = totalAmount + bill.total_price
        logging.info("Calc Bill: %s, %s" , bill.pk, bill.create_at)
        _update_outStockRecord_set(bill)
    counter.close_amount = totalAmount
    counter.active = False
    counter.save()
    return HttpResponseRedirect('/counter/close/') 
    
def _update_outStockRecord_set(bill):
    outStockRecordSet = bill.outstockrecord_set.all()
    totalProfit = 0
    for outStockRecord in outStockRecordSet:
        if outStockRecord.serial_no != None:
            product = outStockRecord.serial_no.inStockRecord.product
            totalCost = outStockRecord.serial_no.inStockRecord.cost
            outStockRecord.sell_index = -1
            outStockRecord.serial_no.active = False
            outStockRecord.serial_no.save()
            logging.info("Get price by SerialNo: %s ",totalCost);
        else:
            product = outStockRecord.product
            sales_index = __find_SalesIdx__(product)
            totalCost = __find_cost__(sales_index, outStockRecord)
            outStockRecord.sell_index = sales_index + outStockRecord.quantity
            logging.info("Get cost by FIFO, sales index: %s ,quantity: %s, sell_index: %s",sales_index , outStockRecord.quantity, outStockRecord.sell_index);
        outStockRecord.profit = outStockRecord.amount - totalCost
        outStockRecord.cost = totalCost
        outStockRecord.save()
        totalProfit = totalProfit + outStockRecord.profit
        logging.info("OutStockRecord: %s profit: %s, product: %s, sales index: %s" , outStockRecord.pk , outStockRecord.profit, outStockRecord.product.name, outStockRecord.sell_index)
    bill.profit = totalProfit
    logging.info("Bill: %s total profit: %s" , bill.pk , bill.profit)
    bill.save()

def PersonReport(request):
    startDate = request.GET.get('start_date','')
    endDate = request.GET.get('end_date','')
    if startDate == '' or endDate == '':
        startDate = str(date.min)
        endDate = str(date.max)
    startDate = startDate+" 00:00:00"
    endDate = endDate+" 23:59:59"
    
    products = Product.objects.all()
    salesReport = {}
    
    for product in products:
        users = _build_users_sold_dict(product, startDate, endDate)
        salesReport[product] = users
    
    return render_to_response('report_personalSales.html',{'session': request.session,  'salesReport': salesReport, 'dateRange': str(startDate)+" to "+str(endDate)}, )
        
def _build_users_sold_dict(product, startDate, endDate):
    #outStockRecordSet = OutStockRecord.objects.filter(product=product)
    outStockRecordSet = OutStockRecord.objects.filter(product=product).filter(create_at__range=(startDate,endDate))
    users = {}
    for outStockRecord in outStockRecordSet:
        user = outStockRecord.bill.user
        if user not in users:
            logging.info("create %s in users" % user )
            summaryOutStockRecord = OutStockRecord()
            summaryOutStockRecord.bill = outStockRecord.bill
            summaryOutStockRecord.unit_sell_price = 0
            summaryOutStockRecord.cost = 0
            summaryOutStockRecord.quantity = 0
            summaryOutStockRecord.profit = 0
            summaryOutStockRecord.amount = 0
            users[user] = [summaryOutStockRecord]
        users[user][0].unit_sell_price = users[user][0].unit_sell_price + outStockRecord.unit_sell_price
        users[user][0].cost = users[user][0].cost + outStockRecord.cost
        users[user][0].quantity = users[user][0].quantity + outStockRecord.quantity
        users[user][0].profit = users[user][0].profit + outStockRecord.profit
        users[user][0].amount = users[user][0].amount + outStockRecord.amount
        users[user].append(outStockRecord)
        logging.info("add %s's  outStockRecord" % user )
    return users

        
def __find_SalesIdx__(product):
    sales_index = 0
    #find last time sell record
    lastOutStockRecordSet = OutStockRecord.objects.filter(product=product)
    if lastOutStockRecordSet.count() != 0:
        lastOutStockRecord = lastOutStockRecordSet.order_by('create_at')[0]
        sales_index = lastOutStockRecord.sell_index
        logging.info("Product: "+product.name+"'s sales_index: " + str(sales_index))
    #logging.info("Product: "+product.name+"'s sales_index: " + str(sales_index))
    return sales_index        

def __find_cost__(salesIdx, outStockRecord):
    product = outStockRecord.product
    sales_index = 0
    #find last time sell record
    historyCost = []
    productQuantity = []
    inStockRecordSet = InStockRecord.objects.filter(product=product).order_by('create_at')
    currentQuantity = 0
    salesIdxPosision = -1
    
    idx = 0
    for inStockRecord in inStockRecordSet:
        historyCost.append(inStockRecord.cost)
        currentQuantity = currentQuantity + inStockRecord.quantity
        productQuantity.append(currentQuantity)
        if salesIdx <= currentQuantity and salesIdxPosision == -1:
            salesIdxPosision = idx
        idx = idx + 1
    totalproductCost = 0
    cost = historyCost[salesIdxPosision]
    for i in range(outStockRecord.quantity):
        logging.error("%s, %s",(salesIdx + i + 1) , productQuantity[salesIdxPosision])        
        if (salesIdx + i + 1) > productQuantity[salesIdxPosision]:
            if salesIdxPosision >= len(historyCost):
                logging.error("salesIdxPosision over limit: %s" % salesIdxPosision )
                pass
            else:
                salesIdxPosision = salesIdxPosision + 1
        cost = historyCost[salesIdxPosision]
        logging.info("salesIdxPosision: %s", salesIdxPosision)
        logging.info("Bill %s, %s cost:  %s  " , outStockRecord.bill.pk, product.name , cost)
        totalproductCost = totalproductCost + cost
    
    return totalproductCost
    
def checkCounter(function=None, redirect_field_name=REDIRECT_FIELD_NAME):
    def decorate(view_func):
        logging.error("here we are");
        return function
        
        #return HttpResponseRedirect('/out_stock_record/create/')

def test(request):
    #uid = session.get_decoded().get('_auth_user_id')
    user = None
    if request.session.get('_auth_user_id'):
        user = User.objects.get(pk=request.session.get('_auth_user_id'))
    
    #return render_to_response('CRUDForm.html',{'sessionid':session_key,  'user':user,  })
    return render_to_response('CRUDForm.html',{'session': request.session,  'user': user}, )
