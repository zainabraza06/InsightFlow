class SourceAnalysis {
  final String sourceType;
  final String content;
  final double credibility;
  final bool hasError;

  SourceAnalysis({
    required this.sourceType,
    required this.content,
    required this.credibility,
    required this.hasError,
  });

  factory SourceAnalysis.fromJson(Map<String, dynamic> json) => SourceAnalysis(
        sourceType: json['source_type'] ?? '',
        content: json['content'] ?? '',
        credibility: (json['credibility_score'] ?? json['credibility_base'] ?? 0).toDouble(),
        hasError: json['content'] == 'URL_FETCH_FAILED' || json['error'] != null,
      );
}
