import json

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django_ratelimit.decorators import ratelimit

from server import helpers
from server.models import Event, ServiceType, Announcement


# Create your views here.
@ratelimit(key='ip', rate='20/h', method='GET')
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
        services_dict[entry.id] = helpers.event_data_packer(
            entry,
            category_map
        )

    json_data = {
        'services': services_dict,
        'categories/types': helpers.get_all_categories_types(),
        'audiences': helpers.get_all_audiences(),
        'announcement': None,  # Default value
        'feedback_key': helpers.get_feedback_key()
    }

    try:
        json_data['announcement'] = (Announcement.objects.latest('date')
                                     .announcement)
    except ObjectDoesNotExist:
        pass  # Keep announcement as None

    return JsonResponse(json_data)

@ratelimit(key='ip', rate='20/h', method='GET')
def detail_view(request, event_id):
    event_data = {
        "event_data": helpers.pull_event_detail_view(event_id)
    }
    return JsonResponse(event_data)

@ratelimit(key='ip', rate='20/h', method='GET')
def database_update(request):
    record_start = timezone.now()
    helpers.update_event_table()
    return HttpResponse(
        f'done : {timezone.now() - record_start} seconds'
    )

@ratelimit(key='ip', rate='20/h', method='GET')
def provider_contact_list(request):
    return JsonResponse(helpers.get_all_providers_json_format())

@csrf_exempt
@ratelimit(key='ip', rate='10/h', method='POST')
def receive_feedback(request):
    if request.method == "POST":
        try:
            incoming_data = json.loads(request.body)
            helpers.insert_new_feedback(
                incoming_data.get('message'),
                incoming_data.get('os_data'),
                incoming_data.get('device_data'),
                incoming_data.get('user_key'),
            )
            return HttpResponse(f'received')
        except ValueError:
            return HttpResponse('rejected')
    return HttpResponse('failed')

