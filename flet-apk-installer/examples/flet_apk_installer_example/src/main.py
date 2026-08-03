import flet as ft

from flet_apk_installer import FletApkInstaller


def main(page: ft.Page):
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.add(

                ft.Container(height=150, width=300, alignment = ft.Alignment.CENTER, bgcolor=ft.Colors.PURPLE_200, content=FletApkInstaller(
                    tooltip="My new FletApkInstaller Control tooltip",
                    value = "My new FletApkInstaller Flet Control",
                ),),

    )


ft.run(main)
