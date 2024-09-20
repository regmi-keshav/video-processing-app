from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from videos.views import Home
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', view=Home.as_view(), name='home'),
    path('api/', include('videos.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
