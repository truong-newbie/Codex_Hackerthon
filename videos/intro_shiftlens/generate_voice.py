"""Generate Vietnamese narration from the reviewed scene script."""

import json
import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".video-build" / "py"))

from gtts import gTTS  # noqa: E402


HERE = Path(__file__).resolve().parent
OUT = HERE / "build" / "audio"
OUT.mkdir(parents=True, exist_ok=True)
scenes = json.loads((HERE / "scenes.json").read_text(encoding="utf-8"))

for index, scene in enumerate(scenes, 1):
    target = OUT / f"{index:02d}.mp3"
    stamp = OUT / f"{index:02d}.sha256"
    digest = hashlib.sha256(scene["voice"].encode("utf-8")).hexdigest()
    if target.exists() and target.stat().st_size > 1000 and stamp.exists() and stamp.read_text() == digest:
        print(f"reuse {target.name}", flush=True)
        continue
    gTTS(scene["voice"], lang="vi").save(str(target))
    stamp.write_text(digest)
    print(f"created {target.name}: {target.stat().st_size} bytes", flush=True)
