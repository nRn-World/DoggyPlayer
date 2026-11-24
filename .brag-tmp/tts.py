import asyncio, json, os, subprocess, wave
import edge_tts

FF = os.path.abspath("node_modules/ffmpeg-static/ffmpeg.exe")
OUT = os.path.join(".brag-tmp", "audio")
os.makedirs(OUT, exist_ok=True)

VOICE = "en-US-GuyNeural"
RATE = "+4%"

SCENES = [
    ("hook",   "This is Doggy Player."),
    ("seek",   "A free desktop player that opens almost any video file, and jumps to any moment instantly. No frozen frames. No audio crackle."),
    ("zoom",   "Scroll to zoom in. Drag to pan around. Or hold Shift and draw a box to punch into one detail."),
    ("fix",    "Sideways clip? Too dark? Rotate it, lift the brightness, and lock it to that file."),
    ("subs",   "Subtitles in SRT, VTT and ASS. Smart playlists. And a real equalizer."),
    ("iptv",   "It even plays live TV. Xtream Codes, M3U and EPG, all built in. No plugins."),
    ("private", "And your files never leave your machine. That daily anonymous ping? You can turn it off."),
    ("cta",    "Windows, macOS and Linux. Free for personal use. Get it on GitHub."),
]


async def one(index, key, text):
    mp3 = os.path.join(OUT, f"{index:02d}_{key}.mp3")
    words = []
    comm = edge_tts.Communicate(text, VOICE, rate=RATE, boundary="WordBoundary")
    with open(mp3, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "w": chunk["text"],
                    "start": chunk["offset"] / 1e7,
                    "end": (chunk["offset"] + chunk["duration"]) / 1e7,
                })
    wav = mp3.replace(".mp3", ".wav")
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", mp3,
                    "-ar", "44100", "-ac", "1", wav], check=True)
    with wave.open(wav) as w:
        dur = w.getnframes() / w.getframerate()
    print(f"{key:8s} {dur:6.2f}s  words={len(words)}")
    return {"key": key, "text": text, "wav": wav, "dur": dur, "words": words}


async def main():
    data = []
    for i, (key, text) in enumerate(SCENES):
        data.append(await one(i, key, text))
    with open(os.path.join(OUT, "vo.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("total speech:", round(sum(d["dur"] for d in data), 2), "s")


asyncio.run(main())
