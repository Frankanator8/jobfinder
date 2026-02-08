class Job {
  final String id;
  final String title;
  final String company;
  final String location;
  final String salary;
  final String description;
  final List<String> requirements;
  final String type; // Full-time, Part-time, Contract, etc.
  final String? logo;
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
    this.logo,
    this.datePosted,
  });

  factory Job.fromJson(Map<String, dynamic> json) {
    return Job(
      id: json['application_id'] as String? ?? '',
      title: json['position_title'] as String? ?? '',
      company: json['company_name'] as String? ?? '',
      location: json['location'] as String? ?? '',
      salary: json['compensation'] as String? ?? '',
      description: json['description'] as String? ?? '',
      requirements: (json['requirements'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      type: json['job_type'] as String? ?? '',
      logo: json['logo'] as String? ?? '',
      datePosted: json['date_posted'] != null
          ? DateTime.tryParse(json['date_posted'].toString())
          : null,
    );
  }
}

