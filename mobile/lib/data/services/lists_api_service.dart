import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../core/config/api_config.dart';

class ListsApiService {
  Future<Map<String, dynamic>> fetchAllLists() async {
    final response = await http.get(
      Uri.parse('${ApiConfig.baseUrl}/lists'),
    );

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
    final response = await http.patch(
      Uri.parse('${ApiConfig.baseUrl}/lists/$listName/item/$itemId'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'done': done,
      }),
    );

    if (response.statusCode != 200) {
      return false;
    }

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return data['updated'] == true;
  }

  Future<bool> deleteItem({
    required String listName,
    required String itemId,
  }) async {
    final response = await http.delete(
      Uri.parse('${ApiConfig.baseUrl}/lists/$listName/item/$itemId'),
    );

    if (response.statusCode != 200) {
      return false;
    }

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return data['deleted'] == true;
  }

  Future<bool> addItem({
    required String listName,
    required String text,
  }) async {
    final response = await http.post(
      Uri.parse('${ApiConfig.baseUrl}/lists/$listName'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'item': text,
        'source_transcript': null,
      }),
    );

    if (response.statusCode != 200) {
      return false;
    }

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return data['added'] == true;
  }

    Future<bool> renameItem({
        required String listName,
        required String itemId,
        required String text,
    }) async {
        final response = await http.patch(
        Uri.parse('${ApiConfig.baseUrl}/lists/$listName/item/$itemId/rename'),
        headers: {
            'Content-Type': 'application/json',
        },
        body: jsonEncode({
            'text': text,
        }),
        );

        if (response.statusCode != 200) {
        return false;
        }

        final data = jsonDecode(response.body) as Map<String, dynamic>;
        return data['updated'] == true;
    }
}