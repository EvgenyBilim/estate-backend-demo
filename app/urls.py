from django.contrib import admin
from core import views as core_views
from cache import views as cache_views
from estate_api import views as estate_api_views
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('api/main-page/', estate_api_views.MainPageAPI.as_view()),

    path('api/homes/', estate_api_views.HomesAPI.as_view()),
    path('api/homes/<str:url>/', estate_api_views.ObjectAPI.as_view()),
    path('api/homes/plans/<str:url>/', estate_api_views.ObjectPlansAPI.as_view()),
    path('api/tags/', estate_api_views.TagsAPI.as_view()),
    path('api/lead/', estate_api_views.LeadAPI.as_view()),

    path('admin/', admin.site.urls),

    path('uploads/', core_views.PanelView.as_view()),
    path('uploads/homes/', core_views.UploadView.as_view(), {'kind': 'homes'}),
    path('uploads/plans/', core_views.UploadView.as_view(), {'kind': 'plans'}),
    path('uploads/category/', core_views.UploadView.as_view(), {'kind': 'category'}),
    path('uploads/photos/', core_views.UploadView.as_view(), {'kind': 'photos'}),
    path('uploads/metro/', core_views.UploadView.as_view(), {'kind': 'metro'}),
    path('uploads/download-zip/', core_views.MakeArchiveView.as_view()),

    path('cache/', cache_views.CacheView.as_view()),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),

    ] + urlpatterns
