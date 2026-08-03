import 'package:flet/flet.dart';
import 'package:flutter/widgets.dart';

import 'flet_apk_installer.dart';

class Extension extends FletExtension {
  @override
  Widget? createWidget(Key? key, Control control) {
    switch (control.type) {
      case "FletApkInstaller":
        return FletApkInstallerControl(
          key: key,
          control: control,
        );
      default:
        return null;
    }
  }
}