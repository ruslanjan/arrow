from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max, Q
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404

from contests.models import Contest, ContestTask
from polygon.models import Problem
from utils import reorder_models_indexes

def contest_control_panel(request):
    return render(request, 'contests/contest/contest_control_panel.html')