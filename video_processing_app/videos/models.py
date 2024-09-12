from django.db import models


class Video(models.Model):
    title = models.CharField(max_length=255)
    video_file = models.FileField(upload_to='videos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Subtitle(models.Model):
    video = models.ForeignKey(
        Video, on_delete=models.CASCADE, related_name='subtitles')
    language = models.CharField(max_length=50, default='en')
    content = models.TextField()
    # e.g. '00:01:15' for 1 minute, 15 seconds
    timestamp = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.language} Subtitle for {self.video.title}"
