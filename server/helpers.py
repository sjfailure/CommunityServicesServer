import datetime
import re
from datetime import time

import pytz
from MySQLdb import NUMBER
from django.core.exceptions import MultipleObjectsReturned
from django.db import IntegrityError, transaction

from server.models import Event, Provider, ServiceCategory, ServiceType, Audience, Service

hard_coded_data_dictionary = {
    'swope laundry monday': {
        'provider': 'Swope Health Services',
        'address': '3801 Dr. Martin Luther King, Jr. Blvd.',
        'service_type': 'Laundry',
        'category': 'Hygiene',
        'audience': 'Unhoused or Experiencing Homelessness',
        'day': 0,
        'note': '1 load per week, showers first come, first served',
        'start_time': '08:00:00',
        'end_time': '12:00:00',
        'period': 0,
    },
    'swope shower monday': {
        'provider': 'Swope Health Services',
        'address': '3801 Dr. Martin Luther King, Jr. Blvd.',
        'service_type': 'Showers',
        'category': 'Hygiene',
        'audience': 'Unhoused or Experiencing Homelessness',
        'day': 0,
        'note': '1 load per week, showers first come, first served',
        'start_time': '08:00:00',
        'end_time': '12:00:00',
        'period': 0,
    },
    'swope laundry friday': {
        'provider': 'Swope Health Services',
        'address': '3801 Dr. Martin Luther King, Jr. Blvd.',
        'service_type': 'Laundry',
        'category': 'Hygiene',
        'audience': 'Unhoused or Experiencing Homelessness',
        'day': 4,
        'note': '1 load per week, showers first come, first served',
        'start_time': '08:00:00',
        'end_time': '14:00:00',
        'period': 0,
    },
    'swope shower friday': {
        'provider': 'Swope Health Services',
        'address': '3801 Dr. Martin Luther King, Jr. Blvd.',
        'service_type': 'Showers',
        'category': 'Hygiene',
        'audience': 'Unhoused or Experiencing Homelessness',
        'day': 4,
        'note': '1 load per week, showers first come, first served',
        'start_time': '08:00:00',
        'end_time': '14:00:00',
        'period': 0,
    },
    'TLFRC womens shower monday': {
        'provider': 'TLFRC: Emancipation Station',
        'address': '717 E. 31st St., Emancipation Station',
        'service_type': 'Showers',
        'category': 'Hygiene',
        'audience': 'Women',
        'day': 0,
        'note': 'lunch at 12pm, women only',
        'start_time': '08:30:00',
        'end_time': '14:30:00',
        'period': 0,
    },
    'TLFRC womens shower tuesday': {
        'provider': 'TLFRC: Emancipation Station',
        'address': '717 E. 31st St., Emancipation Station',
        'service_type': 'Showers',
        'category': 'Hygiene',
        'audience': 'Women',
        'day': 1,
        'note': 'lunch at 12pm, women only',
        'start_time': '08:30:00',
        'end_time': '14:30:00',
        'period': 0,
    },
    'TLFRC womens shower wednesday': {
        'provider': 'TLFRC: Emancipation Station',
        'address': '717 E. 31st St., Emancipation Station',
        'service_type': 'Showers',
        'category': 'Hygiene',
        'audience': 'Women',
        'day': 2,
        'note': 'lunch at 12pm, women only',
        'start_time': '08:30:00',
        'end_time': '14:30:00',
        'period': 0,
    },
    'TLFRC womens shower thursday': {
        'provider': 'TLFRC: Emancipation Station',
        'address': '717 E. 31st St., Emancipation Station',
        'service_type': 'Showers',
        'category': 'Hygiene',
        'audience': 'Women',
        'day': 3,
        'note': 'lunch at 12pm, women only',
        'start_time': '08:30:00',
        'end_time': '14:30:00',
        'period': 0,
    },
    'TLFRC womens shower friday': {
        'provider': 'TLFRC: Emancipation Station',
        'address': '717 E. 31st St., Emancipation Station',
        'service_type': 'Showers',
        'category': 'Hygiene',
        'audience': 'Women',
        'day': 4,
        'note': 'lunch at 12pm, women only',
        'start_time': '08:30:00',
        'end_time': '14:30:00',
        'period': 0,
    },
    'TLFRC laundry tuesday': {
        'provider': 'TLFRC: Emancipation Station',
        'address': '717 E. 31st St., Emancipation Station',
        'service_type': 'Laundry',
        'category': 'Hygiene',
        'audience': 'Everyone',
        'day': 1,
        'note': 'not same day service',
        'start_time': '08:30:00',
        'end_time': '14:30:00',
        'period': 0,
    },
    'TLFRC laundry wednesday': {
        'provider': 'TLFRC: Emancipation Station',
        'address': '717 E. 31st St., Emancipation Station',
        'service_type': 'Laundry',
        'category': 'Hygiene',
        'audience': 'Everyone',
        'day': 2,
        'note': 'not same day service',
        'start_time': '08:30:00',
        'end_time': '14:30:00',
        'period': 0,
    },
    'TLFRC laundry thursday': {
        'provider': 'TLFRC: Emancipation Station',
        'address': '717 E. 31st St., Emancipation Station',
        'service_type': 'Laundry',
        'category': 'Hygiene',
        'audience': 'Everyone',
        'day': 3,
        'note': 'not same day service',
        'start_time': '08:30:00',
        'end_time': '14:30:00',
        'period': 0,
    },
    'Westport Pres shower Thursday': {
        'provider': 'Westport Presbyterian Church',
        'address': '201 Westport Rd.',
        'service_type': 'Shower',
        'category': 'Hygiene',
        'audience': 'Women, Trans, and Non-Confirming',
        'day': 3,
        'note': 'Women, Trans, Gender NonConforming people only',
        'start_time': '17:30:00',
        'end_time': '19:00:00',
        'period': 0,
    },
    'Westport Press shower sunday': {
        'provider': 'Westport Presbyterian Church',
        'address': '201 Westport Rd.',
        'service_type': 'Shower',
        'category': 'Hygiene',
        'audience': 'Everyone',
        'day': 6,
        'note': '',
        'start_time': '07:30:00',
        'end_time': '09:30:00',
        'period': 0,
    },
    'Catholic Charities: SSVF general mon': {
        'provider': 'Catholic Charities: SSVF',
        'address': '8001 Longview Rd., Kansas City, MO 64134',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 0,
        'note': '',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'Catholic Charities: SSVF general tue': {
        'provider': 'Catholic Charities: SSVF',
        'address': '8001 Longview Rd., Kansas City, MO 64134',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 1,
        'note': '',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'Catholic Charities: SSVF general wed': {
        'provider': 'Catholic Charities: SSVF',
        'address': '8001 Longview Rd., Kansas City, MO 64134',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 2,
        'note': '',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'Catholic Charities: SSVF general thu': {
        'provider': 'Catholic Charities: SSVF',
        'address': '8001 Longview Rd., Kansas City, MO 64134',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 3,
        'note': '',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'Catholic Charities: SSVF general fri': {
        'provider': 'Catholic Charities: SSVF',
        'address': '8001 Longview Rd., Kansas City, MO 64134',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 4,
        'note': '',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'kc va general mon': {
        'provider': 'Kansas City VA Medical Center',
        'address': '4801 E. Linwood Ave.',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 0,
        'note': '',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'kc va general tue': {
        'provider': 'Kansas City VA Medical Center',
        'address': '4801 E. Linwood Ave.',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 1,
        'note': '',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'kc va general wed': {
        'provider': 'Kansas City VA Medical Center',
        'address': '4801 E. Linwood Ave.',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 2,
        'note': '',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'kc va general thu': {
        'provider': 'Kansas City VA Medical Center',
        'address': '4801 E. Linwood Ave.',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 3,
        'note': '',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'kc va general fri': {
        'provider': 'Kansas City VA Medical Center',
        'address': '4801 E. Linwood Ave.',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 4,
        'note': '',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'reStart vets mon': {
        'provider': 'reStart, SSVF',
        'address': '918 E. 9th St.',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 0,
        'note': '',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'reStart vets tue': {
        'provider': 'reStart, SSVF',
        'address': '918 E. 9th St.',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 1,
        'note': '',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'reStart vets wed': {
        'provider': 'reStart, SSVF',
        'address': '918 E. 9th St.',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 2,
        'note': '',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'reStart vets thu': {
        'provider': 'reStart, SSVF',
        'address': '918 E. 9th St.',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 3,
        'note': '',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'reStart vets fri': {
        'provider': 'reStart, SSVF',
        'address': '918 E. 9th St.',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 4,
        'note': '',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'veterans comm proj general mon': {
        'provider': 'Veterans Community Project: Outreach Center',
        'address': '8825 Troost Ave.',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 0,
        'note': '',
        'start_time': '09:00:00',
        'end_time': '16:00:00',
        'period': 0,
    },
    'veterans comm proj general tue': {
        'provider': 'Veterans Community Project: Outreach Center',
        'address': '8825 Troost Ave.',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 1,
        'note': '',
        'start_time': '09:00:00',
        'end_time': '16:00:00',
        'period': 0,
    },
    'veterans comm proj general wed': {
        'provider': 'Veterans Community Project: Outreach Center',
        'address': '8825 Troost Ave.',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 2,
        'note': '',
        'start_time': '09:00:00',
        'end_time': '16:00:00',
        'period': 0,
    },
    'veterans comm proj general thu': {
        'provider': 'Veterans Community Project: Outreach Center',
        'address': '8825 Troost Ave.',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 3,
        'note': '',
        'start_time': '09:00:00',
        'end_time': '16:00:00',
        'period': 0,
    },
    'veterans comm proj general fri': {
        'provider': 'Veterans Community Project: Outreach Center',
        'address': '8825 Troost Ave.',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 4,
        'note': '',
        'start_time': '09:00:00',
        'end_time': '13:00:00',
        'period': 0,
    },
    'veterans comm proj 4th wed commissary-food': {
        'provider': 'Veterans Community Project: Outreach Center',
        'address': '8825 Troost Ave.',
        'service_type': 'Pantry',
        'audience': "Military Service Members and Veterans",
        'day': 2,
        'note': 'Food, clothing, and more, free of charge',
        'start_time': '09:00:00',
        'end_time': '15:00:00',
        'period': 4,
    },
    'veterans comm proj 4th wed commissary-clothes': {
        'provider': 'Veterans Community Project: Outreach Center',
        'address': '8825 Troost Ave.',
        'service_type': 'Clothes',
        'audience': "Military Service Members and Veterans",
        'day': 2,
        'note': 'Food, clothing, and more, free of charge',
        'start_time': '09:00:00',
        'end_time': '15:00:00',
        'period': 4,
    },
    'veterans comm proj 4th wed commissary-and more(?)': {
        'provider': 'Veterans Community Project: Outreach Center',
        'address': '8825 Troost Ave.',
        'service_type': 'General',
        'audience': "Military Service Members and Veterans",
        'day': 2,
        'note': 'Food, clothing, and more, free of charge',
        'start_time': '09:00:00',
        'end_time': '15:00:00',
        'period': 4,
    },
    'HALO art&ed mon': {
        'provider': 'The HALO Foundation',
        'address': '1600 Genessee St., Ste. 140',
        'service_type': 'General',
        'audience': 'Children and Teens',
        'day': 0,
        'note': 'ages 4-24 - Art & educational programs, food, dignity items etc., transitional living program youth ages 16-21',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'HALO art&ed tue': {
        'provider': 'The HALO Foundation',
        'address': '1600 Genessee St., Ste. 140',
        'service_type': 'General',
        'audience': 'Children and Teens',
        'day': 1,
        'note': 'ages 4-24 - Art & educational programs, food, dignity items etc., transitional living program youth ages 16-21',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'HALO art&ed wed': {
        'provider': 'The HALO Foundation',
        'address': '1600 Genessee St., Ste. 140',
        'service_type': 'General',
        'audience': 'Children and Teens',
        'day': 2,
        'note': 'ages 4-24 - Art & educational programs, food, dignity items etc., transitional living program youth ages 16-21',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'HALO art&ed thu': {
        'provider': 'The HALO Foundation',
        'address': '1600 Genessee St., Ste. 140',
        'service_type': 'General',
        'audience': 'Children and Teens',
        'day': 3,
        'note': 'ages 4-24 - Art & educational programs, food, dignity items etc., transitional living program youth ages 16-21',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'HALO art&ed fri': {
        'provider': 'The HALO Foundation',
        'address': '1600 Genessee St., Ste. 140',
        'service_type': 'General',
        'audience': 'Children and Teens',
        'day': 4,
        'note': 'ages 4-24 - Art & educational programs, food, dignity items etc., transitional living program youth ages 16-21',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'HALO food mon': {
        'provider': 'The HALO Foundation',
        'address': '1600 Genessee St., Ste. 140',
        'service_type': 'Pantry',
        'audience': 'Children and Teens',
        'day': 0,
        'note': 'ages 4-24 - Art & educational programs, food, dignity items etc., transitional living program youth ages 16-21',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'HALO food tue': {
        'provider': 'The HALO Foundation',
        'address': '1600 Genessee St., Ste. 140',
        'service_type': 'Pantry',
        'audience': 'Children and Teens',
        'day': 1,
        'note': 'ages 4-24 - Art & educational programs, food, dignity items etc., transitional living program youth ages 16-21',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'HALO food wed': {
        'provider': 'The HALO Foundation',
        'address': '1600 Genessee St., Ste. 140',
        'service_type': 'Pantry',
        'audience': 'Children and Teens',
        'day': 2,
        'note': 'ages 4-24 - Art & educational programs, food, dignity items etc., transitional living program youth ages 16-21',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'HALO food thu': {
        'provider': 'The HALO Foundation',
        'address': '1600 Genessee St., Ste. 140',
        'service_type': 'Pantry',
        'audience': 'Children and Teens',
        'day': 3,
        'note': 'ages 4-24 - Art & educational programs, food, dignity items etc., transitional living program youth ages 16-21',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'HALO food fri': {
        'provider': 'The HALO Foundation',
        'address': '1600 Genessee St., Ste. 140',
        'service_type': 'General',
        'audience': 'Pantry',
        'day': 4,
        'note': 'ages 4-24 - Art & educational programs, food, dignity items etc., transitional living program youth ages 16-21',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'HALO housing mon': {
        'provider': 'The HALO Foundation',
        'address': '1600 Genessee St., Ste. 140',
        'service_type': 'Housing',
        'audience': 'Children and Teens',
        'day': 0,
        'note': 'ages 4-24 - Art & educational programs, food, dignity items etc., transitional living program youth ages 16-21',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period':0,
    },
    'HALO housing tue': {
        'provider': 'The HALO Foundation',
        'address': '1600 Genessee St., Ste. 140',
        'service_type': 'Housing',
        'audience': 'Children and Teens',
        'day': 1,
        'note': 'ages 4-24 - Art & educational programs, food, dignity items etc., transitional living program youth ages 16-21',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'HALO housing wed': {
        'provider': 'The HALO Foundation',
        'address': '1600 Genessee St., Ste. 140',
        'service_type': 'Housing',
        'audience': 'Children and Teens',
        'day': 2,
        'note': 'ages 4-24 - Art & educational programs, food, dignity items etc., transitional living program youth ages 16-21',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'HALO housing thu': {
        'provider': 'The HALO Foundation',
        'address': '1600 Genessee St., Ste. 140',
        'service_type': 'Housing',
        'audience': 'Children and Teens',
        'day': 3,
        'note': 'ages 4-24 - Art & educational programs, food, dignity items etc., transitional living program youth ages 16-21',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    'HALO housing fri': {
        'provider': 'The HALO Foundation',
        'address': '1600 Genessee St., Ste. 140',
        'service_type': 'Housing',
        'audience': 'Children and Teens',
        'day': 4,
        'note': 'ages 4-24 - Art & educational programs, food, dignity items etc., transitional living program youth ages 16-21',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },
    # general behavioral health general health ob/gym
    'Lutheran FCS general mon': {
        'provider': 'Lutheran Family and Children\'s Services of Missouri',
        'address': '1 E. Armour Blvd., Ste 102',
        'service_type': 'General',
        'audience': 'Children and Teens',
        'day': 0,
        'note': 'Free counseling ages 3-19 for Jackson County residents, parenting & pregnancy services, adoptive & birth parent services',
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'period': 0,
    },

}

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
        'email': entry.service_id.provider.email,
        'start_time': entry.date.strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': entry.end.strftime('%Y-%m-%d %H:%M:%S'),
        'audience': get_service_target_audience(entry),
        'notes': entry.service_id.note,
    }

def pull_event_detail_view(event_id):
    event = Event.objects.get(id=event_id)
    collected_data = {
        'id': event_id,
        'start': event.date,
        'end': event.end,
        'service_id': event.service_id.id,
        'category': event.service_id.category.category,
        'type': event.service_id.type.type,
        'provider': event.service_id.provider.name,
        'address': event.service_id.provider.address,
        'phone': event.service_id.provider.phone,
        'email_address': event.service_id.provider.email,
        'note': event.service_id.note,
        'audience': event.service_id.audience.audience,
    }
    return collected_data

def insert_new_service_event(category, service_type, day, start_time, end_time, periodic, audience, provider, note=None, report_status=False):
    if not isinstance(category, ServiceCategory):
        raise TypeError(f"Field '{category}' must be ServiceCategory.")
    if not isinstance(service_type, ServiceType):
        raise TypeError(f"Field '{service_type}' must be ServiceType.")
    if not isinstance(audience, Audience):
        raise TypeError(f"Field '{audience}' must be Audience.")
    if not isinstance(provider, Provider):
        raise TypeError(f"Field '{provider}' must be Provider.")
    if not isinstance(day, int):
        raise TypeError(f"Field '{day}' must be int.")
    if day < 0 or day > 6:
        raise ValueError(f"Field '{day}' must be between 0 and 6.")
    if not isinstance(start_time, str):
        raise TypeError(f"Field '{start_time}' must be a str in 'HH:mm:ss' format.")
    time_pattern = r"^([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$"
    if not re.match(time_pattern, start_time):
        raise ValueError(f"Field '{start_time}' must be in 'HH:mm:ss' format.")
    if not isinstance(end_time, str):
        raise TypeError(f"Field '{end_time}' must be a str in 'HH:mm:ss' format.")
    if not re.match(time_pattern, end_time):
        raise ValueError(f"Field '{end_time}' must be in 'HH:mm:ss' format.")
    if not isinstance(periodic, int):
        raise TypeError(f"Field '{periodic}' must be int.")
    if not isinstance(note, str) and note is not None:
        raise TypeError(f"Field '{note}' must be str in 'Note' format.")
    time_zone = pytz.timezone("America/Chicago")
    h1, m1, s1 = start_time.split(":")
    h2, m2, s2 = end_time.split(":")
    start = datetime.time(hour=int(h1), minute=int(m1))
    end = datetime.time(hour=int(h2), minute=int(m2))
    with transaction.atomic():
        service, boolean_return = Service.objects.get_or_create(category=category,
                                      type=service_type,
                                      start_time=start,
                                      end_time=end,
                                      provider=provider,
                                      audience=audience,
                                      day=day,
                                      periodic=periodic,
                                      defaults = {'note': note or ''}
                                      )
    if report_status:
        return service, boolean_return
    return service


def insert_new_provider(**kwargs):
    # 1. Type Checking
    for key, value in kwargs.items():
        if value is not None and not isinstance(value, str):
            raise TypeError(f"Field '{key}' must be str, not {type(value).__name__}")

    # 2. Create the object
    # If 'name' isn't in kwargs, Django uses the model default ('No Provider')
    try:
        with transaction.atomic():
            provider = Provider.objects.create(**kwargs)
    except IntegrityError:
        return None

    # Note: .create() calls .save() automatically, so x.save() is redundant!
    return provider


def retrieve_provider(name, address=None):
    try:
        # If name is unique, this is all you need
        return Provider.objects.get(name=name)

    except Provider.DoesNotExist:
        return None

    except MultipleObjectsReturned:
        # This triggers if more than one provider has that name
        if address:
            # Narrow the search using the address
            try:
                return Provider.objects.get(name=name, address=address)
            except Provider.DoesNotExist:
                return None
        else:
            # You found many, but didn't provide an address to narrow it down
            raise LookupError(f"Multiple providers named '{name}' found. Address required to disambiguate.")

def insert_new_service_category(category):
    x = ServiceCategory.objects.get_or_create(category=category)
    return x[0]

def insert_new_service_type(type, category):
    if not isinstance(category, ServiceCategory):
        raise TypeError(f"Field '{type}' must be ServiceCategory.")

    x = ServiceType.objects.get_or_create(type=type, category=category)
    return x[0]

def retrieve_service_type(type):
    try:
        return ServiceType.objects.get(type=type)
    except ServiceType.DoesNotExist:
        return None

def retrieve_service_category(category):
    try:
        return ServiceCategory.objects.get(category=category)
    except ServiceCategory.DoesNotExist:
        return None

def insert_new_audience(audience):
    x = Audience.objects.get_or_create(audience=audience)
    return x[0]

def retrieve_audience(audience):
    try:
        return Audience.objects.get(audience=audience)
    except Audience.DoesNotExist:
        return None

def create_initial_data(data_dict=None):
    pre_populate_audience()
    pre_populate_providers()
    pre_populate_categories()
    pre_populate_service_type()

    if not data_dict or data_dict is None:
        data_dict = hard_coded_data_dictionary

    for service in data_dict:
        service_dict = data_dict[service]
        provider = retrieve_provider(service_dict['provider_name'], service_dict['address'])
        service_type = retrieve_service_type(service_dict['service_type'])
        category = retrieve_service_category(service_dict['category'])
        audience = retrieve_audience(service_dict['audience'])
        day = service_dict['day']
        start_time = service_dict['start_time']
        end_time = service_dict['end_time']
        note = service_dict['note']
        periodic = service_dict['period']
        insert_new_service_event(category, service_type, day, start_time, end_time, periodic, audience, provider, note)


def pre_populate_providers(providers=None):
    if not providers or providers is None:
        providers= {'AccessKC': [None, '816-276-7517'],
                 'Bishop Sullivan Center: AccessKC Site': ['6435 Truman Rd.', '816-231-0984'],
                 'Bishop Sullivan: One City Cafe': ['3936 Troost Ave.', '816-561-8515'],
                 'Care Beyond the Boulevard: Independence Blvd. Christian Church': ['606 Gladstone Blvd.', None],
                 'Care Beyond the Boulevard: Cherith Brook Catholic Worker': ['3308 E. 12th St.', None],
                 'Catholic Charities: Welcome Center': ['8001 Longview Rd., Kansas City, MO 64134', '816-221-4377'],
                 'Catholic Charities: SSVF': ['8001 Longview Rd., Kansas City, MO 64134', '816-659-8263'],
                 'Central Presbyterian Church': ['3501 Campbell St.', '816-931-2515p2'],
                 'City Union Mission Family Center': ['1310 Wabash Ave.', '816-474-4599'],
                 'City Union Mission Men\'s Shelter': ['1108 E. 10th St.', '816-474-4599'],
                 'Community LINC': ['4012 Troost Ave.', '816-531-3727'],
                 'COMMUNITY RESOURCES @ CENTRAL LIBRARY': ['14 W. 10th St., Central Library, 3rd Floor',
                                                           '816-701-3767'],
                 'Family Promise of the Northland': ['10th & Baltimore Ave.', None],
                 'Fourth Wednesday Commissary': [None, None],
                 'Heartland Center for Behavioral Change': [None, '816-421-6670'],
                 'HOPE FAITH HOMELESS ASSISTANCE CAMPUS': ['705 Virginia Ave.', '816-471-4673'],
                 'Hope House': [None, '816-461-4673'],
                 'Housing Authority of KC': ['3822 Summit St', '816-968-4100'],
                 'Journey to New Life': ['3120 Troost Ave.', '816-960-4808'],
                 'Kansas City VA Medical Center': ['4801 E. Linwood Ave.', '816-861-4700'],
                 'KC CARE Health Center': [None, '816-753-5144'],
                 'KC Health Department': ['3515 Broadway Blvd.', '816-513-6008'],
                 'KC Health Department: Dental': ['2340 E. Meyer Blvd.', '816-513-6008'],
                 'La Clinica': ['148 N. Topping Ave.', '816-581-5671'],
                 'Legal Aid of Western Missouri': ['4001 Dr. Martin Luther King, Jr. Blvd., Ste. 300',
                                                   '816-474-6750'],
                 'Lutheran Family and Children\'s Services of Missouri': ['1 E. Armour Blvd., Ste 102',
                                                                          '866-326-5327'],
                 'Metropolitan Lutheran Ministry': ['3031 Holmes Ave.', '816-931-0027'],
                 'Morning Glory Ministries: 9th St.': ['20 W. 9th St.', None],
                 'Morning Glory Ministries: 12th St.': ['416 W. 12th St.', '816-842-0416'],
                 'Mother’s Refuge': [None, '816-353-8070'],
                 'Neighbor2Neighbor': ['2910 Victor St.', None],
                 'Newhouse': [None, '816-471-5800'],
                 'NourishKC\'s KC Community Kitchen': ['750 Paseo Blvd.', None],
                 'Reconciliation Services': ['3101 Troost Ave.', '816-931-4751'],
                 'Redemptorist Center': ['207 Linwood Blvd.', '816-931-9942'],
                 'ReDiscover': [None, '816-966-0900'],
                 'ReHope': [None, '816-739-0500'],
                 'Relentless Pursuit Outreach & Recovery Drop-In Center': ['5108 Independence Ave.',
                                                                           '816-301-5571'],
                 'Research Psychiatric Center': ['2323 E. 63rd St.', '816-444-8161'],
                 'reStart, Inc.': ['918 E. 9th St.', '816-472-5664'],
                 'reStart, SSVF': ['918 E. 9th St.', '816-886-9148'],
                 'reStart Youth Emergency Shelter': [None, '816-309-9048'],
                 'Rose Brooks Center': [None, '816-861-6100'],
                 'Samuel U. Rogers Health Center': ['825 Euclid Ave.', '816-474-4920'],
                 'SAVE, Inc.': [None, '816-531-8340p200'],
                 'Second Chance': ['3100 Broadway Blvd., Ste. 302', '816-231-0450'],
                 'Shelter KC': ['1520 Cherry St.', '816-421-7643'],
                 'Shelter KC Women\'s Center': [None, '816-348-3287'],
                 'St. Paul\'s Episcopal Church': ['40th St. & Main St.', '816-931-2850'],
                 'Street Outreach': [None, '816-505-4901'],
                 'Street Support KC': ['10th St. and Baltimore Ave.', None],
                 'Swope Health Services': ['3801 Dr. Martin Luther King, Jr. Blvd.', '816-599-5480'],
                 'Synergy House': [None, '816-741-8700'],
                 'Synergy Services': [None, '816-321-7050'],
                 'THE BEEHIVE': ['750 Paseo Blvd.', None],
                 'The HALO Foundation': ['1600 Genessee St., Ste. 140', '816-590-4493'],
                 'The LIGHT House Inc.': [None, '816-916-4434'],
                 'The Salvation Army': ['3013 E. 9th St.', None],
                 'The Salvation Army Adult Rehabilitation Center': ['1351 E. 10th St.', '816-451-5434'],
                 'The Salvation Army: SSVF': ['6618 E.Truman Rd.', '816-670-2414'],
                 'Trinity United Methodist Church': ['620 E. Armour Blvd.', None],
                 'True Light Family Resource Center: 712': ['712 E. 31st St.', '816-561-1700'],
                 'True Light Family Resource Center: 717': ['717 E. 31st St.', None],
                 'TLFRC: Emancipation Station': ['717 E. 31st St., Emancipation Station', '816-531-1300'],
                 'Unity Southeast': ['3421 E. Meyer Blvd', None],
                 'University Health/Behavioral Services': ['300 W. 19th Ter.', '816-404-5700'],
                 'Veterans Community Project: Outreach Center': ['8825 Troost Ave.', '816-599-6503'],
                 'Vivent Health': ['4309 E. 50th Ter., Ste. 200', '816-561-8784'],
                 'Washington Square Park': ['100 E. Pershing Rd.', None],
                 'Westport Presbyterian Church': ['201 Westport Rd.', None],
                 'Youth Resiliency Center': ['2001 NE Parvin, North Kansas City', '816-505-4840'],
                 }
    for provider in providers:
        if len(providers[provider]) > 2:
            email = providers[provider][2]
        else:
            email = None
        insert_new_provider(name=provider, address=providers[provider][0], phone=providers[provider][1], email=email)

def pre_populate_categories(categories=None):
    if not categories or categories is None:
        categories = ['Food', 'Health', 'General', 'Shelter', 'Hygiene']
    for category in categories:
        insert_new_service_category(category)

def pre_populate_service_type(service_types=None):
    if not service_types or service_types is None:
        service_types = {
            "Food": ['Breakfast', 'Lunch', 'Dinner', 'Pantry',],
            'Health': ['Health', 'Behavioral Health', 'Dental', 'Prescriptions', 'Vision', 'Pediatrics', 'OB/GYN',
                          'Drug Treatment',],
            'General': ['General', 'General - Legal', 'General - Financial', ],
            'Shelter': ['Housing', 'Housing referral', 'Rent Assistance', 'Utility Assistance', ],
            'Hygiene': ['Clothes', 'Showers', 'Toiletries', 'Diapers', 'Laundry', ],
        }
    for category in service_types:
        service_category_instance = retrieve_service_category(category)
        for service_type in service_types[category]:
            insert_new_service_type(service_type, service_category_instance)

def pre_populate_audience(audience=None):
    if not audience or audience is None:
        audience = [
            'Everyone',
            'Children and Teens',
            'Military Service Members and Veterans',
            'Justice-Involved and Returning Citizens',
            'Unhoused or Experiencing Homelessness'
        ]
    for audience_type in audience:
        insert_new_audience(audience_type)

