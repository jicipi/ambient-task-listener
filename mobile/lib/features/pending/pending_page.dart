import 'package:flutter/material.dart';
import '../../data/services/lists_api_service.dart';
import '../lists/list_detail_page.dart';

class PendingPage extends StatefulWidget {
  const PendingPage({super.key});

  @override
  State<PendingPage> createState() => _PendingPageState();
}

class _PendingPageState extends State<PendingPage> {
  final ListsApiService _api = ListsApiService();
  late Future<List<Map<String, dynamic>>> _future;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  void _reload() {
    setState(() {
      _future = _api.fetchPendingItems();
    });
  }

  Future<void> _approve(
    String itemId,
    String text,
    String list,
    double? quantity,
    String? unit,
    String? scheduledDate,
  ) async {
    final ok = await _api.approvePendingItem(
      itemId,
      text: text.trim(),
      listName: list,
      quantity: quantity,
      unit: unit,
      scheduledDate: scheduledDate,
    );

    if (ok) {
      _reload();
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Erreur de validation')),
      );
    }
  }

  Future<void> _reject(String itemId) async {
    final ok = await _api.rejectPendingItem(itemId);

    if (ok) {
      _reload();
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Erreur de suppression')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('À confirmer'),
      ),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return Center(child: Text('Erreur: ${snapshot.error}'));
          }

          final items = snapshot.data ?? [];

          if (items.isEmpty) {
            return const Center(
              child: Text('Aucun élément en attente'),
            );
          }

          return ListView.builder(
            itemCount: items.length,
            itemBuilder: (context, index) {
              final item = items[index];

              return _PendingCard(
                item: item,
                onApprove: _approve,
                onReject: _reject,
              );
            },
          );
        },
      ),
    );
  }
}

class _PendingCard extends StatefulWidget {
  final Map<String, dynamic> item;
  final Future<void> Function(
    String itemId,
    String text,
    String list,
    double? quantity,
    String? unit,
    String? scheduledDate,
  ) onApprove;
  final Future<void> Function(String itemId) onReject;

  const _PendingCard({
    required this.item,
    required this.onApprove,
    required this.onReject,
  });

  @override
  State<_PendingCard> createState() => _PendingCardState();
}

class _PendingCardState extends State<_PendingCard> {
  late final TextEditingController _textController;
  late final TextEditingController _quantityController;
  late String _selectedList;
  String? _selectedUnit;
  String? _selectedCategory;
  DateTime? _scheduledDate;

  static const _lists = [
    'shopping',
    'todo',
    'todo_pro',
    'appointments',
    'ideas',
  ];

  static const _units = ['', 'kg', 'g', 'l', 'cl', 'ml', 'bouteille', 'boite', 'paquet'];

  @override
  void initState() {
    super.initState();
    _textController = TextEditingController(
      text: (widget.item["item"] ?? "").toString(),
    );
    _quantityController = TextEditingController(
      text: widget.item["quantity"]?.toString() ?? '',
    );
    _selectedList = (widget.item["list"] ?? "ideas").toString();
    final rawUnit = widget.item["unit"]?.toString() ?? '';
    _selectedUnit = _units.contains(rawUnit) ? rawUnit : '';
    _selectedCategory = widget.item["category"]?.toString();

    final rawDate = widget.item["scheduled_date"] as String?;
    if (rawDate != null) {
      try {
        _scheduledDate = DateTime.parse(rawDate);
      } catch (_) {}
    }
  }

  @override
  void dispose() {
    _textController.dispose();
    _quantityController.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _scheduledDate ?? now,
      firstDate: now.subtract(const Duration(days: 365)),
      lastDate: now.add(const Duration(days: 365 * 5)),
    );
    if (picked != null) {
      setState(() => _scheduledDate = picked);
    }
  }

  String _formatDate(DateTime dt) {
    final d = dt.day.toString().padLeft(2, '0');
    final m = dt.month.toString().padLeft(2, '0');
    return '$d/$m/${dt.year}';
  }

  String? get _isoDate =>
      _scheduledDate != null
          ? '${_scheduledDate!.year}-${_scheduledDate!.month.toString().padLeft(2, '0')}-${_scheduledDate!.day.toString().padLeft(2, '0')}'
          : null;

  @override
  Widget build(BuildContext context) {
    final itemId = (widget.item["id"] ?? "").toString();
    final transcript = (widget.item["transcript"] ?? "").toString();
    final intent = (widget.item["intent"] ?? "").toString();

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Transcript (context for the user)
            if (transcript.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.mic, size: 14, color: Colors.grey),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        transcript,
                        style: const TextStyle(fontSize: 12, color: Colors.grey),
                      ),
                    ),
                    if (intent.isNotEmpty)
                      Container(
                        margin: const EdgeInsets.only(left: 6),
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: Colors.blue.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          intent,
                          style: const TextStyle(fontSize: 10, color: Colors.blue),
                        ),
                      ),
                  ],
                ),
              ),

            // Texte proposé
            TextField(
              controller: _textController,
              decoration: const InputDecoration(
                labelText: 'Texte',
                border: OutlineInputBorder(),
                isDense: true,
              ),
            ),
            const SizedBox(height: 8),

            // Liste
            DropdownButtonFormField<String>(
              value: _selectedList,
              decoration: const InputDecoration(
                labelText: 'Liste',
                border: OutlineInputBorder(),
                isDense: true,
              ),
              items: _lists.map((l) => DropdownMenuItem(value: l, child: Text(l))).toList(),
              onChanged: (v) {
                if (v != null) setState(() => _selectedList = v);
              },
            ),
            const SizedBox(height: 8),

            // Shopping: quantité + unité + catégorie
            if (_selectedList == 'shopping') ...[
              Row(
                children: [
                  Expanded(
                    flex: 2,
                    child: TextField(
                      controller: _quantityController,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      decoration: const InputDecoration(
                        labelText: 'Qté',
                        border: OutlineInputBorder(),
                        isDense: true,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    flex: 3,
                    child: DropdownButtonFormField<String>(
                      value: _selectedUnit ?? '',
                      decoration: const InputDecoration(
                        labelText: 'Unité',
                        border: OutlineInputBorder(),
                        isDense: true,
                      ),
                      items: _units.map((u) => DropdownMenuItem(
                        value: u,
                        child: Text(u.isEmpty ? '—' : u),
                      )).toList(),
                      onChanged: (v) => setState(() => _selectedUnit = v),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                value: ListDetailPage.shoppingCategories.contains(_selectedCategory)
                    ? _selectedCategory
                    : 'autres',
                decoration: const InputDecoration(
                  labelText: 'Catégorie',
                  border: OutlineInputBorder(),
                  isDense: true,
                ),
                items: ListDetailPage.shoppingCategories
                    .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                    .toList(),
                onChanged: (v) { if (v != null) setState(() => _selectedCategory = v); },
              ),
              const SizedBox(height: 8),
            ],

            // Appointments: date
            if (_selectedList == 'appointments') ...[
              InkWell(
                onTap: _pickDate,
                child: InputDecorator(
                  decoration: const InputDecoration(
                    labelText: 'Date',
                    border: OutlineInputBorder(),
                    isDense: true,
                    suffixIcon: Icon(Icons.calendar_today, size: 18),
                  ),
                  child: Text(
                    _scheduledDate != null ? _formatDate(_scheduledDate!) : 'Sans date',
                    style: TextStyle(
                      color: _scheduledDate != null ? null : Colors.grey,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 8),
            ],

            // Actions
            Row(
              children: [
                FilledButton.icon(
                  onPressed: itemId.isEmpty
                      ? null
                      : () {
                          final qty = double.tryParse(
                            _quantityController.text.trim().replaceAll(',', '.'),
                          );
                          final unit = (_selectedUnit?.isEmpty ?? true) ? null : _selectedUnit;
                          widget.onApprove(
                            itemId,
                            _textController.text,
                            _selectedList,
                            qty,
                            unit,
                            _isoDate,
                          );
                        },
                  icon: const Icon(Icons.check),
                  label: const Text('Valider'),
                ),
                const SizedBox(width: 12),
                OutlinedButton.icon(
                  onPressed: itemId.isEmpty ? null : () => widget.onReject(itemId),
                  icon: const Icon(Icons.close),
                  label: const Text('Refuser'),
                  style: OutlinedButton.styleFrom(foregroundColor: Colors.red),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
