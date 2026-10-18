# Changelog

All notable changes to Doggy Player. The newest release is also described in [RELEASE_NOTES.md](RELEASE_NOTES.md).

## v1.1.77

Maintenance release: documentation only (new README, changelog, license wording). No player changes.


## v1.1.76

Smooth seeking on long videos, plus safety and housekeeping fixes:

* One arrow-key press now seeks exactly once (it used to replay a moment after every press).
* Holding an arrow key scrubs smoothly; quick presses back and forth resume playback once.
* Fixed a pause/play flicker, a timeline click that left the video paused, and needless redraws.
* No more background re-encoding of long films.
* The local media server requires a per-run token; conversion caches are capped at 10 GB.
* The anonymous daily usage count can be switched off in Settings.


## v1.1.75

Seeking now behaves like VLC: the jump is instant, with no audio/video "vibration" at the start of a seek:

* **No more stutter at the start of a seek:** Playback now starts when real data exists instead of as soon as the track layout is known, so Chromium no longer fires `waiting` on every source swap.
* **Audio starts with the picture:** The re-encode pipe interleaves audio with the first picture instead of pushing the first audio packet ~0.4s further into the stream.
* **Seeking becomes native:** Files whose video codec Chromium cannot decode (H.263, MPEG-4, MJPEG, WMV, ProRes, ...) are re-encoded once in the background to a dense-keyframe H.264/AAC MP4 and cached; an already cached copy is adopted immediately on the next play.
* **Exact seek positions:** Pipe restarts are millisecond exact instead of rounded down to whole seconds.
* **Automatic update:** Installed apps receive v1.1.75 via the built-in updater.

## v1.1.72

Smoother, quieter seeking:

* **Keyframe densification:** Files that seek poorly are re-encoded once to a dense-keyframe MP4 and cached, so subsequent jumps are fast.
* **Seek controller fixes:** Rapid scrubbing and hold-to-seek no longer stack requests; the playhead stays with the picture.
* **Vibration removal:** Reworked the seek path so jumps no longer produce the audio "vibration" heard before.
* **Automatic update:** Installed apps receive v1.1.72 via the built-in updater.

## v1.1.71

Bug fixes.

## v1.1.70

Bug fixes.

## v1.1.69

Fixes settings dropdowns that closed immediately so you could not change default speed or IPTV default quality:

* **Settings menus stay open:** Replaced fragile native `<select>` controls with custom menus for language, default speed, and IPTV default quality.
* **Focus trap fixed:** The settings overlay no longer steals focus on every video time update (which closed open dropdowns instantly).
* **Auto-update for all platforms:** Windows (`latest.yml`), macOS (`latest-mac.yml`) and Linux (`latest-linux.yml`) are published to GitHub Releases.

## v1.1.68

Fixes seek freezes on large files that are MPEG-TS (or similar) despite a `.mp4` extension:

* **Root cause:** Some “`.mp4`” files are actually MPEG-TS — Chromium freezes about 1 second on every seek.
* **Fix:** Detect real container, remux once with stream-copy to a real MP4 + faststart (quality preserved), then play that file.
* **Cached:** Next open of the same file skips remux and seeks immediately.
* **Automatic update:** Installed apps receive v1.1.68 via the built-in updater after release assets are published.

## v1.1.67

Hotfix for a regression in v1.1.66:

* **Frozen picture / working audio:** Removed the FFmpeg scrub-preview overlay that could stay on top of the video after seeking.
* **Reliable resume:** Video playback is forced to continue after seek so picture and sound stay together.
* **Automatic update:** Installed apps receive v1.1.67 via the built-in updater after release assets are published.

## v1.1.66

Doggy Player v1.1.66 fixes the remaining freeze when seeking large/HQ videos with arrow keys or the timeline:

* **Live scrub preview:** Holding ←/→ or dragging the timeline shows FFmpeg JPEG frames on top of the video so the picture keeps updating.
* **Seek once on release:** The real `<video>` seek runs only when you release keys/mouse — no stacked freezes on big files.
* **fastSeek, no pause-first:** Single seeks use keyframe seeking without pausing first (which made freezes worse in v1.1.65).
* **Automatic update:** Installed apps receive v1.1.66 via the built-in updater after release assets are published.

## v1.1.65

Doggy Player v1.1.65 fixes freeze-on-seek for large and high-quality videos:

* **No more freeze when seeking:** Playback pauses briefly during seek, then resumes so the decoder is not overloaded on big/HQ files.
* **Direct disk playback:** Common local formats (mp4, mkv, mov, webm, …) use `file://` instead of HTTP Range for much faster seeks.
* **Smarter seek queue:** Rapid scrubbing and hold-to-seek coalesce into one in-flight seek (last-wins) instead of stacking decode jobs.
* **Smoother timeline & arrows:** UI time updates immediately; media seeks less often while you drag or hold ←/→.
* **Transcoded formats:** Debounced FFmpeg restarts for avi/ts and similar so seeks no longer pile up.
* **Automatic update:** Installed apps on **Windows, macOS and Linux** receive v1.1.65 automatically via the built-in updater (`latest.yml` / `latest-mac.yml` / `latest-linux.yml`).

## v1.1.64

Doggy Player v1.1.64 delivers buttery-smooth seeking for large/long videos and pro-grade hold-to-seek controls:

* **Fixed lag on large files:** Timeline scrubbing is now debounced (`75ms`), uses `fastSeek` to the nearest keyframe and a subtle spinner instead of black flash — no more freeze on 4K/long `.mp4`/`.mkv`.
* **Faster local streaming:** Electron stream server now serves `32 MB` chunks with `512 KB` `highWaterMark`, proper `Content-Range` handling and MIME detection for instant seeks.
* **New seek steps:** Single tap `Arrow Left/Right` is now `5s` (was `10s`), `Shift` + arrow = `15s`, `Ctrl` + arrow = `20s`.
* **Hold to seek:** Hold `Arrow Left/Right` (or `Ctrl`/`Shift` + arrow) to continuously seek until you release — perfect for long videos.
* **Smarter UI:** Seeking state is tracked separately from buffering, so `onTimeUpdate` stays smooth and the timeline stays responsive while the video decodes.
* **Automatic update:** Installed apps on **Windows, macOS and Linux** receive v1.1.64 automatically via the built-in updater (`latest.yml` / `latest-mac.yml` / `latest-linux.yml`).

## v1.1.63

Doggy Player v1.1.63 adds flexible video brightness controls with per-video persistence:

* **Brightness adjustment:** Make the active video darker or brighter from 50% to 150%.
* **Visible percentage:** The current brightness percentage is displayed in the player controls and as an on-video indicator while adjusting.
* **Keyboard control:** Use `Ctrl + Arrow Up` and `Ctrl + Arrow Down` to change brightness in 5% steps.
* **Per-video lock:** Lock a brightness value for one video and automatically restore it whenever that video is opened again.
* **Non-destructive processing:** Brightness affects playback only and never modifies the original video file.
* **Automatic update:** Existing installations receive v1.1.63 through Doggy Player's built-in updater after the release assets are published.

