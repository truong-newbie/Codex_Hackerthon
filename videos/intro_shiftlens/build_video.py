"""Build the approximately two-minute ShiftLens introduction video.

Requires FFmpeg from the isolated .video-build npm install, slides from render.js,
and narration from generate_voice.py.
"""

import json
import re
import subprocess
import textwrap
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BUILD = HERE / "build"
SEGMENTS = BUILD / "segments"
SEGMENTS.mkdir(parents=True, exist_ok=True)
FFMPEG = ROOT / ".video-build" / "node_modules" / "ffmpeg-static" / "ffmpeg.exe"
SCENES = json.loads((HERE / "scenes.json").read_text(encoding="utf-8"))


def ffmpeg(*args):
    command = [str(FFMPEG), "-hide_banner", "-loglevel", "error", *map(str, args)]
    subprocess.run(command, check=True)


def audio_duration(path):
    result = subprocess.run([str(FFMPEG), "-i", str(path)], capture_output=True, text=True)
    match = re.search(r"Duration: (\d+):(\d+):([\d.]+)", result.stderr)
    if not match:
        raise RuntimeError(f"Unable to determine MP3 duration: {path}")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def timestamp(seconds):
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def subtitle_chunks(voice):
    words = voice.split()
    chunks = []
    current = []
    for word in words:
        current.append(word)
        if len(" ".join(current)) > 62 and (word.endswith((",", ".", ";", "!", "?")) or len(" ".join(current)) > 86):
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    if len(chunks) > 1 and len(chunks[-1]) < 25:
        chunks[-2] += " " + chunks.pop()
    return chunks


subtitle_lines = []
cue = 1
timeline = 0.0
segment_paths = []

for index, scene in enumerate(SCENES, 1):
    image = BUILD / "slides" / f"{index:02}.png"
    audio = BUILD / "audio" / f"{index:02}.mp3"
    if not image.is_file() or not audio.is_file():
        raise FileNotFoundError(f"Missing slide or narration for scene {index}")
    speech = audio_duration(audio)
    pad = 1.1 if index == len(SCENES) else 0.55
    length = speech + pad
    output = SEGMENTS / f"{index:02}.mp4"
    video_filter = (
        "zoompan=z='min(zoom+0.00012,1.045)':"
        "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        "d=1:s=1280x720:fps=30,"
        "fade=t=in:st=0:d=0.22,"
        f"fade=t=out:st={length-0.28:.3f}:d=0.28,format=yuv420p"
    )
    audio_filter = (
        "afade=t=in:st=0:d=0.12,"
        f"afade=t=out:st={max(speech-0.25,0):.3f}:d=0.25,"
        f"apad=pad_dur={pad:.3f},atrim=duration={length:.3f}"
    )
    print(f"Encoding scene {index:02}: {length:.2f}s", flush=True)
    ffmpeg(
        "-y", "-loop", "1", "-framerate", "30", "-i", image,
        "-i", audio, "-t", f"{length:.3f}",
        "-vf", video_filter, "-af", audio_filter,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac",
        "-b:a", "128k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", output,
    )
    segment_paths.append(output)

    chunks = subtitle_chunks(scene["voice"])
    weights = [len(chunk.split()) for chunk in chunks]
    total_weight = sum(weights)
    elapsed = 0.0
    for chunk, weight in zip(chunks, weights):
        chunk_length = speech * weight / total_weight
        start = timeline + elapsed
        end = timeline + elapsed + chunk_length
        wrapped = "\n".join(textwrap.wrap(chunk, width=62, break_long_words=False))
        subtitle_lines.extend([str(cue), f"{timestamp(start)} --> {timestamp(end)}", wrapped, ""])
        cue += 1
        elapsed += chunk_length
    timeline += length

subtitle_path = HERE / "ShiftLens_intro_vi.srt"
subtitle_path.write_text("\n".join(subtitle_lines), encoding="utf-8")
concat_path = BUILD / "concat.txt"
concat_path.write_text(
    "\n".join(f"file '{segment.as_posix()}'" for segment in segment_paths) + "\n",
    encoding="utf-8",
)
joined = BUILD / "joined.mp4"
ffmpeg("-y", "-f", "concat", "-safe", "0", "-i", concat_path, "-c", "copy", joined)
final = HERE / "ShiftLens_intro_2min.mp4"
ffmpeg(
    "-y", "-i", joined, "-i", subtitle_path,
    "-map", "0:v:0", "-map", "0:a:0", "-map", "1:s:0",
    "-c:v", "copy", "-c:a", "copy", "-c:s", "mov_text",
    "-metadata:s:s:0", "language=vie", "-disposition:s:0", "default",
    "-movflags", "+faststart", final,
)
print(f"Created {final} ({timeline:.2f}s)", flush=True)
