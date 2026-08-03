import flet as ft
import os
from pathlib import Path
import platform


def main(page: ft.Page):
    page.title = "Flet Storage Test"
    page.scroll = ft.ScrollMode.AUTO

    data = os.getenv("FLET_APP_STORAGE_DATA")
    temp = os.getenv("FLET_APP_STORAGE_TEMP")
    external = os.getenv("FLET_APP_STORAGE_EXTERNAL")

    controls = [
        ft.Text("Storage Environment Variables", size=24, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.Text(f"Platform: {platform.system()}"),
        ft.Text(""),
        ft.Text("FLET_APP_STORAGE_DATA"),
        ft.TextField(value=str(data), read_only=True),
        ft.Text(""),
        ft.Text("FLET_APP_STORAGE_TEMP"),
        ft.TextField(value=str(temp), read_only=True),
        ft.Text(""),
        ft.Text("FLET_APP_STORAGE_EXTERNAL"),
        ft.TextField(value=str(external), read_only=True),
    ]

    if external:
        produced = Path(external) / "Download" / "FNAF_Launcher"

        controls.extend([
            ft.Divider(),
            ft.Text("Your code produces:", weight=ft.FontWeight.BOLD),
            ft.TextField(
                value=str(produced),
                read_only=True,
                multiline=True,
            ),
            ft.Text(f"Exists: {produced.exists()}"),
        ])

    if data:
        produced = Path(data) / "FNAF_Launcher"

        controls.extend([
            ft.Divider(),
            ft.Text("Private app storage:", weight=ft.FontWeight.BOLD),
            ft.TextField(
                value=str(produced),
                read_only=True,
                multiline=True,
            ),
            ft.Text(f"Exists: {produced.exists()}"),
        ])

    page.add(ft.Column(controls))


ft.app(main)