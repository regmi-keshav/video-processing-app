from django.urls import path
from .views import VideoListView, VideoCreateView, VideoDetailView, SubtitleListView, SearchSubtitleView

urlpatterns = [
    path('videos/', VideoListView.as_view(),
         name='video-list'),  # List all videos
    path('upload/', VideoCreateView.as_view(),
         name='video-create'),  # Upload a new video
    path('videos/<int:pk>/', VideoDetailView.as_view(), name='video-detail'),
    path('videos/<int:video_id>/subtitles/',
         SubtitleListView.as_view(), name='video-subtitles-list'),
    path('videos/<int:video_id>/subtitles/search/',
         SearchSubtitleView.as_view(), name='video-subtitles-search'),
]
