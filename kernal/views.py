from pos.kernal.models import *
from pos.kernal.consignment_tool import __query_consignment_cost_qty__
from pos.kernal.consignment_tool import __close_consignment__
from pos.kernal.consignment_tool import __query_customer__
from pos.kernal.consignment_tool import __query_supplier__
from pos.kernal.consignment_tool import __consignment_out_balance_by_serials_no__
from pos.kernal.consignment_tool import __check_consignment_out_balance_input__
from pos.kernal.consignment_tool import __check_consignment_in_balance_input__
from pos.kernal.consignment_tool import __retriever_original_cost__
from pos.kernal.consignment_tool import __retriever_original_cost_by_FIFO__
from pos.kernal.consignment_tool import __build_consignment_in_by_instockrecords__
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.views.generic import list_detail, date_based, create_update
from django.contrib import messages
from django.core import serializers
from django.db.models import Count
from datetime import date
from datetime import datetime
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template import RequestContext
from barn import BarnOwl 
# import the logging library

import logging
from pos.kernal.barn import SerialRequiredException, CounterNotReadyException,\
    BarnMouse, SerialRejectException, Hermes, Thanatos, MickyMouse
from pos.kernal.excel import ExcelWriter


logging.basicConfig(
    level = logging.WARN,
    format = '%(asctime)s %(levelname)s %(funcName)s():%(lineno)s %(message)s',
)
# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
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
    total = 0
    for payment in payments:
        total += payment.bill.total_price
    return render_to_response('cash_sales_list.html',{'payments': payments, 'total': total, 'dateRange': str(startDate)+" to "+str(endDate)}, )
   
def InvoiceComplete(request, billID):
    bill = Bill.objects.get(pk = billID)
    payments = Payment.objects.filter(bill = bill)
    logger.debug("Bill: '%s' complete", bill.pk)
    for payment in payments:
        payment.status = 'Complete'
        payment.save()
        logger.debug("payment '%s' completed", payment.pk)
    return HttpResponseRedirect('/search/invoice/')

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

def ReportInventoryReceipt(request):    
    startDate = request.GET.get('start_date','')
    endDate = request.GET.get('end_date','')
    if startDate == '' or endDate == '':
        startDate = str(date.min)
        endDate = str(date.max)
    startDate = startDate+" 00:00:00"
    endDate = endDate+" 23:59:59"
    inStockBatch = InStockBatch.objects.all().filter(create_at__range=(startDate,endDate)).filter(active = True).order_by("-create_at")
    return render_to_response('report_inventory_receipt.html',{'inStockBatch': inStockBatch, 'dateRange': str(startDate)+" to "+str(endDate)}, )    

def ReportConsignmentInBalance(request):
    startDate = request.GET.get('start_date','')
    endDate = request.GET.get('end_date','')
    if startDate == '' or endDate == '':
        startDate = str(date.min)
        endDate = str(date.max)
    startDate = startDate+" 00:00:00"
    endDate = endDate+" 23:59:59"
    consignmentInDetails = ConsignmentInDetail.objects.filter(create_at__range=(startDate,endDate)).filter(inStockBatch__status='Incomplete')
    return render_to_response('report_consignment_in_balance.html',{'consignmentInDetails': consignmentInDetails, 'dateRange': str(startDate)+" to "+str(endDate)}, )
    
def ReportConsignmentOutBalance(request):
    startDate = request.GET.get('start_date','')
    endDate = request.GET.get('end_date','')
    if startDate == '' or endDate == '':
        startDate = str(date.min)
        endDate = str(date.max)
    startDate = startDate+" 00:00:00"
    endDate = endDate+" 23:59:59"
    consignmentOutDetails = ConsignmentOutDetail.objects.all().filter(create_at__range=(startDate,endDate)).filter(payment__status='Incomplete')
    return render_to_response('report_consignment_out_balance.html',{'consignmentOutDetails': consignmentOutDetails, 'dateRange': str(startDate)+" to "+str(endDate)}, )
    
def ReportDaily(request):
    startDate = request.GET.get('start_date','')
    endDate = request.GET.get('end_date','')
    if startDate == '' or endDate == '':
        startDate = str(date.min)
        endDate = str(date.max)
    startDate = startDate+" 00:00:00"
    endDate = endDate+" 23:59:59"
    bills = Bill.objects.all().filter(create_at__range=(startDate,endDate)).filter(Q(mode='cash')|Q(mode='pawning')).filter(active = True)
    profitTable = {}
    total_amount = 0
    total_profit = 0
    for bill in bills:
        total_amount = total_amount + bill.total_price
        total_profit = total_profit + bill.profit
        logger.debug("Total: %s", total_amount)
        logger.debug("profit: %s", total_profit)
        outStockRecords = OutStockRecord.objects.filter(bill=bill)
        total_proift = 0
        for outStockRecord in outStockRecords:
            total_proift = total_proift + outStockRecord.profit
        profitTable[bill.pk] = total_proift
    return render_to_response('report_dailySales.html',{'bills': bills, 'profitTable':profitTable, 'dateRange': str(startDate)+" to "+str(endDate),'total_amount':total_amount, 'total_profit': total_profit})

    
def ReportDailySales(request):
    startDate = request.GET.get('start_date','')
    endDate = request.GET.get('end_date','')
    if startDate == '' or endDate == '':
        startDate = str(date.min)
        endDate = str(date.max)
    startDate = startDate+" 00:00:00"
    endDate = endDate+" 23:59:59"
    
    total_amount = 0
    total_profit = 0    
    
    outstocks = OutStockRecord.objects.all().filter(create_at__range=(startDate,endDate))
    for outstock in outstocks:
       
        outstock.tt = outstock.unit_sell_price * outstock.quantity
        outstock.user = outstock.bill.sales_by.username
        total_amount = total_amount + (outstock.unit_sell_price * outstock.quantity)
            
    profitTable = {}

    return render_to_response('report_daily_sales.html',{ 'outstocks':outstocks, 'profitTable':profitTable, 'dateRange': str(startDate)+" to "+str(endDate),'start_date': str(startDate), 'end_date': str(endDate),'total_amount':total_amount, 'total_profit': total_profit})

def _wrapper_download_file(text, filename):
    response = HttpResponse(text, mimetype="application/vnd.ms-excel; charset=utf-8")
    response['Content-Disposition'] = 'attachment; filename='+filename     
    return response

def ReportDailySalesExcel(request):
    startDate = request.GET.get('start_date','')
    endDate = request.GET.get('end_date','')
    if startDate == '' or endDate == '':
        startDate = str(date.min)
        endDate = str(date.max)
    startDate = startDate
    endDate = endDate
    
    total_amount = 0
    
    outstocks = OutStockRecord.objects.filter(create_at__range=(startDate,endDate))
    headers = ['Inv No', 'Product', 'Cashier', 'Total', 'Type', 'Date']
    contents = []
    for outstock in outstocks:
        outstock.tt = outstock.unit_sell_price * outstock.quantity
        outstock.user = outstock.bill.sales_by.username
        total_amount = total_amount + (outstock.unit_sell_price * outstock.quantity)
        contents.append(';'.join([str(outstock.pk),outstock.product.name,outstock.user,str(outstock.tt),outstock.bill.mode,str(outstock.create_at)]))
    
    contents.append(';;Total:;'+str(total_amount)+';;;')
    filename = "report.xls"
    ExcelWriter(filename).export(headers, contents)
    return _wrapper_download_file(open(filename, 'rb'), filename)


    
    
def __categorys_arrays__():
    category_arr = []
    categorys = Category.objects.all().exclude(category_name = 'FOC')
    for category in categorys:
        category_arr.append(category.category_name)
    return category_arr

def __statistic_bill_detail_by_category__(bill, categorysTitle):
    categorySummary = []
    for i in range(len(categorysTitle)):
        categorySummary.append(0)
    outStockRecords = OutStockRecord.objects.filter(bill=bill)
    for outStockRecord in outStockRecords:
        index = -1
        try:
            index = categorysTitle.index(outStockRecord.product.category.category_name)
        except ValueError:
            pass
        if  index == -1:
            logger.error("Category '%s' not found in databases !! ", outStockRecord.product.category.category_name)
        categorySummary[index] = categorySummary[index] + outStockRecord.amount
    return categorySummary
    
def ReportDailyCategory(request):
    startDate = request.GET.get('start_date','')
    endDate = request.GET.get('end_date','')
    if startDate == '' or endDate == '':
        startDate = str(date.min)
        endDate = str(date.max)
    startDate = startDate+" 00:00:00"
    endDate = endDate+" 23:59:59"
    bills = Bill.objects.filter(create_at__range=(startDate,endDate)).filter(Q(mode='cash')|Q(mode='invoice')|Q(mode='trade-in')|Q(mode='warranty'))
    categorysTitle = __categorys_arrays__()
    dateTable = {}
    for bill in bills:
        bill_date = bill.create_at.strftime("%Y-%m-%d")
        if bill_date not in dateTable:
            categorysSummary = []
            for i in range(len(categorysTitle)):
                categorysSummary.append(0)
            dateTable[bill_date] = categorysSummary
        statistic_result = __statistic_bill_detail_by_category__(bill, categorysTitle)
        total_summary = dateTable[bill_date]
        for i in range(len(categorysTitle)):
            total_summary[i] = total_summary[i] + statistic_result[i]
    return render_to_response('report_dailySales_by_category.html',{'dateTable': sorted(dateTable.iteritems(), reverse=True), 'categorysTitle':categorysTitle ,  'dateRange': str(startDate)+" to "+str(endDate)}, )
    
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

    """
    input
    [
     (u'do_date', [u'2011-06-22']), 
     (u'do_no', [u'BC1655']), 
     (u'inv_no', [u'BC1654']), 
     (u'salesMode', [u'cash']), 
     (u'item', [u'NK1280PPL']), 
     (u'mode', [u'purchase']), 
     (u'supplier', [u'Super-Link Station (M) Sdn Bhd']), 
     
     (u'110_serial-0', [u'NK1208001']), 
     (u'110_serial-2', [u'NK1208003']), 
     (u'110_quantity', [u'3']), 
     (u'110_serial-1', [u'NK1208002'])
     (u'110_cost', [u'1000']), 
     
     (u'111_serial-0', [u'NK1280PPL001']), 
     (u'111_serial-1', [u'NK1280PPL002']), 
     (u'111_quantity', [u'3']), 
     (u'111_serial-2', [u'NK1280PPL003']), 
     (u'111_cost', [u'2000']), 
    ]

    output 
    {
     u'111': {
                 u'serial-2': [u'NK1280PPL003'], 
                 u'serial-1': [u'NK1280PPL002'], 
                 u'serial-0': [u'NK1280PPL001'], 
                 u'cost': [u'2000'], 
                 u'quantity': [u'3']
             }, 
     u'110': {
                 u'serial-0': [u'NK1208001'], 
                 u'serial-2': [u'NK1208003'], 
                 u'serial-1': [u'NK1208002'], 
                 u'cost': [u'1000'], 
                 u'quantity': [u'3']
             }
     }
"""
def __convert_inventory_URL_2_inStockBatch_dict__(request):
    dict = {}
    sales_item = request.GET.lists()
    for key,  value in sales_item:
        if key.find("_") != -1:
            continue
        if key not in dict :
            dict[key] ={}
        dict[key] = value[0]
        
    dict [u'_auth_user_id'] = request.session.get('_auth_user_id')
    dict [u'do_no'] = request.GET.get('do_no')
    dict [u'inv_no'] = request.GET.get('inv_no')
    dict [u'refBill_no'] = request.GET.get('refBill_no')
    dict [u'do_date'] = request.GET.get('do_date')
    logger.debug("InStockBatch parameters: %s", dict)        
    return dict

def __convert_inventory_URL_2_dict__(request):
    dict = {}
    sales_item = request.GET.lists()
    logger.debug("instock items url parameters: %s", sales_item)
    for key,  value in sales_item:
        if key == "do_no":
            continue
        if key == "inv_no":
            continue            
        if key == "do_date":
            continue
        if key.find("_") == -1:
            continue
        pk = key.split("_")[0]
        attr = key.split("_")[1]
        if pk not in dict :
            dict[pk] ={}
        dict[pk][attr]= value[0]
    return dict

def __build_instock_batch__(request):
    mode = request.GET.get('mode', 'purchase')
    today = date.today()
    do_date = request.GET.get('do_date', today.strftime("%d/%m/%y"))
    supplier_name = request.GET.get('supplier', "")
    supplier = None
    try:
        supplier = Supplier.objects.filter(name=supplier_name)[0:1].get()
    except Supplier.DoesNotExist:
        try:
            customer = Customer.objects.filter(name=supplier_name)[0:1].get()
            supplier = Supplier()
            supplier.name = customer.name
            supplier.supplier_code = customer.customer_code
            supplier.contact_person = customer.contact_person
            supplier.phone_office = customer.phone
            supplier.phone_mobile = customer.phone
            supplier.fax = customer.fax
            supplier.email = customer.email
            supplier.address = customer.address
            supplier.active = True            
            supplier.save()            
            logger.warn("Supplier '%s' found, auto create supplier", supplier_name)                
        except Customer.DoesNotExist:
            logger.warn("Supplier '%s' not found in Customer, auto create supplier", supplier_name)    
            supplier = Supplier()
            supplier.name = supplier_name
            supplier.supplier_code = supplier_name
            supplier.contact_person = supplier_name
            supplier.save()
    inStockBatch = InStockBatch()
    inStockBatch.mode = mode
    inStockBatch.supplier = supplier
    inStockBatch.user = User.objects.get(pk=request.session.get('_auth_user_id'))
    inStockBatch.do_date = do_date
    inStockBatch.invoice_no = request.GET.get('inv_no', "-")
    inStockBatch.do_no = request.GET.get('do_no', "-")
    inStockBatch.status = 'Incomplete'
    inStockBatch.save();
    logger.debug("InStockBatch: '%s' build", inStockBatch.pk)
    return inStockBatch    

def __build_instock_records__(inStockBatch, inventoryDict, status):
    logger.debug("build InStock records")
    inStockRecords = []
    # build OutStockRecord to save data
    for pk in inventoryDict :
        product = None
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            logger.error("Product primary key: '%s' not found, this round fail, continue. ", pk)
            continue
        except ValueError:
            logger.error("Product primary key: '%s' not valid, this round fail, continue. ", pk)
            continue        
        cost = float(inventoryDict [pk]['cost'][0])
        quantity = int(inventoryDict [pk]['quantity'] [0])
        inStockRecord = InStockRecord()
        inStockRecord.inStockBatch = inStockBatch
        inStockRecord.barcode = pk
        inStockRecord.product = product
        inStockRecord.cost = cost
        inStockRecord.quantity = quantity
        inStockRecord.startIDX = 0
        inStockRecord.status = status
        inStockRecord.save()
        logger.debug("instock '%s' build success, cost: '%s', quantity:'%s' ", product.name, inStockRecord.cost, inStockRecord.quantity)
        inStockRecords.append(inStockRecord)
    return inStockRecords

def __build_serial_no__(request, inStockRecords, dict):   
    logger.debug("build Serial Numbs ")
    serials = []
    for inStockRecord in inStockRecords:
        product = inStockRecord.product
        for value in dict[str(product.pk)] :
            if 'serial-' in value:
                serialNO = request.GET.get(str(product.pk)+"_"+value, '') 
                if serialNO == '':
                    continue
                # look up from serial no table
                try:
                    serial = SerialNo.objects.get(serial_no = serialNO)
                    serial.inStockRecord = inStockRecord
                    serial.active = True
                    serial.save()
                    serials.append(serial)
                    logger.debug("Serial no: %s found, unlock it", serialNO)
                except SerialNo.DoesNotExist:
                    serial = SerialNo()
                    serial.inStockRecord = inStockRecord
                    serial.serial_no = serialNO
                    serial.active = True
                    serial.save()  
                    serials.append(serial)
                    logger.debug("build serial no: '%s' for product: '%s'", serialNO, product.name)
    return serials                
    
def InventoryConfirm(request):
    inventoryDict = {}
    if request.method == 'GET':
        # process Request parameter
        inStockBatchDict = __convert_inventory_URL_2_inStockBatch_dict__(request)
        inventoryDict = __convert_inventory_URL_2_dict__(request)
        logger.debug("inventory dict build success: %s", inventoryDict)
        owl = BarnOwl()
        result = None
        try:
            result = owl.InStock(request.GET.get("mode"), inStockBatchDict, inventoryDict)
        except SerialRequiredException as srException:
            error_msg = srException.value + " Required Serial Number"
            return render_to_response('inventory_base.html', {'form': InStockBatchForm, 'action': '/inventory/confirm', 'error_msg': error_msg})
        except SerialRejectException as srException:
            error_msg = srException.value + " Serial Number NOT required"
            return render_to_response('inventory_base.html', {'form': InStockBatchForm, 'action': '/inventory/confirm', 'error_msg': error_msg})
        logger.info("InventoryConfirm finish")

        hermes = Hermes()
        hermes.ConsignmentIn(result[0])
        hermes.ConsignmentOutReturn(result[0])

        return HttpResponseRedirect('/inventory/result/'+str(result[0].pk))
"""
    __convert_sales_URL_2_dict__(): 
    
    Input Data array
        [
        // Bill data
         (u'customer', [u'Cash']), 
         (u'salesby', [u'1']), 
         (u'amountTendered', [u'300']), 
         (u'salesMode', [u'cash']), 
         (u'item', [u'EXT5001']), 
         (u'mode', [u'sale']), 
         (u'discount', [u'0.00']), 
         (u'total', [u'300']), 
         (u'subTotal', [u'300']), 
         (u'change', [u'0'])
        // Payment data
         (u'transactionNo', [u'']), 
        // OutStockRecord data
         (u'EXT5001_pk', [u'35']), 
         (u'EXT5001_quantity', [u'1']), 
         (u'EXT5001_imei', [u'EXT5001']), 
         (u'EXT5001_price', [u'300']), 
        ]
        
    Output Data Dict
        {
         u'EXT5001': {
                         u'imei': [u'EXT5001'], 
                         u'pk': [u'35'], 
                         u'price': [u'300'], 
                         u'quantity': [u'1']
                     }
         }    
"""
def __convert_sales_URL_2_dict__(request):
    salesDict = {}
    sales_item = request.GET.lists()
    logger.debug("instock items url parameters: %s", sales_item)    
    for key,  value in sales_item:
        if '_' not in key:
            continue
        pk = key.split("_")[0]
        attr = key.split("_")[1]
        if pk not in salesDict:
            salesDict[pk] ={}
        salesDict[pk] [attr]= value[0]
    return salesDict

def __build_bill__(request, customer, counter):
    bill = Bill()
    bill.mode = request.GET.get('mode', 'sale')
    bill.subtotal_price = request.GET.get('subTotal', '0')
    bill.discount = request.GET.get('discount', '0')
    bill.total_price = request.GET.get('total', '0')
    bill.tendered_amount = request.GET.get('amountTendered', '0')
    bill.change = request.GET.get('change', '0')
    bill.customer = customer
    bill.profit = 0
    bill.counter = counter
    bill.sales_by = User.objects.get(pk=int(request.GET.get('salesby','-1')))
    bill.issue_by = User.objects.get(pk=request.session.get('_auth_user_id'))
    bill.fulfill_payment = False
    bill.save()
    logging.debug("Bill '%s' create", bill.pk)
    return bill

def __build_payment__(request, bill, customer):    
    payment = Payment()
    payment.bill = bill
    salesMode = request.GET.get('salesMode', '')
    logger.debug("SalesMode: %s", salesMode)
    if salesMode == "cash":
        payment.term = "Cash"
        payment.type = "Cash Sales"
        payment.status = "Complete"
    elif salesMode == "invoice":
        payment.term = customer.term
        payment.type = "Invoice"
        payment.status = "Incomplete"    
    elif salesMode == "adjust":
        payment.term = "adjust"
        payment.type = "adjust"
        payment.status = "Complete"            
    elif salesMode == "Consignment":
        payment.term = "Consignment"
        payment.type = "Consignment"
        payment.status = "Incomplete"    
    elif salesMode == "Consignment_in_balance":
        payment.term = "Consignment_in_balance"
        payment.type = "Consignment_in_balance"
        payment.status = "Incomplete"    
    elif salesMode == "Consignment_out_sales":
        payment.term = "Consignment_out_sales"
        payment.type = "Consignment_out_sales"
        payment.status = "Complete"         
    else:
        logger.error("salesMode out of expect: %s ", salesMode)
    logger.debug("build '%s' payment", salesMode)                
    transactionNo = request.GET.get('transactionNo', '')
    if transactionNo != '': 
        logger.info("paid by creadit card")
        payment.term = "CreaditCard"
        payment.transaction_no = transactionNo
    logger.debug("payment success builded")
    payment.save()    
    return payment

def __lock_serial_no__(request, pk):
    serial_no = None
    try:
        imei = request.GET.get(pk+'_imei', 'None')
        serial_no = SerialNo.objects.get(serial_no = imei)
        serial_no.active = False
        serial_no.save()
        logger.info("product found by imei : %s " % pk)
    except SerialNo.DoesNotExist:
        logger.info("no imei no '%s'. found", pk)
    return serial_no

def __build_FOC_product__(product_name):    
    category = None
    brand = None
    uom = None
    categorys = Category.objects.filter(category_name = "FOC")
    if categorys.count() == 0:
        category = Category()
        category.category_name = "FOC"
        category.save()
    else:
        category = categorys[0]
    brands = Brand.objects.filter(brand_name = "FOC")
    if brands.count() == 0:
        brand = Brand()
        brand.category = category
        brand.brand_name = "FOC"
        brand.save()
    else:
        brand = brands[0]
    uoms = UOM.objects.filter(name="FOC")
    if uoms.count() == 0:
        uom = UOM()
        uom.name = "FOC"
        uom.save()
    else:
        uom = uoms[0]        
    product = Product()
    product.barcode = "FOC"
    product.name = product_name
    product.description = product_name
    product.category =  category
    product.brand =  brand
    product.retail_price = 0
    product.cost = 0
    product.uom = uom
    product.active = False
    product.save()
    return product    

def __build_outstock_record__(request, bill, payment, dict , type):
    outStockRecords = []
    # build OutStockRecord to save data
    for barcode in dict:
        logger.debug("build OutStockRecord by: '%s'", barcode)
        outStockRecord = OutStockRecord()
        outStockRecord.bill = bill
        outStockRecord.barcode = barcode
        logger.info("looking for pk : %s " % barcode)
        if "-foc-product" in barcode:
            logger.info("Foc product !! : %s " % barcode)    
            products = Product.objects.filter(name=barcode)
            if products.count() == 0:
                logger.info("Foc product NOT found in DB !! : %s , create it" % barcode)    
                outStockRecord.product =  __build_FOC_product__(barcode)
            else:
                outStockRecord.product = products[0]
        else:
            serial_no = __lock_serial_no__(request, barcode)
            outStockRecord.serial_no = serial_no
            if serial_no:
                logger.info("product found by imei : %s " % barcode)
                outStockRecord.product = serial_no.inStockRecord.product
            else:
                logger.info("product found by pk : %s " % barcode)
                outStockRecord.product = Product.objects.get(pk=barcode)
        outStockRecord.unit_sell_price = dict[barcode]['price'][0]
        outStockRecord.quantity = dict[barcode]['quantity'] [0]
        outStockRecord.amount = str(float(dict[barcode]['price'][0]) * float(dict[barcode]['quantity'] [0])) 
        outStockRecord.sell_index = 0;
        outStockRecord.profit = 0;
        outStockRecord.cost = -1;
        outStockRecord.type = type
        outStockRecord.save()
        outStockRecords.append(OutStockRecord.objects.get(pk=outStockRecord.pk))
        if payment.type == "Consignment":
            consignmentOut = ConsignmentOutDetail()
            consignmentOut.payment = payment
            consignmentOut.outStockRecord = outStockRecord
            consignmentOut.serialNo = serial_no
            consignmentOut.quantity = outStockRecord.quantity
            consignmentOut.balance = 0
            consignmentOut.save()
            logger.debug("build Prodict '%s' OutStockRecord '%s' consignment detail.", outStockRecord.product.name, outStockRecord.pk )
        return outStockRecords

def DepositSave(request):
    cname = request.GET.get("customer")
    thanatos = Thanatos()
    customer = thanatos.Customer(cname)
    form = DepositForm(request.GET)
    deposit = form.save(commit=False)
    deposit.customer = customer
    deposit.active = True
    deposit.save()
    logger.info("Deposite '%s' create success", deposit.pk)
    return HttpResponseRedirect('/search/deposit/')

def ServiceSave(request):
    salesDict = {}
    if request.method == 'GET':
        bill_dict = __convert_sales_URL_2_bill_dict__(request)
        salesDict = __convert_sales_URL_2_dict__(request)
        owl = BarnOwl()
        try:
            bills_and_payments = owl.OutStock(request.GET.get('mode', 'sale'), bill_dict, salesDict)
            payment = bills_and_payments[1]
            outStockRecords = bills_and_payments[2]
        except CounterNotReadyException as e:
            logger.warn("Can not found 'OPEN' Counter, direct to open page")
            return HttpResponseRedirect('/admin/kernal/counter/add/')    
        # process Request parameter
        bill = bills_and_payments[0]
        payment = bills_and_payments[1]
        if payment.type == 'Invoice':
            logger.debug("Invoice bill, direct to invoice interface")
            return HttpResponseRedirect('/sales/invoice/'+str(bill.pk))        
        elif payment.type == 'Consignment':
            logger.debug("Consignment bill, direct to Consignment interface")
            return HttpResponseRedirect('/sales/consignment/'+str(bill.pk))                    
        else:
            logger.debug("Cash sales bill, direct to Recept interface")
            return HttpResponseRedirect('/sales/bill/'+str(bill.pk))        
    
#    cname = request.GET.get("customer")
#    thanatos = Thanatos()
#    customer = thanatos.Customer(cname)
#    form = ServiceJobForm(request.GET)
#    service = form.save(commit=False)
#    service.customer = customer
#    service.profit = float(service.price) - float(service.cost)
#    service.active = True
#    service.save()
#    logger.info("Service job '%s' create success", service.pk)
#    return HttpResponseRedirect('/search/service/')

def RepairSave(request):
    form = RepairForm(request.GET)
    repair = form.save(commit=False)
    repair.mode = "repair"
    repair.status = "Incomplete"
    repair.active = True
    repair.key = repair.key.strip()
    repair.save()
    logger.info("Service job '%s' create success", repair.pk)
    return HttpResponseRedirect('/search/repair/')

def ProductCostUpdate(request):
    inStockBatch_pk = request.GET.get("inStockBatch_pk")
    hermes = Hermes()
    if not hermes.is_all_close:
        error_msg = "Cost update fail, reason: Counter Not Close"
        return QueryInventory(request, inStockBatch_pk, error_msg)
    
    inStockBatch = InStockBatch.objects.get(pk=int(inStockBatch_pk))
    inStockRecords = InStockRecord.objects.filter(inStockBatch = inStockBatch)

    for inStockRecord in inStockRecords:
        cost = float(request.GET.get("inStockRecord_" + str(inStockRecord.pk), "0"))
        mouse = None
        if inStockRecord.product.algo.name == Algo.PERCENTAGE:
            mouse = MickyMouse(inStockRecord.product)
        else:
            mouse = BarnMouse(inStockRecord.product)        
        mouse.UpdateCost(inStockRecord.pk, cost)
    hermes.ReCalcCounters(inStockBatch.create_at)
    return HttpResponseRedirect('/inventory/result/'+inStockBatch_pk)

def __convert_sales_URL_2_bill_dict__(request):
    dict = {}
    sales_item = request.GET.lists()
    logger.debug("instock items url parameters: %s", sales_item)    
    for key,  value in sales_item:
        if '_' in key:
            continue
        if key not in dict :
            dict[key] ={}
        dict[key] = value[0]
    dict [u'_auth_user_id'] = request.session.get('_auth_user_id')
    logger.debug("Bill Dict: %s", dict)        
    return dict

def SalesConfirm(request):
    salesDict = {}
    if request.method == 'GET':
        bill_dict = __convert_sales_URL_2_bill_dict__(request)
        salesDict = __convert_sales_URL_2_dict__(request)
        owl = BarnOwl()
        try:
            bills_and_payments = owl.OutStock(request.GET.get('mode', 'sale'), bill_dict, salesDict)
            hermes = Hermes()
            payment = bills_and_payments[1]
            outStockRecords = bills_and_payments[2]
            hermes.ConsignmentOut(payment, outStockRecords)
            hermes.BalanceConsignmentIN(outStockRecords)
        except CounterNotReadyException as e:
            logger.warn("Can not found 'OPEN' Counter, direct to open page")
            return HttpResponseRedirect('/admin/kernal/counter/add/')    
        # process Request parameter
        bill = bills_and_payments[0]
        payment = bills_and_payments[1]
        if payment.type == 'Invoice':
            logger.debug("Invoice bill, direct to invoice interface")
            return HttpResponseRedirect('/sales/invoice/'+str(bill.pk))        
        elif payment.type == 'Consignment':
            logger.debug("Consignment bill, direct to Consignment interface")
            return HttpResponseRedirect('/sales/consignment/'+str(bill.pk))                    
        else:
            logger.debug("Cash sales bill, direct to Recept interface")
            return HttpResponseRedirect('/sales/bill/'+str(bill.pk))        

def ConsignmentOutSalesConfirm(request):
    salesDict = {}
    if request.method == 'GET':
        bill_dict = __convert_sales_URL_2_bill_dict__(request)
        salesDict = __convert_sales_URL_2_dict__(request)
        owl = BarnOwl()
        product_dict = owl._build_product_dict(salesDict)
        
        try:
            thanatos = Thanatos()
            customer = thanatos.Customer(bill_dict.get("customer"))
            payments = Payment.objects.filter(Q(bill__customer = customer)&Q(type=Hermes.CONSIGNMENT_OUT))
            hermes = Hermes()
            bill_id = None            
            for payment in payments:
                bill_id = payment.bill.pk
                hermes.ConsignmentOutSale(payment, bill_dict, salesDict)
            
        except CounterNotReadyException as e:
            logger.warn("Can not found 'OPEN' Counter, direct to open page")
            return HttpResponseRedirect('/admin/kernal/counter/add/')    
        return HttpResponseRedirect('/sales/bill/'+str(bill_id))        


def __consignment_out_handler__(request, is_sales):
    inventoryDict = {}
    if request.method == 'GET':
        customer = __query_customer__(request, 'supplier')
        inventoryDict = __convert_inventory_URL_2_dict__(request)
        error_msg = __check_consignment_out_balance_input__(request, inventoryDict, customer)
        if error_msg:
            return render_to_response('consignment_out_balance_form.html',{'title':'Consignment OutStock Balance', 'form': InStockBatchForm, 'action':'/consignment/out/balance/confirm/', 'error_msg': error_msg})            
        logger.debug("inventory dict build success: %s", inventoryDict)
        inStockBatch = __build_instock_batch__(request)
        inStockRecords = __build_instock_records__(inStockBatch, inventoryDict, 'ConsignmentOutBalance')
        __retriever_original_cost__(request, inStockRecords, inventoryDict, customer)  
        serials = __build_serial_no__(request, inStockRecords, inventoryDict)  
        __consignment_out_balance_by_serials_no__(request, serials)
        __close_consignment__(request)
        if is_sales:
            logger.debug("Consignment Out Sales.")
        logger.info("InventoryConfirm finish")
        return HttpResponseRedirect('/inventory/result/'+str(inStockBatch.pk))
        
#def ConsignmentOutSale(request):
#    salesDict = {}
#    if request.method == 'GET':
#        # check Counter 
#        counters = None
#        counters = Counter.objects.filter(active=True).order_by('-create_at')
#        if counters.count() == 0:
#            logger.warn("Can not found 'OPEN' Counter, direct to open page")
#            return HttpResponseRedirect('/admin/kernal/counter/add/')    
#        # process Request parameter
#        salesDict = __convert_sales_URL_2_dict__(request)
#        logger.debug("sales dict: %s" , salesDict)
#        customer = __query_customer__(request, 'customer')
#        bill = __build_bill__(request, customer, counters[0])
#        payment = __build_payment__(request, bill, customer)
#        __build_outstock_record__(request, bill, payment, salesDict, 'ConsignmentOutSales')      
#        if payment.type == 'Invoice':
#            logger.debug("Invoice bill, direct to invoice interface")
#            return HttpResponseRedirect('/sales/invoice/'+str(bill.pk))        
#        elif payment.type == 'Consignment':
#            logger.debug("Consignment bill, direct to Consignment interface")
#            return HttpResponseRedirect('/sales/consignment/'+str(bill.pk))                    
#        elif payment.type == 'Consignment_out_sales':
#            logger.debug("Consignment_out_sales bill, direct to Consignment_out_sales interface")
#            return HttpResponseRedirect('/sales/Consignment_out_sales/'+str(bill.pk))                                
#        else:
#            logger.debug("Cash sales bill, direct to Recept interface")
#            return HttpResponseRedirect('/sales/bill/'+str(bill.pk))     
    
def ConsignmentOutBalance(request):
#    ConsignmentOutSale
    return __consignment_out_handler__(request, False)

def __record_as_disable_stock__(outStockRecord, inStockRecord, start_idx, qty, type, serialNo):
    disableStock = DisableStock()
    disableStock.inStockRecord = inStockRecord
    disableStock.outStockRecord = outStockRecord
    disableStock.type = type
    disableStock.serialNo = serialNo
    disableStock.quantity = qty
    disableStock.index = start_idx
    disableStock.save()
    logger.debug("disable stock record '%s' added. inStockRecord: '%s', start idx: '%s', quantity: '%s' ", disableStock.pk, inStockRecord.pk, start_idx, qty)
        
def __build_Consignment_In_index__(supplier, outStockRecords):
    logger.debug("Balance Consignment In Detail. supplier: '%s', OutStockRecords count: '%s' ", supplier, len(outStockRecords))
    for outStockRecord in outStockRecords:
        if outStockRecord.serial_no:
            consignmentInDetails = ConsignmentInDetail.objects.filter(Q(serialNo = outStockRecord.serial_no)&Q(status='Incomplete'))
            if consignmentInDetails.count() == 0:
                logger.error("ConsignmentInDetail not found by SerialNo '%s'", outStockRecord.serial_no)
                continue
            consignmentInDetail = consignmentInDetails[0]
            __record_as_disable_stock__(outStockRecord, outStockRecord.serial_no.inStockRecord, consignmentInDetail.balance, 1, 'Consignment_In_Balance', outStockRecord.serial_no)
            consignmentInDetail.balance = consignmentInDetail.quantity
            consignmentInDetail.status = 'Complete'
            consignmentInDetail.save()
            inStockBatch = InStockBatch.objects.get(pk=consignmentInDetail.inStockBatch.pk)
            inStockBatch.status = 'Complete'
            inStockBatch.save()
            logger.debug("ConsignmentInDetails '%s' found by SerialNo, QTY: '%s', balance: '%s', status '%s'", consignmentInDetail.pk, consignmentInDetail.quantity, consignmentInDetail.balance, consignmentInDetail.status)
            continue
        logger.debug("ConsignmentInDetails not found by SerianNo, try FIFO")
        product = outStockRecord.product
        out_qty = outStockRecord.quantity
        inStockRecords = InStockRecord.objects.filter(Q(inStockBatch__supplier = supplier)&Q(inStockBatch__mode = 'Consignment_IN')&Q(inStockBatch__status = 'Incomplete')).order_by('create_at')
        for inStockRecord in inStockRecords:
            consignmentInDetail = ConsignmentInDetail.objects.filter(Q(inStockRecord = inStockRecord))[0]
            if consignmentInDetail.status == "Complete":
                logger.debug("ConsignmentInDetail '%s' completed, skip", consignmentInDetail.pk)
                continue
            waiting_balance = consignmentInDetail.quantity - consignmentInDetail.balance
            __record_as_disable_stock__(outStockRecord, inStockRecord, consignmentInDetail.balance, waiting_balance, 'Consignment_In_Balance', outStockRecord.serial_no)            
            if waiting_balance == 0:
                consignmentInDetail.status = 'Complete'
                consignmentInDetail.save()
                logger.debug("inStockRecord '%s' found, status: '%s', balance qty: '%s', balance: '%s'", inStockRecord.pk, consignmentInDetail.status, consignmentInDetail.quantity, consignmentInDetail.balance)
            else:
                if out_qty >= waiting_balance:
                    out_qty =  out_qty - waiting_balance
                    consignmentInDetail.balance = consignmentInDetail.quantity
                    consignmentInDetail.status = 'Complete'
                    consignmentInDetail.save()                   
                    logger.debug("inStockRecord '%s' found, status: '%s', balance qty: '%s', balance: '%s'", inStockRecord.pk, consignmentInDetail.status, consignmentInDetail.quantity, consignmentInDetail.balance)
                else:
                    consignmentInDetail.balance = consignmentInDetail.balance + out_qty
                    consignmentInDetail.status = 'focusing'
                    consignmentInDetail.save()
                    logger.debug("inStockRecord '%s' found, status: '%s', balance qty: '%s', balance: '%s'", inStockRecord.pk, consignmentInDetail.status, consignmentInDetail.quantity, consignmentInDetail.balance)
                    break
                
def __build_Consignment_Out_index__(supplier, outStockRecords):
    logger.debug("Balance Consignment In Detail. supplier: '%s', OutStockRecords count: '%s' ", supplier, len(outStockRecords))
    for outStockRecord in outStockRecords:
        if outStockRecord.serial_no:
            consignmentInDetails = ConsignmentInDetail.objects.filter(Q(serialNo = outStockRecord.serial_no)&Q(status='Incomplete'))
            if consignmentInDetails.count() == 0:
                logger.error("ConsignmentInDetail not found by SerialNo '%s'", outStockRecord.serial_no)
                continue
            consignmentInDetail = consignmentInDetails[0]
            __record_as_disable_stock__(outStockRecord, outStockRecord.serial_no.inStockRecord, consignmentInDetail.balance, 1, 'Consignment_In_Balance', outStockRecord.serial_no)
            consignmentInDetail.balance = consignmentInDetail.quantity
            consignmentInDetail.status = 'Complete'
            consignmentInDetail.save()
            logger.debug("ConsignmentInDetails '%s' found by SerialNo, QTY: '%s', balance: '%s', status '%s'", consignmentInDetail.pk, consignmentInDetail.quantity, consignmentInDetail.balance, consignmentInDetail.status)
            continue
        logger.debug("ConsignmentInDetails not found by SerianNo, try FIFO")
        product = outStockRecord.product
        out_qty = outStockRecord.quantity
        inStockRecords = InStockRecord.objects.filter(Q(inStockBatch__supplier = supplier)&Q(inStockBatch__mode = 'Consignment_IN')&Q(inStockBatch__status = 'Incomplete')).order_by('create_at')
        for inStockRecord in inStockRecords:
            consignmentInDetail = ConsignmentInDetail.objects.filter(Q(inStockRecord = inStockRecord))[0]
            if consignmentInDetail.status == "Complete":
                logger.debug("ConsignmentInDetail '%s' completed, skip", consignmentInDetail.pk)
                continue
            waiting_balance = consignmentInDetail.quantity - consignmentInDetail.balance
            __record_as_disable_stock__(outStockRecord, inStockRecord, consignmentInDetail.balance, waiting_balance, 'Consignment_In_Balance', outStockRecord.serial_no)            
            if waiting_balance == 0:
                consignmentInDetail.status = 'Complete'
                consignmentInDetail.save()
                logger.debug("inStockRecord '%s' found, status: '%s', balance qty: '%s', balance: '%s'", inStockRecord.pk, consignmentInDetail.status, consignmentInDetail.quantity, consignmentInDetail.balance)
            else:
                if out_qty >= waiting_balance:
                    out_qty =  out_qty - waiting_balance
                    consignmentInDetail.balance = consignmentInDetail.quantity
                    consignmentInDetail.status = 'Complete'
                    consignmentInDetail.save()                   
                    logger.debug("inStockRecord '%s' found, status: '%s', balance qty: '%s', balance: '%s'", inStockRecord.pk, consignmentInDetail.status, consignmentInDetail.quantity, consignmentInDetail.balance)
                else:
                    consignmentInDetail.balance = consignmentInDetail.balance + out_qty
                    consignmentInDetail.status = 'focusing'
                    consignmentInDetail.save()
                    logger.debug("inStockRecord '%s' found, status: '%s', balance qty: '%s', balance: '%s'", inStockRecord.pk, consignmentInDetail.status, consignmentInDetail.quantity, consignmentInDetail.balance)
                    break
                    
def ConsignmentInBalance(request):
    inventoryDict = {}
    if request.method == 'GET':
        bill_dict = __convert_sales_URL_2_bill_dict__(request)
        salesDict = __convert_sales_URL_2_dict__(request)
        thanatos = Thanatos()
        supplier = thanatos.Supplier(request.GET.get('supplier', 'Cash'))
        
        owl = BarnOwl()
        bill = None
        try:
            bills_and_payments = owl.OutStock(request.GET.get('mode', 'sale'), bill_dict, salesDict)
            hermes = Hermes()
            bill = bills_and_payments[0]
            payment = bills_and_payments[1]
            outStockRecords = bills_and_payments[2]
            hermes.ConsignmentOut(payment, outStockRecords)
            hermes.BalanceConsignmentIN(outStockRecords, supplier)
        except CounterNotReadyException as e:
            logger.warn("Can not found 'OPEN' Counter, direct to open page")
            return HttpResponseRedirect('/admin/kernal/counter/add/')    
        
        if payment.type == 'Invoice':
            logger.debug("Invoice bill, direct to invoice interface")
            return HttpResponseRedirect('/sales/invoice/'+str(bill.pk))        
        elif payment.type == 'Consignment':
            logger.debug("Consignment bill, direct to Consignment interface")
            return HttpResponseRedirect('/sales/consignment/'+str(bill.pk))                    
        else:
            logger.debug("Cash sales bill, direct to Recept interface")
            return HttpResponseRedirect('/sales/bill/'+str(bill.pk))                        
        inventoryDict = __convert_inventory_URL_2_dict__(request)
        error_msg = __check_consignment_in_balance_input__(request, inventoryDict, supplier)
        if error_msg:
            return render_to_response('consignment_in_balance_form.html',{'form': ConsignmentInBalanceForm, 'action':'/consignment/in/balance/confirm/', 'error_msg': error_msg})            
        return HttpResponseRedirect('/report/consignment/in/balance/')

        
def QueryBill(request, displayPage, billID):    
    list_per_page = 25
    if displayPage == 'bill':
        list_per_page = 25
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
    user = request.user
    return render_to_response(displayPage+".html",{'bill': bill, 'outStockRecordset':outStockRecordset, 'company': company, 'user': user, 'form':VoidBillForm()}, context_instance=RequestContext(request))
        
def QueryInventory(request, inStockBatchID, error_msg = None):    
    list_per_page = 25
    inStockBatch = InStockBatch.objects.get(pk=inStockBatchID)
    resultSet = InStockRecord.objects.filter(inStockBatch = inStockBatch)
    paginator = Paginator(resultSet, list_per_page) # Show 25 contacts per page    
    page = request.GET.get('page','1')
    try:
        inStockRecordSet = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        inStockRecordSet = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        inStockRecordSet = paginator.page(paginator.num_pages)
    total_qty = 0    
    for inStockRecord in inStockRecordSet.object_list:
        total_qty += inStockRecord.quantity
    company = Company.objects.all()[0]    
    if not error_msg:
        error_msg = ""
    return render_to_response('inventory_result.html',{'inStockBatch': inStockBatch , 'total_qty': total_qty, 'inStockRecordset': inStockRecordSet, 'error_msg': error_msg})

def __count_product_stock__(starttime, endtime, stockRecords, product):
    summary = [0, 0, 0, 0] #  statistic less than starttime, statistic fall in time, total statistic, cost
    for stockRecord in stockRecords:
        if stockRecord.create_at < starttime:
            summary[0] = summary[0] + stockRecord.quantity
        elif stockRecord.create_at > starttime and stockRecord.create_at < endtime:
            summary[1] = summary[1] + stockRecord.quantity
        summary[2] = summary[2] + stockRecord.quantity    
        if hasattr(stockRecord, 'unit_sell_price'): # that mean this is OutStockRecord
            summary[3] = summary[3] +  stockRecord.cost
        else: # that mean this is InStockRecord
            summary[3] = summary[3] + ( stockRecord.cost * stockRecord.quantity) 
    logger.debug("Product '%s' quantity count by %s ~ %s, result: %s, %s, %s, %s", product.name, starttime, endtime, summary[0], summary[1], summary[2], summary[3] )
    return summary 
     
#def __count_inventory_stock__(starttime, endtime, product):
#    result = []
#    inStockSummary = []
#    outStockSummary = []
#    inStockRecords = InStockRecord.objects.filter(product = product)
#    outStockRecords = OutStockRecord.objects.filter(product = product)
#    inStockSummary = __count_product_stock__(starttime, endtime, inStockRecords, product)
#    outStockSummary = __count_product_stock__(starttime, endtime, outStockRecords, product)
#    # count old stock record
#    old_inStock = inStockSummary[0]
#    old_outStock = outStockSummary[0]
#    old_Stock = old_inStock - old_outStock
#    # logger.debug("the product '%s' stock before '%s', InStock: '%s', OutStock:'%s', Balance: '%s'", product.name, starttime, old_inStock, old_outStock, old_Stock)
#    # count current stock record
#    current_inStock = inStockSummary[1]
#    current_outStock = outStockSummary[1]
#    current_Stock = current_inStock - current_outStock    
#    #logger.debug("the product '%s' stock fall in: '%s' ~ '%s', InStock: '%s', OutStock:'%s', Balance: '%s'", product.name, starttime, endtime, current_inStock, current_outStock, current_Stock)
#    # count all stock record
#    total_inStock = inStockSummary[2]
#    total_outStock = outStockSummary[2]
#    total_Stock = total_inStock - total_outStock    
#    #logger.debug("the product '%s' total stock, InStock: '%s', OutStock:'%s', Balance: '%s'", product.name, total_inStock, total_outStock, total_Stock)
#    # count all stock cost
#    cost_inStock = inStockSummary[3]
#    cost_outStock = outStockSummary[3]
#    cost_Stock = cost_inStock - cost_outStock    
#    #cost_Stock = round(cost_Stock, 2)
#    logger.debug("the product '%s' cost stock, InStock: '%s', OutStock:'%s', Balance: '%s'", product.name, cost_inStock, cost_outStock, cost_Stock)
#    result.append(product.name)
#    result.append(product.description)
#    result.append(old_Stock)
#    result.append(current_inStock)
#    result.append(current_outStock)
#    result.append(total_Stock)
#    result.append(cost_Stock)
#    logger.debug("Product: '%s' count: '%s' ", product.name, result)
#    return result

def CountInventory(request):
    startDate = request.GET.get('start_date','')
    endDate = request.GET.get('end_date','')
    if startDate == '' or endDate == '':
        startDate = str(date.min)
        endDate = str(date.max)
    startDate = startDate+" 00:00:00"
    endDate = endDate+" 23:59:59"
    logger.debug("%s", startDate)
    products = Product.objects.filter(Q(active=True)).order_by("name")
    list = []
    for product in products:
        stockCost = None
        try:
            stockCost = StockCost.objects.get(product=product)
        except StockCost.DoesNotExist:
            BarnMouse(product)
            stockCost = StockCost.objects.get(product=product)
        if stockCost.qty == 0:
            continue
        result = []
        result.append(product.name)
        result.append(product.description)
        result.append(0) #old_Stock
        result.append(0) #current_inStock
        result.append(0) # current_outStock
        result.append(stockCost.qty)
        result.append(stockCost.on_hand_value)
        result.append(stockCost.avg_cost)        
        list.append(result) 
#        list.append(__count_inventory_stock__(starttime, endtime, product)) 
    return render_to_response('stock_take.html',{'stockList': list, 'dateRange': str(startDate)+" to "+str(endDate)}, )
    
"""
    auto-complete view start
"""
def __autocomplete_wrapper__(querySet, filter):
    logger.debug("wraping querySet count: '%s', into autocomplete format %s ", len(querySet), filter)
    list = ''
    for result in querySet:
        string = filter(result) + "\n"
        list = list + string
        logger.debug("wrapper str: '%s'", string)
    token = list.split('\n')
    token.sort(cmp=lambda x1, x2: len(x1)- len(x2))
    list = '\n'.join(token)
    return list

def _str_2_int(string):
    try:
        return int(string)
    except ValueError:
        return -1    

def DepositList(request):
    keyword = request.GET.get('q', "")
    logger.debug("search Deposit list by keyword: %s", keyword)
    
    querySet = __search__(Deposit, Q(customer__name__contains=keyword)|Q(refBill=keyword)|Q(pk=_str_2_int(keyword)))
    list = __autocomplete_wrapper__(querySet, lambda model: str(model.pk))    
    return HttpResponse(list.encode("utf-8"), mimetype="text/plain")

def ServiceList(request):
    keyword = request.GET.get('q', "")
    logger.debug("search Service list by keyword: %s", keyword)
    
    querySet = __search__(Bill, Q(refbill__contains=keyword)|Q(customer__name__contains=keyword))
    list = __autocomplete_wrapper__(querySet, lambda model: str(model.pk))    
    return HttpResponse(list, mimetype="text/plain")

def RepairList(request):
    keyword = request.GET.get('q', "")
    logger.debug("search Repair list by keyword: %s", keyword)
    
    querySet = __search__(ExtraCost, Q(mode="repair") & Q(status = "Incomplete") & Q(active = True) & (Q(key__contains=keyword)|Q(refBill=keyword)|Q(pk=_str_2_int(keyword))))
    list = __autocomplete_wrapper__(querySet, lambda model: str(model.key))    
    return HttpResponse(list, mimetype="text/plain")

def CustomerList(request):
    keyword = request.GET.get('q', "")
    logger.debug("search Customer list by keyword: %s", keyword)
    querySet = __search__(Customer, Q(name__contains=keyword)|Q(customer_code__contains=keyword))
    list = __autocomplete_wrapper__(querySet, lambda model: model.name)    
    return HttpResponse(list, mimetype="text/plain")
    
def SupplierList(request):
    keyword = request.GET.get('q', "")
    logger.debug("search supplier list by keyword: %s", keyword)
    querySet = __search__(Supplier, Q(name__contains=keyword)|Q(supplier_code__contains=keyword))
    list = __autocomplete_wrapper__(querySet, lambda model: model.name)    
    return HttpResponse(list, mimetype="text/plain")
    
def ProductList(request):    
    keyword = request.GET.get('q', "")
    logger.debug("search product list by keyword: %s", keyword)
    mode = request.GET.get('mode','purchase')
    if mode == 'pawning':        
        serialNoQuerySet = __search__(SerialNo, Q(serial_no__contains=keyword) & Q(active__exact=True))
        serialNoList = __autocomplete_wrapper__(serialNoQuerySet, lambda model: model.serial_no)        
        list = serialNoList
        return HttpResponse(list, mimetype="text/plain")
    else:
        productQuerySet = __search__(Product, Q(barcode__contains=keyword)|Q(name__contains=keyword)).order_by("name")
        productList = __autocomplete_wrapper__(productQuerySet, lambda model: model.name)        
        
        serialNoQuerySet = __search__(SerialNo, Q(serial_no__contains=keyword) & Q(active__exact=True)).exclude(inStockRecord__inStockBatch__mode__exact='pawning')
        serialNoList = __autocomplete_wrapper__(serialNoQuerySet, lambda model: model.serial_no)        
        list = productList+serialNoList
        return HttpResponse(list, mimetype="text/plain")    
        
    
    productQuerySet = __search__(Product, Q(barcode__contains=keyword)|Q(name__contains=keyword))
    productList = __autocomplete_wrapper__(productQuerySet, lambda model: model.name)        

    serialNoQuerySet = __search__(SerialNo, Q(serial_no__contains=keyword) & Q(active__exact=True))
    serialNoList = __autocomplete_wrapper__(serialNoQuerySet, lambda model: model.serial_no)        
    list = productList+serialNoList
    return HttpResponse(list, mimetype="text/plain")
	
def ProductNameSearch(request):
    keyword = request.GET.get('q',"")
    logger.debug("search product name by keyword:%s",keyword)
    product = __search__(Product,Q(name__contains = keyword))
    list = __autocomplete_wrapper__(product,lambda model: model.name)
    return HttpResponse(list,mimetype="text/plain")

def ProductNameInfo(request,query):
    logger.debug(" search product name by keyword: %s",query)    
    productSet = __search__(Product, Q(name__contains= query))

    json = __json_wrapper__(productSet)
    return HttpResponse(json, mimetype="application/json")
   
def PaymentList(request):    
    keyword = request.GET.get('q', "")
    logger.debug("sarch payment list by keyword: %s", keyword)
    customerQuerySet = __search__(Customer, Q(name__contains=keyword))
    list = __autocomplete_wrapper__(customerQuerySet, lambda model: model.name)        
    paymentQuerySet = __search__(Payment, Q(type__exact=keyword))
    list += __autocomplete_wrapper__(paymentQuerySet, lambda model: str(model.pk))        
    return HttpResponse(list, mimetype="text/plain")    

def IMEIList(request):    
    keyword = request.GET.get('q', "")
    logger.debug("sarch imei list by keyword: %s", keyword)
    serialNoSet = __search__(SerialNo, Q(serial_no__contains=keyword))
    if serialNoSet:
        list = __autocomplete_wrapper__(serialNoSet, lambda model: model.serial_no)
    return HttpResponse(list, mimetype="text/plain")        
"""
    auto-complete view end
"""

def CategoryInfo(request):
    categorys = Category.objects.all()
    brands = Brand.objects.all()
#    types = Type.objects.all()
    categorys_str = __json_wrapper__(categorys).replace("[","").replace("]","")
    brands_str = __json_wrapper__(brands).replace("[","").replace("]","")
#    types_str = __json_wrapper__(types).replace("[","").replace("]","")
#    json = "["+categorys_str+", "+brands_str+", "+types_str+"]"
    json = "["+categorys_str+", "+brands_str+"]"
    return HttpResponse(json, mimetype="application/json")

def __search__(models, query):
    logger.debug("Search Object: %s by query: %s", models.__name__, query)
    modelsSet = models.objects.filter(query)
    logger.debug("Search Result: %s ", str(modelsSet.count()))
    return modelsSet
    
def ProductInfo(request, query):
    if '<' in query:
        query = query.split('<')[0]
    logger.info("query product info by query: %s " % query)
    # serialNoSet = SerialNo.objects.filter(Q(serial_no__contains=query))
    try:
        #serialNo = SerialNo.objects.get(serial_no=query)
        serialNo = SerialNo.objects.get(serial_no=query)
        owl = BarnOwl()
        if serialNo:
            logger.info("SerialNo '%s' Found!! entry serial-no process flow." % str(serialNo.serial_no))
            product = serialNo.inStockRecord.product
            product.cost = owl.Cost(product,serialNo)
            serial_no = serialNo.serial_no
            productSet = []
            productSet.append(product)
            json = __json_wrapper__(productSet)
            #newJson = json.replace("\"pk\": "+str(product.pk),"\"pk\": " + "\""+serial_no+"\"")
            newJson = json.replace("\"pk\"","\"imei\": " + "\""+serial_no+"\", \"pk\"")
            logger.debug("Json: %s" % newJson)
            return HttpResponse(newJson, mimetype="application/json")    
    except SerialNo.DoesNotExist:
        logger.info("SerialNo '%s' Not Found!! try search product barcode and name " % query)
    productSet = __search__(Product, (Q(active = True)&(Q(barcode__exact=query)|Q(name__exact=query))))
    json = __json_wrapper__(productSet)
    return HttpResponse(json, mimetype="application/json")

    
def ProductInventory(request, productID, serial=None):
    logger.info("check product: '%s'  inventory" % productID)
    product = Product.objects.get(pk=productID)
    mouse = None
    if product.algo.name == Algo.PERCENTAGE:
        mouse = MickyMouse(product)
    else:
        mouse = BarnMouse(product)
    qty = mouse.QTY(serial)
    json = "[{\"inventory\":"+str(qty)+"}]"
    return HttpResponse(json, mimetype="application/json")

def ProductRealCost(request, productID, serial=None):
    logger.info("check product: '%s'  inventory" % productID)
    product = Product.objects.get(pk=productID)
    owl = BarnOwl()
    cost = owl.Cost(product)
    json = "[{\"Cost\":"+str(cost)+"}]"    
    return HttpResponse(json, mimetype="application/json")
    
def __json_wrapper__(querySet):
    if len(querySet) == 0:
        logger.debug("queryset count is 0")
        return '[]'
    json = serializers.serialize("json",  querySet , use_natural_keys=True)
    return json

def CustomerInfo(request, query):
    logger.info("get customer info by keyword: %s " , query)
    customerSet = __search__(Customer, Q(name__contains=query))
    json = __json_wrapper__(customerSet)
    return HttpResponse(json, mimetype="application/json")        
    
def SupplierInfo(request, query):
    logger.info("get supplier info by keyword: %s " , query)
    supplierSet = __search__(Supplier, Q(name__contains=query)|Q(supplier_code__contains=query))
    json = __json_wrapper__(supplierSet)
    return HttpResponse(json, mimetype="application/json")            

def PaymentInfo(request, type, query):
    logger.info("get '%s' payment info by keyword: %s " , type, query)
    payments = __search__(Payment, (Q(bill__customer__name__exact=query) & Q(type__exact=type)))
    json = __json_wrapper__(payments.order_by("-create_at"))
    return HttpResponse(json, mimetype="application/json")

def GadaiList(request):
    logger.info("gaidai query %s:")
    keyword = request.GET.get('q',"")
    gadaiQuerySet = __search__(InStockBatch,Q(supplier__name__contains = keyword)|Q(refBill_no__contains = keyword))
    list = __autocomplete_wrapper__(gadaiQuerySet, lambda model: str(model.pk))
    gadaiStatusQuerySet = __search__(SerialNo, Q(serial_no__contains = keyword)&Q(inStockRecord__inStockBatch__mode__exact='pawning'))
    list +=__autocomplete_wrapper__(gadaiStatusQuerySet,lambda model:str(model.pk))
    return HttpResponse(list,mimetype="text/plain")
	
def GadaiInfo(request,query):	
    logger.info("gaidai query %s:",query)
    gadai = __search__(InStockBatch,(Q(supplier__name__contains = query)))
    if gadai.count() == 0:
        serial = SerialNo.objects.get(serial_no = query)
        gadai = [serial.inStockRecord.inStockBatch]
    else:
        gadai = gadai.order_by("-create_at")
    json =__json_wrapper__(gadai)
    return HttpResponse(json, mimetype="application/json")
    
def VoidBillList(request):
    keyword = request.GET.get('q',"")
    voidBillQuerySet = __search__(Bill,(Q(reason__contains = keyword)))
    list = __autocomplete_wrapper__(voidBillQuerySet, lambda model:str(model.reason))
    return HttpResponse(list,mimetype="text/plain")

def VoidBillInfo(request,query):
    logger.debug("voidbill : %s",query)
    void_bill = __search__(Bill, (Q(active = False)&Q(reason__contains = query)))
    json = __json_wrapper__(void_bill.order_by("-create_at"))
    return HttpResponse(json, mimetype="application/json")
	
def CloseCounterList(request):
    keyword = request.GET.get('q',"")
    logger.debug("keyword is :%s",keyword)
    #closeCounterQuerySet = __search__(Counter,Q(user__username__contains = keyword))
    #logger.debug("closeCounterQuerySet :%s ",closeCounterQuerySet.count())
    #list = __autocomplete_wrapper__(closeCounterQuerySet,lambda model:str(model.pk))
    
    return HttpResponse("",mimetype="text/plain")
	
def CloseCounterInfo(request,query):
    close_counter = __search__(Counter,Q(user__username__contains = query ))
    json = __json_wrapper__(close_counter.order_by("-create_at"))
    return HttpResponse(json, mimetype="application/json")
    

def DepositInfo(request, query):
    logger.info("get deposit info by keyword: %s " , query)
    deposits = __search__(Deposit, (Q(customer__name__contains=query) | Q(refBill = query) | Q(pk=_str_2_int(query)) ))
    json = __json_wrapper__(deposits.order_by("-create_at"))
    return HttpResponse(json, mimetype="application/json")                

def ServiceInfo(request, query):
    logger.info("get Service job info by keyword: %s " , query)
#    services = __search__(ServiceJob, (Q (imei = query) | Q(customer__name__contains=query) | Q(refBill = query) | Q(pk=_str_2_int(query)) ))
    #querySet = __search__(Bill, Q(refbill__contains=query)|Q(customer__name__contains=query))
    querySet = __search__(Bill, Q(pk__exact=query))
    json = __json_wrapper__(querySet.order_by("-create_at"))
    return HttpResponse(json, mimetype="application/json")                

def RepairInfo(request, query):
    logger.info("get Repair job info by keyword: %s " , query)
    repairs = __search__(ExtraCost, Q(mode="repair") & Q(status = "Incomplete") & Q(active = True) & (Q(key__contains=query)|Q(refBill=query)|Q(pk=_str_2_int(query))))
    json = __json_wrapper__(repairs.order_by("-create_at"))
    return HttpResponse(json, mimetype="application/json")                

def RepairBinding(request, imei, billID):
    logger.info("Repair binding Bill: '%s' , IMEI: '%s' " , billID, imei)
    extraCosts = ExtraCost.objects.filter(key=imei)
    bill = Bill.objects.get(pk=int(billID))
    for extraCost in extraCosts:
        extraCost.bill = bill
        extraCost.save()
        logger.debug("extraCost: '%s' binding with bill: '%s'", extraCost.pk, bill.pk)
    owl = BarnOwl()
    owl.RecalcBill(bill.pk)
    return HttpResponse("OK", mimetype="plain/text")      

def ExtraCostList(request, billID):
    logger.info("get ExtraCost List by BillID: %s " , billID)
    bill = Bill.objects.get(pk = int(billID))
    costs = ExtraCost.objects.filter(bill = bill)
    json = __json_wrapper__(costs.order_by("-create_at"))
    return HttpResponse(json, mimetype="application/json")                

def __find_payment_by_serial_no__(serial):
    ans = []
    outStockRecords = OutStockRecord.objects.filter(serial_no = serial).order_by("-create_at")
    for outStockRecord in outStockRecords:
        bill = outStockRecord.bill
        payments = Payment.objects.filter(bill=bill)
        if payments.count() != 0:
            payment = payments.order_by("-create_at")[0]
            logger.debug("found Serial: '%s' bill: '%s', payment: '%s' ", serial.serial_no, bill.pk, payment.pk)
            ans.append(payment)
        else:
            logger.debug("No payment found on Serial: '%s' bill: '%s'", serial.serial_no, bill.pk)
    return ans

def __find_instockBatch_by_serial_no__(serial):
    serialNoMappings = SerialNoMapping.objects.filter(serial_no = serial)
    result = set()
    for serialNoMapping in serialNoMappings:
        result.add(serialNoMapping.inStockRecord)
    return result

def ImeiInfo(request, imei):
    logger.info("get imei: '%s' info " , imei)
    serial = SerialNo.objects.get(serial_no = imei)
    result = __find_payment_by_serial_no__(serial)
    result.extend(__find_instockBatch_by_serial_no__(serial))
    json = __json_wrapper__(result)
    return HttpResponse(json, mimetype="application/json")                    
    
def PaymentInfoByPK(request, pk):
    logger.info("get payment info by PK: %s " , pk)
    payments = __search__(Payment, Q(pk=pk))
    json = __json_wrapper__(payments.order_by("-create_at"))
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
#            type_pk = request.GET.get('type','-1')
            category = None
            brand = None
            type = None
            try:
                category = Category.objects.get(category_name=category_pk)
                brand = Brand.objects.get(pk=int(brand_pk))
#                type = Type.objects.get(pk=int(type_pk))
            except Category.DoesNotExist:
                logger.error("ProductSave fail: Category.DoesNotExist")
                return HttpResponseRedirect('/product/search/')    
            except Brand.DoesNotExist:
                logger.error("ProductSave fail: Brand.DoesNotExist")
                return HttpResponseRedirect('/product/search/')    
#            except Type.DoesNotExist:
#                logger.error("ProductSave fail: Type.DoesNotExist")
                #return HttpResponseRedirect('/product/search/')                    
            product.category = category
            product.brand = brand
            product.type = type
            product.active=True
            product.save()
            logger.info("ProductSave success")
            return HttpResponseRedirect('/product/search/')
        else:
            logger.error("ProductSave fail: Form Validate faile")
            return HttpResponseRedirect('/product/search/')

def ProductUpdateView(request, productID):
    product = Product.objects.get(pk=productID)
    form = ProductForm(instance=product)
    barcode = product.barcode
    return render_to_response('product_form.html',{'form': form, 'submit_form':'/product/save/'+productID, 'form_title': 'Update Product', 'barcode': barcode, 'product': product})

def PrintBarcode(request, barcode):    
    return render_to_response('printBarcode.html',{'barcode': barcode})
    
def ProductDelete(request):
    if request.method == 'GET':
        delete_products = request.GET.getlist('delete_product[]')
        for name in delete_products:
            logger.debug("Delete product '%s'", name)
            products = Product.objects.filter(name=name)
            for product in products:
                product.active = False
                product.save()
    return HttpResponseRedirect('/product/search/')        

#def InStockRecordSave(request):
#    if request.method == 'GET':
#        form = InStockRecordForm(request.GET)
#        if form.is_valid():
#            inStockRecord = form.save(commit = True)
#            inStockRecord.save()
#            return HttpResponseRedirect('/in_stock_record/search/')
#        else:
#            return HttpResponseRedirect('/in_stock_record/create/')

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
        logger.error('inStockRecordSet is None')
        return 0;
    if inStockRecordSet.count() == 0:
        logger.warn('no inStockRecord found')
        return 0;        
    product = inStockRecordSet[0].product
    product_name = product.name
    sellCount = 0
    serial = SerialNo.objects.filter(inStockRecord__product = product)
    if serial.count() == 0:
        logger.debug("Product '%s' not base on serial_no, use FIFO", product_name)
        if outStockRecord is not None:
            sellCount = outStockRecord.sell_index
        else:
            logger.error("Input parameter error, outStockRecord is None, return 0")
            return 0
    else:
        logger.debug("Product '%s' base on serial_no, use Serial count", product_name)
        stockCount = serial.filter(active = True).count()
        logger.debug("Inventory '%s' count: %s", product_name, stockCount)
        return stockCount
    for inStockRecord in inStockRecordSet:
        count = count + inStockRecord.quantity
    count = count - sellCount
    logger.debug("Inventory '%s' count: %s", inStockRecord.product.name, count)
    return count

@permission_required('kernal.change_counter', login_url='/accounts/login/')
def CounterUpdate(request):
    counterID =  int(request.GET.get('counterID', ""))
    hermes = Hermes()
    hermes.ReCalcCounterByPK(counterID)
    return HttpResponseRedirect('/counter/close/') 

def __check_available_inStock_qty__(inStockRecord):
    disableInStockRecords = DisableStock.objects.filter(inStockRecord = inStockRecord)
    availableQTY = 0
    unAvailableQTY = 0
    if disableInStockRecords.count() != 0:
        availableQTY = inStockRecord.quantity - disableInStockRecords[0].quantity
        unAvailableQTY = disableInStockRecords[0].quantity
    else:
        availableQTY = inStockRecord.quantity
        unAvailableQTY = 0
    logger.debug("inStockRecord '%s' recornized, available '%s', unAvailable: '%s' ", inStockRecord.pk, availableQTY, unAvailableQTY)        
    return [availableQTY, unAvailableQTY]


	
#def __count_sales_index__(product, sales_index, quantity):
#    logger.debug("Count '%s' sales index, last idx: '%s', QTY: '%s' ", product.pk, sales_index, quantity)
#    inStockRecordSet = InStockRecord.objects.filter(product=product).order_by('create_at')
#    currentQuantity = 0
#    disableCount = 0
#    countdown = quantity
#    for inStockRecord in inStockRecordSet:
#        currentQuantity = currentQuantity + inStockRecord.quantity
#        if sales_index <= currentQuantity:
#            logger.debug("inStockRecord '%s' match, processing...", inStockRecord.pk)
#            qtys = __check_available_inStock_qty__(inStockRecord)
#            availableQty = qtys[0]
#            disableCount += qtys[1]
#            countdown = countdown - availableQty
#            if countdown <= 0:
#                break
#        else:
#            logger.debug("inStockRecord '%s' saled, skip", inStockRecord.pk)
#    new_idx = sales_index + quantity + disableCount
#    logger.debug("sales idx : '%s', Disable Stock: '%s' ", new_idx, disableCount)
#    return new_idx
    
#def _update_outStockRecord_set(bill):
#    outStockRecordSet = bill.outstockrecord_set.all()
#    totalProfit = 0
#    for outStockRecord in outStockRecordSet:
#        if outStockRecord.serial_no != None:
#            product = outStockRecord.serial_no.inStockRecord.product
#            totalCost = outStockRecord.serial_no.inStockRecord.cost
#            outStockRecord.sell_index = -1
#            outStockRecord.serial_no.active = False
#            outStockRecord.serial_no.save()
#            logger.info("Get price by SerialNo: %s ",totalCost);
#        else:
#            product = outStockRecord.product
#            sales_index = __find_SalesIdx__(product)
#            totalCost = __find_cost__(sales_index, outStockRecord)
#            outStockRecord.sell_index = __count_sales_index__(product, sales_index, outStockRecord.quantity) 
#            logger.info("Get cost by FIFO, sales index: %s ,quantity: %s, sell_index: %s",sales_index , outStockRecord.quantity, outStockRecord.sell_index);
#        outStockRecord.profit = outStockRecord.amount - totalCost
#        outStockRecord.cost = totalCost
#        outStockRecord.save()
#        totalProfit = totalProfit + outStockRecord.profit
#        logger.info("OutStockRecord: %s profit: %s, product: %s, sales index: %s" , outStockRecord.pk , outStockRecord.profit, outStockRecord.product.name, outStockRecord.sell_index)
#    bill.profit = totalProfit
#    logger.info("Bill: %s total profit: %s" , bill.pk , bill.profit)
#    bill.save()

def DeleteBill(request):
    logger.info("Void Bill")
    pk = request.GET.get('bill_id','')
    owl = BarnOwl()    
    owl.DeleteBill(pk, request.GET.get("reason",""))
    owl.RecalcBill(pk)
    
    return HttpResponseRedirect('/report/daily/')
    
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
        if len(users) == 0:
            continue
        salesReport[product] = users
    
    return render_to_response('report_personalSales.html',{'session': request.session,  'salesReport': salesReport, 'dateRange': str(startDate)+" to "+str(endDate)}, )
        
def _build_users_sold_dict(product, startDate, endDate):
    #outStockRecordSet = OutStockRecord.objects.filter(product=product)
    outStockRecordSet = OutStockRecord.objects.filter(product=product).filter(create_at__range=(startDate,endDate)).filter(Q(bill__mode = "cash")|Q(bill__mode = "invoice"))
    users = {}
    for outStockRecord in outStockRecordSet:
        user = outStockRecord.bill.sales_by
        if user not in users:
            logger.info("create %s in users" % user )
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
        logger.debug("product: '%s' outstockrecord: '%s' profit: '%s', total: profit: '%s'", outStockRecord.product.pk, outStockRecord.pk, outStockRecord.profit, users[user][0].profit)
        users[user][0].amount = users[user][0].amount + outStockRecord.amount
        users[user].append(outStockRecord)
        logger.info("add %s's  outStockRecord" % user )
    return users
        
#def __find_SalesIdx__(product):
#    sales_index = 0
#    #find last time sell record
#    lastOutStockRecordSet = OutStockRecord.objects.filter(Q(product=product)&(Q(type="sales")|Q(type="ConsignmentOutSales")))
#    if lastOutStockRecordSet.count() != 0:
#        lastOutStockRecord = lastOutStockRecordSet.order_by('create_at')[0]
#        sales_index = lastOutStockRecord.sell_index
#        logger.info("Product: "+product.name+"'s sales_index: " + str(sales_index))
#    #logger.info("Product: "+product.name+"'s sales_index: " + str(sales_index))
#    return sales_index        

#def __find_cost__(salesIdx, outStockRecord):
#    if outStockRecord.product.barcode == "FOC":
#        logger.debug("FOC product found, cost == 0 ")
#        return 0
#    product = outStockRecord.product
#    sales_index = 0
#    #find last time sell record
#    historyCost = []
#    productQuantity = []
#    inStockRecordSet = InStockRecord.objects.filter(product=product).order_by('create_at')
#    currentQuantity = 0
#    salesIdxPosision = -1
#    idx = 0
#    for inStockRecord in inStockRecordSet:
#        historyCost.append(inStockRecord.cost)
#        currentQuantity = currentQuantity + inStockRecord.quantity
#        productQuantity.append(currentQuantity)
#        if salesIdx <= currentQuantity and salesIdxPosision == -1:
#            salesIdxPosision = idx
#        idx = idx + 1
#    totalproductCost = 0
#    cost = historyCost[salesIdxPosision]
#    for i in range(outStockRecord.quantity):
#        logger.error("%s, %s",(salesIdx + i + 1) , productQuantity[salesIdxPosision])        
#        if (salesIdx + i + 1) > productQuantity[salesIdxPosision]:
#            if salesIdxPosision >= len(productQuantity):
#                logger.error("salesIdxPosision over limit: %s" % salesIdxPosision )
#                pass
#            else:
#                salesIdxPosision = salesIdxPosision + 1
#        if salesIdxPosision >= len(historyCost):
#            salesIdxPosision = len(historyCost)-1
#        cost = historyCost[salesIdxPosision]
#        logger.info("salesIdxPosision: %s", salesIdxPosision)
#        logger.info("Bill %s, %s cost:  %s  " , outStockRecord.bill.pk, product.name , cost)
#        totalproductCost = totalproductCost + cost
#    return totalproductCost