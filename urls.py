from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from django.views.generic import list_detail, date_based, create_update
from pos.kernal.models import Product,  InStockRecord, OutStockRecord, ProductForm, InStockRecordForm, OutStockRecordForm
from pos.kernal.views import ProductInfo, ProductInventory, ProductSave,  ProductDelete,OutStockRecordSave, InStockRecordSave, ProductUpdateView
from pos.kernal.views import SalesConfirm, InventoryConfirm
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
    'queryset': Product.objects.filter(disable=False),                      
    'allow_empty': True,                      
    'template_name': 'product_list.html', 
    'extra_context': {'form': ProductForm, 'submit_form':'/product/save/', 'main_link': main_link},    
}


"""
response AJAX method for create product
"""
product_form = {
    'model': Product, 
    'extra_context': {'form': ProductForm, 'submit_form':'/product/save', 'form_title': 'New Product'},    
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
    'queryset': OutStockRecord.objects.all(),                      
    'allow_empty': True,                      
    'template_name': 'product_list.html', 
    'extra_context': {'main_link': main_link},
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
    url(r'^$', list_detail.object_list, product_list_view),
    
    url(r'^product/create/$', create_update.create_object, product_form), 
    url(r'^product/search/$', list_detail.object_list, product_list_view),
    url(r'^product/update/(?P<productID>\w+)', ProductUpdateView), 
    url(r'^product/delete/$', ProductDelete),    
    url(r'^product/save/(?P<productID>\w+)*', ProductSave), # controller
	url(r'^product/info/(?P<barcode>\w+)*', ProductInfo), # controller
    url(r'^product/inventory/(?P<barcode>\w+)*', ProductInventory), # controller
    
    
    
	url(r'^inventory/list/$', direct_to_template,  {'template': 'inventory_form.html'}),
    url(r'^inventory/confirm/$', InventoryConfirm),    
    url(r'^^inventory/result/$', direct_to_template,  {
                            'template': 'under_constructor.html', 
                            'extra_context':{ 'msg':'Inventory insert success, but this result page is under constructor !!'}
                            }),                                
    url(r'^in_stock_record/create/$', create_update.create_object, in_stock_record_crud_view), 
    url(r'^in_stock_record/search/$', list_detail.object_list,  in_stock_record_list_view), 
    url(r'^in_stock_record/save/$', InStockRecordSave), 

    url(r'^out_stock_record/create/$', create_update.create_object, out_stock_record_crud_view), 
    url(r'^out_stock_record/search/$', list_detail.object_list,  out_stock_record_list_view), 
    url(r'^out_stock_record/save/$', OutStockRecordSave), 
    url(r'^sales/order/$', direct_to_template,  {'template': 'pos.html'}),
    url(r'^sales/list/$', direct_to_template,  {'template': 'sales_form.html'}),
    url(r'^sales/confirm/$', SalesConfirm),
    url(r'^sales/invoice/$', direct_to_template,  {
                            'template': 'under_constructor.html', 
                            'extra_context':{ 'msg':'Data insert success !! but invoice page is under constructor !!'}
                            }),
    url(r'^underconstructor/$', direct_to_template,  {
                            'template': 'under_constructor.html', 
                            'extra_context':{ 'msg':'this page is under constructor !!'}
                            }),                            
    #url(r'^sales/confirm/$', printData),
    
    

)
