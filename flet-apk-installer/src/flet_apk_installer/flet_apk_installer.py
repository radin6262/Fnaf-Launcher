from typing import Optional

import flet as ft


@ft.control("FletApkInstaller")
class FletApkInstaller(ft.LayoutControl):
    """
    Flet control for installing APK files through Android's package installer.
    """

    path: str = ft.control_attr("path")

    def __init__(
        self,
        path: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if path is not None:
            self.path = path