
from django.db import models


class Language(models.Model):
    # ISO language code (e.g., 'eng', 'spa')
    code = models.CharField(max_length=10, unique=True)
    # Human-readable language name (e.g., 'English', 'Spanish')
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Video(models.Model):
    title = models.CharField(max_length=255)
    video_file = models.FileField(upload_to='videos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Subtitle(models.Model):
    video = models.ForeignKey(
        Video, on_delete=models.CASCADE, related_name='subtitles')
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    content = models.TextField()  # Full content of the subtitle
    # Start timestamp (format: HH:MM:SS)
    timestamp_start = models.CharField(max_length=15, null=True)
    # End timestamp (format: HH:MM:SS)
    timestamp_end = models.CharField(max_length=15, null=True)

    class Meta:
        unique_together = ('video', 'language', 'timestamp_start')

    def __str__(self):
        return f"{self.language.code} Subtitle for {self.video.title} from {self.timestamp_start} to {self.timestamp_end}"
