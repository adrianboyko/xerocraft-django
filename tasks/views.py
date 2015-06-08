from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext, loader
from tasks.models import Task

def index(request):
    template = loader.get_template('tasks/index.html')
    return HttpResponse(template.render(None))

def list(request):
    """ This view will present all tasks with status and optional filtering.
    """
    task_list = Task.objects.all()
    template = loader.get_template('tasks/list.html')
    context = RequestContext(request, {'task_list': task_list})
    return HttpResponse(template.render(context))
