from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from tasks.models import Task

from datetime import date

from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics import renderPDF
from reportlab.lib.units import inch
from reportlab.rl_config import defaultPageSize

import base64
import uuid
import hashlib


def list(request):
    """ This view will present all tasks with status and optional filtering.
    """
    task_list = Task.objects.all()
    return render(request,'tasks/list.html',{'task_list': task_list})
