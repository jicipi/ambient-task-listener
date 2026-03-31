import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_timezone/flutter_timezone.dart';
import 'package:timezone/data/latest.dart' as tz;
import 'package:timezone/timezone.dart' as tz;

class NotificationService {
  static final _plugin = FlutterLocalNotificationsPlugin();
  static bool _initialized = false;

  static Future<void> init() async {
    if (kIsWeb) return;
    if (_initialized) return;

    try {
      tz.initializeTimeZones();
      try {
        final tzName = await FlutterTimezone.getLocalTimezone();
        tz.setLocalLocation(tz.getLocation(tzName));
      } catch (_) {
        tz.setLocalLocation(tz.getLocation('Europe/Paris'));
      }

      const darwinSettings = DarwinInitializationSettings(
        requestAlertPermission: false,
        requestBadgePermission: false,
        requestSoundPermission: false,
      );

      const initSettings = InitializationSettings(
        iOS: darwinSettings,
        macOS: darwinSettings,
      );
      await _plugin.initialize(initSettings);
      _initialized = true;
    } catch (e) {
      debugPrint('NotificationService init failed: $e');
    }
  }

  static Future<void> requestPermissions() async {
    if (kIsWeb) return;
    try {
      await _plugin
          .resolvePlatformSpecificImplementation<
              IOSFlutterLocalNotificationsPlugin>()
          ?.requestPermissions(alert: true, badge: true, sound: true);
      await _plugin
          .resolvePlatformSpecificImplementation<
              MacOSFlutterLocalNotificationsPlugin>()
          ?.requestPermissions(alert: true, badge: true, sound: true);
    } catch (e) {
      debugPrint('NotificationService requestPermissions failed: $e');
    }
  }

  static Future<void> scheduleAppointmentNotifications(
    List<Map<String, dynamic>> appointments,
  ) async {
    if (kIsWeb) return;
    if (!_initialized) return;

    try {
      await _plugin.cancelAll();

      final now = tz.TZDateTime.now(tz.local);
      int id = 0;

      for (final apt in appointments) {
        if (apt["done"] == true) continue;

        final dateStr = apt["scheduled_date"] as String?;
        if (dateStr == null) continue;

        final date = DateTime.tryParse(dateStr);
        if (date == null) continue;

        final scheduleTime = tz.TZDateTime(
          tz.local,
          date.year,
          date.month,
          date.day,
          9,
          0,
        );

        if (scheduleTime.isBefore(now)) continue;

        final text = (apt["text"] ?? "").toString();

        await _plugin.zonedSchedule(
          id++,
          'Rendez-vous',
          text,
          scheduleTime,
          const NotificationDetails(
            iOS: DarwinNotificationDetails(
              presentAlert: true,
              presentBadge: true,
              presentSound: true,
            ),
            macOS: DarwinNotificationDetails(
              presentAlert: true,
              presentBadge: true,
              presentSound: true,
            ),
          ),
          androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
          uiLocalNotificationDateInterpretation:
              UILocalNotificationDateInterpretation.absoluteTime,
        );
      }
    } catch (e) {
      debugPrint('NotificationService schedule failed: $e');
    }
  }
}
