from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from scheduling.mythology import Supervisor, SchedulerFactory, JobAgent
from kernal.views import __json_wrapper__
from scheduling.models import JobForm, ClothesTemplateForm, ClothesTemplate,\
    Task, Worker, WorkerAbility
import logging
# Create your views here.
logging.basicConfig(
    level = logging.WARN,
    format = '%(asctime)s %(levelname)s %(module)s.%(funcName)s():%(lineno)s %(message)s',
)
# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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
    clothes_templates = ClothesTemplate.objects.filter(active = True)
    return render_to_response('create_clothes_information.html',{'job': job, 'clothes_templates': clothes_templates, 'action': '/workflow/clothes/information/add/done/'})

def CreateClothesInformationDone(request):
    jobid = request.GET.get('jobid', None)
    if not jobid:
        logger.error("ClothesInformation create fail, jobid null")
        return
    factory = SchedulerFactory()
    job_agent = JobAgent(factory.jobs(jobid))
    clothes_template_pk = int(request.GET.get('clothes_template_pk'))
    clothes_template = ClothesTemplate.objects.get(pk = clothes_template_pk)
    fields = request.GET.get(str(clothes_template_pk)+'_fields', '')
    job_agent.create_clothesInformation(clothes_template, None, fields)
    return HttpResponseRedirect('/workflow/job/report/')

def CreateStepDone(request, jobid, taskid, workerid):
    factory = SchedulerFactory()
    job_agent = JobAgent(factory.jobs(jobid))
    task = Task.objects.get(pk=int(taskid))
    worker_ability = WorkerAbility.objects.get(pk=int(workerid))
    job_agent.create_step(task = task, worker = worker_ability.worker, cost = worker_ability.cost, start_at = '2011-12-11', end_at = '2011-12-15')
    tasks = Task.objects.filter(active = True)
    return render_to_response('create_step.html',{'job': job, 'tasks': tasks, 'action': '/workflow/step/add/done/'})
     

def CreateStep(request, jobid):
    factory = SchedulerFactory()
    job = factory.jobs(jobid)
    tasks = Task.objects.filter(active = True)
    return render_to_response('create_step.html',{'job': job, 'tasks': tasks, 'action': '/workflow/step/add/done/'})
     
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
    