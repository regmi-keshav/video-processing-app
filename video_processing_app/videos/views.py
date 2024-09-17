from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from .models import Video, Subtitle
from .serializers import VideoSerializer, SubtitleSerializer
from .tasks import extract_subtitles_task


class VideoListView(generics.ListAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer


class VideoCreateView(generics.CreateAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            video = serializer.save()
            # Trigger background subtitle extraction task
            extract_subtitles_task.delay(video.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VideoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer


class SubtitleListView(generics.ListAPIView):
    serializer_class = SubtitleSerializer

    def get_queryset(self):
        video_id = self.kwargs['video_id']
        try:
            video = Video.objects.get(id=video_id)
            return video.subtitles.all()
        except Video.DoesNotExist:
            raise NotFound("Video not found.")


class SearchSubtitleView(generics.ListAPIView):
    serializer_class = SubtitleSerializer

    def get_queryset(self):
        video_id = self.kwargs['video_id']
        search_term = self.request.GET.get('query', '').strip()

        if not search_term:
            raise ValidationError("Search term cannot be empty.")

        try:
            video = Video.objects.get(id=video_id)
            return video.subtitles.filter(content__icontains=search_term)
        except Video.DoesNotExist:
            raise NotFound("Video not found.")
