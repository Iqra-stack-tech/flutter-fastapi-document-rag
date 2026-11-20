import 'dart:convert';

import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;

import '../config/api_config.dart';
import '../models/ask_result.dart';
import '../models/chat_message.dart';
import '../models/document_info.dart';
import '../models/source_reference.dart';

class RagApiService {
  const RagApiService();

  String _readError(http.Response response) {
    try {
      final decoded = jsonDecode(response.body);

      if (decoded is Map<String, dynamic>) {
        return decoded['detail']?.toString() ?? 'Request failed.';
      }
    } catch (_) {
      // Ignore non-JSON backend responses.
    }

    return 'Request failed with status ${response.statusCode}.';
  }

  Future<DocumentInfo?> getStatus() async {
    final response = await http
        .get(
          Uri.parse('${ApiConfig.baseUrl}/status'),
        )
        .timeout(
          const Duration(seconds: 20),
        );

    if (response.statusCode != 200) {
      throw Exception(_readError(response));
    }

    final decoded =
        jsonDecode(response.body) as Map<String, dynamic>;

    if (decoded['indexed'] != true) {
      return null;
    }

    final document = decoded['document'];

    if (document is! Map<String, dynamic>) {
      return null;
    }

    return DocumentInfo.fromJson(document);
  }

  Future<DocumentInfo> uploadPdf(PlatformFile file) async {
    final bytes = await file.readAsBytes();

    final request = http.MultipartRequest(
      'POST',
      Uri.parse('${ApiConfig.baseUrl}/upload'),
    );

    request.files.add(
      http.MultipartFile.fromBytes(
        'file',
        bytes,
        filename: file.name,
      ),
    );

    final streamedResponse = await request.send().timeout(
          const Duration(minutes: 3),
        );

    final response = await http.Response.fromStream(
      streamedResponse,
    );

    if (response.statusCode < 200 ||
        response.statusCode >= 300) {
      throw Exception(_readError(response));
    }

    final decoded =
        jsonDecode(response.body) as Map<String, dynamic>;

    final document = decoded['document'];

    if (document is! Map<String, dynamic>) {
      throw Exception(
        'Backend returned invalid document information.',
      );
    }

    return DocumentInfo.fromJson(document);
  }

  Future<AskResult> ask({
    required String question,
    required List<ChatMessage> history,
  }) async {
    final response = await http
        .post(
          Uri.parse('${ApiConfig.baseUrl}/ask'),
          headers: {
            'Content-Type': 'application/json',
          },
          body: jsonEncode(
            {
              'question': question,
              'history': history
                  .map(
                    (message) => message.toHistoryJson(),
                  )
                  .toList(),
            },
          ),
        )
        .timeout(
          const Duration(seconds: 90),
        );

    if (response.statusCode < 200 ||
        response.statusCode >= 300) {
      throw Exception(_readError(response));
    }

    final decoded =
        jsonDecode(response.body) as Map<String, dynamic>;

    final rawSources = decoded['sources'] as List? ?? [];

    final sources = rawSources
        .whereType<Map<String, dynamic>>()
        .map(SourceReference.fromJson)
        .toList();

    return AskResult(
      answer: decoded['answer']?.toString() ?? 'No answer returned.',
      sources: sources,
    );
  }
}
