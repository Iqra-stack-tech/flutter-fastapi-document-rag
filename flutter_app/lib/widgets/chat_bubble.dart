import 'package:flutter/material.dart';

import '../models/chat_message.dart';
import 'source_chip.dart';

class ChatBubble extends StatelessWidget {
  final ChatMessage message;

  const ChatBubble({
    super.key,
    required this.message,
  });

  @override
  Widget build(BuildContext context) {
    final isUser = message.isUser;

    return Align(
      alignment:
          isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(
          maxWidth: 760,
        ),
        margin: const EdgeInsets.only(
          bottom: 18,
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            if (!isUser) ...[
              Container(
                width: 34,
                height: 34,
                decoration: const BoxDecoration(
                  color: Color(0xFFEDEBFF),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.auto_awesome,
                  size: 17,
                  color: Color(0xFF625BF6),
                ),
              ),
              const SizedBox(width: 10),
            ],
            Flexible(
              child: Column(
                crossAxisAlignment: isUser
                    ? CrossAxisAlignment.end
                    : CrossAxisAlignment.start,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 17,
                      vertical: 14,
                    ),
                    decoration: BoxDecoration(
                      color: isUser
                          ? const Color(0xFF625BF6)
                          : Colors.white,
                      borderRadius: BorderRadius.circular(18),
                      border: isUser
                          ? null
                          : Border.all(
                              color: const Color(0xFFE5E7EB),
                            ),
                    ),
                    child: SelectableText(
                      message.content,
                      style: TextStyle(
                        height: 1.55,
                        color: isUser
                            ? Colors.white
                            : const Color(0xFF1F2937),
                      ),
                    ),
                  ),
                  if (!isUser && message.sources.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(
                        top: 9,
                      ),
                      child: Wrap(
                        spacing: 7,
                        runSpacing: 7,
                        children: message.sources
                            .map(
                              (source) => SourceChip(
                                source: source,
                              ),
                            )
                            .toList(),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
