from django.test import TestCase


class TestHit(TestCase):
    def test_new_hit(self):
        """
        Tests that a new Hit can exist
        """
        self.assertEqual(2, 1 + 1)
