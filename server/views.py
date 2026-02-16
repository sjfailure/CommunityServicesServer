import time
from http.client import HTTPResponse

import django.http
from django.conf import settings
from django.db.models.functions import JSONObject
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render




import server.models
from server import helpers
from server.models import Event


# Create your views here.

# TODO Prepare API endpoints

# TODO App connectors needed to continue API development

def main_data(request):
    data = Event.objects.select_related('service_id__provider').prefetch_related(
        # 'service_id__category',
        'service_id__type',
        'service_id__audience'
    ).all()

    json_data = {'services': {}}
    for entry in data:
        # Using entry.id as a key is fine, but GSON usually prefers an Array []
        # of objects rather than a Dictionary {} of objects for lists.
        json_data['services'][entry.id] = helpers.event_data_packer(entry)

    return JsonResponse(json_data)

def detail_view(request, event_id):
    event_data = {"event_data": helpers.pull_event_detail_view(event_id)}
    return JsonResponse(event_data)

def database_update(request):
    helpers.update_event_table()
    return HttpResponse('done')