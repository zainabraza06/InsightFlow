import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import 'login_screen.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  Map<String, dynamic>? _user;

  @override
  void initState() {
    super.initState();
    AuthService.getUser().then((u) => setState(() => _user = u));
  }

  Future<void> _logout() async {
    await AuthService.logout();
    if (!mounted) return;
    Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => const LoginScreen()));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0a0a0f),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0f0f1a),
        title: const Text('Settings', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600)),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // User card
          if (_user != null) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF0f0f1a),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0x4D00d4ff)),
              ),
              child: Row(
                children: [
                  Container(
                    width: 48, height: 48,
                    decoration: BoxDecoration(color: const Color(0x1A00d4ff), borderRadius: BorderRadius.circular(24)),
                    child: Center(child: Text(
                      (_user!['name'] as String? ?? 'U')[0].toUpperCase(),
                      style: const TextStyle(color: Color(0xFF00d4ff), fontSize: 20, fontWeight: FontWeight.bold),
                    )),
                  ),
                  const SizedBox(width: 12),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(_user!['name'] as String? ?? '', style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w600)),
                      Text(_user!['email'] as String? ?? '', style: const TextStyle(color: Color(0xFF6b7280), fontSize: 12)),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
          ],

          // System info
          _section('System', [
            _infoRow('Version', 'InsightFlow 2.0'),
            _infoRow('Model', 'Gemini 2.0 Flash'),
            _infoRow('Agents', '5 (Orion, Raven, Cipher, Resolver, Executor)'),
            _infoRow('Challenge', 'Challenge 1 — Autonomous Agent'),
          ]),
          const SizedBox(height: 16),

          // Integrations
          _section('Real Integrations', [
            _infoRow('Email', 'Gmail SMTP (Step 2)'),
            _infoRow('Sheets', 'Google Sheets (Step 3)'),
            _infoRow('Webhook', 'Slack Webhook (Step 4)'),
          ]),
          const SizedBox(height: 24),

          // Logout
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: _logout,
              style: OutlinedButton.styleFrom(
                foregroundColor: const Color(0xFFEF4444),
                side: const BorderSide(color: Color(0x4DEF4444)),
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: const Text('Sign Out', style: TextStyle(fontWeight: FontWeight.w600)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _section(String title, List<Widget> children) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(title.toUpperCase(), style: const TextStyle(color: Color(0xFF6b7280), fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 1)),
      const SizedBox(height: 8),
      Container(
        decoration: BoxDecoration(color: const Color(0xFF0f0f1a), borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFF1a1a2e))),
        child: Column(children: children),
      ),
    ],
  );

  Widget _infoRow(String label, String value) => Padding(
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(width: 80, child: Text(label, style: const TextStyle(color: Color(0xFF6b7280), fontSize: 13))),
        Expanded(child: Text(value, style: const TextStyle(color: Color(0xFFD1D5DB), fontSize: 13))),
      ],
    ),
  );
}
