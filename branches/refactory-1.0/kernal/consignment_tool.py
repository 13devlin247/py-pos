from pos.kernal.models import Customer
from pos.kernal.models import Supplier
from pos.kernal.models import ConsignmentOutDetail
from pos.kernal.models import ConsignmentInDetail
from pos.kernal.models import InStockBatch
from pos.kernal.models import Payment 
from django.db.models import Q


from pos.kernal.models import SerialNo
# import the logging library
import logging

logging.basicConfig(
    level = logging.WARN,
    format = '%(asctime)s %(levelname)s %(funcName)s():%(lineno)s %(message)s',
)
# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def __retriever_original_cost_by_FIFO__(consignmentOutDetails, quantity):
    return_quantity = quantity
    total_cost = 0
    counter = 0
    for consignmentOutDetail in consignmentOutDetails:
        logger.debug("calc ConsignmentOutDetail: '%s', date:'%s', ", consignmentOutDetail.pk, consignmentOutDetail.create_at)
        infor = __query_consignment_cost_qty__(consignmentOutDetail)
        cost = infor[0]
        total_cost += cost
        counter = counter + 1
        qty = infor[1]
        if return_quantity < qty:
            consignmentOutDetail.balance = consignmentOutDetail.balance + return_quantity
            consignmentOutDetail.save()
            logger.debug("last quantity match.")
            break
        else: 
            consignmentOutDetail.balance = consignmentOutDetail.quantity
            consignmentOutDetail.save()
            return_quantity = return_quantity - qty  
    if counter == 0:
        logger.warn("no consignment found !! ")
        return 0
    logger.debug("Avg cost: '%s'", (total_cost / counter))
    return total_cost / counter

def __query_customer__(request, textFieldID):
    customerName = request.GET.get(textFieldID, 'Cash')
    customerList = Customer.objects.filter(name=customerName)
    customer = None
    if customerList.count() == 0:
        logger.debug("Customer '%s' not found, auto create cusomer info.")
        customer = Customer()
        customer.customer_code = customerName
        customer.name = customerName
        customer.save()
        logger.debug("Customer build success: %s", customer)
    customer = Customer.objects.filter(name=customerName)[0]
    logger.debug("Customer found: %s", customer)
    return customer
    
def __query_supplier__(request, textFieldID):
    supplierName = request.GET.get(textFieldID, 'Cash')
    supplierList = Supplier.objects.filter(name=supplierName)
    supplier = None
    if supplierList.count() == 0:
        logger.debug("Supplier '%s' not found, auto create supplier info.")
        supplier = Supplier()
        supplier.customer_code = supplierName
        supplier.name = supplierName
        supplier.save()
        logger.debug("Supplier build success: %s", supplier)
    supplier = Supplier.objects.filter(name=supplierName)[0]
    logger.debug("Supplier found: %s", supplier)
    return supplier    

def __consignment_out_balance_by_serials_no__(request, serials):
    logger.debug("balancing by serials no - Consignment Out")
    
    for serial in serials:
        consignmentOutDetails = ConsignmentOutDetail.objects.filter(serialNo = serial)
        if consignmentOutDetails.count() == 0:
            logger.warn("something wrong, serial '%s' not found in consignment", serial)
        else:
            logger.debug("Consignment Out serial '%s' found, balancing 'quantity' and 'balance' ", serial)
            consignmentOutDetail = consignmentOutDetails[0]
            consignmentOutDetail.balance = consignmentOutDetail.quantity
            consignmentOutDetail.save()
    
def __query_consignment_cost_qty__(consignmentOutDetail):
    cost = consignmentOutDetail.outStockRecord.cost / consignmentOutDetail.quantity
    quantity = consignmentOutDetail.quantity - consignmentOutDetail.balance
    logger.debug("consignment '%s' cost: '%s', quantity: '%s' ", consignmentOutDetail.pk, cost, quantity)
    return [cost, quantity]

  
def __close_consignment__(request):
    logger.debug("check and close all balance consignment")
    customer = __query_customer__(request, 'supplier')
    logger.debug("Customer found: %s", customer)
    
    payments = Payment.objects.filter(Q(bill__customer=customer)&Q(type__exact = "Consignment")&Q(status__exact = "Incomplete")).order_by("create_at")
    for payment in payments:
        payment_finish = True
        consignmentOuts = payment.consignmentoutdetail_set.all()
        for consignmentOut in consignmentOuts:
            if consignmentOut.quantity != consignmentOut.balance:
                payment_finish = False
                break
        if payment_finish:
            logger.debug("Consignment '%s' finish, close it", payment.pk)
            payment.status = "Complete"
            payment.save()    

def __query_consignment_qty__(product):
    pass
     
def __is_serial__(dict):
    for key in dict:
        if 'serial-' in key:
            return False
    return True
        
def __check_consignment_in_balance_input__(request, inventoryDict, supplier):
    error_msg = None
    inStockBatchs = InStockBatch.objects.filter(Q(supplier = supplier)&Q(status__exact='Incomplete')&Q(mode__exact='Consignment_IN')).order_by("create_at")
    
    # ####################################### #
    # check condition to prevent error input  #
    # ####################################### #
    
    logger.debug("check incomplete Consignment count '%s'", inStockBatchs.count())
    if inStockBatchs.count() == 0:
        logger.error("No incomplete consigment found by Supplier '%s' ", supplier.name)
        error_msg = "No incomplete consigment found by Supplier '"+supplier.name+"'"
    return error_msg              
        
def __check_consignment_out_balance_input__(request, inventoryDict, customer):
    error_msg = None
    payments = Payment.objects.filter(Q(bill__customer = customer)&Q(status__exact='Incomplete')).order_by("create_at")
    
    # ####################################### #
    # check condition to prevent error input  #
    # ####################################### #
    
    logger.debug("check incomplete Consignment count '%s'", payments.count())
    if payments.count() == 0:
        logger.error("No incomplete consigment found by Customer '%s' ", customer.name)
        error_msg = "No incomplete consigment found by Customer '"+customer.name+"'"
    
    #__query_consignment_cost_qty__(consignmentOutDetail)
    """    
    for key, value in inventoryDict:
        inStockQty = value['quantity']
        consignmentQty = 0
        if __is_serial__(value):
            error_serial = __find_no_match_serial__(inventoryDict)
            if len(error_serial) != 0:
                error_msg = "serial: "
                for serial in error_serial:
                    error_msg += serial + ", "
                error_msg += " not found on Customer '"+customer.name+"' consignment!"   
                return error_msg
            consignmentQty = value['quantity']
        else:
            __use_FIFO__()
        product = Product.objects.get(pk = int(key))
        consignmentQty = __query_consignment_qty__(product)
    """ 
    return error_msg      

def __retriever_original_cost_by_serial_no__(product, dict, inStockRecord):
    for value in dict[str(product.pk)] :
        if 'serial-' in value:
            serialNO = dict[str(product.pk)][value] [0]
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
    
def __retriever_original_cost__(request, inStockRecords, dict, customer):   
    logger.debug("retriever original cost")
    for inRecord in inStockRecords:
        product = inRecord.product
        serials = SerialNo.objects.filter(inStockRecord__product=product)
        # if product cost count by FIFO
        if serials.count() == 0:
            logger.debug("serials not found, use FIFO algo")
            consignmentOutDetails = ConsignmentOutDetail.objects.filter(Q(payment__bill__customer = customer)&Q(payment__status__exact='Incomplete')).order_by("create_at")
            cost = __retriever_original_cost_by_FIFO__(consignmentOutDetails, inRecord.quantity)
            inRecord.cost = cost
            inRecord.save()
        # if product cost count by Serial No
        else:
            __retriever_original_cost_by_serial_no__(product, dict, inRecord)
    return inStockRecords                    

def __find_serial__(inStockRecord, serials):
    for serial in serials:
        if serial.inStockRecord == inStockRecord:
            return serial
    return None
    
def __build_consignment_in_by_instockrecords__(inStockRecords, serials):        
    for inStockRecord in inStockRecords:
        serialNo = __find_serial__(inStockRecord, serials)
        consignmentInDetail = ConsignmentInDetail()
        consignmentInDetail.inStockBatch = inStockRecord.inStockBatch
        consignmentInDetail.inStockRecord = inStockRecord
        consignmentInDetail.serialNo = serialNo
        consignmentInDetail.quantity = inStockRecord.quantity
        consignmentInDetail.balance = 0
        consignmentInDetail.status = 'Incomplete'
        consignmentInDetail.save()        
        logger.debug("Consignment IN record build! '%s'", consignmentInDetail.pk)
        