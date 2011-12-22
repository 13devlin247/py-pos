'''
Created on 2011/10/22

@author: Administrator
'''
from django.db.models.query_utils import Q

import logging
from scheduling.models import WorkerAbility, Worker, Job, Step,\
    ClothesInformation, Task
logging.basicConfig(
    level = logging.WARN,
    format = '%(asctime)s %(levelname)s %(module)s.%(funcName)s():%(lineno)s %(message)s',
)
# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

INCOMPLETE = 'incomplete'

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
        logger.debug('Job %s created' % job.pk)
        return job

class TaskAgent(object):
    def __init__(self, instance):
        self.instance = instance
    
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
        step.status = INCOMPLETE
        step.start_at = start_at
        step.end_at = end_at
        step.active = True
        step.save()
        logger.debug("JobAgent %s create step %s success" % (self.instance.name, step.task.name))
        return step
        
    def create_clothesInformation(self, clothes_template, draft, fields = '{}'):
        if not clothes_template:
            logger.error("ClothesInformation create fail, clothes template null")
            return
        clothes_information = ClothesInformation()
        clothes_information.clothesTemplate = clothes_template
        clothes_information.hand_draft = draft
        clothes_information.fields_values = fields
        clothes_information.active = True
        clothes_information.save()
        logger.debug("clothes_information %s created" % clothes_information.pk)
        return ClothesInformationAgent(clothes_information)

class ClothesInformationAgent(object):
    def __init__(self, instance):
        self.instance = instance
        
    def update(self, value):
        if not value:
            logger.error('ClothesInformation %s update fail, value null', self.instance.pk)
            return
        self.instance.fields_values = value
        self.instance.save()
        logger.debug('ClothesInformation %s update success', self.instance.pk)
    
    def disable(self, reason):
        if not reason:
            logger.error('ClothesInformation %s disable fail, reason null', self.instance.pk)
            return
        self.instance.active = False
        self.instance.reason = reason
        self.instance.save()
        logger.debug('ClothesInformation %s disable success', self.instance.pk)
        
class Supervisor(object):
    def __init__(self):
        pass

    def filter_worker_ability(self, task):
        if not task:
            logger.error(" Supervisor filter worker fail, task null")
            return Worker.objects.filter(active = True)
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
    
            
        