from django.db import models
from django.contrib.auth.models import User
from django.forms.models import ModelForm

# Create your models here.
class ClothesTemplate(models.Model):
    draft = models.ImageField(upload_to='static/images/upload/', max_length=100)
    name = models.CharField(max_length=100, null=True)
    fields = models.TextField(null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(True)
    reason = models.CharField(max_length=100, null=True, blank=True)    
    
    def __unicode__(self):
        return self.name

class ClothesTemplateForm(ModelForm):
    class Meta:
        model = ClothesTemplate
        exclude = ('active', 'reason')

class Job(models.Model):
    name = models.CharField(max_length=100, null=True)
    cost = models.DecimalField(max_digits=100, decimal_places=2, null=True)
    description = models.TextField(blank=True, null=True)
    start_at = models.DateTimeField(auto_now_add=False)
    end_at = models.DateTimeField(auto_now_add=False)
    status = models.DecimalField(max_digits=100, decimal_places=2, null=True)
    creator = models.ForeignKey(User, related_name="create_by")
    create_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(True)
    reason = models.CharField(max_length=100, null=True, blank=True)

    def __unicode__(self):
        return self.name

    
class JobForm(ModelForm):
    class Meta:
        model = Job
        exclude = ('active', 'reason', 'creator' , 'status', 'cost')

class ClothesChoosed(models.Model):
    job = models.ForeignKey(Job)
    clothesTemplate = models.ForeignKey(ClothesTemplate)
    hand_draft = models.ImageField(upload_to='static/images/upload/', max_length=100, null=True)
    fields_values = models.TextField(null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(True)
    reason = models.CharField(max_length=100, null=True, blank=True)

class Task(models.Model):
    name = models.CharField(max_length=100, null=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(True)
    reason = models.CharField(max_length=100, null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return self.name
    
    def natural_key(self):
        return self.name      
              
class Worker(models.Model):
    name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=75, null=True, blank=True)
    address = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(True)
    reason = models.CharField(max_length=100, null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return self.name
    
    def natural_key(self):
        return "%s@%s" % (self.name, self.pk)
                
class WorkerAbility(models.Model):
    task = models.ForeignKey(Task)
    worker = models.ForeignKey(Worker, related_name="worker")
    cost = models.DecimalField(max_digits=100, decimal_places=2, null = True)
    active = models.BooleanField(True)
    reason = models.CharField(max_length=100, null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return self.task.name  + " - " + self.worker.name
    

        
class Step(models.Model):
    job = models.ForeignKey(Job)
    task = models.ForeignKey(Task)
    worker = models.ForeignKey(Worker)
    cost = models.DecimalField(max_digits=100, decimal_places=2, null = True)
    status = models.CharField(max_length=100, null=True)
    start_at = models.DateTimeField(auto_now_add=False)
    end_at = models.DateTimeField(auto_now_add=False)
    active = models.BooleanField(True)
    reason = models.CharField(max_length=100, null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True)
                        
                        
