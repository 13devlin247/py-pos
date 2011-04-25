from pos.kernal.models import Product,  InStockRecord, OutStockRecord, Profit, ProductForm, InStockRecordForm, OutStockRecordForm, ProfitForm
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.generic import list_detail, date_based, create_update

import logging
logging.basicConfig(level=logging.DEBUG)
"""
Below function for ajax use
"""
#def ajaxProductDetailView(request):
   # if request.method == 'GET':
        
def ProductDetail(request, barcode):
    queryset = Product.objects.filter(barcode=barcode)
    return list_detail.object_list(request,  queryset=queryset)

""" 
below function for save form object to databases
"""
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

def ProfitSave(request):
    if request.method == 'GET':
        form = ProfitForm(request.GET)
        if form.is_valid():
            profit = form.save(commit = True)
            profit.save()
            return HttpResponseRedirect('/profit/search/')
        else:
            form = ProductForm()
            return HttpResponseRedirect('/profit/create/')

