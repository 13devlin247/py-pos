from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from scheduling.mythology import Supervisor, SchedulerFactory, JobAgent,\
    ClothesAgent
from kernal.views import __json_wrapper__
from scheduling.models import JobForm, ClothesTemplateForm, ClothesTemplate,\
    Task, Worker, WorkerAbility, ClothesChoosed
from datetime import date    
import logging
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

def CreateStepDone(request, jobid, taskid, workerid, cost):
    startDate = request.GET.get('start_date','')
    endDate = request.GET.get('end_date','')
    if startDate == '' or endDate == '':
        startDate = str(date.min)
        endDate = str(date.max)
    startDate = startDate+" 00:00:00"
    endDate = endDate+" 23:59:59"
    
    factory = SchedulerFactory()
    job_agent = JobAgent(factory.jobs(jobid))
    task = Task.objects.get(pk=int(taskid))
    worker_ability = WorkerAbility.objects.get(pk=int(workerid))
    job_agent.create_step(task = task, worker = worker_ability.worker, cost = cost, start_at = startDate, end_at = endDate)
    return HttpResponseRedirect('/workflow/step/add/'+str(job_agent.pk))
     
def RemoveStep(request, jobid, stepid):
    factory = SchedulerFactory()
    job_agent = JobAgent(factory.jobs(jobid))
    job_agent.remove_step(stepid, 'assign error')
    return HttpResponseRedirect('/workflow/step/add/'+str(job_agent.pk))

def CreateStep(request, jobid):
    factory = SchedulerFactory()
    job = factory.jobs(jobid)
    tasks = Task.objects.filter(active = True)
    return render_to_response('create_step.html',{'job': JobAgent(job), 'tasks': tasks, 'action': '/workflow/step/add/done/'})
     
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
    