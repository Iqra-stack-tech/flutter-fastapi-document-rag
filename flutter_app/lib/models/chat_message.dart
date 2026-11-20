import 'source_reference.dart';

class ChatMessage {
  final String role;
  final String content;
  final List<SourceReference> sources;

  const ChatMessage({
    required this.role,
    required this.content,
    this.sources = const [],
  });

  bool get isUser => role == 'user';

  Map<String, dynamic> toHistoryJson() {
    return {
      'role': role,
      'content': content,
    };
  }
}
