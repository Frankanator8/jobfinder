import 'package:flutter/material.dart';
import '../models/user_profile.dart';

class UserInfoScreen extends StatefulWidget {
  final UserProfile? initialProfile;
  final Function(UserProfile) onSave;

  const UserInfoScreen({
    super.key,
    this.initialProfile,
    required this.onSave,
  });

  @override
  State<UserInfoScreen> createState() => _UserInfoScreenState();
}

class _UserInfoScreenState extends State<UserInfoScreen> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _nameController;
  late TextEditingController _emailController;
  late TextEditingController _phoneController;
  late TextEditingController _locationController;
  late TextEditingController _currentRoleController;
  late TextEditingController _experienceController;
  late TextEditingController _bioController;
  late TextEditingController _skillController;

  String _preferredJobType = 'Full-time';
  String _salaryRange = '';
  List<String> _skills = [];

  final List<String> _jobTypes = [
    'Full-time',
    'Part-time',
    'Contract',
    'Internship',
    'Freelance',
  ];

  final List<String> _salaryRanges = [
    '\$50k - \$75k',
    '\$75k - \$100k',
    '\$100k - \$125k',
    '\$125k - \$150k',
    '\$150k - \$200k',
    '\$200k+',
  ];

  @override
  void initState() {
    super.initState();
    final profile = widget.initialProfile ?? UserProfile();
    _nameController = TextEditingController(text: profile.name);
    _emailController = TextEditingController(text: profile.email);
    _phoneController = TextEditingController(text: profile.phone);
    _locationController = TextEditingController(text: profile.location);
    _currentRoleController = TextEditingController(text: profile.currentRole);
    _experienceController = TextEditingController(text: profile.experience);
    _bioController = TextEditingController(text: profile.bio);
    _skillController = TextEditingController();
    _preferredJobType = profile.preferredJobType.isNotEmpty
        ? profile.preferredJobType
        : 'Full-time';
    _salaryRange = profile.salaryRange;
    _skills = List.from(profile.skills);
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _locationController.dispose();
    _currentRoleController.dispose();
    _experienceController.dispose();
    _bioController.dispose();
    _skillController.dispose();
    super.dispose();
  }

  void _addSkill() {
    final skill = _skillController.text.trim();
    if (skill.isNotEmpty && !_skills.contains(skill)) {
      setState(() {
        _skills.add(skill);
        _skillController.clear();
      });
    }
  }

  void _removeSkill(String skill) {
    setState(() {
      _skills.remove(skill);
    });
  }

  void _saveProfile() {
    if (_formKey.currentState!.validate()) {
      final profile = UserProfile(
        name: _nameController.text.trim(),
        email: _emailController.text.trim(),
        phone: _phoneController.text.trim(),
        location: _locationController.text.trim(),
        currentRole: _currentRoleController.text.trim(),
        experience: _experienceController.text.trim(),
        skills: _skills,
        bio: _bioController.text.trim(),
        preferredJobType: _preferredJobType,
        salaryRange: _salaryRange,
      );

      widget.onSave(profile);
      Navigator.pop(context);
      
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Profile saved successfully'),
          backgroundColor: Color(0xFF34A853),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: isDark ? const Color(0xFF202124) : Colors.white,
      appBar: AppBar(
        title: const Text('Profile'),
        elevation: 0,
        backgroundColor: isDark ? const Color(0xFF303134) : Colors.white,
        foregroundColor: isDark ? Colors.white : const Color(0xFF202124),
        surfaceTintColor: Colors.transparent,
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            // Personal Information Section
            _buildSectionHeader('Personal Information'),
            const SizedBox(height: 16),
            _buildTextField(
              controller: _nameController,
              label: 'Full Name',
              icon: Icons.person_outline,
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Please enter your name';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            _buildTextField(
              controller: _emailController,
              label: 'Email',
              icon: Icons.email_outlined,
              keyboardType: TextInputType.emailAddress,
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Please enter your email';
                }
                if (!value.contains('@')) {
                  return 'Please enter a valid email';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            _buildTextField(
              controller: _phoneController,
              label: 'Phone Number',
              icon: Icons.phone_outlined,
              keyboardType: TextInputType.phone,
            ),
            const SizedBox(height: 16),
            _buildTextField(
              controller: _locationController,
              label: 'Location',
              icon: Icons.location_on_outlined,
              hintText: 'City, State or Remote',
            ),
            const SizedBox(height: 32),

            // Professional Information Section
            _buildSectionHeader('Professional Information'),
            const SizedBox(height: 16),
            _buildTextField(
              controller: _currentRoleController,
              label: 'Current Role',
              icon: Icons.work_outline,
              hintText: 'e.g., Software Engineer',
            ),
            const SizedBox(height: 16),
            _buildTextField(
              controller: _experienceController,
              label: 'Years of Experience',
              icon: Icons.trending_up_outlined,
              keyboardType: TextInputType.number,
              hintText: 'e.g., 5',
            ),
            const SizedBox(height: 16),
            _buildTextField(
              controller: _bioController,
              label: 'Bio',
              icon: Icons.description_outlined,
              maxLines: 4,
              hintText: 'Tell us about yourself...',
            ),
            const SizedBox(height: 32),

            // Job Preferences Section
            _buildSectionHeader('Job Preferences'),
            const SizedBox(height: 16),
            _buildDropdown(
              label: 'Preferred Job Type',
              value: _preferredJobType,
              items: _jobTypes,
              onChanged: (value) {
                setState(() {
                  _preferredJobType = value!;
                });
              },
            ),
            const SizedBox(height: 16),
            _buildDropdown(
              label: 'Salary Range',
              value: _salaryRange.isEmpty ? null : _salaryRange,
              items: _salaryRanges,
              onChanged: (value) {
                setState(() {
                  _salaryRange = value ?? '';
                });
              },
            ),
            const SizedBox(height: 32),

            // Skills Section
            _buildSectionHeader('Skills'),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _buildTextField(
                    controller: _skillController,
                    label: 'Add Skill',
                    icon: Icons.add_circle_outline,
                    onSubmitted: (_) => _addSkill(),
                  ),
                ),
                const SizedBox(width: 12),
                ElevatedButton(
                  onPressed: _addSkill,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF4285F4),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 24,
                      vertical: 16,
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: const Text('Add'),
                ),
              ],
            ),
            if (_skills.isNotEmpty) ...[
              const SizedBox(height: 16),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: _skills.map((skill) {
                  return Chip(
                    label: Text(skill),
                    onDeleted: () => _removeSkill(skill),
                    deleteIcon: const Icon(Icons.close, size: 18),
                    backgroundColor: isDark
                        ? Colors.grey.shade800
                        : Colors.grey.shade100,
                    labelStyle: TextStyle(
                      color: isDark ? Colors.white : const Color(0xFF202124),
                    ),
                  );
                }).toList(),
              ),
            ],
            const SizedBox(height: 48),

            // Save Button
            ElevatedButton(
              onPressed: _saveProfile,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF4285F4),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
                elevation: 0,
              ),
              child: const Text(
                'Save Profile',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Text(
      title,
      style: TextStyle(
        fontSize: 18,
        fontWeight: FontWeight.w500,
        color: isDark ? Colors.white : const Color(0xFF202124),
      ),
    );
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    String? hintText,
    TextInputType? keyboardType,
    int maxLines = 1,
    String? Function(String?)? validator,
    void Function(String)? onSubmitted,
  }) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return TextFormField(
      controller: controller,
      keyboardType: keyboardType,
      maxLines: maxLines,
      validator: validator,
      onFieldSubmitted: onSubmitted,
      style: TextStyle(
        color: isDark ? Colors.white : const Color(0xFF202124),
      ),
      decoration: InputDecoration(
        labelText: label,
        hintText: hintText,
        prefixIcon: Icon(icon, color: const Color(0xFF4285F4)),
        filled: true,
        fillColor: isDark
            ? Colors.grey.shade900.withOpacity(0.5)
            : Colors.grey.shade50,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(
            color: isDark ? Colors.grey.shade800 : Colors.grey.shade300,
          ),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(
            color: isDark ? Colors.grey.shade800 : Colors.grey.shade300,
          ),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(
            color: Color(0xFF4285F4),
            width: 2,
          ),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(
            color: Color(0xFFEA4335),
          ),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(
            color: Color(0xFFEA4335),
            width: 2,
          ),
        ),
      ),
    );
  }

  Widget _buildDropdown({
    required String label,
    required String? value,
    required List<String> items,
    required void Function(String?) onChanged,
  }) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return DropdownButtonFormField<String>(
      value: value,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: const Icon(Icons.settings_outlined, color: Color(0xFF4285F4)),
        filled: true,
        fillColor: isDark
            ? Colors.grey.shade900.withOpacity(0.5)
            : Colors.grey.shade50,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(
            color: isDark ? Colors.grey.shade800 : Colors.grey.shade300,
          ),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(
            color: isDark ? Colors.grey.shade800 : Colors.grey.shade300,
          ),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(
            color: Color(0xFF4285F4),
            width: 2,
          ),
        ),
      ),
      items: items.map((item) {
        return DropdownMenuItem<String>(
          value: item,
          child: Text(
            item,
            style: TextStyle(
              color: isDark ? Colors.white : const Color(0xFF202124),
            ),
          ),
        );
      }).toList(),
      onChanged: onChanged,
      style: TextStyle(
        color: isDark ? Colors.white : const Color(0xFF202124),
      ),
    );
  }
}

