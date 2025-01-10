import random
import string

from os import path as ospath, cpu_count
from aiofiles.os import remove as aioremove, path as aiopath, makedirs
from time import time
from re import search as re_search
from asyncio import create_subprocess_exec, gather, create_task
from asyncio.subprocess import PIPE
from PIL import Image
from aioshutil import move

from bot import LOGGER, subprocess_lock
from bot.helper.ext_utils.bot_utils import cmd_exec
from bot.helper.ext_utils.bot_utils import sync_to_async, clean_video_name
from bot.helper.ext_utils.files_utils import ARCH_EXT, get_mime_type


def getSplitSizeBytes(size):
    size = size.lower()
    if size.endswith("mb"):
        size = size.split("mb")[0]
        size = int(float(size) * 1048576)
    elif size.endswith("gb"):
        size = size.split("gb")[0]
        size = int(float(size) * 1073741824)
    else:
        size = 0
    return size

async def createThumb(msg, _id="", temp=False):
    if not _id:
        _id = msg.id
    path = "Thumbnails/"
    if temp:
        path = "Temp_thumb/"
    await makedirs(path, exist_ok=True)
    photo_dir = await msg.download()
    des_dir = f"{path}{_id}.jpg"
    await sync_to_async(Image.open(photo_dir).convert("RGB").save, des_dir, "JPEG")
    await aioremove(photo_dir)
    return des_dir

async def createWM(msg, _id=""):
    if not _id:
        _id = msg.id
    path = "Watermark/"
    await makedirs(path, exist_ok=True)
    photo_dir = await msg.download()
    des_dir = f"{path}{_id}.png"
    await sync_to_async(Image.open(photo_dir).convert("RGBA").save, des_dir, "PNG")
    await aioremove(photo_dir)
    return des_dir

async def storeSubFile(msg, _id="", soft=False):
    if not _id:
        _id = msg.id
    path = f"SubsFile/"
    if soft:
        path = f"SubsFile/{_id}/"
    await makedirs(path, exist_ok=True)
    file_dir = await msg.download()
    ext = ospath.splitext(file_dir)[-1].lower()
    if ext in ['.srt', '.ass', '.ssa', '.vtt']:
        des_dir = f"{path}{_id}{ext}"
        if soft:
            random_name = ''.join(random.choices(string.digits, k=3))
            des_dir = f"{path}{_id}_{random_name}{ext}"
    else:
        LOGGER.error(f"Jenis file subtitle tidak didukung! - File: {file_dir}")
        raise ValueError("Jenis file subtitle tidak didukung!")
    await move(file_dir, des_dir)
    return des_dir

async def is_multi_streams(path):
    
    try:
        result = await cmd_exec(
            [
                "ffprobe",
                "-hide_banner",
                "-loglevel",
                "error",
                "-print_format",
                "json",
                "-show_streams",
                path,
            ]
        )
        if res := result[1]:
            LOGGER.warning(f"Get Video Streams: {res} - File: {path}")
    except Exception as e:
        LOGGER.error(f"Get Video Streams: {e}. Mostly File not found! - File: {path}")
        return False
    fields = eval(result[0]).get("streams")
    if fields is None:
        LOGGER.error(f"get_video_streams: {result}")
        return False
    videos = 0
    audios = 0
    for stream in fields:
        if stream.get("codec_type") == "video":
            videos += 1
        elif stream.get("codec_type") == "audio":
            audios += 1
    return videos > 1 or audios > 1


async def get_media_info(path):
    try:
        result = await cmd_exec(
            [
                "ffprobe",
                "-hide_banner",
                "-loglevel",
                "error",
                "-print_format",
                "json",
                "-show_format",
                path,
            ]
        )
        if res := result[1]:
            LOGGER.warning(f"Get Media Info: {res} - File: {path}")
    except Exception as e:
        LOGGER.error(f"Get Media Info: {e}. Mostly File not found! - File: {path}")
        return 0, None, None
    fields = eval(result[0]).get("format")
    if fields is None:
        LOGGER.error(f"get_media_info: {result}")
        return 0, None, None
    duration = round(float(fields.get("duration", 0)))
    tags = fields.get("tags", {})
    artist = tags.get("artist") or tags.get("ARTIST") or tags.get("Artist")
    title = tags.get("title") or tags.get("TITLE") or tags.get("Title")
    return duration, artist, title


async def get_document_type(path):
    is_video, is_audio, is_image = False, False, False
    if path.endswith(tuple(ARCH_EXT)) or re_search(
        r".+(\.|_)(rar|7z|zip|bin)(\.0*\d+)?$", path
    ):
        return is_video, is_audio, is_image
    mime_type = await sync_to_async(get_mime_type, path)
    if mime_type.startswith("image"):
        return False, False, True
    if mime_type.startswith("audio"):
        return False, True, False
    if not mime_type.startswith("video") and not mime_type.endswith("octet-stream"):
        return is_video, is_audio, is_image
    try:
        result = await cmd_exec(
            [
                "ffprobe",
                "-hide_banner",
                "-loglevel",
                "error",
                "-print_format",
                "json",
                "-show_streams",
                path,
            ]
        )
        if res := result[1]:
            LOGGER.warning(f"Get Document Type: {res} - File: {path}")
            return is_video, is_audio, is_image
    except Exception as e:
        LOGGER.error(f"Get Document Type: {e}. Mostly File not found! - File: {path}")
        return is_video, is_audio, is_image
    fields = eval(result[0]).get("streams")
    if fields is None:
        LOGGER.error(f"get_document_type: {result}")
        return is_video, is_audio, is_image
    for stream in fields:
        if stream.get("codec_type") == "video":
            is_video = True
        elif stream.get("codec_type") == "audio":
            is_audio = True
    return is_video, is_audio, is_image


async def take_ss(video_file, ss_nb) -> list:
    if ss_nb > 10:
        ss_nb = 10
    duration = (await get_media_info(video_file))[0]
    if duration != 0:
        dirpath, name = video_file.rsplit("/", 1)
        name, _ = ospath.splitext(name)
        dirpath = f"{dirpath}/screenshots/"
        await makedirs(dirpath, exist_ok=True)
        interval = duration // ss_nb + 1
        cap_time = interval
        outputs = []
        cmd = ""
        for i in range(ss_nb):
            output = f"{dirpath}SS.{name}_{i:02}.png"
            outputs.append(output)
            cmd += f'opera -hide_banner -loglevel error -ss {cap_time} -i "{video_file}" -q:v 1 -frames:v 1 "{output}"'
            cap_time += interval
            if i + 1 != ss_nb:
                cmd += " && "
        _, err, code = await cmd_exec(cmd, True)
        if code != 0:
            LOGGER.error(
                f"Error while creating sreenshots from video. Path: {video_file} stderr: {err}"
            )
            return []
        return outputs
    else:
        LOGGER.error("take_ss: Can't get the duration of video")
        return []
    

async def get_audio_thumb(audio_file):
    des_dir = "Thumbnails/"
    await makedirs(des_dir, exist_ok=True)
    des_dir = f"Thumbnails/{time()}.jpg"
    cmd = [
        "opera",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        audio_file,
        "-an",
        "-vcodec",
        "copy",
        des_dir,
    ]
    _, err, code = await cmd_exec(cmd)
    if code != 0 or not await aiopath.exists(des_dir):
        LOGGER.error(
            f"Error while extracting thumbnail from audio. Name: {audio_file} stderr: {err}"
        )
        return None
    return des_dir


async def create_thumbnail(video_file, duration):
    des_dir = "Thumbnails"
    await makedirs(des_dir, exist_ok=True)
    des_dir = ospath.join(des_dir, f"{time()}.jpg")
    if duration is None:
        duration = (await get_media_info(video_file))[0]
    if duration == 0:
        duration = 3
    duration = duration // 2
    cmd = [
        "opera",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        str(duration),
        "-i",
        video_file,
        "-vf",
        "thumbnail",
        "-frames:v",
        "1",
        des_dir,
    ]
    _, err, code = await cmd_exec(cmd)
    if code != 0 or not await aiopath.exists(des_dir):
        LOGGER.error(
            f"Error while extracting thumbnail from video. Name: {video_file} stderr: {err}"
        )
        return None
    return des_dir


async def split_file(
    path,
    size,
    dirpath,
    split_size,
    listener,
    start_time=0,
    i=1,
    inLoop=False,
    multi_streams=True,
):
    if listener.seed and not listener.newDir:
        dirpath = f"{dirpath}/splited_files_mltb"
        await makedirs(dirpath, exist_ok=True)
    parts = -(-size // listener.splitSize)
    if listener.equalSplits and not inLoop:
        split_size = (size // parts) + (size % parts)
    if not listener.as_doc and (await get_document_type(path))[0]:
        if multi_streams:
            multi_streams = await is_multi_streams(path)
        duration = (await get_media_info(path))[0]
        base_name, extension = ospath.splitext(path)
        split_size -= 5000000
        while i <= parts or start_time < duration - 4:
            out_path = f"{base_name}.part{i:03}{extension}"
            cmd = [
                "opera",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                str(start_time),
                "-i",
                path,
                "-fs",
                str(split_size),
                "-map",
                "0",
                "-map_chapters",
                "-1",
                "-async",
                "1",
                "-strict",
                "-2",
                "-c",
                "copy",
                out_path,
            ]
            if not multi_streams:
                del cmd[10]
                del cmd[10]
            async with subprocess_lock:
                if listener.suproc == "cancelled":
                    return False
                listener.suproc = await create_subprocess_exec(*cmd, stderr=PIPE)
            _, stderr = await listener.suproc.communicate()
            code = listener.suproc.returncode
            if code == -9:
                return False
            elif code != 0:
                stderr = stderr.decode().strip()
                try:
                    await aioremove(out_path)
                except:
                    pass
                if multi_streams:
                    LOGGER.warning(
                        f"{stderr}. Retrying without map, -map 0 not working in all situations. Path: {path}"
                    )
                    return await split_file(
                        path,
                        size,
                        dirpath,
                        split_size,
                        listener,
                        start_time,
                        i,
                        True,
                        False,
                    )
                else:
                    LOGGER.warning(
                        f"{stderr}. Unable to split this video, if it's size less than {listener.maxSplitSize} will be uploaded as it is. Path: {path}"
                    )
                return "errored"
            out_size = await aiopath.getsize(out_path)
            if out_size > listener.maxSplitSize:
                dif = out_size - listener.maxSplitSize
                split_size -= dif + 5000000
                await aioremove(out_path)
                return await split_file(
                    path,
                    size,
                    dirpath,
                    split_size,
                    listener,
                    start_time,
                    i,
                    True,
                    multi_streams,
                )
            lpd = (await get_media_info(out_path))[0]
            if lpd == 0:
                LOGGER.error(
                    f"Something went wrong while splitting, mostly file is corrupted. Path: {path}"
                )
                break
            elif duration == lpd:
                LOGGER.warning(
                    f"This file has been splitted with default stream and audio, so you will only see one part with less size from orginal one because it doesn't have all streams and audios. This happens mostly with MKV videos. Path: {path}"
                )
                break
            elif lpd <= 3:
                await aioremove(out_path)
                break
            start_time += lpd - 3
            i += 1
    else:
        out_path = f"{path}."
        async with subprocess_lock:
            if listener.suproc == "cancelled":
                return False
            listener.suproc = await create_subprocess_exec(
                "split",
                "--numeric-suffixes=1",
                "--suffix-length=3",
                f"--bytes={split_size}",
                path,
                out_path,
                stderr=PIPE,
            )
        _, stderr = await listener.suproc.communicate()
        code = listener.suproc.returncode
        if code == -9:
            return False
        elif code != 0:
            stderr = stderr.decode().strip()
            LOGGER.error(f"{stderr}. Split Document: {path}")
    return True


async def createSampleVideo(
    listener, video_file, sample_duration, part_duration, oneFile=False
):
    filter_complex = ""
    dir, name = video_file.rsplit("/", 1)
    output_file = f"{dir}/SAMPLE.{name}"
    segments = [(0, part_duration)]
    duration = (await get_media_info(video_file))[0]
    remaining_duration = duration - (part_duration * 2)
    parts = (sample_duration - (part_duration * 2)) // part_duration
    time_interval = remaining_duration // parts
    next_segment = time_interval
    for _ in range(parts):
        segments.append((next_segment, next_segment + part_duration))
        next_segment += time_interval
    segments.append((duration - part_duration, duration))

    for i, (start, end) in enumerate(segments):
        filter_complex += (
            f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}]; "
        )
        filter_complex += (
            f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]; "
        )

    for i in range(len(segments)):
        filter_complex += f"[v{i}][a{i}]"

    filter_complex += f"concat=n={len(segments)}:v=1:a=1[vout][aout]"

    cmd = [
        "opera",
        "-i",
        video_file,
        "-filter_complex",
        filter_complex,
        "-map",
        "[vout]",
        "-map",
        "[aout]",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-threads",
        f"{cpu_count() // 2}",
        output_file,
    ]
    async with subprocess_lock:
        if listener.suproc == "cancelled":
            return False
    listener.suproc = await create_subprocess_exec(*cmd, stderr=PIPE)
    _, stderr = await listener.suproc.communicate()
    code = listener.suproc.returncode
    if code == -9:
        return False
    elif code != 0:
        stderr = stderr.decode().strip()
        LOGGER.error(
            f"{stderr}. Something went wrong while creating sample video, mostly file is corrupted. Path: {video_file}"
        )
        return video_file
    else:
        if oneFile:
            newDir, _ = ospath.splitext(video_file)
            await makedirs(newDir, exist_ok=True)
            await gather(
                move(video_file, f"{newDir}/{name}"),
                move(output_file, f"{newDir}/SAMPLE.{name}"),
            )
            return newDir
        return True

############################# by pikachu #################
watermark_dict = {
    "top_left": "10:10",
    "top_center": "(W-w)/2:10",
    "top_right": "W-w-10:10",
    "bottom_left": "10:H-h-10",
    "bottom_center": "(W-w)/2:H-h-10",
    "bottom_right": "W-w-10:H-h-10",
}
watermark_reso_dict = {
    "kecil": "scale=iw*0.1:-1",
    "sedang": "scale=iw*0.2:-1",
    "besar": "scale=iw*0.3:-1",
    "extra": "scale=iw*0.4:-1",
    "ultra": "scale=iw*0.5:-1",
    "super": "scale=iw*0.6:-1",
    }

font_sizes = {
    "kecil": 12,
    "sedang": 14,
    "besar": 16,
    "ultra": 22,
    "extra": 24,
    "super": 26,
}

font_colors = {
    "putih": "&HFFFFFF&",
    "biru": "&HFF0000&",
    "hijau": "&H00FF00&",
    "merah": "&H0000FF&",
    "cyan": "&HFFFF00&",
    "kuning": "&H00FFFF&",
    "magenta": "&HFF00FF&",
    "hitam": "&H000000&",
    "purple": "&H800080&",
}

fonts_dict = {
    1: "Standard Symbols PS",
    2: "Century Schoolbook L",
    3: "URW Gothic",
    4: "Nimbus Roman",
    5: "DejaVu Sans Mono",
    6: "URW Palladio L",
    7: "Nimbus Sans",
    8: "URW Gothic L",
    9: "Dingbats",
    10: "URW Chancery L",
    11: "Nimbus Mono PS",
    12: "Nimbus Sans Narrow",
    13: "URW Bookman",
    14: "DejaVu Sans",
    15: "Noto Sans Mono",
    16: "C059",
    17: "Nimbus Sans L",
    18: "Droid Sans Fallback",
    19: "Z003",
    20: "Standard Symbols L",
    21: "D050000L",
    22: "Nimbus Mono L",
    23: "Nimbus Roman No9 L",
    24: "Noto Mono",
    25: "P052",
    26: "DejaVu Serif",
    27: "URW Bookman L"
}
async def PerformVideoEditor(
    listener, video_file, oneFile=False
):
    cmd = ["opera", "-y", "-i", video_file]

    # Extract
    extract = listener.video_editor.get("extract", False)
    if extract:
        output_dir = await extract_subtitles(video_file)
        if not output_dir:
            return False
        return output_dir
    
    # Compress
    compress_settings = listener.video_editor.get("compress", {})
    resolution = compress_settings.get("resolution")
    ext = listener.video_editor.get("extension", "mkv")
    dir = ospath.dirname(video_file)
    base_name = clean_video_name(video_file)
    resolution_label = ""
    if resolution:
        resolution_label = f"-{resolution.split(':')[1]}p"
        base_name = clean_video_name(video_file, compress=True)
    output_file = f"{dir}/{base_name}{resolution_label}"

    # Rename
    rename = listener.video_editor.get("rename")
    if rename:
        output_file = f"{dir}/{rename}{resolution_label}"
        if not resolution:
            output_file = f"{dir}/{rename}"

    # Watermark
    watermark = listener.video_editor.get("watermark", {})
    watermark_file = watermark.get("file", None)
    watermark_position = watermark.get("position", "top_left")
    watermark_size = watermark.get("size", "sedang")
    if watermark_file:
        output_file += f"_WM"

    # Hardsub
    hardsub = listener.video_editor.get("hardsub", {})
    hardsub_file = hardsub.get("file", None)
    hardsub_size = hardsub.get("size", "sedang")
    hardsub_color = hardsub.get("color", "putih")
    hardsub_font = hardsub.get("font", 5)
    hardsub_bold = hardsub.get("bold", False)
    bold = 1 if hardsub_bold else 0
    if hardsub_file:
        output_file += f"_HS"

    # Softsub
    softsub = listener.video_editor.get("softsub", [])
    if softsub:
        for sub in softsub:
            softsub_file = sub.get("file", None)
            cmd.extend(["-i", softsub_file])
        for index, sub in enumerate(softsub):
            language = sub.get("language", "Tidak diketahui")
            cmd.extend([f"-metadata:s:s:{index}", f"language={language}"])
    if softsub:
        output_file += f"_SS"
    
    output_file += f".{ext}"
    filter_str = []
    if watermark_file and watermark_position and watermark_size:
        watermark_filter = (
            f"movie={watermark_file}, {watermark_reso_dict[watermark_size]} [watermark_resized]; "
        )
        if resolution:
            watermark_filter += f"[0:v]scale={resolution}[scaled]; "
            watermark_filter += f"[scaled][watermark_resized] overlay={watermark_dict[watermark_position]}"
        else:
            watermark_filter += f"[0:v][watermark_resized] overlay={watermark_dict[watermark_position]}"
        filter_str.append(watermark_filter)
    elif resolution:
        filter_str.append(f"scale={resolution}")

    if hardsub_file and hardsub_size and hardsub_color and hardsub_font:
        hardsub_filter = (
            f"subtitles={hardsub_file}:force_style='FontSize={font_sizes[hardsub_size]},PrimaryColour={font_colors[hardsub_color]},FontName={fonts_dict[int(hardsub_font)]},Bold={bold}'"
        )
        filter_str.append(hardsub_filter)

    if filter_str:
        cmd.extend(["-vf", ",".join(filter_str)])
    cmd.extend(["-map", "0:v", "-map", "0:a"])
    for i in range(len(softsub)):
        cmd.extend(["-map", str(i + 1)])
    if softsub:
        if ext == "mp4":
            cmd.extend(["-c:s", "mov_text"])
        elif ext == "mkv":
            cmd.extend(["-c:s", "srt"])

    video_codec = listener.video_editor.get("video_codec", "libx264")
    audio_codec = listener.video_editor.get("audio_codec", "default")
    audio_bitrate = listener.video_editor.get("audio_bitrate", "128k")
    preset = listener.video_editor.get("preset", "veryfast")
    crf = listener.video_editor.get("crf", "23")
    if not (resolution or watermark or hardsub):
        cmd.extend(["-c:v", "copy", "-c:a", "copy"])
    else:
        if resolution or watermark_file or hardsub_file:
            cmd.extend(["-c:v", f"{video_codec}", "-preset", f"{preset}", "-crf", f"{crf}"])
        else:
            cmd.extend(["-c:v", "copy"])
        if audio_codec == "default":
            cmd.extend(["-c:a", "copy"])
        else:
            cmd.extend(["-c:a", f"{audio_codec}", "-b:a", f"{audio_bitrate}"])
        cmd.extend(["-threads", f"{cpu_count() // 2}"])
    cmd.append(output_file)

    LOGGER.info(f"FFmpeg filter: {','.join(filter_str)}")
    LOGGER.info(f"FFmpeg command: {' '.join(cmd)}")
    async with subprocess_lock:
        if listener.suproc == "cancelled":
            return False
    listener.suproc = await create_subprocess_exec(*cmd, stderr=PIPE)
    _, stderr = await listener.suproc.communicate()
    code = listener.suproc.returncode

    if watermark_file:
        try:
            await aioremove(watermark_file)
        except:
            pass
    if hardsub_file:
        try:
            await aioremove(hardsub_file)
        except:
            pass
    if softsub:
        for sub in softsub:
            try:
                await aioremove(sub["file"])
            except:
                continue

    if code == -9:
        return False
    elif code != 0:
        stderr = stderr.decode().strip()
        LOGGER.error(
            f"{stderr}. Something went wrong while perform video editor, mostly file is corrupted. Path: {video_file}"
        )
        return video_file
    else:
        if oneFile:
            await aioremove(video_file)
            return output_file
        return True
    
async def extract_subtitles(video_file):
    try:
        dir = ospath.dirname(video_file)
        output_dir = f"{dir}/subtitles"
        await makedirs(output_dir, exist_ok=True)
        command = ['opera', '-i', video_file]
        process = await create_subprocess_exec(*command, stdout=PIPE, stderr=PIPE)
        stdout, stderr = await process.communicate()
        subtitle_streams = []
        for line in stderr.decode().splitlines():
            if 'Subtitle' in line:
                parts = line.split()
                stream_index = parts[1].replace('#', '').split('(')[0].rstrip(':')
                try:
                    language = parts[1].split('(')[1].split(')')[0]
                except:
                    language = "Tidak Diketahui"
                subtitle_type = parts[3] if len(parts) > 3 else "Tidak Diketahui"
                subtitle_streams.append({'stream_index': stream_index, 'language': language, 'subtitle_type': subtitle_type})
        if len(subtitle_streams) == 0:
            LOGGER.error(f"Subtitle not found on {ospath.basename(video_file)}")
            return None
        tasks = []
        for data in subtitle_streams:
            idx = data['stream_index']
            language = data['language']
            subtitle_type = data['subtitle_type']
            if subtitle_type == "subrip":
                ext = "srt"
            elif subtitle_type == "ass":
                ext = "ass"
            else:
                ext = "srt"
            subtitle_file = f"{output_dir}/subtitles_{idx}_{language}.{ext}"
            task = create_task(extract_single_subtitle(video_file, idx, subtitle_file, ext))
            tasks.append(task)
        await gather(*tasks)
        await aioremove(video_file)
        return output_dir
    except Exception as e:
        LOGGER.error(f"Gagal saat mencoba extract subtitle: {e}")
        return None

async def extract_single_subtitle(video_file, stream_index, subtitle_file, ext):
    try:
        command = [
            'opera',
            '-i', video_file,
            '-map', f'{stream_index}',
            '-c:s', f'{ext}',
            subtitle_file 
        ]
        process = await create_subprocess_exec(*command, stdout=PIPE, stderr=PIPE)
        await process.communicate()
        LOGGER.info(f"FFmpeg command: {' '.join(command)}")
    except Exception as e:
        LOGGER.error(f"Error extracting subtitle {stream_index}: {e}")
        return None