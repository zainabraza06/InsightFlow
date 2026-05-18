import 'package:flutter/material.dart';
import 'screens/login_screen.dart';
import 'screens/input_screen.dart';
import 'screens/history_screen.dart';
import 'screens/settings_screen.dart';
import 'services/auth_service.dart';

void main() => runApp(const InsightFlowApp());

class InsightFlowApp extends StatelessWidget {
  const InsightFlowApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'InsightFlow',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          brightness: Brightness.dark,
          scaffoldBackgroundColor: const Color(0xFF0a0a0f),
          colorScheme: const ColorScheme.dark(primary: Color(0xFF00d4ff)),
          fontFamily: 'Inter',
          useMaterial3: true,
        ),
        home: const _AuthGate(),
      );
}

class _AuthGate extends StatefulWidget {
  const _AuthGate();

  @override
  State<_AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<_AuthGate> {
  bool _checking = true;
  bool _authed = false;

  @override
  void initState() {
    super.initState();
    AuthService.isAuthenticated().then((v) {
      if (mounted) setState(() { _authed = v; _checking = false; });
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_checking) {
      return const Scaffold(
        backgroundColor: Color(0xFF0a0a0f),
        body: Center(child: CircularProgressIndicator(color: Color(0xFF00d4ff))),
      );
    }
    return _authed ? const _MainShell() : const LoginScreen();
  }
}

class _MainShell extends StatefulWidget {
  const _MainShell();

  @override
  State<_MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<_MainShell> {
  int _tab = 0;

  final _screens = const [
    InputScreen(),
    HistoryScreen(),
    SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _tab, children: _screens),
      bottomNavigationBar: NavigationBar(
        backgroundColor: const Color(0xFF0f0f1a),
        indicatorColor: const Color(0x1A00d4ff),
        selectedIndex: _tab,
        onDestinationSelected: (i) => setState(() => _tab = i),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.bolt_outlined, color: Color(0xFF6b7280)),
            selectedIcon: Icon(Icons.bolt, color: Color(0xFF00d4ff)),
            label: 'Analyze',
          ),
          NavigationDestination(
            icon: Icon(Icons.history_outlined, color: Color(0xFF6b7280)),
            selectedIcon: Icon(Icons.history, color: Color(0xFF00d4ff)),
            label: 'History',
          ),
          NavigationDestination(
            icon: Icon(Icons.settings_outlined, color: Color(0xFF6b7280)),
            selectedIcon: Icon(Icons.settings, color: Color(0xFF00d4ff)),
            label: 'Settings',
          ),
        ],
      ),
    );
  }
}
