from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from videos.views import index
urlpatterns = [
    path('admin/', admin.site.urls),           # Admin route (optional)
    # Include URLs from the 'videos' app
    path('videos/', include('videos.urls')),
    path('', index, name='index'),  # Root URL
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
