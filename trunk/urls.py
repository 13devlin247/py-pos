from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from django.views.generic import list_detail, date_based, create_update
from pos.kernal.models import Product,  InStockRecord, OutStockRecord, Profit, ProductForm, InStockRecordForm, OutStockRecordForm, ProfitForm
from pos.kernal.views import ProductSave, ProductCheck, ProductDelete,OutStockRecordSave, InStockRecordSave, ProfitSave, ProductUpdateView
from pos.kernal.views import ProductDetail
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

profit_list_view = {
    'queryset': Profit.objects.all(),                      
    'allow_empty': True,                      
    'template_name': 'product_list.html', 
    'extra_context': {'main_link': main_link},
}

profit_crud_view  = {
    'model': Profit, 
    'extra_context': {'form': ProfitForm, 'submit_form':'/profit/save', 'main_link': main_link},
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
    url(r'^$', direct_to_template,  {'template': 'product.php.html'}),
    
    url(r'^product/create/$', create_update.create_object, product_form), 
    url(r'^product/search/$', list_detail.object_list, product_list_view),
    url(r'^product/update/(?P<productID>\w+)', ProductUpdateView), 
    url(r'^product/delete/$', ProductDelete),    
    url(r'^product/save/(?P<productID>\w+)*', ProductSave), # controller
	url(r'^product/check/(?P<barcode>\w+)*', ProductCheck), # controller
    
	
    url(r'^in_stock_record/create/$', create_update.create_object, in_stock_record_crud_view), 
    url(r'^in_stock_record/search/$', list_detail.object_list,  in_stock_record_list_view), 
    url(r'^in_stock_record/save/$', InStockRecordSave), 

    url(r'^out_stock_record/create/$', create_update.create_object, out_stock_record_crud_view), 
    url(r'^out_stock_record/search/$', list_detail.object_list,  out_stock_record_list_view), 
    url(r'^out_stock_record/save/$', OutStockRecordSave), 
    url(r'^sales/order/$', direct_to_template,  {'template': 'pos.html'}),
    url(r'^sales/list/$', direct_to_template,  {'template': 'sales_form.html'}),
    

    url(r'^profit/create/$', create_update.create_object, profit_crud_view), 
    url(r'^profit/search/$', list_detail.object_list,  profit_list_view), 
    url(r'^profit/save/$', ProfitSave), 
)
