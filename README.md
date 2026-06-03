# Pulse Player Fixed v3

Pulse Player – Feel Every Beat, Watch Every Moment.

## What was fixed in v3

- Fixed macOS read-only path problems by storing app data in the user's Library/Application Support, cache, and logs folders.
- Fixed PySide6 enum compatibility for playlist drag/drop.
- Improved VLC audio output startup and forces audio unmuted with saved volume when media starts.
- Added embedded album-art extraction using Mutagen for MP3/FLAC/M4A and folder artwork fallback: `cover.jpg`, `cover.png`, `folder.jpg`, `folder.png`.
- Redesigned playlist into a VLC-style right panel with compact rows, numbering, metadata, and album-art icons.
- Fixed seek/progress handling with a bigger progress bar like VLC.
- Made the volume slider smaller and added a real-time percentage label.
- Added safer VLC seeking and more frequent progress updates.

## Install

```bash
cd ~/Downloads/pulse_player
python3 -m pip install -r requirements.txt
```

Install VLC app on macOS if it is not already installed.

## Run

```bash
cd ~/Downloads/pulse_player
python3 main.py
```

You may also run it from anywhere:

```bash
/usr/local/bin/python3 /Users/waqasabbasi/Downloads/pulse_player/main.py
```

## Notes

If video plays but there is no sound, check:

1. macOS system volume.
2. VLC app is installed.
3. Pulse Player volume is above 0%.
4. Press `M` once to ensure mute is off.
5. Test the same file in VLC app.

## Package Windows EXE

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --onefile --name "Pulse Player" main.py
```

## Package macOS APP

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name "Pulse Player" main.py
```

## Package Linux

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name pulse-player main.py
```


## v6 Update

- Added VLC-style Shuffle button.
- Added Repeat / Loop modes: Off, Repeat All, Repeat One.
- Added shortcuts: Shift+P = Previous, Shift+N = Next, S = Shuffle, L = Repeat mode.
- Added tooltips for the new controls.

## v7 UI / playlist improvements

- Orange VLC-style hover highlight in playlist.
- Current playing file shows a ▶ marker.
- Audio files show 32×32 album artwork when available.
- Video files show cached 32×32 thumbnails when FFmpeg is installed.
- Double-click playlist item plays immediately.
- Right-click playlist menu: Play, Remove, Remove All, Open Location, Properties.
- VLC-style resume prompt with text buttons: Continue, Restart/Open from Start, No/Cancel.

For video thumbnails, install FFmpeg and make sure `ffmpeg` is available in Terminal/Command Prompt.


## v8 changes

- Removed Internet / network video stream feature.
- Improved playlist text contrast and orange hover highlighting.
- Optimized bulk local file adding by reducing playlist repainting during add operations.
- Playlist remains local-file focused for smoother performance and simpler VLC-style use.


## v9 Update

- Audio/music fullscreen now keeps all features visible:
  album art, playlist, progress bar, playback buttons, shuffle/repeat, speed,
  volume, menu bar, and tooltips.
- Video fullscreen still auto-hides controls after 5 seconds of inactivity,
  like VLC.
