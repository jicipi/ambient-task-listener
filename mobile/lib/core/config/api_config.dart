import 'package:shared_preferences/shared_preferences.dart';

class ApiConfig {
  static const String _defaultUrl = 'http://172.20.10.8:8000';
  static const String _prefsKey = 'backend_url';

  static Future<String> getBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_prefsKey) ?? _defaultUrl;
  }

  static Future<void> setBaseUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefsKey, url.trimRight().replaceAll(RegExp(r'/+$'), ''));
  }

  static String toWsUrl(String baseUrl) {
    final wsBase = baseUrl
        .replaceFirst('https://', 'wss://')
        .replaceFirst('http://', 'ws://');
    return '$wsBase/ws';
  }
}
