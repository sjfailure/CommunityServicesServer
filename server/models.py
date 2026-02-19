import datetime
import logging

from django.db import models, transaction

# Create your models here.


class ServiceCategory(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.TextField(null=False)

class ServiceType(models.Model):
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=255)
    category = models.ForeignKey(ServiceCategory, default=1, on_delete=models.SET_DEFAULT)

    class Meta:
        unique_together = (('type', 'category'))

class Provider(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField(default='No Provider', null=False)
    address = models.TextField(null=True)
    phone = models.TextField(null=True)
    email = models.TextField(null=True)

    class Meta:
        unique_together = (('name', 'address'),)

class Audience(models.Model):
    id = models.AutoField(primary_key=True)
    audience = models.TextField(null=False)

class Day(models.Model):
    id = models.AutoField(primary_key=True)

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        """Override of save prevents adding more than 7 days or altering the Day table."""
        if not self.pk and Day.objects.count() >= 7:
            raise PermissionError("The week only has 7 days. Don't play God.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Override of delete prevents removing days fromt he Day table"""
        raise PermissionError("What?! 7 days a week too much for you?! (Cannot alter Day table)")

class ServiceManager(models.Manager):
    """
    Manager for models.Service table, handles M2M relationship building
    for class.
    NOTE: categories parameter has been deprecated, no longer used.
    Category information for a Service object should be accessed via
    the Type relationship.
    """
    def create_or_update_service(self, provider, start_time, end_time,
                                 day, types, audiences, periodic=0,
                                 note='', categories=None,
                                 report_status=False):

        # 1. Standardize Time (handles "13:00:00" string or
        # datetime.time object)
        if isinstance(start_time, str):
            start_time = datetime.time.fromisoformat(start_time)
        if isinstance(end_time, str):
            end_time = datetime.time.fromisoformat(end_time)

        # 2. Atomic Transaction: Ensures if M2M adding fails,
        # the service isn't created
        with transaction.atomic():
            service, created = self.get_or_create(
                provider=provider,

                start_time=start_time,
                end_time=end_time,
                periodic=periodic,
                defaults={'note': note}
            )

            # 3. Helper to handle single objects vs lists for M2M
            def ensure_list(item):
                if isinstance(item, (list, models.QuerySet)):
                    return item
                return [item]

            # 4. Bulk add M2M relations (Django's .add() handles
            # duplicates for you!)
            # service.category.add(*ensure_list(categories))
            service.type.add(*ensure_list(types))
            service.audience.add(*ensure_list(audiences))
            service.day.add(*ensure_list(day))

        if report_status:
            return service, created
        return service

class Service(models.Model):
    id = models.AutoField(primary_key=True)
    # category = models.ManyToManyField(ServiceCategory)
    type = models.ManyToManyField(ServiceType)
    provider = models.ForeignKey(
        Provider,
        default=1,
        on_delete=models.SET_DEFAULT
    )
    audience = models.ManyToManyField(Audience)
    day = models.ManyToManyField(Day) # 0-6 (M-Sun)
    start_time = models.TimeField(default=datetime.time(0)) # Presents
    # as a datetime.time object in Python???
    end_time = models.TimeField(default=datetime.time(0))
    periodic = models.IntegerField(default=0) # Special field for
    # events that occur periodically,i.e. every 3rd Sat., int
    # indicates nth day of the month
    note = models.TextField(default='', null=True)
    objects = ServiceManager()

    class Meta:
        unique_together = ((
                               'provider',
                               'start_time',
                               'end_time',
                               'periodic',
                               'note'),)


class Event(models.Model):
    id = models.AutoField(primary_key=True)
    service_id = models.ForeignKey(Service, on_delete=models.CASCADE)
    date = models.DateTimeField(default=datetime.date(
        1900,1,1))
    end = models.DateTimeField(default=datetime.date(
        1900,1,1))

    class Meta:
        unique_together = (('service_id', 'date'),)

################################################
# Model function: Dynamic populate of database with service data and
# events from provided source data

class Update(models.Model):
    last_update = models.DateTimeField(default=datetime.date(
        1900,1,1))
