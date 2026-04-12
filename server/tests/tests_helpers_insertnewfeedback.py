import django
from django.utils import timezone

from server import helpers
import server.models as sm


class TestHelpersInsertNewFeedback(django.test.TestCase):

    def setUp(self):
        x = sm.UserKey(
            key="temp_test_key",
            created=timezone.now()
        )
        x.save()
        self.key = "temp_test_key"


    def tearDown(self):
        sm.UserKey.objects.filter(key="temp_test_key").delete()

    def test_insert_feedback_happy_path(self):
        server_starting_info_count = len(sm.Feedback.objects.all())

        feedback_message = "That button is broken."
        feedback_os = 'Android 14'
        feedback_device = "Samsung Galaxy S25"

        helpers.insert_new_feedback(
            message=feedback_message,
            os_data=feedback_os,
            device_data=feedback_device,
            user_key=self.key,
        )

        self.assertTrue(
            len(sm.Feedback.objects.all()) ==
            server_starting_info_count + 1
        )
        feedback_record = sm.Feedback.objects.all()[
            server_starting_info_count + 0
        ]
        self.assertEqual(feedback_record.message, feedback_message)
        self.assertEqual(feedback_record.os_data, feedback_os)
        self.assertEqual(feedback_record.device_data, feedback_device)

    def test_insert_feedback_no_device_data(self):
        server_starting_info_count = len(sm.Feedback.objects.all())
        feedback_message = "That button is broken."

        helpers.insert_new_feedback(
            message=feedback_message,
            user_key=self.key,
        )
        self.assertTrue(
            len(sm.Feedback.objects.all()) ==
                        server_starting_info_count + 1
        )
        feedback_record = sm.Feedback.objects.all()[
            server_starting_info_count + 0
        ]
        self.assertEqual(feedback_record.message, feedback_message)
        self.assertEqual(feedback_record.os_data, '')
        self.assertEqual(feedback_record.device_data, '')

    def test_retains_inputs(self):
        server_starting_info_count = len(sm.Feedback.objects.all())

        feedback_message1 = "test message 1: all good, baby!"
        feedback_message2 = "test message 2: still max-chilling."
        feedback_os1 = 'Android 14'
        feedback_device1 = "Samsung Galaxy S25"
        feedback_os2 = 'Android 10'
        feedback_device2 = "Moto G 2025 Power"

        helpers.insert_new_feedback(
            message=feedback_message1,
            os_data=feedback_os1,
            device_data=feedback_device1,
            user_key=self.key,
        )

        self.assertTrue(
            len(sm.Feedback.objects.all()) ==
                        server_starting_info_count + 1
        )
        feedback_record = sm.Feedback.objects.all()[
            server_starting_info_count
        ]
        self.assertEqual(feedback_record.message, feedback_message1)
        self.assertEqual(feedback_record.os_data, feedback_os1)
        self.assertEqual(feedback_record.device_data, feedback_device1)

        helpers.insert_new_feedback(
            message=feedback_message2,
            os_data=feedback_os2,
            device_data=feedback_device2,
            user_key=self.key,
        )

        self.assertTrue(
            len(
                sm.Feedback.objects.all()) == server_starting_info_count
            + 2)
        feedback_record = sm.Feedback.objects.all()[
            server_starting_info_count + 1
        ]
        self.assertEqual(feedback_record.message, feedback_message2)
        self.assertEqual(feedback_record.os_data, feedback_os2)
        self.assertEqual(feedback_record.device_data, feedback_device2)

    def test_does_not_panic_if_input_too_long(self):
        server_starting_info_count = len(sm.Feedback.objects.all())
        feedback_message = "x" * 2001
        feedback_os = 'a' * 256
        feedback_device = 'S' * 256

        helpers.insert_new_feedback(
            message=feedback_message,
            os_data=feedback_os,
            device_data=feedback_device,
            user_key=self.key,
        )

        # print(f'WHY YOU NO WORK?! {sm.Feedback.objects.all()}')
        self.assertTrue(
            len(sm.Feedback.objects.all()) ==
            server_starting_info_count + 1
        )
        feedback_record = sm.Feedback.objects.all()[
            server_starting_info_count
        ]
        # limit to 2000 characters
        self.assertEqual(feedback_record.message, 'x' * 2000)
        # limit to 255 characters
        self.assertEqual(feedback_record.os_data, 'a' * 255)
        self.assertEqual(feedback_record.device_data, "S" * 255)