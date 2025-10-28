import time

from django.db.models.functions import JSONObject
from django.http import JsonResponse
from django.shortcuts import render

import server.models
from server import helpers
from server.models import Events


# Create your views here.

# TODO Prepare API endpoints

# TODO App connectors needed to continue API development

def main_data(request):
    server.models.update_events_calendar()
    data = Events.objects.select_related(
                        'service_id',                 # Get related Services
                        'service_id__type',          # Get related ServiceType
                        'service_id__provider',       # Get related Providers
                        'service_id__category',       # Get related ServicesCategories
                        'service_id__audience'        # Get related Audience
                         ).all()
    json_data = {'services': {}}
    for entry in data:
        print(f'data for {entry.id} processed')
        json_data['services'][entry.id] = helpers.event_data_packer(entry)
    return JsonResponse(json_data)
