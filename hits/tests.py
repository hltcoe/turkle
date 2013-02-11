from django.test import TestCase
from models import Hit, AwsMTurkTemplate


class TestHit(TestCase):

    def test_new_hit(self):
        """
        unicode() should be the template's title followed by :id of the hit.
        """
        es_tweets = AwsMTurkTemplate(title='spanish tweets', template='blah')
        es_tweets.save()
        hit = Hit(template=es_tweets, template_values='{}')
        hit.save()
        self.assertEqual('spanish tweets:1', unicode(hit))

class TestAwsMTurkTemplate(TestCase):

    def test_new_template(self):
        """
        unicode() should be the template's title followed by :id of the hit.
        """
        es_tweets = AwsMTurkTemplate(title='spanish tweets', template='blah')
        es_tweets.save()
        self.assertEqual('spanish tweets template', unicode(es_tweets))
