import 'dart:async';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../../data/services/lists_api_service.dart';
import '../../core/config/api_config.dart';
import 'shopping_mode_page.dart';

// ---------------------------------------------------------------------------
// _AnimatedItem — FadeTransition + légère translation verticale à l'apparition
// ---------------------------------------------------------------------------

class _AnimatedItem extends StatefulWidget {
  final int index;
  final Widget child;

  const _AnimatedItem({
    required Key key,
    required this.index,
    required this.child,
  }) : super(key: key);

  @override
  State<_AnimatedItem> createState() => _AnimatedItemState();
}

class _AnimatedItemState extends State<_AnimatedItem>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _opacity;
  late final Animation<Offset> _slide;

  @override
  void initState() {
    super.initState();

    final delay = Duration(milliseconds: (widget.index * 30).clamp(0, 300));

    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 200),
    );

    _opacity = CurvedAnimation(parent: _ctrl, curve: Curves.easeOut);
    _slide = Tween<Offset>(
      begin: const Offset(0, 0.08), // ~10 px logiques vers le bas
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeOut));

    Future.delayed(delay, () {
      if (mounted) _ctrl.forward();
    });
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _opacity,
      child: SlideTransition(position: _slide, child: widget.child),
    );
  }
}

// ---------------------------------------------------------------------------
// ListDetailPage
// ---------------------------------------------------------------------------

class ListDetailPage extends StatefulWidget {
  final String listKey;
  final String title;

  const ListDetailPage({
    super.key,
    required this.listKey,
    required this.title,
  });

  static const shoppingCategories = [
    'fruits',
    'légumes',
    'viande',
    'poisson',
    'produits laitiers',
    'épicerie',
    'ménager',
    'autres',
  ];

  @override
  State<ListDetailPage> createState() => _ListDetailPageState();
}

class _ListDetailPageState extends State<ListDetailPage> {
  final ListsApiService _api = ListsApiService();

  late Future<Map<String, dynamic>> _future;
  WebSocketChannel? _channel;

  /// Ordre des catégories chargé depuis le backend (shopping uniquement).
  List<String> _categoryOrder = [];

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
    _channel = WebSocketChannel.connect(
      Uri.parse(ApiConfig.toWsUrl(baseUrl)),
    );

    _channel!.stream.listen(
      (message) {
        debugPrint('ListDetail WS message: $message');
        _reload();
      },
      onError: (error) {
        debugPrint('ListDetail WS error: $error');
        _reconnect();
      },
      onDone: () {
        debugPrint('ListDetail WS closed');
        _reconnect();
      },
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
      if (widget.listKey == 'shopping') {
        _future = _loadShoppingData();
      } else {
        _future = _api.fetchAllLists();
      }
    });
  }

  /// Pour shopping : charge les items et l'ordre des catégories en parallèle.
  Future<Map<String, dynamic>> _loadShoppingData() async {
    final results = await Future.wait([
      _api.fetchAllLists(),
      _api.fetchCategoryOrder(widget.listKey),
    ]);

    final allLists = results[0] as Map<String, dynamic>;
    final order = results[1] as List<String>;

    if (mounted) {
      setState(() => _categoryOrder = order);
    }

    return allLists;
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
    }
  }

  Future<void> _deleteItem({required String itemId}) async {
    final ok = await _api.deleteItem(
      listName: widget.listKey,
      itemId: itemId,
    );

    if (ok) {
      _reload();
    }
  }

  // -------------------------------------------------------------------------
  // Dialog : réordonner les catégories
  // -------------------------------------------------------------------------

  Future<void> _showCategoryOrderDialog(List<String> currentCategories) async {
    final working = List<String>.from(currentCategories);

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setLocal) {
            return AlertDialog(
              title: const Text('Ordre des catégories'),
              content: SizedBox(
                width: double.maxFinite,
                height: 350,
                child: ReorderableListView(
                  onReorder: (oldIdx, newIdx) {
                    setLocal(() {
                      if (newIdx > oldIdx) newIdx -= 1;
                      final item = working.removeAt(oldIdx);
                      working.insert(newIdx, item);
                    });
                  },
                  children: working
                      .map(
                        (cat) => ListTile(
                          key: ValueKey(cat),
                          title: Text(cat),
                          trailing: const Icon(Icons.drag_handle),
                        ),
                      )
                      .toList(),
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(ctx, false),
                  child: const Text('Annuler'),
                ),
                FilledButton(
                  onPressed: () => Navigator.pop(ctx, true),
                  child: const Text('Valider'),
                ),
              ],
            );
          },
        );
      },
    );

    if (confirmed != true) return;

    await _api.updateCategoryOrder(widget.listKey, working);
    setState(() => _categoryOrder = working);
  }

  // -------------------------------------------------------------------------
  // Dialogs add / edit
  // -------------------------------------------------------------------------

  Future<void> _showAddItemDialog() async {
    final controller = TextEditingController();
    final quantityController = TextEditingController();
    DateTime? selectedDate;
    String? selectedUnit;

    final isAppointments = widget.listKey == "appointments";
    final isShopping = widget.listKey == "shopping";

    const units = ['', 'kg', 'g', 'l', 'cl', 'ml', 'bouteille', 'boite', 'paquet'];

    final result = await showDialog<bool>(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setLocalState) {
            return AlertDialog(
              title: Text('Ajouter dans ${widget.title}'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: controller,
                    autofocus: true,
                    decoration: const InputDecoration(hintText: 'Nom'),
                  ),
                  if (isShopping) ...[
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          flex: 2,
                          child: TextField(
                            controller: quantityController,
                            keyboardType: const TextInputType.numberWithOptions(decimal: true),
                            decoration: const InputDecoration(labelText: 'Qté'),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          flex: 3,
                          child: DropdownButtonFormField<String>(
                            value: selectedUnit ?? '',
                            decoration: const InputDecoration(labelText: 'Unité'),
                            items: units.map((u) => DropdownMenuItem(
                              value: u,
                              child: Text(u.isEmpty ? '—' : u),
                            )).toList(),
                            onChanged: (v) => setLocalState(() => selectedUnit = v == '' ? null : v),
                          ),
                        ),
                      ],
                    ),
                  ],
                  if (isAppointments) ...[
                    const SizedBox(height: 12),
                    InkWell(
                      onTap: () async {
                        final now = DateTime.now();
                        final picked = await showDatePicker(
                          context: context,
                          initialDate: selectedDate ?? now,
                          firstDate: now.subtract(const Duration(days: 365)),
                          lastDate: now.add(const Duration(days: 365 * 5)),
                        );
                        if (picked != null) {
                          setLocalState(() => selectedDate = picked);
                        }
                      },
                      child: InputDecorator(
                        decoration: const InputDecoration(
                          labelText: 'Date',
                          border: OutlineInputBorder(),
                          isDense: true,
                          suffixIcon: Icon(Icons.calendar_today, size: 18),
                        ),
                        child: Text(
                          selectedDate != null
                              ? '${selectedDate!.day.toString().padLeft(2, '0')}/${selectedDate!.month.toString().padLeft(2, '0')}/${selectedDate!.year}'
                              : 'Sans date',
                          style: TextStyle(
                            color: selectedDate != null ? null : Colors.grey,
                          ),
                        ),
                      ),
                    ),
                  ],
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(false),
                  child: const Text('Annuler'),
                ),
                FilledButton(
                  onPressed: () => Navigator.of(context).pop(true),
                  child: const Text('Ajouter'),
                ),
              ],
            );
          },
        );
      },
    );

    if (result != true || controller.text.trim().isEmpty) return;

    String? isoDate;
    if (isAppointments && selectedDate != null) {
      isoDate =
          '${selectedDate!.year}-${selectedDate!.month.toString().padLeft(2, '0')}-${selectedDate!.day.toString().padLeft(2, '0')}';
    }

    String text = controller.text.trim();
    if (isShopping) {
      final qtyStr = quantityController.text.trim();
      if (qtyStr.isNotEmpty) {
        text = selectedUnit != null && selectedUnit!.isNotEmpty
            ? '$qtyStr $selectedUnit $text'
            : '$qtyStr $text';
      }
    }

    final ok = await _api.addItem(
      listName: widget.listKey,
      text: text,
      scheduledDate: isoDate,
    );

    if (ok) _reload();
  }

  Future<void> _editAppointmentDialog({
    required String itemId,
    required String currentText,
    String? currentScheduledDate,
  }) async {
    final textController = TextEditingController(text: currentText);
    DateTime? selectedDate;
    if (currentScheduledDate != null) {
      try {
        selectedDate = DateTime.parse(currentScheduledDate);
      } catch (_) {}
    }

    final result = await showDialog<bool>(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setLocalState) {
            return AlertDialog(
              title: const Text('Modifier le rendez-vous'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: textController,
                    autofocus: true,
                    decoration: const InputDecoration(labelText: 'Titre'),
                  ),
                  const SizedBox(height: 12),
                  InkWell(
                    onTap: () async {
                      final now = DateTime.now();
                      final picked = await showDatePicker(
                        context: context,
                        initialDate: selectedDate ?? now,
                        firstDate: now.subtract(const Duration(days: 365)),
                        lastDate: now.add(const Duration(days: 365 * 5)),
                      );
                      if (picked != null) {
                        setLocalState(() => selectedDate = picked);
                      }
                    },
                    child: InputDecorator(
                      decoration: const InputDecoration(
                        labelText: 'Date',
                        border: OutlineInputBorder(),
                        isDense: true,
                        suffixIcon: Icon(Icons.calendar_today, size: 18),
                      ),
                      child: Text(
                        selectedDate != null
                            ? '${selectedDate!.day.toString().padLeft(2, '0')}/${selectedDate!.month.toString().padLeft(2, '0')}/${selectedDate!.year}'
                            : 'Sans date',
                        style: TextStyle(
                          color: selectedDate != null ? null : Colors.grey,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context, false),
                  child: const Text('Annuler'),
                ),
                FilledButton(
                  onPressed: () => Navigator.pop(context, true),
                  child: const Text('Valider'),
                ),
              ],
            );
          },
        );
      },
    );

    if (result != true) return;

    final newText = textController.text.trim();
    if (newText.isNotEmpty) {
      await _api.renameItem(
        listName: widget.listKey,
        itemId: itemId,
        text: newText,
      );
    }

    final isoDate = selectedDate != null
        ? '${selectedDate!.year}-${selectedDate!.month.toString().padLeft(2, '0')}-${selectedDate!.day.toString().padLeft(2, '0')}'
        : null;

    if (isoDate != currentScheduledDate) {
      await _api.updateItemScheduledDate(
        listName: widget.listKey,
        itemId: itemId,
        scheduledDate: isoDate,
      );
    }

    _reload();
  }

  Future<void> _editItemDialog({
    required String itemId,
    required String currentText,
    required String currentCategory,
    dynamic currentQuantity,
    String? currentUnit,
  }) async {
    final textController = TextEditingController(text: currentText);
    final quantityController = TextEditingController(
      text: currentQuantity != null ? currentQuantity.toString() : '',
    );
    String? selectedUnit = currentUnit;
    String selectedCategory = currentCategory;

    const units = ['', 'kg', 'g', 'l', 'cl', 'ml', 'bouteille', 'boite', 'paquet'];

    final result = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text("Modifier l'item"),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: textController,
                autofocus: true,
                decoration: const InputDecoration(labelText: "Nom"),
              ),
              if (widget.listKey == "shopping") ...[
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      flex: 2,
                      child: TextField(
                        controller: quantityController,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        decoration: const InputDecoration(labelText: "Qté"),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      flex: 3,
                      child: StatefulBuilder(
                        builder: (context, setLocalState) {
                          return DropdownButtonFormField<String>(
                            value: selectedUnit ?? '',
                            decoration: const InputDecoration(labelText: "Unité"),
                            items: units.map((u) => DropdownMenuItem(
                              value: u,
                              child: Text(u.isEmpty ? '—' : u),
                            )).toList(),
                            onChanged: (v) => setLocalState(() => selectedUnit = v == '' ? null : v),
                          );
                        },
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                StatefulBuilder(
                  builder: (context, setLocalState) {
                    return DropdownButtonFormField<String>(
                      value: selectedCategory,
                      decoration: const InputDecoration(labelText: "Catégorie"),
                      items: ListDetailPage.shoppingCategories.map((c) =>
                        DropdownMenuItem(value: c, child: Text(c)),
                      ).toList(),
                      onChanged: (v) { if (v != null) setLocalState(() => selectedCategory = v); },
                    );
                  },
                ),
              ],
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text("Annuler"),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text("Valider"),
            ),
          ],
        );
      },
    );

    if (result != true) return;

    final newText = textController.text.trim();
    if (newText.isEmpty) { _reload(); return; }

    String textToSend = newText;
    if (widget.listKey == "shopping") {
      final qtyStr = quantityController.text.trim();
      if (qtyStr.isNotEmpty) {
        textToSend = selectedUnit != null && selectedUnit!.isNotEmpty
            ? '$qtyStr $selectedUnit $newText'
            : '$qtyStr $newText';
      }
    }

    await _api.renameItem(
      listName: widget.listKey,
      itemId: itemId,
      text: textToSend,
    );

    if (widget.listKey == "shopping" && selectedCategory != currentCategory) {
      await _api.updateItemCategory(
        listName: widget.listKey,
        itemId: itemId,
        category: selectedCategory,
      );
    }

    _reload();
  }

  // -------------------------------------------------------------------------
  // Build
  // -------------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title),
        actions: [
          if (widget.listKey == "shopping") ...[
            IconButton(
              icon: const Icon(Icons.tune),
              tooltip: 'Ordre des catégories',
              onPressed: () => _showCategoryOrderDialog(
                _categoryOrder.isNotEmpty
                    ? _categoryOrder
                    : ListDetailPage.shoppingCategories,
              ),
            ),
            IconButton(
              icon: const Icon(Icons.shopping_cart_checkout),
              tooltip: 'Mode courses',
              onPressed: () => Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => const ShoppingModePage(),
                ),
              ),
            ),
          ],
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showAddItemDialog,
        child: const Icon(Icons.add),
      ),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snapshot) {
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }

          final data = snapshot.data!;
          final rawItems = (data[widget.listKey] as List?) ?? [];
          final items = List<Map<String, dynamic>>.from(rawItems);

          if (items.isEmpty) {
            return const Center(child: Text("Liste vide"));
          }

          // ------------------------------------------------------------------
          // Appointments: liste plate triée par date
          // ------------------------------------------------------------------
          if (widget.listKey == "appointments") {
            final sorted = List<Map<String, dynamic>>.from(items);
            sorted.sort((a, b) {
              final da = a["scheduled_date"] as String?;
              final db = b["scheduled_date"] as String?;
              if (da == null && db == null) return 0;
              if (da == null) return 1;
              if (db == null) return -1;
              return da.compareTo(db);
            });

            return ListView(
              children: sorted.asMap().entries.map((entry) {
                final idx = entry.key;
                final item = entry.value;
                final itemId = item["id"];
                final text = item["text"] ?? "";
                final done = item["done"] == true;
                final scheduledDate = item["scheduled_date"] as String?;

                String? dateDisplay;
                if (scheduledDate != null) {
                  try {
                    final dt = DateTime.parse(scheduledDate);
                    final day = dt.day.toString().padLeft(2, '0');
                    final month = dt.month.toString().padLeft(2, '0');
                    final year = dt.year.toString();
                    dateDisplay = '$day/$month/$year';
                  } catch (_) {
                    dateDisplay = scheduledDate;
                  }
                }

                return _AnimatedItem(
                  key: ValueKey('anim-$itemId'),
                  index: idx,
                  child: Dismissible(
                    key: ValueKey('apt-$itemId'),
                    direction: DismissDirection.horizontal,
                    background: Container(
                      alignment: Alignment.centerLeft,
                      padding: const EdgeInsets.only(left: 20),
                      color: Colors.blue,
                      child: const Icon(Icons.edit, color: Colors.white),
                    ),
                    secondaryBackground: Container(
                      alignment: Alignment.centerRight,
                      padding: const EdgeInsets.only(right: 20),
                      color: Colors.red,
                      child: const Icon(Icons.delete_outline, color: Colors.white),
                    ),
                    confirmDismiss: (direction) async {
                      if (direction == DismissDirection.startToEnd) {
                        await _editAppointmentDialog(
                          itemId: itemId.toString(),
                          currentText: text,
                          currentScheduledDate: scheduledDate,
                        );
                      } else {
                        await _deleteItem(itemId: itemId);
                      }
                      return false;
                    },
                    child: ListTile(
                      leading: scheduledDate != null
                          ? const Icon(Icons.event, color: Colors.blueGrey)
                          : Checkbox(
                              value: done,
                              onChanged: (v) {
                                if (v != null) {
                                  _toggleDone(itemId: itemId, newValue: v);
                                }
                              },
                            ),
                      title: Text(
                        text,
                        style: TextStyle(
                          decoration: done ? TextDecoration.lineThrough : null,
                        ),
                      ),
                      subtitle: dateDisplay != null
                          ? Text(
                              dateDisplay,
                              style: const TextStyle(
                                fontSize: 12,
                                color: Colors.blueGrey,
                              ),
                            )
                          : null,
                      trailing: Checkbox(
                        value: done,
                        onChanged: (v) {
                          if (v != null) {
                            _toggleDone(itemId: itemId, newValue: v);
                          }
                        },
                      ),
                    ),
                  ),
                );
              }).toList(),
            );
          }

          // ------------------------------------------------------------------
          // Shopping: groupé par catégorie, ordre depuis le backend
          // ------------------------------------------------------------------
          if (widget.listKey == "shopping") {
            final Map<String, List<Map<String, dynamic>>> grouped = {};

            for (final item in items) {
              final cat = (item["category"] ?? "autres").toString().toLowerCase();
              grouped.putIfAbsent(cat, () => []);
              grouped[cat]!.add(item);
            }

            // Ordre : catégories persistées d'abord, puis le reste trié alpha
            final orderedSet = _categoryOrder.toSet();
            final extraCats = grouped.keys
                .where((c) => !orderedSet.contains(c))
                .toList()
              ..sort();
            final categories = [
              ..._categoryOrder.where((c) => grouped.containsKey(c)),
              ...extraCats,
            ];

            // Index global pour l'animation
            int animIdx = 0;

            return ListView(
              children: categories.expand((cat) {
                final categoryItems = grouped[cat]!;

                final widgets = <Widget>[
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: Text(
                      cat.toUpperCase(),
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Colors.grey,
                      ),
                    ),
                  ),
                  ...categoryItems.map((item) {
                    final currentIdx = animIdx++;
                    final itemId = item["id"];
                    final text = item["text"] ?? "";
                    final done = item["done"] == true;
                    final quantity = item["quantity"];
                    final unit = item["unit"];
                    final itemCategory = item["category"] ?? "autres";

                    String display = text;
                    if (quantity != null && unit != null) {
                      display = "$quantity $unit $text";
                    } else if (quantity != null) {
                      display = "$quantity $text";
                    }

                    return _AnimatedItem(
                      key: ValueKey('anim-$itemId'),
                      index: currentIdx,
                      child: Dismissible(
                        key: ValueKey('item-$itemId'),
                        direction: DismissDirection.horizontal,
                        background: Container(
                          alignment: Alignment.centerLeft,
                          padding: const EdgeInsets.only(left: 20),
                          color: Colors.blue,
                          child: const Icon(Icons.edit, color: Colors.white),
                        ),
                        secondaryBackground: Container(
                          alignment: Alignment.centerRight,
                          padding: const EdgeInsets.only(right: 20),
                          color: Colors.red,
                          child: const Icon(Icons.delete_outline, color: Colors.white),
                        ),
                        confirmDismiss: (direction) async {
                          if (direction == DismissDirection.startToEnd) {
                            await _editItemDialog(
                              itemId: itemId,
                              currentText: text,
                              currentCategory: itemCategory,
                              currentQuantity: quantity,
                              currentUnit: unit?.toString(),
                            );
                          } else {
                            await _deleteItem(itemId: itemId);
                          }
                          return false;
                        },
                        child: ListTile(
                          leading: Checkbox(
                            value: done,
                            onChanged: (v) {
                              if (v != null) _toggleDone(itemId: itemId, newValue: v);
                            },
                          ),
                          title: Text(
                            display,
                            style: TextStyle(
                              decoration: done ? TextDecoration.lineThrough : null,
                            ),
                          ),
                        ),
                      ),
                    );
                  }),
                ];

                return widgets;
              }).toList(),
            );
          }

          // ------------------------------------------------------------------
          // todo / todo_pro / ideas: ReorderableListView avec drag & drop
          // ------------------------------------------------------------------
          return ReorderableListView(
            onReorder: (oldIndex, newIndex) async {
              if (newIndex > oldIndex) newIndex -= 1;
              final reordered = List<Map<String, dynamic>>.from(items);
              final moved = reordered.removeAt(oldIndex);
              reordered.insert(newIndex, moved);
              final ids = reordered
                  .map((e) => e["id"].toString())
                  .toList();
              await _api.reorderItems(listName: widget.listKey, ids: ids);
              _reload();
            },
            children: items.asMap().entries.map((entry) {
              final idx = entry.key;
              final item = entry.value;
              final itemId = item["id"];
              final text = item["text"] ?? "";
              final done = item["done"] == true;

              // ReorderableListView exige que la Key soit directement sur le
              // widget enfant direct — on enveloppe _AnimatedItem dans un
              // widget qui porte la bonne key pour le reorderable.
              return _AnimatedItem(
                key: ValueKey('anim-$itemId'),
                index: idx,
                child: Dismissible(
                  key: ValueKey('inline-$itemId'),
                  direction: DismissDirection.horizontal,
                  background: Container(
                    alignment: Alignment.centerLeft,
                    padding: const EdgeInsets.only(left: 20),
                    color: Colors.blue,
                    child: const Icon(Icons.edit, color: Colors.white),
                  ),
                  secondaryBackground: Container(
                    alignment: Alignment.centerRight,
                    padding: const EdgeInsets.only(right: 20),
                    color: Colors.red,
                    child: const Icon(Icons.delete_outline, color: Colors.white),
                  ),
                  confirmDismiss: (direction) async {
                    if (direction == DismissDirection.startToEnd) {
                      await _editItemDialog(
                        itemId: itemId.toString(),
                        currentText: text,
                        currentCategory: (item["category"] ?? "autres").toString(),
                        currentQuantity: item["quantity"],
                        currentUnit: item["unit"]?.toString(),
                      );
                    } else {
                      await _deleteItem(itemId: itemId.toString());
                    }
                    return false;
                  },
                  child: _InlineEditTile(
                    key: ValueKey('tile-$itemId'),
                    text: text,
                    display: text,
                    done: done,
                    onToggle: () => _toggleDone(itemId: itemId.toString(), newValue: !done),
                    onRename: (newText) async {
                      await _api.renameItem(
                        listName: widget.listKey,
                        itemId: itemId.toString(),
                        text: newText,
                      );
                      _reload();
                    },
                  ),
                ),
              );
            }).toList(),
          );
        },
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// _InlineEditTile (inchangé)
// ---------------------------------------------------------------------------

class _InlineEditTile extends StatefulWidget {
  final String text;
  final String display;
  final bool done;
  final VoidCallback onToggle;
  final Future<void> Function(String) onRename;

  const _InlineEditTile({
    super.key,
    required this.text,
    required this.display,
    required this.done,
    required this.onToggle,
    required this.onRename,
  });

  @override
  State<_InlineEditTile> createState() => _InlineEditTileState();
}

class _InlineEditTileState extends State<_InlineEditTile> {
  bool _editing = false;
  late TextEditingController _ctrl;
  final FocusNode _focus = FocusNode();

  @override
  void initState() {
    super.initState();
    _ctrl = TextEditingController(text: widget.text);
    _focus.addListener(() {
      if (!_focus.hasFocus && _editing) {
        Future.delayed(const Duration(milliseconds: 150), () {
          if (mounted && _editing) {
            setState(() {
              _editing = false;
              _ctrl.text = widget.text;
            });
          }
        });
      }
    });
  }

  @override
  void didUpdateWidget(_InlineEditTile old) {
    super.didUpdateWidget(old);
    if (!_editing) _ctrl.text = widget.text;
  }

  @override
  void dispose() {
    _ctrl.dispose();
    _focus.dispose();
    super.dispose();
  }

  void _confirm() {
    final newText = _ctrl.text.trim();
    setState(() => _editing = false);
    if (newText.isNotEmpty && newText != widget.text) widget.onRename(newText);
  }

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Checkbox(value: widget.done, onChanged: (_) => widget.onToggle()),
      title: _editing
          ? TextField(
              controller: _ctrl,
              focusNode: _focus,
              autofocus: true,
              decoration: const InputDecoration(
                isDense: true,
                contentPadding: EdgeInsets.symmetric(vertical: 6),
                border: UnderlineInputBorder(),
              ),
              onSubmitted: (_) => _confirm(),
              textInputAction: TextInputAction.done,
            )
          : GestureDetector(
              onTap: () {
                _ctrl.text = widget.text;
                setState(() => _editing = true);
                WidgetsBinding.instance.addPostFrameCallback((_) {
                  _focus.requestFocus();
                  _ctrl.selection = TextSelection(
                    baseOffset: 0,
                    extentOffset: _ctrl.text.length,
                  );
                });
              },
              child: Text(
                widget.display,
                style: TextStyle(
                  decoration: widget.done ? TextDecoration.lineThrough : null,
                ),
              ),
            ),
      trailing: _editing
          ? Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(
                  icon: const Icon(Icons.check, color: Colors.green),
                  onPressed: _confirm,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
                IconButton(
                  icon: const Icon(Icons.close, color: Colors.grey),
                  onPressed: () => setState(() {
                    _editing = false;
                    _ctrl.text = widget.text;
                  }),
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
              ],
            )
          : null,
    );
  }
}
