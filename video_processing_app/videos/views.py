import subprocess
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from .models import Video, Subtitle
from .serializers import VideoSerializer
from django.http import JsonResponse
from django.db.models import Q


def index(request):
    return render(request, 'index.html')


class VideoUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = VideoSerializer(data=request.data)
        if serializer.is_valid():
            video = serializer.save()
            self.extract_subtitles(video)  # Direct subtitle extraction
            return Response({'message': 'Video uploaded and subtitles processed successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def extract_subtitles(self, video):
        video_path = video.video_file.path
        subtitle_path = f"{video_path}.srt"

        # Use ffmpeg to extract subtitles
        command = ['ffmpeg', '-i', video_path, '-map', '0:s:0', subtitle_path]
        subprocess.run(command)

        # Read the extracted subtitle file and save it to the database
        with open(subtitle_path, 'r') as subtitle_file:
            subtitle_lines = subtitle_file.readlines()

        timestamp = ""
        for line in subtitle_lines:
            if '-->' in line:
                timestamp = line.strip().split('-->')[0].strip()
            elif line.strip():
                Subtitle.objects.create(
                    video=video, content=line.strip(), timestamp=timestamp)


class VideoListView(APIView):
    def get(self, request, *args, **kwargs):
        videos = Video.objects.all()
        serializer = VideoSerializer(videos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubtitleSearchView(APIView):
    def get(self, request, video_id, *args, **kwargs):
        query = request.GET.get('q', '').lower()
        subtitles = Subtitle.objects.filter(
            video_id=video_id, content__icontains=query)
        results = [{'timestamp': s.timestamp, 'content': s.content}
                   for s in subtitles]
        return JsonResponse({'results': results}, safe=False)
