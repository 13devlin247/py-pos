'''
Created on 2011/10/22

@author: Administrator
'''
from pos.scheduling.models import WorkerAbility, Worker
from django.db.models.query_utils import Q

import logging
logging.basicConfig(
    level = logging.WARN,
    format = '%(asctime)s %(levelname)s %(module)s.%(funcName)s():%(lineno)s %(message)s',
)
# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Eunomia(object):
    '''
    Eunomia was the goddess of law and legislation,
    '''
    def __init__(self):
        '''
        Constructor
        '''
    
    
class Athene(object):
    def __init__(self):
        '''
        Constructor
        '''
    
    def create_worker(self, name, address, contact_number):
        worker = Worker()
        worker.name = name
        worker.address = address
        worker.contact_number = contact_number
        worker.save()
        return worker
    
    def create_worker_ability(self, worker, task, max_task, cost):
        wa = WorkerAbility()
        wa.worker = worker
        wa.task = task
        wa.max_task = max_task
        wa.cost = cost
        wa.save()
        return wa
    
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
    
            
        