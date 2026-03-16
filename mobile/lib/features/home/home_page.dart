import 'package:flutter/material.dart';
import '../../data/services/lists_api_service.dart';
import '../lists/list_detail_page.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final ListsApiService _apiService = ListsApiService();

  late Future<Map<String, dynamic>> _listsFuture;

  void _reload() {
    setState(() {
      _listsFuture = _apiService.fetchAllLists();
    });
  }

  @override
  void initState() {
    super.initState();
    _reload();
  }

  String _labelForKey(String key) {
    switch (key) {
      case 'shopping':
        return 'Shopping';
      case 'todo':
        return 'Todo';
      case 'todo_pro':
        return 'Todo Pro';
      case 'appointments':
        return 'Appointments';
      case 'ideas':
        return 'Ideas';
      default:
        return key;
    }
  }

  IconData _iconForKey(String key) {
    switch (key) {
      case 'shopping':
        return Icons.shopping_cart_outlined;
      case 'todo':
        return Icons.checklist_outlined;
      case 'todo_pro':
        return Icons.work_outline;
      case 'appointments':
        return Icons.event_outlined;
      case 'ideas':
        return Icons.lightbulb_outline;
      default:
        return Icons.list_alt_outlined;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Ambient Task Listener'),
      ),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _listsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return Center(
              child: Text('Erreur API : ${snapshot.error}'),
            );
          }

          final data = snapshot.data ?? {};

          final keys = [
            'shopping',
            'todo',
            'todo_pro',
            'appointments',
            'ideas',
          ];

          return Padding(
            padding: const EdgeInsets.all(16),
            child: GridView.builder(
              itemCount: keys.length,
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
                childAspectRatio: 2.5,
              ),
              itemBuilder: (context, index) {
                final key = keys[index];
                final items = (data[key] as List?) ?? [];

                final total = items.length;
                final done = items.where((e) => e["done"] == true).length;
                final remaining = total - done;

                String subtitle;
                if (key == 'todo' || key == 'todo_pro') {
                  subtitle = total == 0 ? "0 item" : "$remaining / $total";
                } else {
                  subtitle = "$total item${total > 1 ? 's' : ''}";
                }

                return InkWell(
                  onTap: () async {
                    await Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => ListDetailPage(
                          listKey: key,
                          title: _labelForKey(key),
                        ),
                      ),
                    );

                    _reload();
                  },
                  child: Card(
                    elevation: 2,
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      child: Row(
                        children: [
                          Icon(
                            _iconForKey(key),
                            size: 28,
                            color: Theme.of(context).colorScheme.primary,
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  _labelForKey(key),
                                  style: Theme.of(context).textTheme.titleMedium,
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  subtitle,
                                  style: Theme.of(context).textTheme.bodySmall,
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}