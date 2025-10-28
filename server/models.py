import copy
import datetime, calendar
import logging

import pytz
from django.db import models, DataError

# Create your models here.

class ServicesCategories(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.TextField(null=False)

class ServiceType(models.Model):
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=255, unique=True)
    category = models.ForeignKey(ServicesCategories, default=1, on_delete=models.SET_DEFAULT)

class Providers(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField(default='No Provider')
    address = models.TextField(null=True)
    phone = models.TextField(null=True)

class Audience(models.Model):
    id = models.AutoField(primary_key=True)
    audience = models.TextField(null=False)

class Services(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.ForeignKey(ServicesCategories, default=1, on_delete=models.SET_DEFAULT)
    type = models.ForeignKey(ServiceType, default=1, on_delete=models.SET_DEFAULT)
    day = models.IntegerField(default=0) # 0-6 (M-Sun)
    start_time = models.TimeField(default=datetime.time(0)) # Presents as a datetime.time object in Python???
    end_time = models.TimeField(default=datetime.time(0))
    periodic = models.IntegerField(default=0) # Special field for events that occur periodically,i.e. every 3rd Sat., int indicates nth day of the month
    provider = models.ForeignKey(Providers, default=1, on_delete=models.SET_DEFAULT)
    note = models.TextField(default='')
    audience = models.ForeignKey(Audience, default=1, on_delete=models.SET_DEFAULT)

    class Meta:
        unique_together = (('provider', 'category', 'type', 'day', 'periodic', 'start_time'),)

class Events(models.Model):
    id = models.AutoField(primary_key=True)
    service_id = models.ForeignKey(Services, on_delete=models.CASCADE)
    date = models.DateTimeField(default=datetime.date(1900,1,1))
    end = models.DateTimeField(default=datetime.date(1900,1,1))

    class Meta:
        unique_together = (('service_id', 'date'),)

################################################
# Model function: Dynamic populate of database with service data and events from provided source data

class Update(models.Model):
    last_update = models.DateTimeField(default=datetime.date(1900,1,1))

local_tz = pytz.timezone('America/Chicago')

def create_initial_data(apps=None, schema_editor=None):
    print('THIS FUNCTION HAS BEEN INITIATED')
    def pre_populate():
        default_provider = Providers(
            name='No Provider',
        )
        default_provider.save() # default for MySQL
        providers = {'AccessKC': [None, '816-276-7517'],
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
        provider_key_reference = copy.deepcopy(providers)
        for provider in providers:
            # print(f'creating Providers({provider}, ')
            if not Providers.objects.filter(
                name=provider,
                address=providers[provider][0],
                phone=providers[provider][1]
            ).exists():
                x = Providers.objects.create(
                    name=provider,
                    address=providers[provider][0],
                    phone=providers[provider][1])
                x.save()
                provider_key_reference[provider].append(x)
            else:
                provider_key_reference[provider].append(
                    Providers.objects.get(
                        name=provider,
                        address=providers[provider][0],
                        phone=providers[provider][1]
                    )
                )

        service_categories = ['Food', 'Health', 'General', 'Shelter', 'Hygiene']
        service_categories_key_reference = {}
        for service_cat in service_categories:
            if not ServicesCategories.objects.filter(
                category=service_cat
            ).exists():
                x = ServicesCategories.objects.create(category=service_cat)
                x.save()
                service_categories_key_reference[service_cat] = x
            else:
                service_categories_key_reference[service_cat] = ServicesCategories.objects.get(category=service_cat)

        print('START ServiceTypes')
        service_types = ['Breakfast',
                         'Lunch',
                         'Dinner',
                         'Pantry',
                         'Health',
                         'Behavioral Health',
                         'Dental',
                         'Prescriptions',
                         'Vision',
                         'Pediatrics',
                         'OB/GYN',
                         'General',
                         'General - Legal',
                         'General - Financial',
                         'Housing referral',
                         'Rent Assistance',
                         'Utility Assistance',
                         'Clothes',
                         'Showers',
                         'Toiletries',
                         'Diapers',
                         'Laundry',
                         'Drug Treatment',
                         ]
        service_type_map = {}
        print("ENTERING loop for ServiceTypes")
        for types in service_types:
            print(f'ITERATION: type={type}')
            if ServiceType.objects.filter(type=types):
                x = ServiceType.objects.get(type=types)
                super_category = x.category
                service_type_map[types] = {'instance': x, 'category': super_category}
                print(f'skipping {types}')
                continue
            if types in ['Breakfast', 'Lunch', 'Dinner', 'Pantry', ]:
                super_category = service_categories_key_reference['Food']
            elif types in ['Health', 'Behavioral Health', 'Dental', 'Prescriptions', 'Vision', 'Pediatrics', 'OB/GYN',
                          'Drug Treatment',]:
                super_category = service_categories_key_reference['Health']
            elif types in ['General', 'General - Legal', 'General - Financial', ]:
                super_category = service_categories_key_reference['General']
            elif types in ['Housing referral', 'Rent Assistance', 'Utility Assistance', ]:
                super_category = service_categories_key_reference['Shelter']
            elif types in ['Clothes', 'Showers', 'Toiletries', 'Diapers', 'Laundry', ]:
                super_category = service_categories_key_reference['Hygiene']
            else:
                raise DataError(f'Service Type {types} not expected.')
            print(f'Filing ServiceType(types={types}, category={super_category}')
            x = ServiceType(type=types, category=super_category)
            x.save()
            service_type_map[types] = {'instance': x, 'category': super_category}

        audience_reference_map = {}
        for audience in [
            'Everyone',
            'Children and Teens',
            'Military Service Members and Veterans',
            'Justice-Involved and Returning Citizens',
            'Unhoused or Experiencing Homelessness'
        ]:
            if not Audience.objects.filter(audience=audience).exists():
                x = Audience(audience=audience)
                x.save()
            else:
                x = Audience.objects.get(audience=audience)
            audience_reference_map[audience] = x

        # Input each service, one row per service offered
        # Times in 24:00 format
        # Skip periodic or none-weekly services, to add with specific algorithms.

        services = [] # list of Services instances to instantiate through bulk_create().


        def bishop_sullivan_one_cafe_lunch_dinner(services_list, ):
            provider = 'Bishop Sullivan: One City Cafe'
            category = service_categories_key_reference['Food']
            type_lunch = service_type_map['Lunch']['instance']
            type_dinner = service_type_map['Dinner']['instance']
            audience = audience_reference_map['Everyone']

            def lunch(day, start_time, end_time, note=''):
                return Services(
                    provider=provider_key_reference[provider][2],
                    category=category,
                    type=type_lunch,
                    day=day,
                    start_time=start_time,
                    end_time=end_time,
                    audience=audience,
                    note=note,
                    periodic=0,
                )

            def dinner(day, start_time, end_time, note=''):
                return Services(
                    provider=provider_key_reference[provider][2],
                    category=category,
                    type=type_dinner,
                    day=day,
                    start_time=start_time,
                    end_time=end_time,
                    audience=audience,
                    note=note,
                    periodic=0,
                )

            for i in range(0, 5):  # Lunch every weekday at noon
                if i != 4:  # Dinner M-Th at 4:30
                    services_list.append(dinner(i,
                                                datetime.time(16, minute=30),
                                                datetime.time(hour=18, minute=00)
                                                ),
                                         )
                # services_list.append(lunch(i,
                #                            datetime.time(12,0),
                #                            datetime.time(13, 0)
                #                            )
                #                      )

        bishop_sullivan_one_cafe_lunch_dinner(services)

        def family_promise_northland(service_list):
            service_list.append(Services(
                category=service_categories_key_reference["Food"],
                type=service_type_map['Lunch']['instance'],
                day=3,
                start_time=datetime.time(11),
                end_time=datetime.time(11,30),
                periodic=1,
                provider=provider_key_reference['Family Promise of the Northland'][2],
                note='1st, 3rd, & 5th Thursday',
                audience=audience_reference_map['Everyone']
            ))
            service_list.append(Services(
                category=service_categories_key_reference["Food"],
                type=service_type_map['Lunch']['instance'],
                day=3,
                start_time=datetime.time(11),
                end_time=datetime.time(11, 30),
                periodic=3,
                provider=provider_key_reference['Family Promise of the Northland'][2],
                note='1st, 3rd, & 5th Thursday',
                audience=audience_reference_map['Everyone']
            ))
            service_list.append(Services(
                category=service_categories_key_reference["Food"],
                type=service_type_map['Lunch']['instance'],
                day=3,
                start_time=datetime.time(11),
                end_time=datetime.time(11, 30),
                periodic=5,
                provider=provider_key_reference['Family Promise of the Northland'][2],
                note='1st, 3rd, & 5th Thursday',
                audience=audience_reference_map['Everyone']
            ))

        family_promise_northland(services)

        def independence_boulevard_christian_church(service_list):
            service_list.append(Services(
                category=service_categories_key_reference["Food"],
                type=service_type_map['Dinner']['instance'],
                day=0,
                start_time=datetime.time(17,30),
                end_time=datetime.time(19),
                periodic=0,
                provider=provider_key_reference['Care Beyond the Boulevard: Independence Blvd. Christian Church'][2],
                note='Dinner/toiletries/clothes (provided by Micha Ministries)',
                audience=audience_reference_map['Everyone']
            ))
            service_list.append(Services(
                category=service_categories_key_reference["Hygiene"],
                type=service_type_map['Toiletries']['instance'],
                day=0,
                start_time=datetime.time(17, 30),
                end_time=datetime.time(19),
                periodic=0,
                provider=provider_key_reference['Care Beyond the Boulevard: Independence Blvd. Christian Church'][2],
                note='Dinner/toiletries/clothes',
                audience=audience_reference_map['Everyone']
            ))
            service_list.append(Services(
                category=service_categories_key_reference["Hygiene"],
                type=service_type_map['Clothes']['instance'],
                day=0,
                start_time=datetime.time(17, 30),
                end_time=datetime.time(19),
                periodic=0,
                provider=provider_key_reference['Care Beyond the Boulevard: Independence Blvd. Christian Church'][2],
                note='Dinner/toiletries/clothes',
                audience=audience_reference_map['Everyone']
            ))

        independence_boulevard_christian_church(services)

        def nourishkcs_kc_community_kitchen(service_list):
            for i in range(0, 5):
                service_list.append(
                    Services(
                        provider=provider_key_reference['NourishKC\'s KC Community Kitchen'][2],
                        category=service_categories_key_reference['Food'],
                        type=service_type_map['Lunch']['instance'],
                        day=i,
                        start_time=datetime.time(12),
                        end_time=datetime.time(15,0),
                        audience=audience_reference_map['Everyone'],
                        note='new time is noon to 3pm',
                        periodic=0,
                    )
                )

        nourishkcs_kc_community_kitchen(services)

        def metropolitan_lutheran_ministry(service_list):
            for i in range(0, 5):
                service_list.append(Services(
                    provider=provider_key_reference['Metropolitan Lutheran Ministry'][2],
                    category=service_categories_key_reference['Food'],
                    type=service_type_map['Lunch']['instance'],
                    day=i,
                    start_time=datetime.time(12),
                    end_time=datetime.time(15, 0),
                    audience=audience_reference_map['Everyone'],
                    note='Food pantry & sack lunches',
                    periodic=0,
                ))
                service_list.append(Services(
                    provider=provider_key_reference['Metropolitan Lutheran Ministry'][2],
                    category=service_categories_key_reference['Food'],
                    type=service_type_map['Pantry']['instance'],
                    day=i,
                    start_time=datetime.time(8,30),
                    end_time=datetime.time(11, 0),
                    audience=audience_reference_map['Everyone'],
                    note='Food pantry & sack lunches',
                    periodic=0,
                ))

        metropolitan_lutheran_ministry(services)

        def morining_glory_minstries(service_list):
            for i in range(0, 5):
                service_list.append(Services(
                    provider=provider_key_reference['Morning Glory Ministries: 9th St.'][2],
                    category=service_categories_key_reference['Food'],
                    type=service_type_map['Breakfast']['instance'],
                    day=i,
                    start_time=datetime.time(7),
                    end_time=datetime.time(8),
                    audience=audience_reference_map['Everyone'],
                    note='Food pantry & sack lunches',
                    periodic=0,
                ))

        morining_glory_minstries(services)

        def neighor_2_neighbor(service_list):
            provider = 'Neighbor2Neighbor'
            # hygiene - toiletries
            # health - Drug Treatment
            # food - breakfast
            # food - lunch
            # shelter - housing referall
            # general - general
            note = 'www.n2n4kc.com/services Wed & Fri 10am-11:30 am Hygiene items. Mon-Fri 9am-12pm Drug treatment ' +\
                    'referrals before/after breakfast & lunch, housing referrals, case management M&W'
            # Hygiene supplies, w/f
            service_list.append(
                Services(
                    provider=provider_key_reference[provider][2],
                    category=service_categories_key_reference['Hygiene'],
                    type=service_type_map['Toiletries']['instance'],
                    day=2,
                    start_time=datetime.time(10),
                    end_time=datetime.time(11, 30),
                    audience=audience_reference_map['Everyone'],
                    note=note,
                    periodic=0,
                )
            )
            service_list.append(
                Services(
                    provider=provider_key_reference[provider][2],
                    category=service_categories_key_reference['Hygiene'],
                    type=service_type_map['Toiletries']['instance'],
                    day=4,
                    start_time=datetime.time(10),
                    end_time=datetime.time(11, 30),
                    audience=audience_reference_map['Everyone'],
                    note=note,
                    periodic=0,
                )
            )
            for i in range(5):
                service_list.append(
                    Services(
                        provider=provider_key_reference[provider][2],
                        category=service_categories_key_reference['Food'],
                        type=service_type_map['Breakfast']['instance'],
                        day=i,
                        start_time=datetime.time(9),
                        end_time=datetime.time(12),
                        audience=audience_reference_map['Everyone'],
                        note=note,
                        periodic=0,
                    )
                )
                service_list.append(
                    Services(
                        provider=provider_key_reference[provider][2],
                        category=service_categories_key_reference['Food'],
                        type=service_type_map['Lunch']['instance'],
                        day=i,
                        start_time=datetime.time(9),
                        end_time=datetime.time(12),
                        audience=audience_reference_map['Everyone'],
                        note=note,
                        periodic=0,
                    )
                )
                service_list.append(
                    Services(
                        provider=provider_key_reference[provider][2],
                        category=service_categories_key_reference['Shelter'],
                        type=service_type_map['Housing referral']['instance'],
                        day=i,
                        start_time=datetime.time(9),
                        end_time=datetime.time(12),
                        audience=audience_reference_map['Everyone'],
                        note=note,
                        periodic=0,
                    )
                )
                service_list.append(
                    Services(
                        provider=provider_key_reference[provider][2],
                        category=service_categories_key_reference['General'],
                        type=service_type_map['General']['instance'],
                        day=i,
                        start_time=datetime.time(9),
                        end_time=datetime.time(12),
                        audience=audience_reference_map['Everyone'],
                        note=note,
                        periodic=0,
                    )
                )

        neighor_2_neighbor(services)

        def redemptorist_center(service_list):
            for i in range(5):
                service_list.append(Services(
                    provider=provider_key_reference['Redemptorist Center'][2],
                    category=service_categories_key_reference['Food'],
                    type=service_type_map['Lunch']['instance'],
                    day=i,
                    start_time=datetime.time(10),
                    end_time=datetime.time(13),
                    audience=audience_reference_map["Everyone"],
                    note='',
                    periodic=0,
                ))
                if i != 4:
                    service_list.append(Services(
                        provider=provider_key_reference['Redemptorist Center'][2],
                        category=service_categories_key_reference['Food'],
                        type=service_type_map['Pantry']['instance'],
                        day=i,
                        start_time=datetime.time(10),
                        end_time=datetime.time(13),
                        audience=audience_reference_map["Everyone"],
                        note='',
                        periodic=0,
                    ))

        redemptorist_center(services)

        def salvation_army(service_list):
            provider = provider_key_reference['The Salvation Army'][2]
            for i in range(4): # monday thru thursday
                service_list.append(Services(
                    category=service_categories_key_reference['Food'],
                    type=service_type_map['Lunch']['instance'],
                    day=i,
                    start_time=datetime.time(11, 30),
                    end_time=datetime.time(12, 30),
                    periodic=0,
                    provider=provider,
                    note='',
                    audience=audience_reference_map['Everyone']
                ))

        salvation_army(services)

        def trinity_unity_meth_church(service_list):
            lunch = service_type_map['Lunch']
            pantry = service_type_map['Pantry']
            toiletries = service_type_map['Toiletries']
            laundry = service_type_map['Laundry']
            provider = provider_key_reference['Trinity United Methodist Church'][2]
            for service in [lunch, pantry, toiletries, laundry]: # Lunch, Pantry, Toiletries, and Laundry, M 12-1
                service_list.append(
                    Services(
                        category=service['category'],
                        type=service['instance'],
                        day=0,
                        start_time=datetime.time(12),
                        end_time=datetime.time(13),
                        periodic=0,
                        provider=provider,
                        note='Lunch with food pantry, toiletry & laundry voucher',
                        audience=audience_reference_map['Everyone'],
                    )
                )
            # lunch only, Th 11:30-12:30
            service_list.append(
                Services(
                    category=lunch['category'],
                    type=lunch['instance'],
                    day=5,
                    start_time=datetime.time(11, 30),
                    end_time=datetime.time(12, 30),
                    periodic=0,
                    provider=provider,
                    note='Lunch only (on Saturdays)',
                    audience=audience_reference_map['Everyone'],
                )
            )

        trinity_unity_meth_church(services)

        def tlfrc_emancipation_station(service_list):
            provider = provider_key_reference['TLFRC: Emancipation Station'][2]
            audience = audience_reference_map["Everyone"]
            for i in range(5):
                service_list.append(
                    Services(
                        category=service_type_map["Breakfast"]['category'],
                        type = service_type_map["Breakfast"]['instance'],
                        day=i,
                        start_time=datetime.time(8,30),
                        end_time=datetime.time(10),
                        periodic=0,
                        provider=provider,
                        note='',
                        audience=audience
                    )
                )
                service_list.append(
                    Services(
                        category=service_type_map["Lunch"]['category'],
                        type=service_type_map["Lunch"]['instance'],
                        day=i,
                        start_time=datetime.time(12),
                        end_time=datetime.time(13),
                        periodic=0,
                        provider=provider,
                        note='Limited',
                        audience=audience
                    )
                )

        tlfrc_emancipation_station(services)

        def unity_southeast(service_list):
            provider = provider_key_reference['Unity Southeast'][2]
            breakfast = service_type_map['Breakfast']
            pantry = service_type_map['Pantry']
            dinner = service_type_map['Dinner']
            category = lambda x: x['category']
            audience = audience_reference_map['Everyone']
            service_list.append(
                Services(
                    provider=provider,
                    category=category(breakfast),
                    type=breakfast['instance'],
                    day=6,
                    start_time=datetime.time(9,30),
                    end_time=datetime.time(10,30),
                    periodic=0,
                    note='',
                    audience=audience,
                )
            )
            service_list.append(
                Services(
                    provider=provider,
                    category=category(pantry),
                    type=pantry['instance'],
                    day=6,
                    start_time=datetime.time(10),
                    end_time=datetime.time(11),
                    periodic=0,
                    note='',
                    audience=audience,
                )
            )
            service_list.append(
                Services(
                    provider=provider,
                    category=category(dinner),
                    type=dinner['instance'],
                    day=2,
                    start_time=datetime.time(17, 30),
                    end_time=datetime.time(19),
                    periodic=0,
                    note='',
                    audience=audience,
                )
            )

        unity_southeast(services)

        def washington_square_park(service_list):
            service_list.append(
                Services(
                    category=service_categories_key_reference["Food"],
                    type=service_type_map['Dinner']['instance'],
                    day=2,
                    start_time=datetime.time(18, 30),
                    end_time=datetime.time(20),
                    periodic=0,
                    provider=provider_key_reference['Washington Square Park'][2],
                    note='Provided by Kansas City Heroes',
                    audience=audience_reference_map['Everyone']
                )
            )

        washington_square_park(services)

        def westport_presbyterian_church(service_list):
            provider = provider_key_reference['Westport Presbyterian Church'][2]
            service_list.append(
                Services(
                    category=service_categories_key_reference["Food"],
                    type=service_type_map['Breakfast']['instance'],
                    day=6,
                    start_time=datetime.time(8),
                    end_time=datetime.time(9, 30),
                    periodic=0,
                    provider=provider,
                    note='',
                    audience=audience_reference_map['Everyone']
                )
            )
            service_list.append(
                Services(
                    category=service_categories_key_reference["Food"],
                    type=service_type_map['Lunch']['instance'],
                    day=2,
                    start_time=datetime.time(11),
                    end_time=datetime.time(12),
                    periodic=0,
                    provider=provider,
                    note='lunch bags',
                    audience=audience_reference_map['Everyone']
                )
            )

        westport_presbyterian_church(services)

        for serv in services:
            print(f'checking service {serv.provider.id}-{serv.category}-{serv.type}-{serv.day}-{serv.periodic}-{str(serv.start_time)}')
        Services.objects.bulk_create(services)

    pre_populate()

def update_events_calendar():
    """
    Uses Services as listed in the Services table to populate the Events table with event dates and times,
    will not create duplicates due to Events.Meta.unique_together() constraints.
    """

    x = Update.objects.all()
    if not x:
        x = Update.objects.create()
        x.save()
        x = Update.objects.all()
    if datetime.datetime.now(local_tz) - x[0].last_update > datetime.timedelta(days=1):
        purge_old_events()
        services = Services.objects.all()

        for service in services:
            for date_offset in range(31):
                working_date = (datetime.datetime.combine(datetime.date.today(), service.start_time)
                                + datetime.timedelta(days=date_offset))

                # Check if the service is available on this day
                if service.day == working_date.weekday():
                    end_time = datetime.datetime.combine(working_date, service.end_time)
                    logging.debug(f'server.models.py - update_events_calendar() service start and end datetime calucations: {working_date.isoformat(), end_time.isoformat()}')

                    # Add only if the end time is in the future
                    if end_time > datetime.datetime.now():
                        events.append(
                            Events(
                                service_id=service,
                                date=local_tz.localize(working_date),
                                end=local_tz.localize(end_time)
                            )
                        )

        Events.objects.bulk_create(events, ignore_conflicts=True)
        x = Update.objects.all()
        x[0].last_update = datetime.datetime.now(tz=local_tz)

def purge_old_events():
    """
    Purges events from the Events table if their end_time and date has passed.
    """
    Events.objects.filter(end__lt=datetime.datetime.now()).delete()
