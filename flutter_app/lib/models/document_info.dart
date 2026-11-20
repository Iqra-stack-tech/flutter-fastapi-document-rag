class DocumentInfo {
  final String filename;
  final int chunksCreated;
  final int vectorDimension;
  final String collection;

  const DocumentInfo({
    required this.filename,
    required this.chunksCreated,
    required this.vectorDimension,
    required this.collection,
  });

  factory DocumentInfo.fromJson(Map<String, dynamic> json) {
    return DocumentInfo(
      filename: json['filename']?.toString() ?? 'Unknown.pdf',
      chunksCreated: (json['chunks_created'] as num?)?.toInt() ?? 0,
      vectorDimension:
          (json['vector_dimension'] as num?)?.toInt() ?? 0,
      collection: json['collection']?.toString() ?? '',
    );
  }
}
