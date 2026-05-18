import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'debate_screen.dart';

const _seeds = {
  'sales': {
    'text': 'Regional Q3 sales report: Lahore division shows 25% decline in orders. Field reps report customer churn to competitor offering 15% lower pricing on electronics.',
    'csv': 'month,orders,revenue_pkr,returns\nJuly,1200,2400000,45\nAugust,980,1960000,67\nSeptember,900,1800000,89',
    'url': '',
    'topic': 'sales',
    'domain': 'Business',
  },
  'fuel': {
    'text': 'Breaking: Government announces 18% increase in petroleum prices effective immediately. Diesel up PKR 22/litre. Transport associations warn of 30% logistics cost surge.',
    'csv': 'date,diesel_pkr,transport_index,delivery_complaints\n2026-05-01,278,100,12\n2026-05-08,290,108,28\n2026-05-15,312,119,54',
    'url': '',
    'topic': 'fuel',
    'domain': 'Logistics',
  },
  'supply': {
    'text': 'Port congestion at Karachi delays shipments average 12 days. Three major electronics suppliers halting production due to power rationing. Warehouse manager email says stock is fine for 6 weeks.',
    'csv': 'sku,stock_units,days_remaining,supplier_status,last_updated\nSKU-001,450,12,delayed,2026-05-10\nSKU-002,80,2,critical,2026-05-14\nSKU-003,1200,31,normal,2026-04-28',
    'url': '',
    'topic': 'supply',
    'domain': 'Logistics',
  },
};

class InputScreen extends StatefulWidget {
  const InputScreen({super.key});

  @override
  State<InputScreen> createState() => _InputScreenState();
}

class _InputScreenState extends State<InputScreen> {
  final _textCtrl = TextEditingController();
  final _urlCtrl = TextEditingController();
  final _csvCtrl = TextEditingController();
  String _domain = 'Business';
  String _topic = '';
  bool _includeFeed = true;
  bool _loading = false;

  void _loadSeed(String key) {
    final s = _seeds[key]!;
    setState(() {
      _textCtrl.text = s['text']!;
      _urlCtrl.text = s['url']!;
      _csvCtrl.text = s['csv']!;
      _topic = s['topic']!;
      _domain = s['domain']!;
    });
  }

  Future<void> _ingest() async {
    setState(() => _loading = true);
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => const AlertDialog(
        backgroundColor: Color(0xFF111118),
        content: Row(children: [
          CircularProgressIndicator(color: Color(0xFF4f8ef7)),
          SizedBox(width: 16),
          Text('Ingesting sources...', style: TextStyle(color: Colors.white70)),
        ]),
      ),
    );
    try {
      final data = await ApiService().ingest(
        text: _textCtrl.text,
        url: _urlCtrl.text,
        csvData: _csvCtrl.text,
        domain: _domain,
        topic: _topic,
        includeFeed: _includeFeed,
      );
      if (mounted) {
        Navigator.of(context).pop();
        Navigator.push(context, MaterialPageRoute(
          builder: (_) => DebateScreen(ingestData: data, domain: _domain),
        ));
      }
    } catch (e) {
      if (mounted) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    }
    if (mounted) setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF0d0d14),
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('⬡ InsightFlow', style: TextStyle(color: Color(0xFF4f8ef7), fontWeight: FontWeight.bold)),
            Text('Autonomous Intelligence', style: TextStyle(fontSize: 11, color: Colors.white38)),
          ],
        ),
      ),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        _label('Domain'),
        DropdownButtonFormField<String>(
          value: _domain,
          dropdownColor: const Color(0xFF111118),
          decoration: _inputDecoration(),
          items: ['Business', 'Policy', 'Logistics', 'Finance', 'News']
              .map((d) => DropdownMenuItem(value: d, child: Text(d)))
              .toList(),
          onChanged: (v) => setState(() => _domain = v!),
        ),
        const SizedBox(height: 12),
        Wrap(spacing: 8, children: [
          _seedChip('📉 Sales Drop', () => _loadSeed('sales')),
          _seedChip('⛽ Fuel Hike', () => _loadSeed('fuel')),
          _seedChip('🏭 Supply Chain', () => _loadSeed('supply')),
        ]),
        const SizedBox(height: 12),
        _label('Text / Article / Report'),
        TextFormField(
          controller: _textCtrl,
          maxLines: 4,
          style: const TextStyle(fontSize: 13),
          decoration: _inputDecoration(hint: 'Paste text, news article, or report...'),
        ),
        const SizedBox(height: 12),
        _label('URL (optional)'),
        TextFormField(
          controller: _urlCtrl,
          decoration: _inputDecoration(hint: 'Article URL to fetch (optional)'),
          style: const TextStyle(fontSize: 13),
        ),
        const SizedBox(height: 12),
        _label('CSV Data (optional)'),
        TextFormField(
          controller: _csvCtrl,
          maxLines: 3,
          style: const TextStyle(fontSize: 13),
          decoration: _inputDecoration(hint: 'Paste CSV — include date/month column for temporal analysis'),
        ),
        const SizedBox(height: 8),
        SwitchListTile(
          value: _includeFeed,
          onChanged: (v) => setState(() => _includeFeed = v),
          title: const Text('Include live signal feed', style: TextStyle(fontSize: 13, color: Colors.white70)),
          activeColor: const Color(0xFF4f8ef7),
          contentPadding: EdgeInsets.zero,
        ),
        const SizedBox(height: 16),
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: _loading ? null : _ingest,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF4f8ef7),
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            child: const Text('Ingest All Sources', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ),
      ]),
    );
  }

  Widget _seedChip(String label, VoidCallback onTap) => ActionChip(
        label: Text(label, style: const TextStyle(fontSize: 12)),
        backgroundColor: const Color(0xFF0d0d14),
        side: const BorderSide(color: Color(0xFF1e1e2e)),
        onPressed: onTap,
      );

  Widget _label(String text) => Padding(
        padding: const EdgeInsets.only(bottom: 4),
        child: Text(text, style: const TextStyle(fontSize: 11, color: Colors.white38)),
      );

  InputDecoration _inputDecoration({String hint = ''}) => InputDecoration(
        hintText: hint,
        hintStyle: const TextStyle(color: Colors.white24, fontSize: 12),
        filled: true,
        fillColor: const Color(0xFF0d0d14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: Color(0xFF1e1e2e)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: Color(0xFF1e1e2e)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: Color(0xFF4f8ef7)),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      );
}
