import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../core/config/api_config.dart';

class ListsApiService {
  Future<Map<String, dynamic>> fetchAllLists() async {
    final baseUrl = await ApiConfig.getBaseUrl();
    final response = await http.get(Uri.parse('$baseUrl/lists'));

    if (response.statusCode != 200) {
      throw Exception('Failed to load lists');
    }

    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<bool> updateItemDone({
    required String listName,
    required String itemId,
    required bool done,
  }) async {
    final baseUrl = await ApiConfig.getBaseUrl();
    final response = await http.patch(
      Uri.parse('$baseUrl/lists/$listName/item/$itemId'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'done': done}),
    );

    if (response.statusCode != 200) return false;
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return data['updated'] == true;
  }

  Future<bool> deleteItem({
    required String listName,
    required String itemId,
  }) async {
    final baseUrl = await ApiConfig.getBaseUrl();
    final response = await http.delete(
      Uri.parse('$baseUrl/lists/$listName/item/$itemId'),
    );

    if (response.statusCode != 200) return false;
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return data['deleted'] == true;
  }

  Future<bool> addItem({
    required String listName,
    required String text,
    String? scheduledDate,
  }) async {
    final baseUrl = await ApiConfig.getBaseUrl();
    final response = await http.post(
      Uri.parse('$baseUrl/lists/$listName'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'item': text,
        'source_transcript': null,
        'scheduled_date': scheduledDate,
      }),
    );

    if (response.statusCode != 200) return false;
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return data['created'] == true;
  }

  Future<bool> renameItem({
    required String listName,
    required String itemId,
    required String text,
  }) async {
    final baseUrl = await ApiConfig.getBaseUrl();
    final response = await http.patch(
      Uri.parse('$baseUrl/lists/$listName/item/$itemId/rename'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'text': text}),
    );

    if (response.statusCode != 200) return false;
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return data['updated'] == true;
  }

  Future<bool> updateItemScheduledDate({
    required String listName,
    required String itemId,
    String? scheduledDate,
  }) async {
    final baseUrl = await ApiConfig.getBaseUrl();
    final response = await http.patch(
      Uri.parse('$baseUrl/lists/$listName/item/$itemId/scheduled_date'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'scheduled_date': scheduledDate}),
    );

    if (response.statusCode != 200) return false;
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return data['updated'] == true;
  }

  Future<bool> reorderItems({
    required String listName,
    required List<String> ids,
  }) async {
    final baseUrl = await ApiConfig.getBaseUrl();
    final response = await http.patch(
      Uri.parse('$baseUrl/lists/$listName/reorder'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'ids': ids}),
    );

    if (response.statusCode != 200) return false;
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return data['reordered'] == true;
  }

  Future<bool> updateItemCategory({
    required String listName,
    required String itemId,
    required String category,
  }) async {
    final baseUrl = await ApiConfig.getBaseUrl();
    final response = await http.patch(
      Uri.parse('$baseUrl/lists/$listName/item/$itemId/category'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'category': category}),
    );

    if (response.statusCode != 200) return false;
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return data['updated'] == true;
  }

  Future<List<Map<String, dynamic>>> fetchPendingItems() async {
    final baseUrl = await ApiConfig.getBaseUrl();
    final response = await http.get(Uri.parse('$baseUrl/pending'));

    if (response.statusCode != 200) {
      throw Exception('Erreur lors du chargement des éléments à confirmer');
    }

    final decoded = jsonDecode(response.body) as List;
    return decoded.map((e) => Map<String, dynamic>.from(e)).toList();
  }

  Future<bool> approvePendingItem(
    String itemId, {
    String? text,
    String? listName,
    double? quantity,
    String? unit,
    String? scheduledDate,
  }) async {
    final baseUrl = await ApiConfig.getBaseUrl();
    final response = await http.post(
      Uri.parse('$baseUrl/pending/$itemId/approve'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'text': text,
        'list': listName,
        'quantity': quantity,
        'unit': unit,
        'scheduled_date': scheduledDate,
      }),
    );

    return response.statusCode == 200;
  }

  Future<bool> rejectPendingItem(String itemId) async {
    final baseUrl = await ApiConfig.getBaseUrl();
    final response = await http.delete(Uri.parse('$baseUrl/pending/$itemId'));
    return response.statusCode == 200;
  }

  Future<List<String>> fetchCategoryOrder(String listName) async {
    final baseUrl = await ApiConfig.getBaseUrl();
    final response = await http.get(
      Uri.parse('$baseUrl/lists/$listName/category-order'),
    );

    if (response.statusCode != 200) return [];
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final cats = data['categories'] as List?;
    return cats?.map((e) => e.toString()).toList() ?? [];
  }

  Future<bool> updateCategoryOrder(
      String listName, List<String> categories) async {
    final baseUrl = await ApiConfig.getBaseUrl();
    final response = await http.put(
      Uri.parse('$baseUrl/lists/$listName/category-order'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'categories': categories}),
    );

    if (response.statusCode != 200) return false;
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return data['ok'] == true;
  }

  Future<int> fetchPendingCount() async {
    final items = await fetchPendingItems();
    return items.length;
  }

  Future<Map<String, int>> fetchPendingCountsByList() async {
    final items = await fetchPendingItems();
    final Map<String, int> counts = {};
    for (final item in items) {
      final listName = (item['list'] ?? 'inbox').toString();
      counts[listName] = (counts[listName] ?? 0) + 1;
    }
    return counts;
  }

  Future<Map<String, double>> fetchConfidenceSettings() async {
    final baseUrl = await ApiConfig.getBaseUrl();
    final response = await http.get(Uri.parse('$baseUrl/settings/confidence'));

    if (response.statusCode != 200) {
      throw Exception('Impossible de charger les seuils de confiance');
    }

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return {
      'add_threshold': (data['add_threshold'] as num).toDouble(),
      'ignore_threshold': (data['ignore_threshold'] as num).toDouble(),
    };
  }

  Future<bool> updateConfidenceSettings({
    required double addThreshold,
    required double ignoreThreshold,
  }) async {
    final baseUrl = await ApiConfig.getBaseUrl();
    final response = await http.put(
      Uri.parse('$baseUrl/settings/confidence'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'add_threshold': addThreshold,
        'ignore_threshold': ignoreThreshold,
      }),
    );

    if (response.statusCode != 200) return false;
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return data['ok'] == true;
  }
}
