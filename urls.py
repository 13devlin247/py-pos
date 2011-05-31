from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from django.views.generic import list_detail, date_based, create_update
from pos.kernal.models import Product,  InStockRecord, OutStockRecord, Counter, Payment
from pos.kernal.models import ProductForm, InStockRecordForm, OutStockRecordForm, InStockBatchForm
from pos.kernal.views import ProductInfo, ProductInventory, ProductSave,  ProductDelete,OutStockRecordSave, InStockRecordSave, ProductUpdateView
from pos.kernal.views import SalesConfirm, InventoryConfirm, QueryBill,  QueryInventory
from pos.kernal.views import ReportDaily
from pos.kernal.models import Supplier, SupplierForm, Customer, CustomerForm, ReportFilterForm
from pos.kernal.views import SupplierSave, CustomerSave
from pos.kernal.views import SupplierList, CustomerList, ProductList
from pos.kernal.views import CustomerInfo, SupplierInfo
from pos.kernal.views import test
from django.contrib.auth.decorators import login_required
from pos.kernal.views import CounterUpdate
from pos.kernal.views import PersonReport



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
    'queryset': Product.objects.filter(active=True),                      
    'allow_empty': True,                      
    'template_name': 'product_list.html', 
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
    url(r'^product/update/(?P<productID>\w+)', login_required(ProductUpdateView)), 
    url(r'^product/delete/$', login_required(ProductDelete)),    
    url(r'^product/save/(?P<productID>\w+)*', login_required(ProductSave)), # controller
    url(r'^product/info/(?P<query>\w+)*', login_required(ProductInfo)), # controller
    url(r'^product/inventory/(?P<pk>\w+)*', login_required(ProductInventory)), # controller

    url(r'^supplier/create/$', login_required(create_update.create_object), supplier_form), 
    url(r'^supplier/search/$', login_required(list_detail.object_list), product_list_view),
    url(r'^supplier/update/(?P<productID>\w+)', login_required(ProductUpdateView)), 
    url(r'^supplier/delete/$', login_required(ProductDelete)),    
    url(r'^supplier/save/(?P<supplierID>\w+)*', login_required(SupplierSave)), # controller

    url(r'^customer/create/$', login_required(create_update.create_object), customer_form), 
    url(r'^customer/search/$', login_required(list_detail.object_list), product_list_view),
    url(r'^customer/update/(?P<productID>\w+)', login_required(ProductUpdateView)), 
    url(r'^customer/delete/$', login_required(ProductDelete)),    
    url(r'^customer/save/(?P<customerID>\w+)*', login_required(CustomerSave)), # controller    
    url(r'^customer/info/(?P<query>\w+)*', login_required(CustomerInfo)),    # customer info json
    url(r'^supplier/info/(?P<query>\w+)*', login_required(SupplierInfo)),    # supplier info json
    
    url(r'^supplier/ajax/$', login_required(SupplierList)),    
    url(r'^customer/ajax/$', login_required(CustomerList)),    
    url(r'^product/ajax/$', login_required(ProductList)),    
    url(r'^inventory/list/$', login_required(direct_to_template),  {'template': 'inventory_form2.html',  'extra_context': {'form': InStockBatchForm} }),
    url(r'^inventory/list2/$', login_required(direct_to_template),  {'template': 'inventory_form.html',  'extra_context': {'form': InStockBatchForm} }),
    url(r'^inventory/confirm/$', login_required(InventoryConfirm)),    
    url(r'^inventory/result/(?P<inStockBatchID>\w+)*', login_required(QueryInventory)),                                
    url(r'^in_stock_record/create/$', login_required(create_update.create_object), in_stock_record_crud_view), 
    url(r'^in_stock_record/search/$', login_required(list_detail.object_list),  in_stock_record_list_view), 
    url(r'^in_stock_record/save/$', login_required(InStockRecordSave)), 

    url(r'^out_stock_record/create/$', login_required(create_update.create_object), out_stock_record_crud_view), 
    url(r'^out_stock_record/search/$', login_required(list_detail.object_list),  out_stock_record_list_view), 
    url(r'^out_stock_record/save/$', login_required(OutStockRecordSave)), 
    url(r'^sales/order/$', login_required(direct_to_template),  {'template': 'pos.html'}),
    url(r'^sales/list/$', login_required(direct_to_template),  {'template': 'sales_base.html',  'extra_context': {'title':'Sales Register'} }),
    url(r'^invoice/list/$', login_required(direct_to_template),  {'template': 'invoice_form.html',  'extra_context': {'title':'Invoice Register'} }),
    url(r'^sales/list1/$', login_required(direct_to_template),  {'template': 'sales_form.html'}),
    url(r'^sales/confirm/$', login_required(SalesConfirm)),
    url(r'^sales/do/list$', login_required(list_detail.object_list),  sales_do_list_view), 
    url(r'^underconstructor/$', login_required(direct_to_template),  {
                            'template': 'under_constructor.html', 
                            'extra_context':{ 'msg':'this page is under constructor !!'}
                            }),                            
    url(r'^report/$', login_required(direct_to_template),  {'template': 'report.html'}),                                        
    url(r'^report/daily/filter/$', login_required(direct_to_template),  {'template': 'report_filter.html',  'extra_context': {'form': ReportFilterForm(), 'action': '/report/daily/'} }),                                    
    url(r'^report/daily/$', login_required(ReportDaily)),                        
    url(r'^report/person/filter/$', login_required(direct_to_template),  {'template': 'report_filter.html',  'extra_context': {'form': ReportFilterForm(), 'action': '/report/person/'} }),                                
    url(r'^report/person/$', PersonReport),                        
    url(r'^sales/do/filter/$', login_required(direct_to_template),  {'template': 'report_filter.html',  'extra_context': {'form': ReportFilterForm(), 'action': '/sales/do/list'} }),                                
    #url(r'^counter/close/$', CloseCounter),         
    url(r'^counter/close/$', login_required(list_detail.object_list), counter_list_view),
    url(r'^counter/save/$', login_required(CounterUpdate)),
    #url(r'^sales/bill/$', direct_to_template,  {'template': 'bill.html'}),
    url(r'^sales/(?P<displayPage>\w+)*/(?P<billID>\w+)*', login_required(QueryBill)),
    #url(r'^report/daily/$', direct_to_template,  {'template': 'report_dailySales.html'}),                        
    #url(r'^sales/confirm/$', printData),
    (r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    (r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'admin/login.html'}),
    
    
    # testing
    url(r'^test/$', login_required(test)),

)
