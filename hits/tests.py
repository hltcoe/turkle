from django.test import TestCase
from models import Hit, AwsMTurkTemplate


class TestHit(TestCase):

    def test_new_hit(self):
        """
        unicode() should be the template's title followed by :id of the hit.
        """
        es_tweets = AwsMTurkTemplate(title='spanish tweets', template='None')
        es_tweets.save()
        hit = Hit(template=es_tweets, template_values='{}')
        hit.save()
        self.assertEqual('spanish tweets:1', unicode(hit))
