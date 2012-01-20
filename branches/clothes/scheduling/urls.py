from django.conf.urls.defaults import patterns, include, url
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.views.generic import list_detail, date_based, create_update
from django.contrib.auth.models import User
from pos.kernal.views import *
from pos.kernal.models import *
from pos.scheduling.views import *
from django.db.models import Q
from datetime import date
#from pos.kernal.views import ajaxProductDetailView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from kernal.views import __json_wrapper__
from scheduling.views import *
from scheduling.views import NextStep,WorkerJob
from scheduling.models import Job, JobForm, ClothesTemplateForm, ClothesTemplate
admin.autodiscover()

clothes_template_report_view = {
    'queryset': ClothesTemplate.objects.filter(active=True),                      
    'allow_empty': True,                      
    'template_name': 'search_clothes_template.html', 
    'extra_context': {'submit_form':'/counter/save/'},    
}

jobs_report_view = {
    'queryset': Job.objects.filter(active=True).exclude(status="100"),                      
    'allow_empty': True,   
    'template_name': 'search_jobs.html', 
    'extra_context': {'submit_form':'/counter/save/'},    
}



urlpatterns = patterns('',
    url(r'^jobs/$', login_required(direct_to_template),  {'template': 'jobs.html'}),
    url(r'^worker/list/$', login_required(WorkerList)),
    url(r'^task/list/$', login_required(TaskList)),
    url(r'^job/list/$', login_required(JobList)),
    url(r'^task/worker/list/(?P<task_pk>[\x20-\x7E]+)$', login_required(TaskWorkerList)),
    url(r'^worker/loading$', login_required(WorkerLoading)),
    
    
    url(r'^clothes/information/add/done/$', login_required(CreateClothesInformationDone)),
    url(r'^clothes/information/remove/choosed_clothes/(?P<job_id>[\x20-\x7E]+)/(?P<choosed_template_id>[\x20-\x7E]+)$', login_required(RemoveClothesInformationDone)),
    url(r'^clothes/information/add/(?P<jobid>[\x20-\x7E]+)$', login_required(CreateClothesInformation)),
    url(r'^step/save/(?P<jobid>[\x20-\x7E]+)/(?P<taskid>[\x20-\x7E]+)/(?P<workerid>[\x20-\x7E]+)/(?P<cost>[\x20-\x7E]+)/$', login_required(CreateStepDone)),
    url(r'^step/add/(?P<jobid>[\x20-\x7E]+)$', login_required(CreateStep)),
    url(r'^step/remove/(?P<jobid>[\x20-\x7E]+)/(?P<stepid>[\x20-\x7E]+)/$', login_required(RemoveStep)),
    url(r'^step/nextstep/(?P<jobid>[\x20-\x7E]+)/$', login_required(NextStep)),
    url(r'^step/prevstep/(?P<jobid>[\x20-\x7E]+)/$', login_required(PrevStep)),
    
    url(r'^clothes/template/add/$', login_required(direct_to_template),  {'template': 'create_clothestemplate.html',  'extra_context': {'form': ClothesTemplateForm(), 'action':'/workflow/clothes/template/add/confirm/'} }),
    url(r'^clothes/template/add/confirm/$', login_required(CreateClothesTemplate)),
    url(r'^clothes/template/report/$', login_required(list_detail.object_list),clothes_template_report_view),
    
    url(r'^job/report/$', login_required(list_detail.object_list),jobs_report_view),
    url(r'^job/add/$', login_required(direct_to_template),  {'template': 'create_jobs.html',  'extra_context': {'form': JobForm(), 'action':'/workflow/job/add/confirm/'} }),
    url(r'^job/add/confirm/$', login_required(CreateJob)),
 
    url(r'^overdue/(?P<duedate>[\x20-\x7E]+)/$',login_required(OverdueStep)),
    url(r'^overdue_report/$',login_required(direct_to_template), {'template': 'report_overdue.html',  'extra_context': {'form': ReportFilterForm(), 'action': '/stock/take/'} }), 
    url(r'^worker_job/$',login_required(WorkerJob)),    
    url(r'^worker_task/(?P<workerid>[\x20-\x7E]+)/$',login_required(WorkerTask)),    
	
)
