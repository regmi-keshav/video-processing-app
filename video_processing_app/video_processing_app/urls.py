from django.contrib import admin
from django.urls import path
from videos.views import HelloWorldView

urlpatterns = [
    path("admin/", admin.site.urls),
    path('videos/', HelloWorldView.as_view(), name='hello-world'),
]
