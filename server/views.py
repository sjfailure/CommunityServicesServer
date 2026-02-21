import time
from http.client import HTTPResponse

import django.http
from django.conf import settings
from django.db.models.functions import JSONObject
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render

from server import helpers
from server.models import Event

# Create your views here.

def main_data(request):
    data = Event.objects.select_related(
        'service_id__provider'
    ).prefetch_related(
        # 'service_id__category',
        'service_id__type',
        'service_id__audience'
    ).all()

    json_data = {'services': {}}
    for entry in data:
        # Using entry.id as a key is fine, but GSON usually prefers an
        # Array [] of objects rather than a Dictionary {} of objects
        # for lists.
        json_data['services'][entry.id] = (
            helpers.event_data_packer(entry))

    # include all Category and Type information
    json_data.setdefault(
        'categories/types', helpers.get_all_categories_types())

    # include all Audiences
    json_data.setdefault(
        'audiences', helpers.get_all_audiences()
    )

    return JsonResponse(json_data)

def detail_view(request, event_id):
    event_data = {
        "event_data": helpers.pull_event_detail_view(event_id)
    }
    return JsonResponse(event_data)

def database_update(request):
    helpers.update_event_table()
    return HttpResponse('done')
