from django.db.models import Q
from rest_framework.exceptions import ValidationError, NotFound
from .serializers import SubtitleSerializer
from .models import Video
from rest_framework import generics
from rest_framework.views import APIView
from .models import Subtitle
from rest_framework import status
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from .models import Video, Subtitle
from .serializers import VideoSerializer, SubtitleSerializer
from .tasks import extract_subtitles_task
from django.views.generic import TemplateView
import logging

# Set up logging
logger = logging.getLogger(__name__)


class Home(TemplateView):
    """
    Serve the main HTML template.
    """
    template_name = 'index.html'


class VideoListView(generics.ListAPIView):
    """
    API endpoint to list all uploaded videos.
    """
    queryset = Video.objects.all()
    serializer_class = VideoSerializer


class VideoCreateView(generics.CreateAPIView):
    """
    API endpoint to upload a new video.
    Triggers a background task for subtitle extraction upon successful upload.
    """
    queryset = Video.objects.all()
    serializer_class = VideoSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            video_file = serializer.validated_data.get('video_file')

            # Validate the file type
            if not video_file.name.endswith(('.mp4', '.mkv', '.avi')):
                return Response({'error': 'Unsupported file type.'}, status=status.HTTP_400_BAD_REQUEST)

            video = serializer.save()
            # Trigger background subtitle extraction task
            extract_subtitles_task.delay(video.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            logger.error(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VideoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint to retrieve, update, or delete a video by ID.
    """
    queryset = Video.objects.all()
    serializer_class = VideoSerializer

    def delete(self, request, *args, **kwargs):
        """
        Handle video deletion.
        """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubtitleListView(generics.ListAPIView):
    """
    API endpoint to list subtitles for a specific video.
    """
    serializer_class = SubtitleSerializer

    def get_queryset(self):
        video_id = self.kwargs['video_id']
        try:
            video = Video.objects.get(id=video_id)
            return video.subtitles.all()
        except Video.DoesNotExist:
            raise NotFound("Video not found.")


class VideoLanguagesView(APIView):
    """
    API endpoint to list all the available languages of subtitles.
    """

    def get(self, request, video_id):
        subtitles = Subtitle.objects.filter(
            video_id=video_id).select_related('language').distinct('language')
        languages = [
            {
                'code': subtitle.language.code,
                'name': subtitle.language.name
            } for subtitle in subtitles
        ]
        return Response(languages, status=status.HTTP_200_OK)


class SearchSubtitleView(generics.ListAPIView):
    """
    API endpoint to search subtitles for a specific video by a query term.
    This approach uses case-insensitive substring matching for flexible search.
    """
    serializer_class = SubtitleSerializer

    def get_queryset(self):
        video_id = self.kwargs['video_id']
        search_term = self.request.GET.get('query', '').strip()

        if not search_term:
            raise ValidationError("Search term cannot be empty.")

        try:
            # Retrieve the video
            video = Video.objects.get(id=video_id)

            # Perform a case-insensitive substring search using icontains
            return video.subtitles.filter(content__icontains=search_term)

        except Video.DoesNotExist:
            raise NotFound("Video not found.")
