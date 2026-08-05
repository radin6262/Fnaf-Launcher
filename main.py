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
from jnius import autoclass

# ============================================
# GAME LIST - Add your games here!
# ============================================
GAMES = [
    {
        "id": "fnaf1",
        "name": "Five Nights at Freddy's",
        "package": "com.scottgames.fivenightsatfreddys",
        "android_url": "https://www.dl.farsroid.com/game/Five-Night-at-Freddys-2.0.7(www.Farsroid.com).apk",
        "windows_url": "https://abrehamrahi.ir/o/public/sZhIO0o1/",
        "icon": "F️",
        "image": "images/fnaf1.png",
    },
    # Add more games here:
    {
        "id": "fnaf2",
        "name": "Five Nights at Freddy's 2",
        "package": "com.scottgames.fnaf2",
        "android_url": "https://example.com/fnaf2.apk",
        "windows_url": "https://example.com/fnaf2.zip",
        "icon": "F",
        "image": "images/fnaf2.png",
    },
    {
        "id": "fnaf3",
        "name": "Five Nights at Freddy's 3",
        "package": "com.scottgames.fnaf3",
        "android_url": "https://example.com/fnaf3.apk",
        "windows_url": "https://example.com/fnaf3.zip",
        "icon": "F",
        "image": "images/fnaf3.png",
    },
    {
        "id": "fnaf4",
        "name": "Five Nights at Freddy's 4",
        "package": "com.scottgames.fnaf4",
        "android_url": "https://example.com/fnaf4.apk",
        "windows_url": "https://example.com/fnaf4.zip",
        "icon": "F",
        "image": "images/fnaf4.png",
    },
]


class FNAFLauncher:
    def __init__(self):
        self.page = None
        self.game_name = "Five Nights at Freddy's"

        self.system = platform.system()
        self.is_android = self.system == "Android"

        if self.is_android:
            data_dir = os.getenv("FLET_APP_STORAGE_DATA")

            if data_dir:
                self.download_dir = Path(data_dir) / "FNAF_Launcher"
            else:
                self.download_dir = Path("/data/data/com.flet.fnaflauncher/files/FNAF_Launcher")
        else:
            # Windows: use Downloads folder
            self.download_dir = Path.home() / "Downloads" / "FNAF_Launcher"

        self.download_dir.mkdir(parents=True, exist_ok=True)

        # Use first game as default for backward compatibility
        self.current_game = GAMES[0] if GAMES else None

        self.links = {
            "android": self.current_game["android_url"] if self.current_game else "",
            "windows": self.current_game["windows_url"] if self.current_game else ""
        }

        self.get_local_path()
        self.download_running = False

    def get_local_path(self):
        """Dynamic file path based on current game ID"""
        if self.current_game is None:
            return None

        game_id = self.current_game["id"]

        if self.is_android:
            self.local_file = self.download_dir / f"{game_id}.apk"
        else:
            self.local_file = self.download_dir / f"{game_id}.zip"
        return self.local_file

    def check_file_exists(self):
        return self.local_file is not None and self.local_file.exists() and self.local_file.stat().st_size > 0

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
                            status = f"Downloading: {downloaded_mb:.1f} MB / {total_mb:.1f} MB ({progress * 100:.1f}%) - {speed:.1f} MB/s"
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

    def is_game_installed(self):
        if not self.is_android or self.current_game is None:
            return False

        package = self.current_game["package"]

        try:
            result = subprocess.run(
                ["pm", "list", "packages"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                print("pm command failed")
                return False

            installed = f"package:{package}" in result.stdout

            print("Package check:")
            print("Looking for:", f"package:{package}")
            print("Installed:", installed)

            return installed

        except Exception as e:
            print("Package check error:", e)
            return False

    def launch_android_game(self):
        if self.current_game is None:
            return False

        package = self.current_game["package"]

        try:
            # Get the current Android Activity
            activity_host = autoclass(os.environ["MAIN_ACTIVITY_HOST_CLASS_NAME"])
            activity = activity_host.mActivity

            # Get PackageManager
            pm = activity.getPackageManager()

            # Get the launch intent for the app
            intent = pm.getLaunchIntentForPackage(package)

            if intent is None:
                print(f"{package} is not installed or has no launchable activity.")
                return False

            # Launch the app
            activity.startActivity(intent)

            print(f"Launched {package}")
            return True

        except Exception as e:
            print("Launch error:", e)
            return False

    def install_apk_android(self):
        if not self.is_android:
            return False

        print("APK installer started")

        if not self.local_file.exists():
            print("APK missing:", self.local_file)
            return False

        try:
            apk_path = str(self.local_file.resolve())

            print("Installing:", apk_path)

            self.apk_installer.path = apk_path

            result = self.apk_installer.install()

            print("Installer result:", result)

            return True

        except Exception as e:
            print("INSTALL ERROR:", e)
            return False

    def launch_windows_game(self):
        if not self.local_file.exists():
            return False

        if self.local_file.suffix == '.zip':
            # Use current game ID for extract directory
            game_id = self.current_game["id"] if self.current_game else "fnaf1"
            extract_dir = self.download_dir / game_id
            extract_dir.mkdir(exist_ok=True)

            # Only extract if not already extracted
            exe_files = list(extract_dir.rglob("*.exe"))
            if not exe_files:
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
        if self.is_android:
            print("IS INSTALLED RESULT:", self.is_game_installed())
            # Check if game is already installed
            if self.is_game_installed():
                print("Game found, launching...")
                if self.launch_android_game():
                    return "launched"
                else:
                    return "launch_failed"

            # Not installed, check if APK is downloaded
            if self.check_file_exists():
                print("APK found, installing...")
                if self.install_apk_android():
                    return "installed"
                else:
                    return "install_failed"
            else:
                return "download_needed"

        else:
            # Windows flow
            if self.check_file_exists():
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

        # Delete the APK/ZIP file
        if self.local_file is not None and self.local_file.exists():
            try:
                self.local_file.unlink()
                deleted = True
            except Exception as e:
                print(f"Error deleting {self.local_file}: {e}")

        # Delete the extracted game folder (Windows)
        if not self.is_android and self.current_game is not None:
            game_id = self.current_game["id"]
            extract_dir = self.download_dir / game_id
            if extract_dir.exists():
                try:
                    shutil.rmtree(extract_dir)
                    deleted = True
                except Exception as e:
                    print(f"Error deleting extracted folder: {e}")

        # If the download directory is empty, remove it
        try:
            if self.download_dir.exists() and not any(self.download_dir.iterdir()):
                self.download_dir.rmdir()
        except Exception as e:
            print(f"Could not remove empty directory: {e}")

        return deleted


def create_game_card(game, launcher, on_install_click, on_clear_click, download_button, clear_button, spinner,
                     file_status, storage_text, progress_bar, status_text, update_file_status, page):
    """Create a styled game card with image and buttons overlay."""

    game_image = ft.Image(
        src=game["image"],
        width=300,
        height=400,
        fit=ft.BoxFit.COVER,
    )

    game_name_overlay = ft.Container(
        content=ft.Text(
            game["name"],
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
            text_align=ft.TextAlign.CENTER,
        ),
        alignment=ft.Alignment(0, -1),
        padding=ft.Padding(0, 10, 0, 0),
        bgcolor=ft.Colors.with_opacity(0.6, ft.Colors.BLACK),
        width=300,
        height=50,
    )

    install_btn = ft.ElevatedButton(
        content=download_button.content,
        on_click=on_install_click,
        width=120,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.with_opacity(0.85, ft.Colors.RED_900),
            color=ft.Colors.WHITE,
        ),
    )

    clear_btn = ft.ElevatedButton(
        "Clear Files",
        on_click=on_clear_click,
        width=120,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.with_opacity(0.75, ft.Colors.GREY_800),
            color=ft.Colors.WHITE,
        ),
    )

    image_stack = ft.Stack(
        [
            game_image,

            # # Game title (optional)
            # ft.Container(
            #     content=ft.Text(
            #         game["name"],
            #         size=18,
            #         weight=ft.FontWeight.BOLD,
            #         color=ft.Colors.WHITE,
            #     ),
            #     bgcolor=ft.Colors.with_opacity(0.6, ft.Colors.BLACK),
            #     padding=ft.Padding(8, 5, 8, 5),
            #     left=0,
            #     top=0,
            # ),

            # Buttons bottom-right
            ft.Container(
                content=ft.Column(
                    [
                        install_btn,
                        clear_btn,
                    ],
                    spacing=5,
                    horizontal_alignment=ft.CrossAxisAlignment.END,
                ),
                right=10,
                bottom=10,
            ),
        ],
        width=300,
        height=400,
    )

    # Status info
    status_info = ft.Row(
        [
            file_status,
            storage_text,
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20,
    )

    return ft.Card(
        elevation=8,
        content=ft.Container(
            width=page.width - 40,
            padding=10,
            bgcolor=ft.Colors.BLACK_87,
            border_radius=15,
            content=ft.Column(
                [
                    image_stack,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    spinner,
                    status_info,
                    progress_bar,
                    status_text,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
        ),
    )


def main(page: ft.Page):
    page.title = "FNAF Launcher"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.Colors.BLACK

    launcher = FNAFLauncher()

    if not launcher.is_android:
        page.window.width = 360
        page.window.height = 800
        page.window.resizable = False

    debug_log = []

    # Create spinner
    spinner = ft.ProgressRing(
        visible=False,
        width=30,
        height=30,
        stroke_width=3,
        color=ft.Colors.RED_400,
    )

    def show_spinner():
        spinner.visible = True
        download_button.disabled = True
        page.update()

    def hide_spinner():
        spinner.visible = False
        download_button.disabled = False
        page.update()

    def apk_debug(e):
        msg = e.get("message", str(e)) if isinstance(e, dict) else str(e)

        debug_log.append(f"[DEBUG] {msg}")
        status_text.color = ft.Colors.BLUE_300

        print(f"[DEBUG] {msg}")

        # Show spinner when installation starts
        if "Opening" in msg.lower() or "package" in msg.lower():
            show_spinner()

        page.update()

    def apk_success(e):
        msg = e.get("message", str(e)) if isinstance(e, dict) else str(e)

        debug_log.append(f"[SUCCESS] {msg}")
        status_text.color = ft.Colors.GREEN

        btn_text.value = "Launch"

        print(f"[SUCCESS] {msg}")

        # Hide spinner on success
        hide_spinner()
        page.update()

    def apk_error(e):
        msg = e.get("message", str(e)) if isinstance(e, dict) else str(e)

        debug_log.append(f"[ERROR] {msg}")
        status_text.value = "\n".join(debug_log[-5:])
        status_text.color = ft.Colors.RED

        print(f"[ERROR] {msg}")

        btn_text.value = "Retry"

        # Hide spinner on error
        hide_spinner()
        page.update()

    launcher.apk_installer = FletApkInstaller(
        on_debug=apk_debug,
        on_success=apk_success,
        on_error=apk_error,
    )

    status_text = ft.Text("Ready", color=ft.Colors.GREY_400)
    progress_bar = ft.ProgressBar(width=300, visible=False, color=ft.Colors.RED)
    file_status = ft.Text("Checking...", size=12, color=ft.Colors.GREY_400)
    storage_text = ft.Text("", size=12, color=ft.Colors.GREY_500)
    btn_text = ft.Text("Install")

    def select_game(game):
        launcher.current_game = game

        launcher.links = {
            "android": game["android_url"],
            "windows": game["windows_url"]
        }

        launcher.local_file = launcher.get_local_path()

        status_text.value = f"Selected: {game['name']}"
        status_text.color = ft.Colors.GREEN

        update_file_status()
        update_button_state()
        rebuild_main_card()
        page.update()

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

            if result == "installed":
                status_text.value = "Opening APK installer..."
                status_text.color = ft.Colors.ORANGE
                btn_text.value = "Installed"
            elif result == "launched":
                status_text.value = "Game launched!"
                status_text.color = ft.Colors.GREEN
                btn_text.value = "Launched"
            else:
                status_text.value = f"Failed to install. Try opening the APK manually."
                status_text.color = ft.Colors.RED
                btn_text.value = "Retry"
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

        if launcher.is_android and launcher.is_game_installed():
            # Game is already installed - just launch it
            status_text.value = "Game found! Launching..."
            status_text.color = ft.Colors.GREEN
            page.update()
            download_button.disabled = True

            if launcher.launch_android_game():
                status_text.value = "Game launched!"
                status_text.color = ft.Colors.GREEN
                btn_text.value = "Launched"
            else:
                status_text.value = "Failed to launch game."
                status_text.color = ft.Colors.RED
                btn_text.value = "Retry"

            download_button.disabled = False
            update_file_status()
            page.update()
            return

        if launcher.check_file_exists():
            status_text.value = f"Game found. {'Installing...' if launcher.is_android else 'Launching...'}"
            status_text.color = ft.Colors.ORANGE
            page.update()
            download_button.disabled = True

            # Show spinner for installation
            if launcher.is_android:
                show_spinner()

            result = launcher.install_or_play()

            if result == "installed":
                status_text.value = "Opening APK installer..."
                status_text.color = ft.Colors.ORANGE
            elif result == "launched":
                status_text.value = "Game launched!"
                status_text.color = ft.Colors.GREEN
                btn_text.value = "Launched"
                hide_spinner()
            else:
                status_text.value = f"Failed to install. Try opening the APK manually."
                status_text.color = ft.Colors.RED
                btn_text.value = "Retry"
                hide_spinner()
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
        if launcher.is_android and launcher.is_game_installed():
            file_status.value = "Installed"
            file_status.color = ft.Colors.GREEN

        elif launcher.check_file_exists():
            file_status.value = "Downloaded"
            file_status.color = ft.Colors.ORANGE

        else:
            file_status.value = "Not downloaded"
            file_status.color = ft.Colors.RED

        size = launcher.get_storage_info()
        storage_text.value = f"{size / (1024 * 1024):.1f} MB" if size > 0 else "None"
        page.update()

    def update_button_state():
        if launcher.is_android and launcher.is_game_installed():
            btn_text.value = "Launch"
        elif launcher.check_file_exists():
            btn_text.value = "Install"
        else:
            btn_text.value = "Download"

        page.update()

    def on_clear_click(e):
        if launcher.clear_game():
            status_text.value = "Game files cleared"
            status_text.color = ft.Colors.ORANGE
            btn_text.value = "Install / Play"
            update_file_status()
            update_button_state()
            rebuild_main_card()
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

    # Create game selection cards
    game_cards = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)

    for game in GAMES:
        game_card = ft.Card(
            content=ft.Container(
                content=ft.Row([
                    ft.Text(game.get("icon", "🎮"), size=24),
                    ft.Text(game["name"], size=16, weight=ft.FontWeight.BOLD, expand=True),
                    ft.ElevatedButton(
                        "Select",
                        on_click=lambda e, g=game: select_game(g),
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.GREY_800,
                            color=ft.Colors.WHITE,
                            padding=ft.Padding(10, 5, 10, 5),
                        ),
                        width=80,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.Padding(15, 8, 15, 0),
            ),
            elevation=2,
            margin=0,
        )
        game_cards.controls.append(game_card)

    # Main card container - will be rebuilt when game changes
    main_card_container = ft.Container()

    def rebuild_main_card():
        """Rebuild the main game card with current game data."""
        if launcher.current_game:
            main_card_container.content = create_game_card(
                launcher.current_game,
                launcher,
                on_install_click,
                on_clear_click,
                download_button,
                clear_button,
                spinner,
                file_status,
                storage_text,
                progress_bar,
                status_text,
                update_file_status,
                page,
            )
        else:
            main_card_container.content = ft.Text("No game selected", color=ft.Colors.RED)
        page.update()

    # Build initial card
    rebuild_main_card()

    # Overlay container with spinner on top
    main_content = ft.Stack([
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Faz Launcher", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(height=10, color=ft.Colors.RED_900),

                # Game selection
                ft.Text("Select Game:", size=14, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=game_cards,
                    height=150,
                ),

                ft.Divider(height=10, color=ft.Colors.RED_900),

                # Current game card
                main_card_container,

                launcher.apk_installer,
                ft.Container(
                    content=ft.Text(
                        "Unofficial Launcher - Cross Platform",
                        size=10, color=ft.Colors.GREY_600, italic=True
                    ),
                    alignment=ft.Alignment(0, 0),
                    margin=ft.Margin(0, 5, 0, 0),
                )
            ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            height=page.height if hasattr(page, 'height') else 800,
        ),
    ])

    page.add(main_content)

    update_file_status()


ft.run(main, assets_dir="assets")