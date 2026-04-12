import json
import datetime
from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse
from server.models import UserKey, Feedback
import server.helpers as helpers



class UserKeyTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.valid_key_str = "test-secret-key-123"
        self.user_key = UserKey.objects.create(
            key=self.valid_key_str,
            created=timezone.now()
        )

    ## --- Helper Function Tests ---

    def test_get_feedback_key(self):
        """
        Verify get_feedback_key creates a record and returns
        a valid key.
        """
        new_key_obj = helpers.get_feedback_key()
        self.assertTrue(
            UserKey.objects.filter(key=new_key_obj.key).exists())
        self.assertEqual(len(new_key_obj.key), 64)

    def test_check_key_valid(self):
        """Ensure check_key returns True for existing keys."""
        self.assertTrue(helpers.check_key(self.valid_key_str))

    def test_check_key_invalid(self):
        """Ensure check_key returns False for non-existent keys."""
        self.assertFalse(helpers.check_key("non-existent-key"))

    def test_insert_feedback_with_valid_key(self):
        """Feedback should be saved when a valid key is provided."""
        helpers.insert_new_feedback(
            message="Great app!",
            user_key=self.valid_key_str
        )
        self.assertEqual(Feedback.objects.count(), 1)
        self.assertEqual(Feedback.objects.first()
                         .message, "Great app!")

    def test_insert_feedback_with_invalid_key(self):
        """
        Feedback should NOT be saved if the key is missing or
        invalid.
        """
        # Case: Invalid Key
        helpers.insert_new_feedback(message="Bad key",
                                    user_key="wrong-key")
        # Case: No Key
        helpers.insert_new_feedback(message="No key", user_key=None)

        self.assertEqual(Feedback.objects.count(), 0)

    def test_purge_old_keys(self):
        """Verify keys older than 30 minutes are deleted."""
        # Create an expired key (31 minutes ago)
        expired_time = timezone.now() - datetime.timedelta(minutes=31)
        UserKey.objects.create(key="expired-key", created=expired_time)

        # Verify both exist initially
        self.assertEqual(UserKey.objects.count(), 2)

        # Run purge
        helpers.purge_old_events()

        # Verify only the valid key remains
        self.assertEqual(UserKey.objects.count(), 1)
        self.assertFalse(
            UserKey.objects.filter(key="expired-key").exists())

    ## --- API View Tests ---

    def test_receive_feedback_api_success(self):
        """POST request with valid key should return 'received'."""
        payload = {
            "message": "API Test",
            "user_key": self.valid_key_str,
            "os_data": "iOS",
            "device_data": "iPhone 15"
        }
        response = self.client.post(
            '/api/feedback/',  # Replace with your actual URL
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'received')
        self.assertEqual(Feedback.objects.count(), 1)

    def test_receive_feedback_api_rejection(self):
        """
        POST request with invalid data/key should handle errors
        gracefully.
        """
        # Case: Key is invalid (helper returns None, view proceeds but
        # no feedback created)
        payload = {
            "message": "Hacker attempt",
            "user_key": "fake-key"
        }
        response = self.client.post(
            '/api/feedback/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        # Note: Your current view returns 'received' even if
        # insert_new_feedback
        # early returns on a bad key. You might want to change that!
        self.assertEqual(Feedback.objects.count(), 0)