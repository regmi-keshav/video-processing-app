import subprocess
import json
import logging
import os
from celery import shared_task
from .models import Video, Subtitle, Language

logger = logging.getLogger(__name__)

# Updated mapping of language codes to their names
LANGUAGE_NAMES = {
    'en': 'English',
    'ru': 'Russian',
    'ja': 'Japanese',
    'x-unknown': 'Unknown',  # For undetermined languages
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
        {'index': 0, 'codec_type': 'subtitle', 'tags': {'language': 'en'}},
        {'index': 1, 'codec_type': 'subtitle', 'tags': {'language': 'ru'}},
        {'index': 2, 'codec_type': 'subtitle', 'tags': {
            'language': 'ja'}},  # No language tag
    ]


def extract_subtitle_stream(video_path, subtitle_index, subtitle_language):
    """Extract a specific subtitle stream from the video in VTT format."""
    subtitle_path = f"{video_path}_stream_{subtitle_language}.vtt"
    ffmpeg_cmd = [
        'ffmpeg', '-i', video_path, '-map', f'0:s:{subtitle_index}', subtitle_path, '-y'
    ]
    subprocess.run(ffmpeg_cmd, check=True)
    return subtitle_path


def parse_subtitles(subtitle_path, video, language):
    """Parse subtitles from the extracted VTT file and create Subtitle instances."""
    subtitles_to_create = []
    with open(subtitle_path, 'r', encoding='utf-8') as file:
        content = file.read().strip().splitlines()

        i = 0
        while i < len(content):
            if '-->' in content[i]:
                # Extract timestamps
                timestamp_start, timestamp_end = content[i].split(' --> ')
                i += 1

                # Gather all lines for this subtitle block
                subtitle_content_lines = []
                while i < len(content) and '-->' not in content[i]:
                    subtitle_content_lines.append(content[i].strip())
                    i += 1

                # Join all subtitle lines into a single block of text
                subtitle_content = ' '.join(subtitle_content_lines).strip()

                # Create subtitle instance
                if subtitle_content:
                    subtitles_to_create.append(
                        Subtitle(
                            video=video,
                            language=language,
                            content=subtitle_content,
                            timestamp_start=timestamp_start,
                            timestamp_end=timestamp_end
                        )
                    )
            else:
                i += 1  # Move to the next line if no timestamp is found

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
                language_code = stream['tags'].get('language', 'x-unknown')
                language = get_language(language_code)

                subtitle_path = f"{video_path}_stream_{language_code}.vtt"

                # Check if the subtitle file already exists
                if os.path.isfile(subtitle_path):
                    logger.info(
                        f"Subtitle file already exists: {subtitle_path}. Skipping extraction for {language_code}.")
                    continue

                subtitle_path = extract_subtitle_stream(
                    video_path, stream['index'], language_code)
                subtitles_to_create.extend(
                    parse_subtitles(subtitle_path, video, language))

        Subtitle.objects.bulk_create(subtitles_to_create)

    except Video.DoesNotExist:
        logger.error(f"Video {video_id} does not exist.")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error processing video {video_id}: {e}")
    except Exception as e:
        logger.error(f"Error processing video {video_id}: {e}")
