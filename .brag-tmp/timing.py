import json, os

FPS = 30
LEAD_IN = 0.55     # silence before the first line
GAP = 0.42         # silence after each scene's narration
TAIL = 0.95        # room after the last line

with open(os.path.join(".brag-tmp", "audio", "vo.json"), encoding="utf-8") as f:
    vo = json.load(f)

scenes = []
t = 0.0
for i, s in enumerate(vo):
    lead = LEAD_IN if i == 0 else 0.0
    start = t
    speech = s["dur"]
    dur = lead + speech + GAP
    if s["key"] == "hook":
        dur += 0.55                 # let the logo breathe
    words = [{"w": w["w"], "start": start + lead + w["start"], "end": start + lead + w["end"]} for w in s["words"]]
    scenes.append({
        "key": s["key"], "text": s["text"], "wav": s["wav"], "start": start,
        "dur": dur, "speech_start": start + lead, "speech_len": speech,
        "speech_end": start + lead + speech, "words": words,
    })
    t = start + dur

total = t + TAIL
for s in scenes:
    s["start_silence"] = s["speech_start"] - s["start"]

with open(os.path.join(".brag-tmp", "timing.json"), "w", encoding="utf-8") as f:
    json.dump({"total": total, "scenes": scenes}, f, indent=2)

for s in scenes:
    print(f"{s['key']:8s} start={s['start']:6.2f} dur={s['dur']:6.2f} speech={s['speech_len']:6.2f}")
print(f"TOTAL {total:.2f}s")
