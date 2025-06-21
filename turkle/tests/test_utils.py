from django.test import TestCase
from django.core.exceptions import ValidationError

from turkle.utils import get_turkle_template_limit, process_html_template


class TestProcessHTMLTemplate(TestCase):
    def test_simple_template(self):
        submit, field_names = process_html_template("<p>${foo}</p><textarea>")
        self.assertFalse(submit)
        self.assertEqual(field_names, {'foo': True})

    def test_too_large_template(self):
        limit = get_turkle_template_limit(True)
        template = 'a' * limit + '<textarea>'
        with self.assertRaisesMessage(ValidationError, 'Template is too large'):
            process_html_template(template)
