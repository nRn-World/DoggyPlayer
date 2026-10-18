<p align="center">
  <img src="public/logo.gif" alt="Doggy Player logo" width="160" />
</p>

<h1 align="center">Doggy Player 🐶</h1>

<p align="center">
  <b>A fast, dark, modern video player with VLC-style instant seeking, zoom &amp; rotate, subtitles and built-in IPTV.</b><br/>
  Free for personal use · Windows · macOS · Linux
</p>

<p align="center">
  <a href="https://github.com/nRn-World/DoggyPlayer/releases/latest"><img src="https://img.shields.io/badge/%E2%AC%87%20Download-latest%20release-2ea44f?style=for-the-badge" alt="Download latest release" /></a>
</p>

<p align="center">
  <a href="https://github.com/nRn-World/DoggyPlayer/releases/latest"><img src="https://img.shields.io/github/v/release/nRn-World/DoggyPlayer?sort=semver&label=latest&color=2ea44f" alt="Latest release" /></a>
  <a href="https://github.com/nRn-World/DoggyPlayer/releases"><img src="https://img.shields.io/github/downloads/nRn-World/DoggyPlayer/total?label=downloads&color=blue" alt="Downloads" /></a>
  <a href="https://github.com/nRn-World/DoggyPlayer/stargazers"><img src="https://img.shields.io/github/stars/nRn-World/DoggyPlayer?style=flat&label=stars&color=yellow" alt="Stars" /></a>
  <a href="LICENSE.txt"><img src="https://img.shields.io/badge/license-CC%20BY--NC%204.0-red.svg" alt="License: CC BY-NC 4.0" /></a>
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-0078D6.svg" alt="Platforms" />
  <img src="https://img.shields.io/badge/Electron-React%2019-61DAFB.svg" alt="Electron + React" />
</p>

<p align="center">
  <a href="Screenshot/Sc1.png"><img src="Screenshot/Sc1.png" alt="Doggy Player main interface" width="80%" /></a>
</p>

---

## Why Doggy Player?

* **Seeking that just works.** Jump anywhere in a long film instantly — no stutter, no audio "vibration", no frozen frame. Files Chromium can't seek well are quietly converted once in the background and cached.
* **Zoom into the picture.** Mouse-wheel zoom, click-to-pan, or hold `Shift` and draw a rectangle to zoom into a detail.
* **Fix bad videos on the fly.** Rotate with `Alt + Arrow`, adjust brightness 50–150 %, and lock the setting per video so it comes back next time.
* **Everything in one place.** Playlists, subtitles (`.srt` `.vtt` `.ass`), an equalizer and IPTV (Xtream Codes, M3U, EPG) — no plugins to hunt for.
* **Private by design.** Nothing leaves your machine except an optional anonymous once-a-day usage count that you can turn off ([details](#-privacy)).

## ⚡ Quick start

1. Open the [**Releases**](https://github.com/nRn-World/DoggyPlayer/releases/latest) page.
2. Download the file for your system:

   | OS | File |
   |---|---|
   | Windows | `Doggy-Player-Setup-<version>.exe` (recommended) |
   | macOS | `Doggy-Player-<version>.dmg` |
   | Linux | `Doggy-Player-<version>.AppImage` |

3. Install, open a video (or drag it onto the window) and enjoy. The built-in updater keeps you on the latest version.

> **Windows SmartScreen** may show a warning for new, unsigned apps — click *More info → Run anyway*. The full source is in this repository.

## Key Features

* **Smooth Seeking on Long Videos (v1.1.76)**: One arrow-key press seeks exactly once, holding an arrow key scrubs smoothly (the picture follows the playhead and playback resumes when you let go), and quick presses back and forth resume playback once after the last press. No background re-encoding of long films.
* **VLC-Style Gapless Seeking (v1.1.75)**: Seeks land instantly with no audio/video "vibration" at the start of a jump — playback begins when real data exists, re-encoded streams interleave audio with the first picture, and pipe restarts use millisecond-exact offsets.
* **Native Seeking for Hard Files**: Files Chromium cannot decode (H.263, MPEG-4, MJPEG, WMV, ProRes, ...) shorter than 30 minutes are re-encoded once in the background to a dense-keyframe H.264/AAC MP4 and cached (capped at 10 GB), so later seeks are as fast as a native file.
* **Smart Remux Seeking (v1.1.68)**: Detects MPEG-TS (and similar) files mislabeled as `.mp4` and remuxes them once to real seekable MP4 — fixes the ~1s freeze on certain large files.
* **Advanced Zooming & Panning**: Smooth mouse-wheel zoom and click-to-pan.
* **Area Selection Zoom**: Hold `Shift` and draw a rectangle to zoom into details.
* **Video Rotation Controls**: Rotate with `Alt + Arrow keys` and reset to the original orientation at any time.
* **Per-Video Rotation Lock**: Save a manual rotation for a specific video and automatically restore it whenever that video is opened again.
* **Clean Rotation UI**: The rotation lock appears only after the user manually rotates the video in Doggy Player, not because of a video's built-in orientation metadata.
* **Video Brightness Control**: Adjust the active video from 50% to 150% brightness without modifying the original media file.
* **Per-Video Brightness Lock**: Lock a brightness level for a specific video and automatically restore it the next time that video is opened.
* **Brightness Shortcuts**: Press `Ctrl + Arrow Up` or `Ctrl + Arrow Down` to adjust brightness in 5% steps with an on-video percentage indicator.
* **Precision Playback Control**: Play, pause, `5s` / `15s` (`Shift`) / `20s` (`Ctrl`) seek with smooth hold-to-scrub, adjustable volume and press-and-hold slow motion (0.25x).
* **Smart Playlist**: Drag-and-drop support with optional automatic removal of finished videos.
* **IPTV Support**: Xtream Codes, M3U, and EPG support built in.
* **Subtitle Engine**: Support for `.srt`, `.vtt`, `.ass`, and additional subtitle formats with synchronization offset.
* **Screenshot Capture**: Capture frames instantly with `Alt + S`.
* **Equalizer**: Professional audio control with +/-12 dB adjustment.

See the [**changelog**](CHANGELOG.md) for everything that has changed between versions.

---

## 📸 Screenshots

<p align="center">
  <a href="Screenshot/Sc1.png">
    <img src="Screenshot/Sc1.png" alt="Main Interface" width="31%" />
  </a>
  <a href="Screenshot/Sc2.png">
    <img src="Screenshot/Sc2.png" alt="Playback Controls" width="31%" />
  </a>
  <a href="Screenshot/Sc3.png">
    <img src="Screenshot/Sc3.png" alt="Playlist & Settings" width="31%" />
  </a>
</p>

<p align="center">
  <a href="Screenshot/IPTV.png">
    <img src="Screenshot/IPTV.png" alt="IPTV Interface" width="31%" />
  </a>
  <a href="Screenshot/Live.png">
    <img src="Screenshot/Live.png" alt="Live TV" width="31%" />
  </a>
  <a href="Screenshot/Movie.png">
    <img src="Screenshot/Movie.png" alt="Movies" width="31%" />
  </a>
</p>

---

## 🧑‍💻 For Developers

We welcome community contributions! Please read our [**Contributing Guidelines**](CONTRIBUTING.md) and [**Code of Conduct**](CODE_OF_CONDUCT.md) first. Looking for a place to start? Check issues labelled [`good first issue`](https://github.com/nRn-World/DoggyPlayer/labels/good%20first%20issue).

```bash
git clone https://github.com/nRn-World/DoggyPlayer.git
cd DoggyPlayer
npm install
npm run dev:electron     # run in development mode
npm run build:electron   # build your own installer
npm test                 # unit tests
npm run test:seek        # drives the real app: one seek per key press, hold, burst and timeline click
```

`test:seek` needs a free port 3000 (or starts its own dev server) and opens the app briefly.

**Tech stack:** [Electron](https://www.electronjs.org/) · [React 19](https://react.dev/) · [Vite](https://vitejs.dev/) · [Tailwind CSS](https://tailwindcss.com/) · [FFmpeg](https://ffmpeg.org/) (`ffmpeg-static`) · [hls.js](https://github.com/video-dev/hls.js/)

---

## 🔒 Privacy

The installed app sends **one anonymous request per day** to a public counter service (`abacus.jasoncameron.dev`) so the author can see roughly how many people use it. It contains no file names, no IPTV details and no identifier — only "one more use today". You can switch it off in **Settings → Send an anonymous daily usage count**. Nothing is sent from development builds.

Local cache: re-encoded and remuxed copies are stored in the app's data folder and are capped at 10 GB (oldest removed first).

## 🛡️ Security

Please review our [**Security Policy**](SECURITY.md) to report vulnerabilities privately — never through a public issue.

## ⚠️ License

Licensed under the **nRn World Non-Commercial License** ([Creative Commons BY-NC 4.0](LICENSE.txt)).

* **Individuals & students:** free to download, use and modify for personal and educational use.
* **Companies & organizations:** professional use requires prior written consent.
* **Commercial use, sale or redistribution for profit** requires a paid license — contact [bynrnworld@gmail.com](mailto:bynrnworld@gmail.com).

---

## 🤝 Community & Support

* ⭐ **Star this project** if Doggy Player is useful to you — it really helps others find it!
* 💬 **Ask questions and share ideas** in [Discussions](https://github.com/nRn-World/DoggyPlayer/discussions).
* 🐛 **Report bugs** or **request features** in [Issues](https://github.com/nRn-World/DoggyPlayer/issues).
* ☕ **Support development:** [Buy me a coffee 💜](https://ko-fi.com/nrnworld)

<p align="center">Created with ❤️ © nRn World</p>
