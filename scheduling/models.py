from django.db import models

# Create your models here.
class ClothTemplate(models.Model):
    image_template = models.ImageField(upload_to='static/images/upload/', max_length=100)

class Job(models.Model):
    image_template = models.ForeignKey(ClothTemplate)
    image_upload = models.ImageField(upload_to='static/images/upload/', max_length=100, null=True)
    description = models.TextField(blank=True, null=True)
    start_at = models.DateTimeField(auto_now_add=False)
    end_at = models.DateTimeField(auto_now_add=False)
    create_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=100, null=True)
    active = models.BooleanField(True)
    reason = models.CharField(max_length=100, null=True)
    cost = models.DecimalField(max_digits=100, decimal_places=2, null=True)

class Task(models.Model):
    description = models.TextField(blank=True)
    active = models.BooleanField(True)
    reason = models.CharField(max_length=100, null=True)
    create_at = models.DateTimeField(auto_now_add=True)
            
class Worker(models.Model):
    name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=100, null=True)
    address = models.CharField(max_length=100, null=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(True)
    reason = models.CharField(max_length=100, null=True)
    create_at = models.DateTimeField(auto_now_add=True)
                        
class WorkerAbility(models.Model):
    task = models.ForeignKey(Task)
    worker = models.ForeignKey(Worker)
    max_task = models.DecimalField(max_digits=100, decimal_places=0)
    available_task = models.DecimalField(max_digits=100, decimal_places=0, null = True)
    cost = models.DecimalField(max_digits=100, decimal_places=2, null = True)
    active = models.BooleanField(True)
    reason = models.CharField(max_length=100, null=True)
    create_at = models.DateTimeField(auto_now_add=True)

class Step(models.Model):
    task = models.ForeignKey(Task)
    worker = models.ForeignKey(Worker)
    cost = models.DecimalField(max_digits=100, decimal_places=2, null = True)
    status = models.CharField(max_length=100, null=True)
    active = models.BooleanField(True)
    reason = models.CharField(max_length=100, null=True)
    create_at = models.DateTimeField(auto_now_add=True)
                        
                        
