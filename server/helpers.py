def get_all_entries():
    pass

def get_service_type(event_query_set_obj):
    return event_query_set_obj.service_id.type.type

def get_service_category(event_query_set_obj):
    return event_query_set_obj.service_id.category.category

def get_provider_name(event_query_set_obj):
    return event_query_set_obj.service_id.provider.name

def get_service_location(event_query_set_obj):
    return event_query_set_obj.service_id.provider.address

def get_provider_phone_number(event_query_set_obj):
    return event_query_set_obj.service_id.provider.phone

def get_service_target_audience(event_query_set_obj):
    return event_query_set_obj.service_id.audience.audience

def event_data_packer(entry):
    return {
        'provider_name': get_provider_name(entry),
        'service_category': get_service_category(entry),
        'service_type': get_service_type(entry),
        'address': get_service_location(entry),
        'phone': get_provider_phone_number(entry),
        'start_time': entry.date.strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': entry.service_id.end_time.strftime('%Y-%m-%d %H:%M:%S'),
        'audience': get_service_target_audience(entry)
    }