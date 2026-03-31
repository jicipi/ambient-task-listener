import 'dart:async';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../../data/services/lists_api_service.dart';
import '../../core/config/api_config.dart';

class ShoppingModePage extends StatefulWidget {
  const ShoppingModePage({super.key});

  @override
  State<ShoppingModePage> createState() => _ShoppingModePageState();
}

class _ShoppingModePageState extends State<ShoppingModePage> {
  final ListsApiService _api = ListsApiService();
  late Future<List<Map<String, dynamic>>> _future;
  WebSocketChannel? _channel;

  @override
  void initState() {
    super.initState();
    _reload();
    _connectWebSocket();
  }

  @override
  void dispose() {
    _channel?.sink.close();
    super.dispose();
  }

  void _connectWebSocket() async {
    _channel?.sink.close();
    final baseUrl = await ApiConfig.getBaseUrl();
    _channel = WebSocketChannel.connect(Uri.parse(ApiConfig.toWsUrl(baseUrl)));
    _channel!.stream.listen(
      (_) => _reload(),
      onError: (_) => _reconnect(),
      onDone: () => _reconnect(),
      cancelOnError: true,
    );
  }

  void _reconnect() {
    Future.delayed(const Duration(seconds: 2), () {
      if (!mounted) return;
      _connectWebSocket();
    });
  }

  void _reload() {
    setState(() {
      _future = _api.fetchAllLists().then((data) {
        final rawItems = (data["shopping"] as List?) ?? [];
        return List<Map<String, dynamic>>.from(rawItems);
      });
    });
  }

  Future<void> _toggle(String itemId, bool currentDone) async {
    await _api.updateItemDone(
      listName: "shopping",
      itemId: itemId,
      done: !currentDone,
    );
    _reload();
  }

  Future<void> _delete(String itemId) async {
    await _api.deleteItem(listName: "shopping", itemId: itemId);
    _reload();
  }

  Future<void> _clearDone(List<Map<String, dynamic>> items) async {
    final doneItems = items.where((e) => e["done"] == true).toList();
    for (final item in doneItems) {
      await _api.deleteItem(
        listName: "shopping",
        itemId: item["id"].toString(),
      );
    }
    _reload();
  }

  Future<void> _showAddDialog() async {
    final controller = TextEditingController();
    final text = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Ajouter'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(hintText: 'Nouvel item'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, controller.text.trim()),
            child: const Text('Ajouter'),
          ),
        ],
      ),
    );
    if (text == null || text.isEmpty) return;
    await _api.addItem(listName: "shopping", text: text);
    _reload();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Courses'),
        actions: [
          FutureBuilder<List<Map<String, dynamic>>>(
            future: _future,
            builder: (context, snapshot) {
              final items = snapshot.data ?? [];
              final doneCount =
                  items.where((e) => e["done"] == true).length;
              if (doneCount == 0) return const SizedBox.shrink();
              return TextButton.icon(
                onPressed: () => _clearDone(items),
                icon: const Icon(Icons.done_all),
                label: Text('Effacer ($doneCount)'),
              );
            },
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showAddDialog,
        child: const Icon(Icons.add),
      ),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _future,
        builder: (context, snapshot) {
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }

          final items = snapshot.data!;
          if (items.isEmpty) {
            return const Center(child: Text('Liste vide'));
          }

          // Group by category
          final Map<String, List<Map<String, dynamic>>> grouped = {};
          for (final item in items) {
            final cat =
                (item["category"] ?? "autres").toString().toLowerCase();
            grouped.putIfAbsent(cat, () => []);
            grouped[cat]!.add(item);
          }

          // Sort categories alphabetically
          final categories = grouped.keys.toList()..sort();

          // Within each category: undone first, then done
          for (final cat in categories) {
            grouped[cat]!.sort((a, b) {
              final da = a["done"] == true;
              final db = b["done"] == true;
              if (da == db) return 0;
              return da ? 1 : -1;
            });
          }

          final tiles = <Widget>[];
          for (final cat in categories) {
            tiles.add(_CategoryHeader(label: cat));
            for (final item in grouped[cat]!) {
              tiles.add(_ShoppingTile(
                key: ValueKey(item["id"]),
                item: item,
                onTap: () =>
                    _toggle(item["id"].toString(), item["done"] == true),
                onDelete: () => _delete(item["id"].toString()),
              ));
            }
          }

          return ListView(children: tiles);
        },
      ),
    );
  }
}

class _CategoryHeader extends StatelessWidget {
  final String label;
  const _CategoryHeader({required this.label});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
      child: Text(
        label.toUpperCase(),
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.bold,
          color: Theme.of(context).colorScheme.primary,
          letterSpacing: 1.2,
        ),
      ),
    );
  }
}

class _ShoppingTile extends StatelessWidget {
  final Map<String, dynamic> item;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  const _ShoppingTile({
    super.key,
    required this.item,
    required this.onTap,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final done = item["done"] == true;
    final text = (item["text"] ?? "").toString();
    final quantity = item["quantity"];
    final unit = item["unit"];

    String display = text;
    if (quantity != null && unit != null) {
      display = "$quantity $unit $text";
    } else if (quantity != null) {
      display = "$quantity $text";
    }

    return Dismissible(
      key: ValueKey('dismiss-${item["id"]}'),
      direction: DismissDirection.endToStart,
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 24),
        color: Colors.red,
        child: const Icon(Icons.delete_outline, color: Colors.white, size: 28),
      ),
      onDismissed: (_) => onDelete(),
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          child: Row(
            children: [
              Icon(
                done ? Icons.check_circle_rounded : Icons.radio_button_unchecked,
                color: done
                    ? Theme.of(context).colorScheme.primary
                    : Theme.of(context).colorScheme.outline,
                size: 30,
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Text(
                  display,
                  style: TextStyle(
                    fontSize: 20,
                    decoration: done ? TextDecoration.lineThrough : null,
                    color: done ? Theme.of(context).colorScheme.outline : null,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
