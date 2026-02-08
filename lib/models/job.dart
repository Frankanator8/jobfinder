class Job {
  final String id;
  final String title;
  final String company;
  final String location;
  final String salary;
  final String description;
  final List<String> requirements;
  final String type; // Full-time, Part-time, Contract, etc.
  final String? jobUrl;
  final String? logo;
  final String? workType;
  final DateTime? datePosted;

  Job({
    required this.id,
    required this.title,
    required this.company,
    required this.location,
    required this.salary,
    required this.description,
    required this.requirements,
    required this.type,
    this.jobUrl,
    this.logo,
    this.workType,
    this.datePosted,
  });

  /// Create a Job from the backend API JSON response.
  factory Job.fromJson(Map<String, dynamic> json) {
    return Job(
      id: json['application_id'] ?? '',
      title: json['position_title'] ?? 'Unknown Position',
      company: json['company_name'] ?? 'Unknown Company',
      location: json['location'] ?? 'Location not specified',
      salary: json['compensation'] ?? 'Not specified',
      description: json['description'] ?? '',
      requirements: _parseRequirements(json['description'] ?? ''),
      type: json['job_type'] ?? 'Full-time',
      jobUrl: json['job_url'],
      logo: json['logo'],
      workType: json['work_type'],
      datePosted: json['date_posted'] != null
          ? DateTime.tryParse(json['date_posted'].toString())
          : null,
    );
  }

  /// Extract rough "requirements" keywords from the description,
  /// since the backend schema doesn't have a separate requirements field.
  static List<String> _parseRequirements(String description) {
    if (description.isEmpty) return [];

    // Common tech keywords to look for in descriptions
    final keywords = [
      'Python', 'Java', 'JavaScript', 'TypeScript', 'Flutter', 'Dart',
      'React', 'Angular', 'Vue', 'Node.js', 'SQL', 'NoSQL', 'AWS',
      'Azure', 'GCP', 'Docker', 'Kubernetes', 'Git', 'REST', 'GraphQL',
      'C++', 'C#', 'Go', 'Rust', 'Swift', 'Kotlin', 'Ruby', 'PHP',
      'HTML', 'CSS', 'MongoDB', 'PostgreSQL', 'Redis', 'Linux',
      'Agile', 'Scrum', 'CI/CD', 'Machine Learning', 'AI',
      'Data Science', 'DevOps', 'Figma', 'UI/UX',
    ];

    final found = <String>[];
    final lowerDesc = description.toLowerCase();
    for (final kw in keywords) {
      if (lowerDesc.contains(kw.toLowerCase()) && found.length < 6) {
        found.add(kw);
      }
    }
    return found;
  }
}

