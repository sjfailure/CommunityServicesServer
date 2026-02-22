import logging

import django

from server import helpers
from server.models import ServiceCategory, ServiceType, Audience

class TestHelpersDataWranglers(django.test.TestCase):
    """
    Test suite for server.helpers code that serves to wrangle data for
    views.py.
    """

    def setUp(self):
        self.category1 = helpers.insert_new_service_category("Test1")
        self.category2 = helpers.insert_new_service_category("Test2")
        self.type1cat1 = helpers.insert_new_service_type(
            "Cat1Type1",
            self.category1,
        )
        self.type2cat1 = helpers.insert_new_service_type(
            "Cat1Type2",
            self.category1,
        )
        self.type3cat2 = helpers.insert_new_service_type(
            "Cat2Type3",
            self.category2,
        )
        self.type4cat2= helpers.insert_new_service_type(
            "Cat2Type4",
            self.category2
        )
        self.duplicate_type = helpers.insert_new_service_type(
            "Cat1Type1",
            self.category2,
            # type is same as self.type1cat1, category is different
        )
        self.audience1 = helpers.insert_new_audience("Audience1")
        self.audience2 = helpers.insert_new_audience("Audience2")
        self.audience3 = helpers.insert_new_audience("Audience3")

    def test_get_all_categories_types_gets_all(self):
        data = helpers.get_all_categories_types()
        self.assertIn(self.category1.category, data.keys())
        self.assertIn(self.category2.category, data.keys())
        self.assertIn(
            self.type1cat1.type,
            data[self.category1.category]
        )
        self.assertIn(
            self.type2cat1.type,
            data[self.category1.category]
        )
        self.assertIn(
            self.type3cat2.type,
            data[self.category2.category]
        )
        self.assertIn(
            self.type4cat2.type,
            data[self.category2.category]
        )

    def test_get_all_categories_type_retains_near_duplicates(self):
        data = helpers.get_all_categories_types()
        self.assertIn(
            self.type1cat1.type,
            data[self.category1.category]
        )
        self.assertIn(
            self.duplicate_type.type,
            data[self.category2.category]
        )

    """
    Testing for get_all_audiences()
    """
    def test_get_all_audiences(self):
        data = helpers.get_all_audiences()
        self.assertIn(self.audience1.audience, data)
        self.assertIn(self.audience2.audience, data)
        self.assertIn(self.audience3.audience, data)
