import 'package:flutter/material.dart';
import 'app/app.dart';
import 'core/services/notification_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await NotificationService.init();
  runApp(const AmbientTaskListenerApp());
}
