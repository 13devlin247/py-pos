'''
Created on 2011/10/22

@author: Administrator
'''
from django.db.models.query_utils import Q

import logging
from scheduling.models import WorkerAbility, Worker, Job, Step,\
    Task, ClothesChoosed
logging.basicConfig(
    level = logging.WARN,
    format = '%(asctime)s %(levelname)s %(module)s.%(funcName)s():%(lineno)s %(message)s',
)
# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

INCOMPLETE = 'incomplete'
WORKING = 'Working'
PENDING = 'Pending'
COMPLETE = 'Complete'

class SchedulerFactory(object):
    '''
    Eunomia was the goddess of law and legislation,
    '''
    def __init__(self):
        '''
        Constructor
        '''
    def overdue_job(self, date):
        if not date:
            logger.error("overdue job filter fail, date null")
            return
        jobs = Job.objects.filter(end_at__lt = date)
        logger.debug("overdue job filter success: %s " % len(jobs))
        return jobs

    def overdue_step(self, date):
        if not date:
            logger.error("overdue step filter fail, date null")
            return
        steps = Step.objects.filter(end_at__lt = date)
        logger.debug("overdue step filter success: %s " % len(steps))
        return steps
    
    def job_steps(self, job, task):
        if not job:
            logger.error('Job step filter faile, job null')
            return
        steps = Step.objects.filter(job = job)
        if task:
            steps = steps.filter(task = task)
        logger.debug("Job step filter success")
        return steps
    
    def jobs(self, jobid=None):
        if jobid:
            return Job.objects.get(pk = int(jobid))    
        return Job.objects.filter(active = True)
    
    def tasks(self):
        return Task.objects.filter(active = True)
    
    def register_job(self, name, start_at, end_at, creator, desc = 'N/A'):
        job = Job()
        job.name = name
        job.cost = 0
        job.description = desc
        job.start_at = start_at
        job.end_at = end_at
        job.status = 0
        job.creator = creator
        job.active = True
        job.save()
        logger.info('Job %s created' % job.pk)
        return job

class TaskAgent(object):
    def __init__(self, instance = None, pk = None):
        if instance:
            self.instance = instance
            return
        self.instance = Task.objects.get(pk=pk)
        return
    
    def update(self, name, desc):
        self.instance.name = name
        self.instance.desc = desc
        self.instance.save()

    def disable(self, reason):
        self.instance.active = False
        self.instance.reason = reason
        self.instance.save()

class StepAgent(object):
    def __init__(self, instance):
        self.instance = instance
        
    def change_worker(self, worker):
        self.instance.worker = worker
        self.instance.save()
         
    def change_start_at(self, date):
        self.instance.start_at = date
        self.instance.save()
        
    def change_end_at(self, date):
        self.instance.end_at = date
        self.instance.save()
        
    def change_status(self, status):
        self.instance.status = status
        self.instance.save()
        
    def disable(self, reason):
        self.instance.active = False
        self.instance.reason = reason
        self.instance.save()
        
    def change_cost(self, cost):
        self.instance.cost = cost
        self.instance.save()

class JobAgent(object):
    def __init__(self, instance):
        self.instance = instance
        self.pk = instance.pk
        self.name = instance.name
        self.description = instance.description
        self.start_at = instance.start_at
        self.end_at = instance.end_at
        self.status = instance.status
    
    def _recal_job_cost(self):
        steps = Step.objects.filter(job = self.instance).filter(active = True)
        total_cost = 0
        for step in steps:
            total_cost += step.cost
        self.instance.cost = total_cost
        self.instance.save()
        logger.info("Job: %s cost :%s " %(self.instance.pk, total_cost))
            
    
    def cost(self):
        return self.instance.cost
    
    def update(self, name = None, cost = None, desc = None, start_at = None, end_at = None, status = None):
        if name:
            self.instance.name = name
        if cost:
            self.instance.cost = cost
        if desc:
            self.instance.desc = desc
        if start_at:
            self.instance.start_at = start_at
        if end_at:
            self.instance.end_at = end_at
        if status:
            self.instance.status = status
        self.instance.save()
        logger.debug("JobAgent %s update done" % self.instance.name)
        
    def disable(self, reason):
        if not reason:
            logger.error('JobAgent: %s disable fail, reason null' )
            return 
        self.instance.active = False
        self.instance.reason = reason
        logger.error('JobAgent: %s disable success, reason null' )            

    def remove_step(self, stepid, reason):
        step = Step.objects.get(pk = int(stepid))
        step.active = False
        step.reason = reason
        step.save()
        logger.info("Step: %s removed." % step.pk)
        self._recal_job_cost()
        
    def steps(self):
        return Step.objects.filter(job = self.instance).filter(active = True).order_by("create_at")
        
    def create_step(self, task, worker, cost, start_at, end_at):
        if not task:
            logger.error("JobAgent %s create step fail, task null" % self.instance.name)
            return
        if not worker:
            logger.error("JobAgent %s create step fail, worker null" % self.instance.name)
            return
        if not start_at:
            logger.error("JobAgent %s create step fail, start_at null" % self.instance.name)
            return
        if not end_at:
            logger.error("JobAgent %s create step fail, end_at null" % self.instance.name)
            return
        step = Step()
        step.job = self.instance
        step.task = task
        step.worker = worker
        step.cost = cost
        step.status = PENDING
        step.start_at = start_at
        step.end_at = end_at
        step.active = True
        step.save()
        logger.debug("JobAgent %s create step %s success" % (self.instance.name, step.task.name))
        self._recal_job_cost()
        return step


# change the next step to complete		
    def next_step(self):
        steps = Step.objects.filter(active=True).filter(job=self.instance).order_by('create_at')

        for step in steps:
            if step.status == WORKING:
                step.status = COMPLETE                
                logger.debug("%s",step.status)
                step.save()	
            elif step.status == PENDING:
                step.status = WORKING
                step.save()	
                break		         
        return step

# change the prev step to working		
    def prev_step(self):
        steps = Step.objects.filter(active=True).filter(job=self.instance).order_by('-create_at')
        
        for step in steps:

            if step.status == WORKING:
                step.status = PENDING
                step.save()
            elif step.status == COMPLETE:
                step.status = WORKING
                step.save()
                break                 
        return step		

    def progress(self):
        steps = Step.objects.filter(active=True).filter(job=self.instance).order_by('-create_at')
        cal_progress = 0.0
        total_progress =len(steps)

        for step in steps:
            if step.status == COMPLETE:
                cal_progress = cal_progress + 1
        
        if total_progress == 0:
            percent = 0
        elif cal_progress == 0:
            percent = 0	
        else:
            percent = float(cal_progress/total_progress)
    
        self.instance.status = int(percent*100)
        self.instance.save()
        logger.debug("Progress-----> %s / %s ",cal_progress,total_progress)	    
        logger.debug("here is the percent-> %s",percent)	    	    
        return percent

    def Overdue_step(self,duedate):
        step = Step.objects.filter(active=True).filter(end_at__lt = duedate).filter(Q(status__exact=WORKING)|Q(status__exact=PENDING))
        logger.debug("Duedate--->%s",duedate)
        logger.debug("Step--->%s",step)
        return step
        
class ClothesAgent(object):

    def __init__(self, job):
        self.job = job
        
    def choose_clothes(self, clothes_templates, draft):
        if not clothes_templates:
            logger.error("ClothesInformation create fail, clothes template null")
            return
        clothes_chooseds = []
        for clothes_template, fields in clothes_templates.items():
            clothes_choosed = ClothesChoosed()
            clothes_choosed.job= self.job
            clothes_choosed.clothesTemplate = clothes_template
            clothes_choosed.fields_values = fields
            clothes_choosed.active = True
            clothes_choosed.save()
            clothes_chooseds.append(clothes_choosed)
            logger.debug("clothes tamplate choosed: %s" % clothes_choosed.clothesTemplate)
        logger.debug("clothes_information %s created" % self.job.pk)
        return clothes_chooseds

    def choosed_clothes_list(self):
        return ClothesChoosed.objects.filter(job = self.job).filter(active = True)
    
    def remove_choosed_clothes(self, pk, reason):
        clothesChoosed = ClothesChoosed.objects.get(pk = pk)
        clothesChoosed.active = False
        clothesChoosed.reason = reason
        clothesChoosed.save()
    
class ClothesChoosedAgent(object):
    def __init__(self, instance):
        self.instance = instance
        
    def update(self, value):
        if not value:
            logger.error('ClothesChoosed %s update fail, value null', self.instance.pk)
            return
        self.instance.fields_values = value
        self.instance.save()
        logger.debug('ClothesChoosed %s update success', self.instance.pk)
    
    def disable(self, reason):
        if not reason:
            logger.error('ClothesChoosed %s disable fail, reason null', self.instance.pk)
            return
        self.instance.active = False
        self.instance.reason = reason
        self.instance.save()
        logger.debug('ClothesChoosed %s disable success', self.instance.pk)
        
class Supervisor(object):
    def __init__(self):
        pass

    def get_worker(self,workerid):
        worker = Worker.objects.get(pk=int(workerid))
        return worker
    
    def worker_loading(self, startDate, endDate):
        logger.debug("calc workers loading")
        if not startDate:
            logger.error(" Supervisor filter worker fail, start date null")
            return []
        if not endDate:
            logger.error(" Supervisor filter worker fail, end date null")
            return []
        
        steps = Step.objects.filter(
                                    Q(start_at__range=(startDate, endDate)) | 
                                    Q(end_at__range=(startDate, endDate))
                                    ).filter(active=True)
        worker_loading = {}
        for step in steps:
            logger.debug("===== %s" % (step.pk))
            if step.worker not in worker_loading:
                worker_loading[step.worker] = 0
            worker_loading[step.worker] += 1
        workers = Worker.objects.filter(active=True)
        for worker in workers:
            if worker not in worker_loading:
                worker_loading[worker] = 0
                
        logger.debug("calc worker loading table done")
        return worker_loading
    
    def filter_worker_ability(self, task):
        if not task:
            logger.error(" Supervisor filter worker fail, task null")
            return []
        
        workers = [] 
        workers_abilitys = WorkerAbility.objects.filter(task = task).filter(active = True)
        for workers_ability in workers_abilitys:
            workers.append(workers_ability)
        logger.debug('Supervisor filter worker success: %s '% len(workers))
        return workers
    
    def filter_worker(self, task):
        if not task:
            logger.error(" Supervisor filter worker fail, task null")
            return Worker.objects.filter(active = True)
        workers = [] 
        workers_abilitys = WorkerAbility.objects.filter(task = task).filter(active = True)
        for workers_ability in workers_abilitys:
            if workers_ability.worker not in workers:
                workers.append(workers_ability.worker)
        logger.debug('Supervisor filter worker success: %s '% len(workers))
        return workers

    def worker_steps(self, workerid):
        #workertask = Step.objects.filter(worker=workerid).filter(active=True).exclude(status="Complete")
        workertask = Step.objects.filter(worker=workerid).filter(active=True)     
        return workertask

class WorkerAgent(object):
    def __init__(self, instance):
        self.worker = instance
    
    def disable(self, reason):
        if not reason:
            logger.error('worker %s disable fail' % self.worker.name)
            return 
        self.worker.active = False
        self.worker.reason = reason
        self.worker.save()
        logger.debug('worker %s disable' % self.worker.name)
        
    def append_worker_ability(self, task, cost):
        if not task:
            logger.error("worker %s append ability fail, task null")
            return
        if not cost:
            logger.error("worker %s append ability fail, cost null")
            return
        worker_ability = WorkerAbility()
        worker_ability.task = task
        worker_ability.cost = cost
        worker_ability.worker = self.worker
        worker_ability.save()
        logger.debug('woker %s append ability %s' % (self.worker.name, task.name))
            
class Athene(object):
    def __init__(self):
        '''
        Constructor
        '''
    
    def create_worker(self, name = 'N/A', address = 'N/A', contact_number = 'N/A', email = 'N/A', gender = 'N/A', desc= 'N/A'):
        worker = Worker()
        worker.name = name
        worker.address = address
        worker.contact_number = contact_number
        worker.email = email
        worker.gender = gender
        worker.desc = desc
        worker.save()
        logger.debug('create worker: %s ' % name)
        return WorkerAgent(worker)
    
    def get_worker(self, pk):
        return Worker.objects.get(pk = pk)
    
    def worker_list(self, Task):
        worker = []
        workerAbilitys = WorkerAbility.objects.filter(task=Task)
        for workerAbility in workerAbilitys:
            if workerAbility.available_task == workerAbility.max_task:
                continue
            worker.append(workerAbility.worker.pk)
        return worker
    
    def assign(self, task, worker):
        try:
            workerAbilitys = WorkerAbility.objects.filter(Q(task=task)&Q(worker=worker))
            for workerAbility in workerAbilitys:
                if workerAbility.available_task == 0:
                    continue
                workerAbility.available_task +=1
                workerAbility.save()
            logger.debug("assign task %s to worker %s", task, worker)
        except WorkerAbility.DoesNotExist:
            logger.error("worker: '%s' not WorkerAbility setting", worker)
    
    def cancel_assign(self, task, worker):
        workerAbilitys = WorkerAbility.objects.filter(Q(task=task) &Q(worker = worker))
        for workerAbility in workerAbilitys:
            workerAbility.available_task = workerAbility.available_task - 1
            workerAbility.save()
    
            
        