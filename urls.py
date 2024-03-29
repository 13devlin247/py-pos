from django.conf.urls.defaults import patterns, include, url
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.views.generic import list_detail, date_based, create_update
from django.contrib.auth.models import User
from pos.kernal.views import *
from pos.kernal.models import *
from django.db.models import Q
from datetime import date

#from pos.kernal.views import ajaxProductDetailView


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

main_link = {
    'product': '/product/create/',                      
    'in stock record': '/in_stock_record/create/',                      
    'out stock record': '/out_stock_record/create/', 
    'profit record': '/profit/create/',
}

"""
show product list
"""
product_list_view = {
    'queryset': Product.objects.filter(active=True).order_by('name'),                      
    'allow_empty': True,                      
    'template_name': 'product_list.html', 
    'paginate_by': 25,
    'extra_context': {'form': ProductForm, 'submit_form':'/product/save/', 'main_link': main_link},    
}

counter_list_view = {
    'queryset': Counter.objects.filter(active=True),                      
    'allow_empty': True,                      
    'template_name': 'counter_list.html', 
    'extra_context': {'form': ProductForm, 'submit_form':'/counter/save/', 'main_link': main_link},    
}

"""
response AJAX method for create product
"""
product_form = {
    'model': Product, 
    'extra_context': {'form': ProductForm, 'submit_form':'/product/save', 'form_title': 'New Product'},    
    'template_name': 'product_form.html', 
}

supplier_form = {
    'model': Supplier, 
    'extra_context': {'form': SupplierForm, 'submit_form':'/supplier/save', 'form_title': 'New Supplier'},    
    'template_name': 'product_form.html', 
}

customer_form = {
    'model': Customer, 
    'extra_context': {'form': CustomerForm, 'submit_form':'/customer/save', 'form_title': 'New Customer'},    
    'template_name': 'product_form.html', 
}

in_stock_record_list_view = {
    'queryset': InStockRecord.objects.all(),                      
    'allow_empty': True,                      
    'template_name': 'product_list.html', 
    'extra_context': {'main_link': main_link}, 
}

in_stock_record_crud_view  = {
    'model': InStockRecord, 
    'extra_context': {'form': InStockRecordForm, 'submit_form':'/in_stock_record/save', 'main_link': main_link},
    'template_name': 'CRUDForm.html', 
}

out_stock_record_list_view = {
    'queryset': OutStockRecord.objects.all().order_by('bill__user'),                      
    'allow_empty': True,                      
    'template_name': 'report_personalSales.html', 
    'extra_context': {'main_link': main_link},
}

imei_list_view = {
    'queryset': Payment.objects.all().order_by('-create_at'),                      
    'allow_empty': True,                      
    'template_name': 'search_imei.html', 
    'extra_context': {'autocomplete_url': '/imei/ajax/','json_url': '/payment/info/', 'display':'bill' }
}

cashsales_list_view = {
    'queryset': Payment.objects.filter(create_at__gt = date.today()).filter(type='Cash Sales').order_by('-create_at'),                      
    'allow_empty': True,                      
    'template_name': 'search_payment.html', 
    'extra_context': {'autocomplete_url': '/payment/ajax/','json_url': '/payment/info/Cash Sales/', 'display':'bill' }
}

consignment_list_view = {
    'queryset': Payment.objects.filter(Q(type__exact='Consignment')|Q(status__exact = 'Incomplete')).order_by('create_at'),                      
    'allow_empty': True,                      
    'template_name': 'search_consignment.html', 
    'extra_context': {'autocomplete_url': '/payment/ajax/','json_url': '/payment/info/Cash Sales/', 'display':'invoice' }
}


invoice_list_view = {
    'queryset': Payment.objects.filter(create_at__gt = date.today()).filter(type='Invoice').order_by('-create_at'),                      
    'allow_empty': True,                      
    'template_name': 'search_payment.html', 
    'extra_context': {'autocomplete_url': '/payment/ajax/','json_url': '/payment/info/Invoice/' , 'display':'invoice' }
}


sales_do_list_view = {
    'queryset': Payment.objects.filter(type='Invoice').order_by('-create_at'),                      
    'allow_empty': True,                      
    'template_name': 'do_list.html', 
}

out_stock_record_crud_view  = {
    'model': OutStockRecord, 
    'extra_context': {'form': OutStockRecordForm, 'submit_form':'/out_stock_record/save', 'main_link': main_link},
    'template_name': 'CRUDForm.html', 
}



urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'pos.views.home', name='home'),
    # url(r'^pos/', include('pos.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', login_required(list_detail.object_list), product_list_view),
    
    url(r'^product/create/$', login_required(create_update.create_object), product_form), 
    url(r'^product/search/$', login_required(list_detail.object_list), product_list_view),
    url(r'^product/update/(?P<productID>[\x20-\x7E]+)', login_required(ProductUpdateView)), 
    url(r'^product/delete/$', login_required(ProductDelete)),    
    url(r'^product/save/(?P<productID>[\x20-\x7E]+)*', login_required(ProductSave)), # controller
    url(r'^product/info/(?P<query>[\x20-\x7E]+)*', login_required(ProductInfo)), # controller
    url(r'^product/inventory/(?P<productID>[\x20-\x7E]+)*', login_required(ProductInventory)), # controller

    url(r'^supplier/create/$', login_required(create_update.create_object), supplier_form), 
    url(r'^supplier/search/$', login_required(list_detail.object_list), product_list_view),
    url(r'^supplier/update/(?P<productID>[\x20-\x7E]+)', login_required(ProductUpdateView)), 
    url(r'^supplier/delete/$', login_required(ProductDelete)),    
    url(r'^supplier/save/(?P<supplierID>[\x20-\x7E]+)*', login_required(SupplierSave)), # controller

    url(r'^customer/create/$', login_required(create_update.create_object), customer_form), 
    url(r'^customer/search/$', login_required(list_detail.object_list), product_list_view),
    url(r'^customer/update/(?P<productID>[\x20-\x7E]+)', login_required(ProductUpdateView)), 
    url(r'^customer/delete/$', login_required(ProductDelete)),    
    url(r'^customer/save/(?P<customerID>[\x20-\x7E]+)*', login_required(CustomerSave)), # controller    
    url(r'^customer/info/(?P<query>[\x20-\x7E]+)*', login_required(CustomerInfo)),    # customer info json
    url(r'^supplier/info/(?P<query>[\x20-\x7E]+)*', login_required(SupplierInfo)),    # supplier info json
    url(r'^payment/info/(?P<type>[\x20-\x7E]+)/(?P<query>[\x20-\x7E]+)', login_required(PaymentInfo)),    # payment info json
    url(r'^payment/info/(?P<pk>[\x20-\x7E]+)*', login_required(PaymentInfoByPK)),    # payment info json    

    url(r'^supplier/ajax/$', login_required(SupplierList)),    
    url(r'^customer/ajax/$', login_required(CustomerList)),    
    url(r'^product/ajax/$', login_required(ProductList)),    
    url(r'^payment/ajax/$', login_required(PaymentList)),    
    url(r'^imei/ajax/$', login_required(IMEIorBillIDList)),        
    url(r'^inventory/$', login_required(direct_to_template),  {'template': 'stock.html'}),
    url(r'^inventory/list/$', login_required(direct_to_template),  {'template': 'inventory_base.html',  'extra_context': {'form': InStockBatchForm, 'action': '/inventory/confirm'} }),
    url(r'^inventory/confirm/$', login_required(InventoryConfirm)),    
    url(r'^inventory/result/(?P<inStockBatchID>[\x20-\x7E]+)*', login_required(QueryInventory)),                                
    url(r'^in_stock_record/create/$', login_required(create_update.create_object), in_stock_record_crud_view), 
    url(r'^in_stock_record/search/$', login_required(list_detail.object_list),  in_stock_record_list_view), 
    url(r'^in_stock_record/save/$', login_required(InStockRecordSave)), 

    url(r'^out_stock_record/create/$', login_required(create_update.create_object), out_stock_record_crud_view), 
    url(r'^out_stock_record/search/$', login_required(list_detail.object_list),  out_stock_record_list_view), 
    url(r'^out_stock_record/save/$', login_required(OutStockRecordSave)), 
    url(r'^sales/order/$', login_required(direct_to_template),  {'template': 'pos.html'}),
    url(r'^sales/$', login_required(direct_to_template),  {'template': 'sales.html'}),
    url(r'^sales/list/$', login_required(direct_to_template),  {'template': 'sales_base.html',  'extra_context': {'title':'Sales Register', 'currentUser': None  , 'users':User.objects.all(), 'action':'/sales/confirm'} }),
    url(r'^invoice/list/$', login_required(direct_to_template),  {'template': 'invoice_form.html',  'extra_context': {'title':'Invoice Register', 'currentUser': None  , 'users':User.objects.all(), 'action':'/sales/confirm'} }),
    url(r'^consignment/in/$', login_required(direct_to_template),  {'template': 'consignment_in_form.html',  'extra_context': {'form': InStockBatchForm, 'action':'/inventory/confirm'} }),
    url(r'^consignment/in/balance/$', login_required(direct_to_template),  {'template': 'consignment_in_balance_form.html',  'extra_context': {'form': ConsignmentInBalanceForm, 'action':'/consignment/in/balance/confirm'} }),
    url(r'^consignment/out/$', login_required(direct_to_template),  {'template': 'consignment_out_form.html',  'extra_context': {'title':'Consignment OutStock Register', 'action':'/sales/confirm'} }),
    url(r'^consignment/out/balance/$', login_required(direct_to_template),  {'template': 'consignment_out_balance_form.html',  'extra_context': {'title':'Consignment OutStock Balance', 'form': InStockBatchForm, 'action':'/consignment/out/balance/confirm/' } }),
    url(r'^consignment/out/sales/$', login_required(direct_to_template),  {'template': 'consignment_out_sale_form.html',  'extra_context': {'title':'Consignment OutStock Balance', 'form': InStockBatchForm, 'action':'/consignment/out/sale/confirm/' } }),
    url(r'^stock/adjust/$', login_required(direct_to_template),  {'template': 'stock_adjust.html',  'extra_context': {'title':'Stock Adjust', 'currentUser': None  , 'users':User.objects.all(), 'action':'/sales/confirm'} }),
    
    url(r'^consignment/out/balance/confirm/$', ConsignmentOutBalance),
    url(r'^consignment/out/sale/confirm/$', ConsignmentOutSale),
    url(r'^consignment/in/balance/confirm/$', ConsignmentInBalance),
    url(r'^sales/list1/$', login_required(direct_to_template),  {'template': 'sales_form.html'}),
    url(r'^sales/confirm/$', login_required(SalesConfirm)),
    url(r'^underconstructor/$', login_required(direct_to_template),  {
                            'template': 'under_constructor.html', 
                            'extra_context':{ 'msg':'this page is under constructor !!'}
                            }),                            
    url(r'^report/$', login_required(direct_to_template),  {'template': 'report.html'}),                                        
    url(r'^report/consignment/in/balance/filter/$', login_required(direct_to_template),  {'template': 'report_filter.html',  'extra_context': {'form': ReportFilterForm(), 'action': '/report/consignment/in/balance/'} }),                                    
    url(r'^report/consignment/in/balance/$', login_required(ReportConsignmentInBalance)),                        
    url(r'^report/consignment/out/balance/filter/$', login_required(direct_to_template),  {'template': 'report_filter.html',  'extra_context': {'form': ReportFilterForm(), 'action': '/report/consignment/out/balance/'} }),                                    
    url(r'^report/consignment/out/balance/$', login_required(ReportConsignmentOutBalance)),                            
    url(r'^report/inventory/filter/$', login_required(direct_to_template),  {'template': 'report_filter.html',  'extra_context': {'form': ReportFilterForm(), 'action': '/report/inventory/receipt/'} }),                                    
    url(r'^report/inventory/receipt/$', login_required(ReportInventoryReceipt)),                                
    
    
    url(r'^report/daily/filter/$', login_required(direct_to_template),  {'template': 'report_filter.html',  'extra_context': {'form': ReportFilterForm(), 'action': '/report/daily/'} }),                                    
    url(r'^report/daily/$', login_required(ReportDaily)),                        
    url(r'^report/stocktake/filter/$', login_required(direct_to_template),  {'template': 'report_filter.html',  'extra_context': {'form': ReportFilterForm(), 'action': '/stock/take/'} }),                                    
    url(r'^stock/take/$', login_required(CountInventory)),             
    url(r'^bill/void/$', login_required(VoidBill)),             
    
    url(r'^report/daily/category/filter/$', login_required(direct_to_template),  {'template': 'report_filter.html',  'extra_context': {'form': ReportFilterForm(), 'action': '/report/daily/category/'} }),                                    
    url(r'^report/daily/category/$', login_required(ReportDailyCategory)),                            
    url(r'^report/person/filter/$', login_required(direct_to_template),  {'template': 'report_filter.html',  'extra_context': {'form': ReportFilterForm(), 'action': '/report/person/'} }),                                
    url(r'^report/person/$', PersonReport),                        
    url(r'^sales/invoice/filter/$', login_required(direct_to_template),  {'template': 'report_filter.html',  'extra_context': {'form': ReportFilterForm(), 'action': '/sales/invoice/list'} }),                                
    url(r'^sales/invoice/list$', login_required(InvoiceReport)), 
    url(r'^sales/cash/filter/$', login_required(direct_to_template),  {'template': 'report_filter.html',  'extra_context': {'form': ReportFilterForm(), 'action': '/sales/cash/list'} }),                                
    url(r'^sales/cash/list$', login_required(CashSalesReport)),     
    url(r'^sales/return/filter/$', login_required(direct_to_template),  {'template': 'report_filter.html',  'extra_context': {'form': ReportFilterForm(), 'action': '/sales/return/list'} }),                                
    url(r'^sales/return/list$', login_required(SalesReturnReport)),         
    url(r'^inventory/return/filter/$', login_required(direct_to_template),  {'template': 'report_filter.html',  'extra_context': {'form': ReportFilterForm(), 'action': '/inventory/return/list'} }),                                
    url(r'^inventory/return/list$', login_required(InventoryReturnReport)),             
    
    url(r'^search/basic/$', login_required(direct_to_template),  {'template': 'search.html',  'extra_context': {'autocomplete_url': '/product/ajax/','json_url': '/product/info/' } }),                                
    url(r'^search/invoice/$', login_required(list_detail.object_list), invoice_list_view),                                    
    url(r'^search/cashsales/$', login_required(list_detail.object_list), cashsales_list_view),                                        
    url(r'^search/imei/$', login_required(list_detail.object_list), imei_list_view),                                        
    url(r'^search/consignment/$', login_required(list_detail.object_list), consignment_list_view),                                        
    
    
    
    

    url(r'^counter/close/$', login_required(list_detail.object_list), counter_list_view),
    url(r'^counter/save/$', login_required(CounterUpdate)),
    url(r'^sales/(?P<displayPage>[\x20-\x7E]+)*/(?P<billID>[\x20-\x7E]+)*', login_required(QueryBill)),
    (r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'admin/login.html'}),
    
    url(r'^category/info/$', login_required(CategoryInfo)),
    url(r'^print/barcode/(?P<barcode>[\x20-\x7E]+)*', login_required(PrintBarcode)),

    
    
    # testing
    url(r'^test/$', login_required(test)),

)
