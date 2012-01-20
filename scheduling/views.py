from django.http import HttpResponseRedirect, HttpResponse
import datetime
from django.shortcuts import render_to_response
from scheduling.mythology import Supervisor, SchedulerFactory, JobAgent,\
    ClothesAgent, TaskAgent
from kernal.views import __json_wrapper__
from scheduling.models import JobForm, ClothesTemplateForm, ClothesTemplate,\
    Task, Worker, WorkerAbility, ClothesChoosed, Step, Job 
from datetime import date    
import logging
from kernal.models import JobResponse
from kernal.barn import Hermes
# Create your views here.
logging.basicConfig(
    level = logging.WARN,
    format = '%(asctime)s %(levelname)s %(module)s.%(funcName)s():%(lineno)s %(message)s',
)
# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def WorkerLoading(request):
    startDate = request.GET.get('start_date','')
    endDate = request.GET.get('end_date','')
    if startDate == '' or endDate == '':
        startDate = str(date.min)
        endDate = str(date.max)
    startDate = startDate+" 00:00:00"
    endDate = endDate+" 23:59:59"

    sp = Supervisor()
    workers_loading_table = sp.worker_loading(startDate, endDate)
    text = '[{'
    for key, value in workers_loading_table.items():
        
        text += "\"%s\":%s," % (key.pk, value)
    text = text[0:len(text)-1]+"}]"  
    json = __json_wrapper__(workers_loading_table)
    return HttpResponse(text, mimetype="application/json")
    
    
def TaskWorkerList(request, task_pk):
    task = Task.objects.get(pk = int(task_pk))
    sp = Supervisor()
    workers = sp.filter_worker_ability(task)
    json = __json_wrapper__(workers)
    return HttpResponse(json, mimetype="application/json")
    

def WorkerList(request):
    sp = Supervisor()
    workers = sp.filter_worker(None)
    json = __json_wrapper__(workers)
    return HttpResponse(json, mimetype="application/json")

def TaskList(request):
    factory = SchedulerFactory()
    tasks = factory.tasks()
    json = __json_wrapper__(tasks)
    return HttpResponse(json, mimetype="application/json")

def JobList(request):
    factory = SchedulerFactory()
    jobs = factory.jobs()
    json = __json_wrapper__(jobs)
    return HttpResponse(json, mimetype="application/json")        

def CreateClothesInformation(request, jobid):
    factory = SchedulerFactory()
    job = factory.jobs(jobid)
    clothes_agent = ClothesAgent(job)
    clothesChooseds = clothes_agent.choosed_clothes_list()
    clothes_templates = ClothesTemplate.objects.filter(active = True)
    return render_to_response('create_clothes_information.html',{'job': job, 'clothesChooseds': clothesChooseds,'clothes_templates': clothes_templates, 'action': '/workflow/clothes/information/add/done/'})

def _filter_clothes_template(request):
    if not request:
        logger.error("filter clothes template fail, request is null")
        return
    clothesTemplates = {}
    for param in request.GET:
        if "clothes_template_pk_" in param:
            pk = param.replace("clothes_template_pk_", "")
            clothesTemplates[ClothesTemplate.objects.get(pk=int(pk))] = request.GET.get(pk+"_fields", "")
    return clothesTemplates
        
def RemoveClothesInformationDone(request, job_id, choosed_template_id):
    factory = SchedulerFactory()
    clothes_agent = ClothesAgent(factory.jobs(job_id))
    reason = request.user.username
    clothes_agent.remove_choosed_clothes(choosed_template_id, reason)
    return HttpResponseRedirect('/workflow/clothes/information/add/%s' % job_id)

def CreateClothesInformationDone(request):
    jobid = request.GET.get('jobid', None)
    if not jobid:
        logger.error("ClothesInformation create fail, jobid null")
        return
    factory = SchedulerFactory()
    clothes_agent = ClothesAgent(factory.jobs(jobid))
    clothes_templates = _filter_clothes_template(request)
    clothes_agent.choose_clothes(clothes_templates, None)
    return HttpResponseRedirect('/workflow/clothes/information/add/%s' % jobid)

def _response_job_cost(job_agent):
    job_response = JobResponse.objects.get(job = job_agent.instance)
    outStockRecord = job_response.outStockRecord
    outStockRecord.cost = job_agent.cost()
    outStockRecord.save()
    job_response.active = False
    job_response.reason = 'Completed'
    job_response.save()
    hermes = Hermes()
    hermes.recalc_cost = False
    hermes.ReCalcCounterByPK(outStockRecord.bill.counter.pk, recalc_bill_profit = True)

def CreateStepDone(request, jobid, taskid, workerid, cost):
    startDate = request.GET.get('start_date','')
    endDate = request.GET.get('end_date','')
    if startDate == '' or endDate == '':
        startDate = str(date.min)
        endDate = str(date.max)
    startDate = startDate+" 00:00:00"
    endDate = endDate+" 23:59:59"
    worker = Supervisor().get_worker(workerid)
    job_agent = JobAgent(SchedulerFactory().jobs(jobid))
    task = TaskAgent(pk = taskid)
    job_agent.create_step(task = task.instance, worker = worker, cost = cost, start_at = startDate, end_at = endDate)
    _response_job_cost(job_agent)
    return HttpResponseRedirect('/workflow/step/add/'+str(job_agent.pk))
     
def RemoveStep(request, jobid, stepid):
    factory = SchedulerFactory()
    job_agent = JobAgent(factory.jobs(jobid))
    job_agent.remove_step(stepid, 'assign error')
    _response_job_cost(job_agent)
    return HttpResponseRedirect('/workflow/step/add/'+str(job_agent.pk))

def CreateStep(request, jobid):
    factory = SchedulerFactory()
    job = factory.jobs(jobid)
    tasks = Task.objects.filter(active = True)

    factory = SchedulerFactory()	
    stepnow = JobAgent(factory.jobs(jobid))
    progress = stepnow.progress()
    progress = int(progress * 100)    
    
    return render_to_response('create_step.html',{'job': JobAgent(job), 'tasks': tasks, 'action': '/workflow/step/add/done/', 'progress':progress})
     
def CreateClothesTemplate(request):
    form = ClothesTemplateForm(request.POST)
    clothesTemplate = form.save(commit=False)
    clothesTemplate.active = True
    clothesTemplate.save()
    return HttpResponseRedirect('/workflow/clothes/template/report/')

def CreateJob(request):
    form = JobForm(request.GET)
    job = form.save(commit=False)
    user = request.user
    factory = SchedulerFactory()
    job_agent = factory.register_job(name = job.name, desc = job.description, start_at = job.start_at, end_at = job.end_at, creator = user)
    logger.debug('Job %s created' % job.name)
    return HttpResponseRedirect('/workflow/job/report/')

def NextStep(request,jobid):
    factory = SchedulerFactory()	
    stepnow = JobAgent(factory.jobs(jobid))
    nextone = stepnow.next_step()
    progress = stepnow.progress()
    logger.debug("%s",nextone)
    return HttpResponseRedirect('/workflow/step/add/'+str(jobid))          

def PrevStep(request,jobid):
    factory = SchedulerFactory()	
    stepnow = JobAgent(factory.jobs(jobid))
    prevone = stepnow.prev_step()
    progress = stepnow.progress()   
    logger.debug("%s",prevone)
    return HttpResponseRedirect('/workflow/step/add/'+str(jobid))    	


def OverdueStep(request,duedate):
    factory = SchedulerFactory()	
    jobs = factory.jobs()
    for job in jobs:
        stepnow = JobAgent(factory.jobs(job.pk))
        totaloverdue = stepnow.Overdue_step(duedate)
        logger.debug("%s",totaloverdue)		
	return render_to_response('report_overdue_today.html',{'totaloverdue':totaloverdue})
  	    
def Overdue(request, jobid, date):
    factory = SchedulerFactory()	
    stepnow = JobAgent(factory.jobs(jobid))
    totaloverdue = stepnow.Overdue_step(date)
    json = __json_wrapper__(totaloverdue)
    return HttpResponse(json, mimetype="application/json")  
	
def WorkerJob(request):
    worker = Worker.objects.filter(active=True).order_by('name')
    return render_to_response('report_worker.html',{'worker':worker})

def WorkerTask(request,workerid):
    supervisor = Supervisor()
    workertask = supervisor.worker_steps(workerid)
    workername = supervisor.get_worker(workerid)
    return render_to_response('report_worker_task.html',{'workertask':workertask,'workername':workername})
	

	
    