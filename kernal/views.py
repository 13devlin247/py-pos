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
from pos.kernal.models import ConsignmentOutDetail
from pos.kernal.models import ConsignmentInDetail
from pos.kernal.models import InStockBatchForm
from pos.kernal.models import ConsignmentInBalanceForm
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
        dict[pk][attr]= value
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
        logger.warn("Supplier '%s' not found, auto create supplier", supplier_name)    
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
        cost = float(inventoryDict [pk]['cost'][0])
        quantity = int(inventoryDict [pk]['quantity'] [0])
        inStockRecord = InStockRecord()
        inStockRecord.inStockBatch = inStockBatch
        inStockRecord.barcode = pk
        inStockRecord.product = product
        inStockRecord.cost = cost
        inStockRecord.quantity = quantity
        inStockRecord.status = status
        inStockRecord.save()
        logger.debug("instock '%s' build success, cost: '%s', quantity:'%s' ", product.name, inStockRecord.cost, inStockRecord.quantity)
        inStockRecords.append(inStockRecord)
    return inStockRecords

def __retriever_original_cost_by_serial_no__(product, dict):
    for value in dict[str(product.pk)] :
        if 'serial-' in value:
            serialNO = dict[str(product.pk)][value] 
            if serialNO == '':
                continue
            # look up from serial no table
            try:
                serial = SerialNo.objects.get(serial_no = serialNO)
                inStockRecord.cost = serial.inStockRecord.cost
                inStockRecord.save()
                logger.debug("replace 2rd InStockRecord.cost with serial no '%s''s original cost '%s'", serialNO, inStockRecord.cost)
            except SerialNo.DoesNotExist:
                logger.error("serial no: '%s' not found", serialNO)    


    

    
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
        inventoryDict = __convert_inventory_URL_2_dict__(request)
        logger.debug("inventory dict build success: %s", inventoryDict)
        inStockBatch = __build_instock_batch__(request)
        
        inStockRecords = __build_instock_records__(inStockBatch, inventoryDict, inStockBatch.mode)
        serials = __build_serial_no__(request, inStockRecords, inventoryDict)  
        logger.info("InventoryConfirm finish")
        if inStockBatch.mode == "Consignment_IN":
            logger.debug("Consignment IN batch found, build consignemnt details.")
            __build_consignment_in_by_instockrecords__(inStockRecords, serials)
        else:
            logger.debug("InStock mode: %s", inStockBatch.mode)
        return HttpResponseRedirect('/inventory/result/'+str(inStockBatch.pk))
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
            
        salesDict[pk] [attr]= value
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

def __build_payment__(request, bill):    
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
    elif salesMode == "Consignment":
        payment.term = "Consignment"
        payment.type = "Consignment"
        payment.status = "Incomplete"    
    elif salesMode == "Consignment_in_balance":
        payment.term = "Consignment_in_balance"
        payment.type = "Consignment_in_balance"
        payment.status = "Incomplete"    
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
            logger.info("Foc product found !! : %s " % barcode)    
            
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
def SalesConfirm(request):
    salesDict = {}
    if request.method == 'GET':
        # check Counter 
        counters = None
        counters = Counter.objects.filter(active=True).order_by('-create_at')
        if counters.count() == 0:
            logger.warn("Can not found 'OPEN' Counter, direct to open page")
            return HttpResponseRedirect('/admin/kernal/counter/add/')    
                
        # process Request parameter
        salesDict = __convert_sales_URL_2_dict__(request)
        logger.debug("sales dict: %s" , salesDict)
        customer = __query_customer__(request, 'customer')
        bill = __build_bill__(request, customer, counters[0])
        payment = __build_payment__(request, bill)
        __build_outstock_record__(request, bill, payment, salesDict, 'sales')      
                
        if payment.type == 'Invoice':
            logger.debug("Invoice bill, direct to invoice interface")
            return HttpResponseRedirect('/sales/invoice/'+str(bill.pk))        
        elif payment.type == 'Consignment':
            logger.debug("Consignment bill, direct to Consignment interface")
            return HttpResponseRedirect('/sales/consignment/'+str(bill.pk))                    
        else:
            logger.debug("Cash sales bill, direct to Recept interface")
            return HttpResponseRedirect('/sales/bill/'+str(bill.pk))        

def ConsignmentOutBalance(request):
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
        logger.info("InventoryConfirm finish")
        return HttpResponseRedirect('/inventory/result/'+str(inStockBatch.pk))

def __build_Consignment_In_index__(supplier, outStockRecords):
    for outStockRecord in outStockRecords:
        product = outStockRecord.product
        out_qty = outStockRecord.quantity
        inStockRecords = InStockRecord.objects.filter(Q(inStockBatch__supplier = supplier)&Q(inStockBatch__mode = 'Consignment_IN')&Q(inStockBatch__status = 'Incomplete')).order_by('create_at')
        for inStockRecord in inStockRecords:
            consignmentInDetail = ConsignmentInDetail.objects.filter(Q(inStockRecord = inStockRecord))[0]
            waiting_balance = consignmentInDetail.quantity - consignmentInDetail.balance
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
        # process Request parameter
        # check Counter 
        counters = None
        counters = Counter.objects.filter(active=True).order_by('-create_at')
        if counters.count() == 0:
            logger.warn("Can not found 'OPEN' Counter, direct to open page")
            return HttpResponseRedirect('/admin/kernal/counter/add/')    
        
        salesDict = __convert_sales_URL_2_dict__(request)
        logger.debug("sales dict: %s" , salesDict)
        customer = __query_customer__(request, 'supplier')
        supplier = __query_supplier__(request, 'supplier')
        bill = __build_bill__(request, customer, counters[0])
        payment = __build_payment__(request, bill)
        outStockRecords = __build_outstock_record__(request, bill, payment, salesDict, 'ConsignmentInBalance')      
        __build_Consignment_In_index__(supplier, outStockRecords)
        
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
            

        
        """
        logger.debug("inventory dict build success: %s", inventoryDict)
        inStockBatch = __build_instock_batch__(request)
        inStockRecords = __build_instock_records__(inStockBatch, inventoryDict)
        __retriever_original_cost__(request, inStockRecords, inventoryDict, customer)  
        serials = __build_serial_no__(request, inStockRecords, inventoryDict)  
        __consignment_out_balance_by_serials_no__(request, serials)
        __close_consignment__(request)
        logger.info("InventoryConfirm finish")
        """        
        return HttpResponseRedirect('/inventory/result/'+str(inStockBatch.pk))

        
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
    

"""
    auto-complete view start
"""
    
def __autocomplete_wrapper__(querySet, filter):
    logger.debug("wraping querySet into autocomplete format %s ", filter)
    list = ''
    for result in querySet:
        list = list + filter(result) + "\n"
    return list

def CustomerList(request):
    keyword = request.GET.get('q', "")
    logger.debug("search Customer list by keyword: %s", keyword)
    querySet = __search__(Customer, Q(name__contains=keyword))
    list = __autocomplete_wrapper__(querySet, lambda model: model.name)    
    return HttpResponse(list, mimetype="text/plain")
    
def SupplierList(request):
    keyword = request.GET.get('q', "")
    logger.debug("search supplier list by keyword: %s", keyword)
    querySet = __search__(Supplier, Q(name__contains=keyword))
    list = __autocomplete_wrapper__(querySet, lambda model: model.name)    
    return HttpResponse(list, mimetype="text/plain")
    
def ProductList(request):    
    keyword = request.GET.get('q', "")
    logger.debug("search product list by keyword: %s", keyword)
    productQuerySet = __search__(Product, Q(barcode__contains=keyword)|Q(name__contains=keyword))
    productList = __autocomplete_wrapper__(productQuerySet, lambda model: model.name)        

    serialNoQuerySet = __search__(SerialNo, Q(serial_no__contains=keyword) & Q(active__exact=True))
    serialNoList = __autocomplete_wrapper__(serialNoQuerySet, lambda model: model.serial_no)        
    list = productList+serialNoList
    return HttpResponse(list, mimetype="text/plain")

def PaymentList(request):    
    keyword = request.GET.get('q', "")
    logger.debug("sarch payment list by keyword: %s", keyword)
    customerQuerySet = __search__(Customer, Q(name__contains=keyword))
    list = __autocomplete_wrapper__(customerQuerySet, lambda model: model.name)        
    paymentQuerySet = __search__(Payment, Q(type__exact=keyword))
    list += __autocomplete_wrapper__(paymentQuerySet, lambda model: str(model.pk))        
    return HttpResponse(list, mimetype="text/plain")    

"""
    auto-complete view end
"""

def CategoryInfo(request):
    categorys = Category.objects.all()
    brands = Brand.objects.all()
    types = Type.objects.all()
    
    categorys_str = __json_wrapper__(categorys).replace("[","").replace("]","")
    brands_str = __json_wrapper__(brands).replace("[","").replace("]","")
    types_str = __json_wrapper__(types).replace("[","").replace("]","")
    json = "["+categorys_str+", "+brands_str+", "+types_str+"]"
#    json = "["+categorys_str+", "+brands_str+"]"
    return HttpResponse(json, mimetype="application/json")

def __search__(models, query):
    logger.debug("Search Object: %s by query: %s", models.__name__, query)
    modelsSet = models.objects.filter(query)
    logger.debug("Search Result: %s ", str(modelsSet.count()))
    return modelsSet
    
def ProductInfo(request, query):
    logger.info("query product info by query: %s " % query)

    # serialNoSet = SerialNo.objects.filter(Q(serial_no__contains=query))
    try:
        #serialNo = SerialNo.objects.get(serial_no=query)
        serialNo = SerialNo.objects.get(serial_no=query)
        if serialNo:
            logger.info("SerialNo '%s' Found!! entry serial-no process flow." % str(serialNo.serial_no))
            product = serialNo.inStockRecord.product
            product.cost = serialNo.inStockRecord.cost
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
        
    productSet = __search__(Product, (Q(barcode__contains=query)|Q(name__contains=query)))
    json = __json_wrapper__(productSet)
    return HttpResponse(json, mimetype="application/json")
    
def ProductInventory(request, productID):
    
    logger.info("check product: '%s'  inventory" % productID)
    product = Product.objects.get(pk=productID)
    inStockRecordSet = InStockRecord.objects.filter(product=product)
    if inStockRecordSet.count() == 0:
        logger.debug("inStockRecordSet not found")
        return HttpResponse(0, mimetype="application/json")    

    outStockRecordSet = OutStockRecord.objects.filter(product=product)
    outStockRecord = None
    if outStockRecordSet.count() != 0:
        outStockRecord = outStockRecordSet.order_by('-create_at')[0]
        if outStockRecord is None:
            logger.error("'%s' outStockRecord not found", product.name)        
        
    inventoryCount = countInventory(inStockRecordSet, outStockRecord)
    json = "[{\"inventory\":"+str(inventoryCount)+"}]"
    return HttpResponse(json, mimetype="application/json")    

def __json_wrapper__(querySet):
    if len(querySet) == 0:
        logger.debug("queryset count is 0")
        return '[]'
    json = serializers.serialize("json",  querySet)
    return json


def CustomerInfo(request, query):
    logger.info("get customer info by keyword: %s " , query)
    customerSet = __search__(Customer, Q(name__contains=query))
    json = __json_wrapper__(customerSet)
    return HttpResponse(json, mimetype="application/json")        
    
def SupplierInfo(request, query):
    logger.info("get supplier info by keyword: %s " , query)
    supplierSet = __search__(Supplier, Q(name__contains=query))
    json = __json_wrapper__(supplierSet)
    return HttpResponse(json, mimetype="application/json")            

def PaymentInfo(request, type, query):
    logger.info("get '%s' payment info by keyword: %s " , type, query)
    payments = __search__(Payment, (Q(bill__customer__name__exact=query) & Q(type__exact=type)))
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
            type_pk = request.GET.get('type','-1')
            
            category = None
            brand = None
            type = None
            
            
            try:
                category = Category.objects.get(pk=int(category_pk))
                brand = Brand.objects.get(pk=int(brand_pk))
                type = Type.objects.get(pk=int(type_pk))
            except Category.DoesNotExist:
                logger.error("ProductSave fail: Category.DoesNotExist")
                return HttpResponseRedirect('/product/search/')    
            except Brand.DoesNotExist:
                logger.error("ProductSave fail: Brand.DoesNotExist")
                return HttpResponseRedirect('/product/search/')    
            except Type.DoesNotExist:
                logger.error("ProductSave fail: Type.DoesNotExist")
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
    counterID =  request.GET.get('counterID', "")
    
    # count close amount
    counter = Counter.objects.get(pk=counterID)
    bills = Bill.objects.filter(counter=counter)
    totalAmount = counter.initail_amount
    for bill in bills:
        totalAmount = totalAmount + bill.total_price
        logger.info("Calc Bill: %s, %s" , bill.pk, bill.create_at)
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
            logger.info("Get price by SerialNo: %s ",totalCost);
        else:
            product = outStockRecord.product
            sales_index = __find_SalesIdx__(product)
            totalCost = __find_cost__(sales_index, outStockRecord)
            outStockRecord.sell_index = sales_index + outStockRecord.quantity
            logger.info("Get cost by FIFO, sales index: %s ,quantity: %s, sell_index: %s",sales_index , outStockRecord.quantity, outStockRecord.sell_index);
        outStockRecord.profit = outStockRecord.amount - totalCost
        outStockRecord.cost = totalCost
        outStockRecord.save()
        totalProfit = totalProfit + outStockRecord.profit
        logger.info("OutStockRecord: %s profit: %s, product: %s, sales index: %s" , outStockRecord.pk , outStockRecord.profit, outStockRecord.product.name, outStockRecord.sell_index)
    bill.profit = totalProfit
    logger.info("Bill: %s total profit: %s" , bill.pk , bill.profit)
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
        users[user][0].amount = users[user][0].amount + outStockRecord.amount
        users[user].append(outStockRecord)
        logger.info("add %s's  outStockRecord" % user )
    return users

        
def __find_SalesIdx__(product):
    sales_index = 0
    #find last time sell record
    lastOutStockRecordSet = OutStockRecord.objects.filter(product=product)
    if lastOutStockRecordSet.count() != 0:
        lastOutStockRecord = lastOutStockRecordSet.order_by('create_at')[0]
        sales_index = lastOutStockRecord.sell_index
        logger.info("Product: "+product.name+"'s sales_index: " + str(sales_index))
    #logger.info("Product: "+product.name+"'s sales_index: " + str(sales_index))
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
        logger.error("%s, %s",(salesIdx + i + 1) , productQuantity[salesIdxPosision])        
        if (salesIdx + i + 1) > productQuantity[salesIdxPosision]:
            if salesIdxPosision >= len(historyCost):
                logger.error("salesIdxPosision over limit: %s" % salesIdxPosision )
                pass
            else:
                salesIdxPosision = salesIdxPosision + 1
        cost = historyCost[salesIdxPosision]
        logger.info("salesIdxPosision: %s", salesIdxPosision)
        logger.info("Bill %s, %s cost:  %s  " , outStockRecord.bill.pk, product.name , cost)
        totalproductCost = totalproductCost + cost
    
    return totalproductCost
    
def checkCounter(function=None, redirect_field_name=REDIRECT_FIELD_NAME):
    def decorate(view_func):
        logger.error("here we are");
        return function
        
        #return HttpResponseRedirect('/out_stock_record/create/')

def test(request):
    #uid = session.get_decoded().get('_auth_user_id')
    user = None
    if request.session.get('_auth_user_id'):
        user = User.objects.get(pk=request.session.get('_auth_user_id'))
    
    #return render_to_response('CRUDForm.html',{'sessionid':session_key,  'user':user,  })
    return render_to_response('CRUDForm.html',{'session': request.session,  'user': user}, )
