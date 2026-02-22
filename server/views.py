import time
from http.client import HTTPResponse

import django.http
from django.conf import settings
from django.db.models.functions import JSONObject
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render

from server import helpers
from server.models import Event, ServiceType


# Create your views here.

def main_data(request):
    # 1. Pre-fetch the category mapping ONCE
    category_map = {
        st.type: st.category.category
        for st in ServiceType.objects.select_related('category').all()
    }

    # 2. Optimize the main QuerySet
    # We must prefetch the specific fields used in event_data_packer
    data = Event.objects.select_related(
        'service_id__provider'
    ).prefetch_related(
        'service_id__type',
        'service_id__audience'
    ).all()

    # 3. Build the response
    services_dict = {}
    for entry in data:
        # Pass the pre-computed map into the helper
        services_dict[entry.id] = helpers.event_data_packer(entry,
                                                            category_map)

    json_data = {
        'services': services_dict,
        'categories/types': helpers.get_all_categories_types(),
        'audiences': helpers.get_all_audiences()
    }

    return JsonResponse(json_data)

def detail_view(request, event_id):
    event_data = {
        "event_data": helpers.pull_event_detail_view(event_id)
    }
    return JsonResponse(event_data)

def database_update(request):
    helpers.update_event_table()
    return HttpResponse('done')
