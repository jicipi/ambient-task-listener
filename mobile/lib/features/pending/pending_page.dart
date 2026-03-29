import 'package:flutter/material.dart';
import '../../data/services/lists_api_service.dart';

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
    int? quantity,
    String? unit,
  ) async {
    final ok = await _api.approvePendingItem(
      itemId,
      text: text.trim(),
      listName: list,
      quantity: quantity,
      unit: unit,
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
    int? quantity,
    String? unit,
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

  final List<String> _lists = const [
    'shopping',
    'todo',
    'todo_pro',
    'appointments',
    'ideas',
  ];

  final List<String> _units = const [
    'kg',
    'g',
    'l',
    'ml',
    'cl',
    'boite',
    'paquet',
    'bouteille',
  ];

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
    _selectedUnit = widget.item["unit"]?.toString();
  }

  @override
  void dispose() {
    _textController.dispose();
    _quantityController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final itemId = (widget.item["id"] ?? "").toString();
    final intent = (widget.item["intent"] ?? "").toString();
    final transcript = (widget.item["transcript"] ?? "").toString();

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextField(
              controller: _textController,
              decoration: const InputDecoration(
                labelText: 'Texte proposé',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              value: _selectedList,
              decoration: const InputDecoration(
                labelText: 'Liste',
                border: OutlineInputBorder(),
              ),
              items: _lists.map((list) {
                return DropdownMenuItem<String>(
                  value: list,
                  child: Text(list),
                );
              }).toList(),
              onChanged: (value) {
                if (value != null) {
                  setState(() {
                    _selectedList = value;
                  });
                }
              },
            ),
            const SizedBox(height: 8),
            if (_selectedList == 'shopping')
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _quantityController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        labelText: 'Quantité',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      value: _selectedUnit,
                      decoration: const InputDecoration(
                        labelText: 'Unité',
                        border: OutlineInputBorder(),
                      ),
                      items: _units.map((unit) {
                        return DropdownMenuItem<String>(
                          value: unit,
                          child: Text(unit),
                        );
                      }).toList(),
                      onChanged: (value) {
                        setState(() {
                          _selectedUnit = value;
                        });
                      },
                    ),
                  ),
                ],
              ),
            if (_selectedList == 'shopping')
              const SizedBox(height: 8),
            Text('Intent: $intent'),
            Text('Liste actuelle: $_selectedList'),
            const SizedBox(height: 6),
            Text(
              'Transcript: $transcript',
              style: const TextStyle(color: Colors.grey),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                FilledButton.icon(
                  onPressed: itemId.isEmpty
                      ? null
                      : () => widget.onApprove(
                            itemId,
                            _textController.text,
                            _selectedList,
                            int.tryParse(_quantityController.text),
                            _selectedUnit,
                          ),
                  icon: const Icon(Icons.check),
                  label: const Text('Valider'),
                ),
                const SizedBox(width: 12),
                OutlinedButton.icon(
                  onPressed: itemId.isEmpty
                      ? null
                      : () => widget.onReject(itemId),
                  icon: const Icon(Icons.close),
                  label: const Text('Refuser'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}