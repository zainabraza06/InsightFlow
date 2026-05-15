import 'package:flutter/material.dart';
import 'screens/input_screen.dart';

void main() => runApp(const NexusApp());

class NexusApp extends StatelessWidget {
  const NexusApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'NEXUS',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          brightness: Brightness.dark,
          scaffoldBackgroundColor: const Color(0xFF0a0a0f),
          colorScheme: const ColorScheme.dark(primary: Color(0xFF4f8ef7)),
          fontFamily: 'Inter',
          useMaterial3: true,
        ),
        home: const InputScreen(),
      );
}
