from django.urls import path
from .views import VideoUploadView, VideoListView, SubtitleSearchView

urlpatterns = [
    # Upload video and process subtitles
    path('upload/', VideoUploadView.as_view(), name='upload-video'),
    # List all uploaded videos
    path('', VideoListView.as_view(), name='list-videos'),
    path('<int:video_id>/search/', SubtitleSearchView.as_view(),
         name='search-subtitles'),  # Search for subtitles within a video
]
