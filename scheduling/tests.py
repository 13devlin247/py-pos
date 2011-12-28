"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from scheduling.models import Job
from scheduling.mythology import Athene, SchedulerFactory, Supervisor, TaskAgent


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
        
class CreateJobTest(TestCase):
    def test_JobScheduler(self):
        factory = SchedulerFactory()
        job_agent = factory.register_job(name = 'test-job', desc = 'testing job', start_at = '2011-12-11', end_at = '2011-12-20', creator)
        assert job_agent is not None
        
        tasks = factory.tasks()
        sp = Supervisor()
        workers = sp.filter_worker(tasks[0])
        assert len(workers) != 0
        
        worker = workers[0]
        task = tasks[0]
        cost = 10.0
        
        step_agent = job_agent.create_step(task = task, worker = worker, cost = cost, start_at = '2011-12-11', end_at = '2011-12-15')
        assert step_agent is not None
        
        # @TODO DESIGN clothes_template
        clothes_information_agent = job_agent.choose_clothes(clothes_template = clothes_template, draft = draft, fields = '{}')
        assert clothes_information_agent is not None
                
        # clothes_information_agent
        clothes_information_agent.update(clothesTemplate = clothesTemplate, fieldValues = '{}', hand_draft = hand)
        clothes_information_agent.disable('reason')
        
        #Job Agent
        job_agent.update(name = name, cost = cost, desc = desc, start_at = '', end_at = '', status = '')
        job_agent.disable('reason')
                
        # Scheduler Factory
        jobs = factory.overdue_job(date = date)
        steps = factory.overdue_step(date = date)
        steps = factory.job_steps(job = job, task = task)
        tasks = factory.tasks()
                
        # Step Agent 
        step_agent.change_worker(worker)
        step_agent.change_start_at('')
        step_agent.change_end_at('')
        step_agent.change_status('')
        step_agent.disable('reason')
        step_agent.change_cost('')
        
        # Task Agent
        task_agent = TaskAgent(task)
        task_agent.disable('reason')
        
        # worker 
        sp = Athene()
        worker_agent = sp. (name = '', address = '', contact_number = '', email = '', gender = '', desc= '')
        worker_agent.append_worker_ability(task = task, cost = cost)
