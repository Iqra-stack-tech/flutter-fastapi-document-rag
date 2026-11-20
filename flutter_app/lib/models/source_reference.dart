class SourceReference {
  final String file;
  final int page;
  final int chunkId;
  final double score;
  final double semanticScore;
  final double keywordScore;

  const SourceReference({
    required this.file,
    required this.page,
    required this.chunkId,
    required this.score,
    required this.semanticScore,
    required this.keywordScore,
  });

  factory SourceReference.fromJson(Map<String, dynamic> json) {
    return SourceReference(
      file: json['file']?.toString() ?? 'Unknown',
      page: (json['page'] as num?)?.toInt() ?? 0,
      chunkId: (json['chunk_id'] as num?)?.toInt() ?? 0,
      score: (json['score'] as num?)?.toDouble() ?? 0,
      semanticScore:
          (json['semantic_score'] as num?)?.toDouble() ?? 0,
      keywordScore:
          (json['keyword_score'] as num?)?.toDouble() ?? 0,
    );
  }
}
