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
    return name.isEmpty &&
        email.isEmpty &&
        phone.isEmpty &&
        location.isEmpty;
  }
}

