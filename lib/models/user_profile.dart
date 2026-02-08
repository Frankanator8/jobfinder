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
    );
  }
}
