import 'package:flutter/material.dart';
import '../features/home/home_page.dart';

class AmbientTaskListenerApp extends StatelessWidget {
  const AmbientTaskListenerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Ambient Task Listener',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: Colors.indigo,
        useMaterial3: true,
      ),
      home: const HomePage(),
    );
  }
}