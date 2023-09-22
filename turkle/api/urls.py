from django.urls import include, path
from rest_framework import permissions
from rest_framework.reverse import reverse
from rest_framework.schemas import get_schema_view
from rest_framework.renderers import JSONOpenAPIRenderer
from rest_framework.routers import APIRootView, DefaultRouter
from rest_framework_nested import routers

from .views import BatchViewSet, BatchCustomPermissionsViewSet, GroupViewSet, \
    ProjectViewSet, ProjectCustomPermissionsViewSet, UserViewSet
from ..utils import get_site_name


class TurkleAPIRootView(APIRootView):
    """
    List of top level API endpoints
    """
    # This class is used to set the description of the root view
    # and to add the schema endpoint to the root page
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.data['schema'] = reverse('schema', request=request)
        return response


router = DefaultRouter()
router.APIRootView = TurkleAPIRootView
router.register(r'batches', BatchViewSet, basename='batch')
router.register(r'groups', GroupViewSet, basename='group')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'users', UserViewSet, basename='user')

proj_permissions_router = routers.NestedSimpleRouter(router, r'projects', lookup='project')
proj_permissions_router.register(
    r'permissions',
    ProjectCustomPermissionsViewSet,
    basename='project-permissions'
)

batch_permissions_router = routers.NestedSimpleRouter(router, r'batches', lookup='batch')
batch_permissions_router.register(
    r'permissions',
    BatchCustomPermissionsViewSet,
    basename='batch-permissions'
)

schema_view = get_schema_view(
    title=get_site_name() + ' API',
    version='1.0',
    renderer_classes=[JSONOpenAPIRenderer],
    permission_classes=(permissions.AllowAny,),
    public=True
)

urlpatterns = [
    path('', include(router.urls)),
    path('', include(proj_permissions_router.urls)),
    path('', include(batch_permissions_router.urls)),
    path('schema/', schema_view, name='schema')
]
