import 'source_reference.dart';

class AskResult {
  final String answer;
  final List<SourceReference> sources;

  const AskResult({
    required this.answer,
    required this.sources,
  });
}
