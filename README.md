# FNAF Launcher

A cross-platform launcher for **Five Nights at Freddy's**, built with **Python** and **Flet**.

The launcher provides a simple interface for downloading and launching the game on both Windows and Android.

## Features

* Cross-platform support

  * Windows
  * Android
* Automatic game download
* Download progress with speed and percentage
* Automatic APK installation on Android
* Automatic extraction and launching of the Windows version
* Storage usage display
* Clear downloaded game files
* Modern dark-themed interface

## Facts

-  This Repo helped build [flet-apk-installer](https://github.com/radin6262/flet-apk-installer)
- check it out. it exposes native android api's to sideload apk's



## Screenshots

*Screenshots will be added soon.*

## Requirements

* Python 3.10 or newer
* Flet 0.86.5 or newer

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/FNAF-Launcher.git
cd FNAF-Launcher
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Running

Desktop:

```bash
flet run
```

Android (development):

```bash
flet debug android
```

## Building

### Windows

```bash
flet build windows
```

### Android

```bash
flet build apk
```

Release build:

```bash
flet build apk --release
```

## Dependencies

* Flet
* Requests
* Flet APK Installer Extension

## Project Structure

```text
FNAF-Launcher/
├── assets/
├── main.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Platform Support

| Platform | Status          |
| -------- |-----------------|
| Windows  | Fully Supported |
| Android  | Expiremental    |
| Linux    | Not Tested      |
| macOS    | Not Tested      |
| iOS      | Not Supported   |

## Notes

* Android uses the system package installer to install the downloaded APK.
* Windows automatically extracts and launches the downloaded game.
* Internet access is required to download the game.

## License

This project is licensed under the MIT License.

## Disclaimer

This launcher is an unofficial project and is not affiliated with or endorsed by Scott Cawthon or the Five Nights at Freddy's franchise. Users are responsible for ensuring they have the legal right to download and use the game files provided by the configured download source.
