import flet as ft
import platform
import os
import subprocess
import requests
import zipfile
import shutil
import time
import threading
from flet_apk_installer import FletApkInstaller
from pathlib import Path

class FNAFLauncher:
    def __init__(self):
        self.page = None
        self.game_name = "Five Nights at Freddy's"

        self.system = platform.system()
        self.is_android = self.system == "Android"

        if self.is_android:
            # Prefer the public Downloads folder
            public_downloads = Path("/storage/emulated/0/Download")
            if public_downloads.exists():
                self.download_dir = public_downloads / "FNAF_Launcher"
            else:
                # Fallback to app-specific external storage
                external = os.getenv("FLET_APP_STORAGE_EXTERNAL")
                if external:
                    self.download_dir = Path(external) / "FNAF_Launcher"
                else:
                    # Final fallback to internal app storage
                    data_dir = os.getenv("FLET_APP_STORAGE_DATA")
                    if data_dir:
                        self.download_dir = Path(data_dir) / "FNAF_Launcher"
                    else:
                        self.download_dir = Path("/data/local/tmp/FNAF_Launcher")
        else:
            # Windows: use Downloads folder
            self.download_dir = Path.home() / "Downloads" / "FNAF_Launcher"

        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.links = {
            "android": "https://www.dl.farsroid.com/game/Five-Night-at-Freddys-2.0.7(www.Farsroid.com).apk",
            "windows": "https://abrehamrahi.ir/o/public/sZhIO0o1/"
        }

        self.get_local_path()
        self.download_running = False

    def get_local_path(self):
        if self.is_android:
            self.local_file = self.download_dir / "fnaf1.apk"
        else:
            self.local_file = self.download_dir / "fnaf1.zip"
        return self.local_file

    def check_file_exists(self):
        return self.local_file.exists() and self.local_file.stat().st_size > 0

    def download_game(self, progress_callback=None, status_callback=None):
        url = self.links["android"] if self.is_android else self.links["windows"]
        try:
            if status_callback:
                status_callback("Connecting...")
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            start_time = time.time()
            self.download_dir.mkdir(parents=True, exist_ok=True)

            total_mb = total_size / (1024 * 1024) if total_size > 0 else 0
            if status_callback:
                if total_mb > 0:
                    status_callback(f"Downloading: 0.0 MB / {total_mb:.1f} MB (0%)")
                else:
                    status_callback("Downloading... (size unknown)")

            with open(self.local_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        elapsed = time.time() - start_time
                        speed = downloaded / elapsed / (1024 * 1024) if elapsed > 0 else 0

                        if total_size > 0:
                            progress = downloaded / total_size
                            downloaded_mb = downloaded / (1024 * 1024)
                            status = f"Downloading: {downloaded_mb:.1f} MB / {total_mb:.1f} MB ({progress*100:.1f}%) - {speed:.1f} MB/s"
                            if progress_callback:
                                progress_callback(progress)
                        else:
                            downloaded_mb = downloaded / (1024 * 1024)
                            status = f"Downloading: {downloaded_mb:.1f} MB downloaded - {speed:.1f} MB/s"
                            if progress_callback:
                                progress_callback(0.5)

                        if status_callback:
                            status_callback(status)

            if status_callback:
                status_callback("Download complete!")
            return True

        except Exception as e:
            if status_callback:
                status_callback(f"Error: {str(e)}")
            print(f"Download error: {e}")
            return False

    def install_apk_android(self):
        if not self.is_android:
            return False

        if not self.local_file.exists():
            return False

        if not hasattr(self, "apk_installer"):
            return False

        self.apk_installer.path = str(self.local_file.resolve())
        self.apk_installer.install()

        # Request successfully sent to Flutter.
        # Flutter will report success/error asynchronously.
        return True
    def launch_windows_game(self):
        if not self.local_file.exists():
            return False

        if self.local_file.suffix == '.zip':
            extract_dir = self.download_dir / "FNAF1"
            extract_dir.mkdir(exist_ok=True)
            with zipfile.ZipFile(self.local_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            exe_files = list(extract_dir.rglob("*.exe"))
            if exe_files:
                subprocess.Popen([str(exe_files[0])], shell=True, cwd=str(extract_dir))
                return True
            return False
        else:
            subprocess.Popen([str(self.local_file)], shell=True)
            return True

    def install_or_play(self):
        if self.check_file_exists():
            if self.is_android:
                if self.install_apk_android():
                    return "installed"
                else:
                    return "install_failed"
            else:
                return "launched" if self.launch_windows_game() else "launch_failed"
        else:
            return "download_needed"

    def get_storage_info(self):
        if self.download_dir.exists():
            size = sum(f.stat().st_size for f in self.download_dir.rglob("*") if f.is_file())
            return size
        return 0

    def clear_game(self):
        deleted = False
        if self.local_file.exists():
            try:
                self.local_file.unlink()
                deleted = True
            except Exception as e:
                print(f"Error deleting {self.local_file}: {e}")

        if not self.is_android:
            extract_dir = self.download_dir / "FNAF1"
            if extract_dir.exists():
                try:
                    shutil.rmtree(extract_dir)
                    deleted = True
                except Exception as e:
                    print(f"Error deleting extracted folder: {e}")

        try:
            if self.download_dir.exists() and not any(self.download_dir.iterdir()):
                self.download_dir.rmdir()
        except Exception as e:
            print(f"Could not remove empty directory: {e}")

        return deleted


def main(page: ft.Page):
    page.title = "FNAF Launcher"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.Colors.BLACK
    page.window.width = 600
    page.window.height = 500
    page.window.resizable = False

    launcher = FNAFLauncher()

    debug_log = []

    def apk_debug(e):
        debug_log.append(f"[DEBUG] {e.data}")

        status_text.value = "\n".join(debug_log[-5:])
        status_text.color = ft.Colors.BLUE_300
        page.update()

    def apk_success(e):
        debug_log.append(f"[SUCCESS] {e.data}")

        status_text.value = "\n".join(debug_log[-5:])
        status_text.color = ft.Colors.GREEN

        btn_text.value = "Installed"
        page.update()

    def apk_error(e):
        debug_log.append(f"[ERROR] {e.data}")

        status_text.value = "\n".join(debug_log[-5:])
        status_text.color = ft.Colors.RED

        btn_text.value = "Retry"
        page.update()

    launcher.apk_installer = FletApkInstaller(
        visible=False,
        on_debug=apk_debug,
        on_success=apk_success,
        on_error=apk_error,
    )

    status_text = ft.Text("Ready", color=ft.Colors.GREY_400)
    progress_bar = ft.ProgressBar(width=400, visible=False, color=ft.Colors.RED)
    file_status = ft.Text("Checking...", size=14, color=ft.Colors.GREY_400)
    storage_text = ft.Text("", size=12, color=ft.Colors.GREY_500)
    btn_text = ft.Text("Install / Play")

    def download_thread():
        def update_progress(p):
            progress_bar.value = p
            progress_bar.visible = True
            page.update()

        def update_status(msg):
            status_text.value = msg
            page.update()

        progress_bar.visible = True
        progress_bar.value = 0.0
        page.update()

        success = launcher.download_game(progress_callback=update_progress, status_callback=update_status)

        if success:
            status_text.value = "Download complete! Installing/Launching..."
            status_text.color = ft.Colors.GREEN
            page.update()
            result = launcher.install_or_play()
        else:
            status_text.value = "Download failed."
            status_text.color = ft.Colors.RED
            btn_text.value = "Retry"

        progress_bar.visible = False
        download_button.disabled = False
        update_file_status()
        page.update()
        launcher.download_running = False

    def on_install_click(e):
        if launcher.download_running:
            return

        if launcher.check_file_exists():
            status_text.value = f"Game found. {'Installing...' if launcher.is_android else 'Launching...'}"
            status_text.color = ft.Colors.ORANGE
            page.update()
            download_button.disabled = True

            result = launcher.install_or_play()
            if result == "installed":
                status_text.value = "APK installer opened! Tap Install to continue."
                status_text.color = ft.Colors.GREEN
                btn_text.value = "Installed"
            elif result == "launched":
                status_text.value = "Game launched!"
                status_text.color = ft.Colors.GREEN
                btn_text.value = "Launched"
            else:
                status_text.value = f"Failed to install. Try opening the APK manually."
                status_text.color = ft.Colors.RED
                btn_text.value = "Retry"
            download_button.disabled = False
            update_file_status()
            page.update()
            return

        status_text.value = "Starting download..."
        status_text.color = ft.Colors.ORANGE
        btn_text.value = "Downloading..."
        download_button.disabled = True
        progress_bar.visible = True
        progress_bar.value = 0.0
        page.update()

        launcher.download_running = True
        threading.Thread(target=download_thread, daemon=True).start()

    def update_file_status():
        if launcher.check_file_exists():
            file_status.value = "Game downloaded"
            file_status.color = ft.Colors.GREEN
            if btn_text.value not in ("Installed", "Launched"):
                btn_text.value = "Install / Play"
        else:
            file_status.value = "Game not downloaded"
            file_status.color = ft.Colors.RED
            if btn_text.value in ("Installed", "Launched"):
                btn_text.value = "Install / Play"

        size = launcher.get_storage_info()
        storage_text.value = f"Storage used: {size / (1024*1024):.1f} MB" if size > 0 else "No files downloaded"
        page.update()

    def on_clear_click(e):
        if launcher.clear_game():
            status_text.value = "Game files cleared"
            status_text.color = ft.Colors.ORANGE
            btn_text.value = "Install / Play"
            update_file_status()
            page.update()
        else:
            status_text.value = "Nothing to clear"
            status_text.color = ft.Colors.GREY_400
            page.update()

    download_button = ft.ElevatedButton(
        content=btn_text,
        on_click=on_install_click,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.RED_900,
            color=ft.Colors.WHITE,
            padding=ft.Padding(15, 15, 15, 15),
        ),
        width=150,
    )

    clear_button = ft.ElevatedButton(
        "Clear",
        on_click=on_clear_click,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.GREY_800,
            color=ft.Colors.WHITE,
            padding=ft.Padding(10, 10, 10, 10),
        ),
        width=80,
    )

    page.add(
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("FNAF Launcher", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(height=20, color=ft.Colors.RED_900),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Five Nights at Freddy's", size=22, weight=ft.FontWeight.BOLD),
                            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                            ft.Row([
                                ft.Text("Platform:", size=14, color=ft.Colors.GREY_400),
                                ft.Text(f"{platform.system()}", size=14, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                            ]),
                            ft.Row([
                                ft.Text("Variant:", size=14, color=ft.Colors.GREY_400),
                                ft.Text("Android APK" if launcher.is_android else "Windows ZIP", size=14, color=ft.Colors.WHITE),
                            ]),
                            ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                            ft.Row([
                                download_button,
                                ft.Column([file_status, storage_text], spacing=2),
                                clear_button,
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            progress_bar,
                            status_text,
                            ft.Text(
                                f"Files stored in: {launcher.download_dir}",
                                size=10, color=ft.Colors.GREY_600, italic=True, selectable=True
                            ),
                        ]),
                        padding=20,
                    ),
                    elevation=5,
                    margin=10,

                ),
                launcher.apk_installer,
                ft.Container(
                    content=ft.Text(
                        "Unofficial Launcher - Cross Platform | FNAF 1",
                        size=12, color=ft.Colors.GREY_600, italic=True
                    ),
                    alignment=ft.Alignment(0, 0),
                )
            ]),
            padding=20,
            expand=True,
        )
    )

    update_file_status()

ft.app(target=main)