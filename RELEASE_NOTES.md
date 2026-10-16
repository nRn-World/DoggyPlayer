# Doggy Player v1.1.76

Seeking is now smooth on long videos, and the app got a round of safety fixes.

## Seeking
* **One press, one jump.** Pressing an arrow key used to seek twice (once on
  key-down, once on key-up), which replayed a fraction of a second and was heard
  and seen as a stutter after every press. It now seeks exactly once.
* **Holding an arrow key scrubs smoothly.** The picture follows the playhead at
  the same speed as before and playback resumes when you let go.
* **Quick presses back and forth** park the picture and resume once, a moment
  after the last press, instead of restarting audio and video on every press.
* Fixed an endless pause/play flicker that could appear after a quick seek, a
  timeline click that left the video paused, and the timeline redrawing the whole
  player 60 times a second.
* Long films are no longer re-encoded in the background (it kept the CPU and
  disk busy for tens of minutes and then swapped the video mid-play).

## Safety and housekeeping
* The local media server now requires a secret per-run token and no longer
  answers requests from other web pages.
* File names are never passed through a shell when reading video length.
* Conversion caches are capped at 10 GB (oldest removed first) and leftovers from
  interrupted conversions are cleaned up at start. An interrupted remux can no
  longer leave a half-written file that is mistaken for a finished one.
* Playback position is saved every 5 seconds and only the newest 500 are kept.
* Privacy: the anonymous once-a-day usage count can be switched off in Settings,
  and is described in the README.

## Upgrade

Existing Doggy Player installations will receive v1.1.76 automatically via the
built-in updater after the release assets have finished building and publishing.
