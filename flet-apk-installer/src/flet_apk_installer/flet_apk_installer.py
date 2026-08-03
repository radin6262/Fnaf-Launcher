from typing import Optional

import flet as ft


@ft.control("FletApkInstaller")
class FletApkInstaller(ft.LayoutControl):
    """
    Flet control for installing APK files through Android's package installer.
    """

    path: Optional[str] = None