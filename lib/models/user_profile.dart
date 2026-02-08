class UserProfile {
  String name;
  String email;
  String phone;
  String location;
  String currentRole;
  String experience;
  List<String> skills;
  String bio;
  String preferredJobType;
  String salaryRange;

  // Scraper / search preferences
  List<String> searchSites;
  String searchLocation;
  int hoursOld;
  String category;

  static const List<String> availableSites = [
    'indeed',
    'linkedin',
    'zip_recruiter',
    'google',
  ];

  static const List<String> availableCategories = [
    'software_engineering',
    'data_science',
    'finance',
    'marketing',
    'design',
    'healthcare',
    'sales',
    'operations',
    'education',
    'legal',
    'human_resources',
    'customer_service',
    'other',
  ];

  static String categoryLabel(String value) {
    return value.replaceAll('_', ' ').split(' ').map((w) {
      if (w.isEmpty) return w;
      return w[0].toUpperCase() + w.substring(1);
    }).join(' ');
  }

  UserProfile({
    this.name = '',
    this.email = '',
    this.phone = '',
    this.location = '',
    this.currentRole = '',
    this.experience = '',
    this.skills = const [],
    this.bio = '',
    this.preferredJobType = '',
    this.salaryRange = '',
    this.searchSites = const ['indeed', 'linkedin', 'zip_recruiter', 'google'],
    this.searchLocation = '',
    this.hoursOld = 72,
    this.category = '',
  });

  bool get isEmpty {
    return name.isEmpty && email.isEmpty && phone.isEmpty && location.isEmpty;
  }

  /// Whether the profile has the minimum required fields filled in
  bool get isComplete => name.isNotEmpty && email.isNotEmpty;

  /// Convert to a Map for Firestore storage
  Map<String, dynamic> toMap() {
    return {
      'name': name,
      'email': email,
      'phone': phone,
      'location': location,
      'currentRole': currentRole,
      'experience': experience,
      'skills': skills,
      'bio': bio,
      'preferredJobType': preferredJobType,
      'salaryRange': salaryRange,
      'searchSites': searchSites,
      'searchLocation': searchLocation,
      'hoursOld': hoursOld,
      'category': category,
    };
  }

  /// Create a UserProfile from a Firestore document map
  factory UserProfile.fromMap(Map<String, dynamic> map) {
    return UserProfile(
      name: map['name'] as String? ?? '',
      email: map['email'] as String? ?? '',
      phone: map['phone'] as String? ?? '',
      location: map['location'] as String? ?? '',
      currentRole: map['currentRole'] as String? ?? '',
      experience: map['experience'] as String? ?? '',
      skills: List<String>.from(map['skills'] as List? ?? []),
      bio: map['bio'] as String? ?? '',
      preferredJobType: map['preferredJobType'] as String? ?? '',
      salaryRange: map['salaryRange'] as String? ?? '',
      searchSites: List<String>.from(map['searchSites'] as List? ?? ['indeed', 'linkedin', 'zip_recruiter', 'google']),
      searchLocation: map['searchLocation'] as String? ?? '',
      hoursOld: map['hoursOld'] as int? ?? 72,
      category: map['category'] as String? ?? '',
    );
  }
}
