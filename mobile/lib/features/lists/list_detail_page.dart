import 'dart:async';
import 'package:flutter/material.dart';
import '../../data/services/lists_api_service.dart';

class ListDetailPage extends StatefulWidget {
  final String listKey;
  final String title;

  const ListDetailPage({
    super.key,
    required this.listKey,
    required this.title,
  });

  @override
  State<ListDetailPage> createState() => _ListDetailPageState();
}

class _ListDetailPageState extends State<ListDetailPage> {
  final ListsApiService _api = ListsApiService();

  late Future<Map<String, dynamic>> _future;
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    _reload();

    _refreshTimer = Timer.periodic(
      const Duration(seconds: 5),
      (_) => _reload(),
    );
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  void _reload() {
    setState(() {
      _future = _api.fetchAllLists();
    });
  }

  Future<void> _toggleDone({
    required String itemId,
    required bool newValue,
  }) async {
    final ok = await _api.updateItemDone(
      listName: widget.listKey,
      itemId: itemId,
      done: newValue,
    );

    if (ok) {
      _reload();
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Erreur de mise à jour')),
      );
    }
  }

  Future<void> _deleteItem({
    required String itemId,
  }) async {
    final ok = await _api.deleteItem(
      listName: widget.listKey,
      itemId: itemId,
    );

    if (ok) {
      _reload();
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Erreur de suppression')),
      );
    }
  }

  Future<void> _showAddItemDialog() async {
    final controller = TextEditingController();

    final text = await showDialog<String>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text('Ajouter dans ${widget.title}'),
          content: TextField(
            controller: controller,
            autofocus: true,
            decoration: const InputDecoration(
              hintText: 'Nouvel item',
            ),
            onSubmitted: (value) {
              Navigator.of(context).pop(value.trim());
            },
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Annuler'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(controller.text.trim()),
              child: const Text('Ajouter'),
            ),
          ],
        );
      },
    );

    if (text == null || text.isEmpty) return;

    final ok = await _api.addItem(
      listName: widget.listKey,
      text: text,
    );

    if (ok) {
      _reload();
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Erreur d’ajout')),
      );
    }
  }

  Future<void> _renameItemDialog(String itemId, String currentText) async {
    final controller = TextEditingController(text: currentText);

    final newText = await showDialog<String>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text("Renommer l'item"),
          content: TextField(
            controller: controller,
            autofocus: true,
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(context);
              },
              child: const Text("Annuler"),
            ),
            FilledButton(
              onPressed: () {
                Navigator.pop(context, controller.text.trim());
              },
              child: const Text("Valider"),
            ),
          ],
        );
      },
    );

    if (newText == null || newText.isEmpty) return;

    final ok = await _api.renameItem(
      listName: widget.listKey,
      itemId: itemId,
      text: newText,
    );

    if (ok) {
      _reload();
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Erreur de renommage")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showAddItemDialog,
        child: const Icon(Icons.add),
      ),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return Center(child: Text("Erreur: ${snapshot.error}"));
          }

          final data = snapshot.data ?? {};
          final rawItems = (data[widget.listKey] as List?) ?? [];
          final items = List<Map<String, dynamic>>.from(rawItems);

          items.sort((a, b) {
            final aDone = a["done"] == true;
            final bDone = b["done"] == true;

            if (aDone != bDone) {
              return aDone ? 1 : -1;
            }

            final aText = (a["text"] ?? "").toString().toLowerCase();
            final bText = (b["text"] ?? "").toString().toLowerCase();

            return aText.compareTo(bText);
          });

          if (items.isEmpty) {
            return const Center(
              child: Text("Liste vide"),
            );
          }

          return ListView.builder(
            itemCount: items.length,
            itemBuilder: (context, index) {
              final item = items[index];
              final itemId = item["id"] ?? "";
              final text = item["text"] ?? "";
              final done = item["done"] ?? false;

              return ListTile(
                leading: Checkbox(
                  value: done,
                  onChanged: (value) {
                    if (value == null || itemId.isEmpty) return;
                    _toggleDone(
                      itemId: itemId,
                      newValue: value,
                    );
                  },
                ),
                title: Text(
                  text,
                  style: TextStyle(
                    decoration: done ? TextDecoration.lineThrough : null,
                  ),
                ),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      icon: const Icon(Icons.edit_outlined),
                      onPressed: () {
                        _renameItemDialog(itemId, text);
                      },
                    ),
                    IconButton(
                      icon: const Icon(Icons.delete_outline),
                      onPressed: itemId.isEmpty
                          ? null
                          : () {
                              _deleteItem(itemId: itemId);
                            },
                    ),
                  ],
                ),
              );
            },
          );
        },
      ),
    );
  }
}