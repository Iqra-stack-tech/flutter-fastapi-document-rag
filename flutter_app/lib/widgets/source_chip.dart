import 'package:flutter/material.dart';

import '../models/source_reference.dart';

class SourceChip extends StatelessWidget {
  final SourceReference source;

  const SourceChip({
    super.key,
    required this.source,
  });

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message:
          'Semantic: ${source.semanticScore.toStringAsFixed(2)}\n'
          'Keyword: ${source.keywordScore.toStringAsFixed(2)}\n'
          'Hybrid: ${source.score.toStringAsFixed(2)}',
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: 10,
          vertical: 7,
        ),
        decoration: BoxDecoration(
          color: const Color(0xFFF3F4F6),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: const Color(0xFFE5E7EB),
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              Icons.description_outlined,
              size: 14,
              color: Color(0xFF625BF6),
            ),
            const SizedBox(width: 5),
            Flexible(
              child: Text(
                '${source.file} · Page ${source.page}',
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            const SizedBox(width: 6),
            Text(
              source.score.toStringAsFixed(2),
              style: const TextStyle(
                fontSize: 10,
                color: Color(0xFF9CA3AF),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
