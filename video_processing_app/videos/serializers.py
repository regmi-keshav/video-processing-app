from rest_framework import serializers
from .models import Video, Subtitle, Language


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'code', 'name']


class SubtitleSerializer(serializers.ModelSerializer):
    language = LanguageSerializer()  # Nested serializer for language

    class Meta:
        model = Subtitle
        fields = ['id', 'language', 'content',
                  'timestamp_start', 'timestamp_end']


class VideoSerializer(serializers.ModelSerializer):
    # Nested serializer for subtitles
    subtitles = SubtitleSerializer(many=True, read_only=True)

    class Meta:
        model = Video
        fields = ['id', 'title', 'video_file', 'uploaded_at', 'subtitles']
