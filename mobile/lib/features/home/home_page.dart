import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../../data/services/lists_api_service.dart';
import '../lists/list_detail_page.dart';
import '../pending/pending_page.dart';
import '../settings/settings_page.dart';
import '../../core/config/api_config.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final ListsApiService _apiService = ListsApiService();

  late Future<Map<String, int>> _pendingCountsFuture;
  late Future<int> _pendingCountFuture;
  late Future<Map<String, dynamic>> _listsFuture;
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

  void _reload() {
    setState(() {
      _listsFuture = _apiService.fetchAllLists();
      _pendingCountFuture = _apiService.fetchPendingCount();
      _pendingCountsFuture = _apiService.fetchPendingCountsByList();
    });
  }

  void _connectWebSocket() async {
    _channel?.sink.close();

    final baseUrl = await ApiConfig.getBaseUrl();
    _channel = WebSocketChannel.connect(
      Uri.parse(ApiConfig.toWsUrl(baseUrl)),
    );

    _channel!.stream.listen(
      (message) {
        debugPrint('HomePage WS message: $message');
        _reload();
      },
      onError: (error) {
        debugPrint('HomePage WS error: $error');
        _reconnect();
      },
      onDone: () {
        debugPrint('HomePage WS closed');
        _reconnect();
      },
      cancelOnError: true,
    );
  }

  void _reconnect() {
    Future.delayed(const Duration(seconds: 2), () {
      if (!mounted) return;
      debugPrint('HomePage WS reconnecting...');
      _connectWebSocket();
    });
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
        title: const Text('Home'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            onPressed: () async {
              await Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const SettingsPage()),
              );
              _connectWebSocket();
              _reload();
            },
          ),
          FutureBuilder<int>(
            future: _pendingCountFuture,
            builder: (context, snapshot) {
              final count = snapshot.data ?? 0;

              return IconButton(
                onPressed: () async {
                  await Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => const PendingPage(),
                    ),
                  );
                  _reload();
                },
                icon: Stack(
                  clipBehavior: Clip.none,
                  children: [
                    const Icon(Icons.help_outline),
                    if (count > 0)
                      Positioned(
                        right: -6,
                        top: -6,
                        child: Container(
                          padding: const EdgeInsets.all(4),
                          decoration: const BoxDecoration(
                            color: Colors.red,
                            shape: BoxShape.circle,
                          ),
                          constraints: const BoxConstraints(
                            minWidth: 18,
                            minHeight: 18,
                          ),
                          child: Text(
                            count.toString(),
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 10,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ),
                      ),
                  ],
                ),
              );
            },
          ),
        ],
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
                  subtitle = total == 0 ? '0 item' : '$remaining / $total';
                } else {
                  subtitle = '$total item${total > 1 ? 's' : ''}';
                }

                return FutureBuilder<Map<String, int>>(
                  future: _pendingCountsFuture,
                  builder: (context, pendingSnapshot) {
                    final pendingCounts = pendingSnapshot.data ?? {};
                    final pendingCountForThisList = pendingCounts[key] ?? 0;

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
                        child: Stack(
                          children: [
                            Padding(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12,
                                vertical: 8,
                              ),
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
                            if (pendingCountForThisList > 0)
                              Positioned(
                                top: 8,
                                right: 8,
                                child: Container(
                                  padding: const EdgeInsets.all(6),
                                  decoration: const BoxDecoration(
                                    color: Colors.orange,
                                    shape: BoxShape.circle,
                                  ),
                                  constraints: const BoxConstraints(
                                    minWidth: 24,
                                    minHeight: 24,
                                  ),
                                  child: Text(
                                    pendingCountForThisList.toString(),
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 12,
                                      fontWeight: FontWeight.bold,
                                    ),
                                    textAlign: TextAlign.center,
                                  ),
                                ),
                              ),
                          ],
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          );
        },
      ),
    );
  }
}