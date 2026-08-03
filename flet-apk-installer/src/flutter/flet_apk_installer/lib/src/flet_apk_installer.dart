import 'package:flet/flet.dart';
import 'package:flutter/material.dart';
import 'package:apk_sideload/install_apk.dart';

class FletApkInstallerControl extends StatefulWidget {
  final Control control;

  const FletApkInstallerControl({
    super.key,
    required this.control,
  });

  @override
  State<FletApkInstallerControl> createState() =>
      _FletApkInstallerControlState();
}

class _FletApkInstallerControlState
    extends State<FletApkInstallerControl> {

  String status = "Ready";

  @override
  void initState() {
    super.initState();
    installApk();
  }

  Future<void> installApk() async {
    String path = widget.control.getString("path", "") ?? "";

    if (path.isEmpty) {
      setState(() {
        status = "No APK path provided";
      });
      return;
    }

    try {
      setState(() {
        status = "Opening installer...";
      });

      final installer = InstallApk();

      await installer.installApk(path);

      setState(() {
        status = "Installer opened";
      });

    } catch (e) {
      setState(() {
        status = "Error: $e";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return LayoutControl(
      control: widget.control,
      child: Text(status),
    );
  }
}