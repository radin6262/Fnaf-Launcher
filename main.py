import flet as ft
import platform
import os
import subprocess
import requests
import zipfile
from pathlib import Path

class FNAFLauncher:
    def __init__(self):
        self.page = None
        self.game_name = "Five Nights at Freddy's"

        self.system = platform.system()
        self.is_android = self.system == "Android"

        # Set directories using Flet's official environment variable for Android
        if self.is_android:
            data_dir = os.getenv("FLET_APP_STORAGE_DATA")
            if data_dir:
                self.download_dir = Path(data_dir) / "FNAF_Launcher"
            else:
                # Fallback for safety
                self.download_dir = Path("/data/data/com.fnaf.launcher/files/FNAF_Launcher")
        else:
            self.download_dir = Path(os.environ.get('APPDATA', '')) / "FNAF_Launcher"

        self.download_dir.mkdir(parents=True, exist_ok=True)

        # Replace these with real download URLs
        self.links = {
            "android": "https://example.com/fnaf1.apk",
            "windows": "https://example.com/fnaf1.zip"
        }

        self.get_local_path()

    def get_local_path(self):
        if self.is_android:
            self.local_file = self.download_dir / "fnaf1.apk"
        else:
            self.local_file = self.download_dir / "fnaf1.zip"
        return self.local_file

    def check_file_exists(self):
        return self.local_file.exists() and self.local_file.stat().st_size > 0

    def download_game(self, progress_callback=None):
        url = self.links["android"] if self.is_android else self.links["windows"]
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            self.download_dir.mkdir(parents=True, exist_ok=True)

            with open(self.local_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0 and progress_callback:
                            progress_callback(downloaded / total_size)
            return True
        except Exception as e:
            print(f"Download error: {e}")
            return False

    def install_apk_android(self):
        """Install APK on Android using the system package installer (Intent)"""
        if not self.is_android:
            return False
        if not self.local_file.exists():
            return False

        try:
            # Use 'am' (Activity Manager) to fire a VIEW intent for the APK
            # This opens the system installer, and the user taps "Install"
            apk_path = str(self.local_file)
            cmd = [
                "am", "start",
                "-a", "android.intent.action.VIEW",
                "-d", f"file://{apk_path}",
                "-t", "application/vnd.android.package-archive"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Intent launch error: {e}")

        # Fallback: try 'pm install' (requires system permission, may fail without root)
        try:
            result = subprocess.run(
                ["pm", "install", "-r", str(self.local_file)],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            print(f"pm install error: {e}")
            return False

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
                return "installed" if self.install_apk_android() else "install_failed"
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
        if self.local_file.exists():
            self.local_file.unlink()
            return True
        return False


def main(page: ft.Page):
    page.title = "FNAF Launcher"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.Colors.BLACK
    page.window.width = 600
    page.window.height = 500
    page.window.resizable = False

    launcher = FNAFLauncher()

    status_text = ft.Text("Ready", color=ft.Colors.GREY_400)
    progress_bar = ft.ProgressBar(width=400, visible=False, color=ft.Colors.RED)
    file_status = ft.Text("Checking...", size=14, color=ft.Colors.GREY_400)
    storage_text = ft.Text("", size=12, color=ft.Colors.GREY_500)
    btn_text = ft.Text("Install / Play")

    def on_install_click(e):
        status_text.value = f"Checking for game on {'Android' if launcher.is_android else 'Windows'}..."
        status_text.color = ft.Colors.WHITE
        download_button.disabled = True
        btn_text.value = "Processing..."
        page.update()

        if launcher.check_file_exists():
            status_text.value = f"Game found. {'Installing...' if launcher.is_android else 'Launching...'}"
            status_text.color = ft.Colors.ORANGE
            page.update()

            result = launcher.install_or_play()
            if result == "installed":
                status_text.value = "APK installed successfully!"
                status_text.color = ft.Colors.GREEN
                btn_text.value = "Installed"
            elif result == "launched":
                status_text.value = "Game launched!"
                status_text.color = ft.Colors.GREEN
                btn_text.value = "Launched"
            else:
                status_text.value = f"Failed to {'install' if launcher.is_android else 'launch'} the game."
                status_text.color = ft.Colors.RED
                btn_text.value = "Retry"
        else:
            status_text.value = "Downloading game... This may take a while."
            status_text.color = ft.Colors.ORANGE
            progress_bar.visible = True
            btn_text.value = "Downloading..."
            page.update()

            def update_progress(p):
                progress_bar.value = p
                status_text.value = f"Downloading: {p*100:.1f}%"
                page.update()

            success = launcher.download_game(update_progress)

            if success:
                status_text.value = "Download complete! Installing/Launching..."
                page.update()
                result = launcher.install_or_play()
                if result == "installed":
                    status_text.value = "APK installed successfully!"
                    status_text.color = ft.Colors.GREEN
                    btn_text.value = "Installed"
                elif result == "launched":
                    status_text.value = "Game launched!"
                    status_text.color = ft.Colors.GREEN
                    btn_text.value = "Launched"
                else:
                    status_text.value = f"Failed to {'install' if launcher.is_android else 'launch'}."
                    status_text.color = ft.Colors.RED
                    btn_text.value = "Retry"
            else:
                status_text.value = "Download failed. Check internet."
                status_text.color = ft.Colors.RED
                btn_text.value = "Retry"

            progress_bar.visible = False
            page.update()

        update_file_status()
        download_button.disabled = False
        page.update()

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
            update_file_status()
            btn_text.value = "Install / Play"
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