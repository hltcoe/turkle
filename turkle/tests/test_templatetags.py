from django.test import TestCase

from turkle.templatetags.turkle_tags import meta_tag


class TestMetaTag(TestCase):
    def test_noindex(self):
        tag = {'name': 'robots', 'content': 'noindex'}
        output = meta_tag(tag)
        self.assertEqual(output, '<meta name="robots" content="noindex">')
