import subprocess
import json
import logging
import os
from celery import shared_task
from .models import Video, Subtitle, Language

logger = logging.getLogger(__name__)

# Mapping of language codes to their names
LANGUAGE_NAMES = {
    'eng': 'English',
    'rus': 'Russian',
    'und': 'Undetermined',
    # Add more languages as needed
}


def get_language(language_code):
    """Retrieve or create a Language instance with a populated name."""
    language_name = LANGUAGE_NAMES.get(language_code, '')
    language, created = Language.objects.get_or_create(
        code=language_code,
        defaults={'name': language_name}
    )

    # Update name if it was empty
    if created or not language.name:
        language.name = language_name
        language.save()

    return language


def get_subtitle_info(video_path):
    """Retrieve subtitle stream information using ffprobe."""
    ffprobe_cmd = [
        'ffprobe', '-v', 'error', '-select_streams', 's',
        '-show_entries', 'stream=index,codec_type:stream_tags=language',
        '-of', 'json', video_path
    ]
    result = subprocess.run(
        ffprobe_cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def get_hardcoded_subtitle_info():
    """Return hardcoded subtitle stream information."""
    return [
        {'index': 0, 'codec_type': 'subtitle', 'tags': {'language': 'eng'}},
        {'index': 1, 'codec_type': 'subtitle', 'tags': {'language': 'rus'}},
        {'index': 2, 'codec_type': 'subtitle', 'tags': {
            'language': 'und'}},  # No language tag
    ]


def extract_subtitle_stream(video_path, subtitle_index):
    """Extract a specific subtitle stream from the video."""
    subtitle_path = f"{video_path}_stream_{subtitle_index}.srt"
    ffmpeg_cmd = [
        'ffmpeg', '-i', video_path, '-map', f'0:s:{subtitle_index}', subtitle_path, '-y'
    ]
    subprocess.run(ffmpeg_cmd, check=True)
    return subtitle_path


def parse_subtitles(subtitle_path, video, language):
    """Parse subtitles from the extracted file and create Subtitle instances."""
    subtitles_to_create = []
    with open(subtitle_path, 'r', encoding='utf-8') as file:
        content = file.read()
        entries = content.strip().split('\n\n')

        for entry in entries:
            lines = entry.splitlines()
            if len(lines) >= 3:
                timestamp_line = lines[1].split(' --> ')
                if len(timestamp_line) == 2:
                    timestamp_start = timestamp_line[0].strip()
                    timestamp_end = timestamp_line[1].strip()
                    subtitle_content = ' '.join(lines[2:]).strip()

                    subtitles_to_create.append(
                        Subtitle(
                            video=video,
                            language=language,
                            content=subtitle_content,
                            timestamp_start=timestamp_start,
                            timestamp_end=timestamp_end
                        )
                    )
    return subtitles_to_create


@shared_task
def extract_subtitles_task(video_id):
    try:
        video = Video.objects.get(id=video_id)
        video_path = video.video_file.path

        # Uncomment this line to use ffprobe
        # subtitles_info = get_subtitle_info(video_path)

        # Use hardcoded subtitles as a fallback
        subtitles_info = get_hardcoded_subtitle_info()

        subtitles_to_create = []

        for stream in subtitles_info:
            if stream['codec_type'] == 'subtitle':
                language_code = stream['tags'].get('language', 'und')
                language = get_language(language_code)

                subtitle_path = f"{video_path}_stream_{stream['index']}.srt"

                # Check if the subtitle file already exists
                if os.path.isfile(subtitle_path):
                    logger.info(
                        f"Subtitle file already exists: {subtitle_path}. Skipping extraction for {language_code}.")
                    continue

                subtitle_path = extract_subtitle_stream(
                    video_path, stream['index'])
                subtitles_to_create.extend(
                    parse_subtitles(subtitle_path, video, language))

        Subtitle.objects.bulk_create(subtitles_to_create)

    except Video.DoesNotExist:
        logger.error(f"Video {video_id} does not exist.")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error processing video {video_id}: {e}")
    except Exception as e:
        logger.error(f"Error processing video {video_id}: {e}")
