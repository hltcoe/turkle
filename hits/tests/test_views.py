import django.test
from django.core.handlers.wsgi import WSGIRequest
from hits.models import Hit, HitTemplate
from hits.views import submission


class TestSubmission(django.test.TestCase):

    def setUp(self):
        template = HitTemplate(name='foo', form='<p></p>')
        template.save()
        self.hit = Hit(template=template, input_csv_fields='{}')
        self.hit.save()

    def test_0(self):
        post_request = RequestFactory().post(
            u'/hits/1/submission',
            {u'foo': u'bar'}
        )
        post_request.csrf_processing_done = True
        submission(post_request, 1)
        h = Hit.objects.get(id=1)

        expect = {u'foo': u'bar'}
        actual = h.answers
        self.assertEqual(expect, actual)


# This was grabbed from
# http://djangosnippets.org/snippets/963/
class RequestFactory(django.test.Client):
    """
    Class that lets you create mock Request objects for use in testing.

    Usage:

    rf = RequestFactory()
    get_request = rf.get('/hello/')
    post_request = rf.post('/submit/', {'foo': 'bar'})

    This class re-uses the django.test.client.Client interface, docs here:
    http://www.djangoproject.com/documentation/testing/#the-test-client

    Once you have a request object you can pass it to any view function,
    just as if that view had been hooked up using a URLconf.

    """
    def request(self, **request):
        """
        Similar to parent class, but returns the request object as soon as it
        has created it.
        """
        environ = {
            'HTTP_COOKIE': self.cookies,
            'PATH_INFO': '/',
            'QUERY_STRING': '',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '',
            'SERVER_NAME': 'testserver',
            'SERVER_PORT': 80,
            'SERVER_PROTOCOL': 'HTTP/1.1',
        }
        environ.update(self.defaults)
        environ.update(request)
        return WSGIRequest(environ)


__all__ = (
    'RequestFactory',
    'TestSubmission',
)
