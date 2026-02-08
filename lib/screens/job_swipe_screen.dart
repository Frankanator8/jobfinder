import 'package:flutter/material.dart';
import '../models/job.dart';
import '../models/user_profile.dart';
import '../services/auth_service.dart';
import '../widgets/swipeable_card_stack.dart';
import 'user_info_screen.dart';

class JobSwipeScreen extends StatefulWidget {
  final VoidCallback? onThemeToggle;
  final UserProfile? userProfile;
  final Function(UserProfile)? onProfileUpdated;

  const JobSwipeScreen({
    super.key,
    this.onThemeToggle,
    this.userProfile,
    this.onProfileUpdated,
  });

  @override
  State<JobSwipeScreen> createState() => _JobSwipeScreenState();
}

class _JobSwipeScreenState extends State<JobSwipeScreen> {
  List<Job> _jobs = [];
  List<Job> _likedJobs = [];
  List<Job> _passedJobs = [];
  UserProfile? _userProfile;
  final GlobalKey<SwipeableCardStackState> _cardStackKey =
      GlobalKey<SwipeableCardStackState>();

  @override
  void initState() {
    super.initState();
    _userProfile = widget.userProfile;
    _loadJobs();
  }

  void _loadJobs() {
    // Sample job data
    setState(() {
      _jobs = [
        Job(
          id: '1',
          title: 'Senior Flutter Developer',
          company: 'TechCorp',
          location: 'San Francisco, CA',
          salary: '\$120k - \$150k',
          description:
              'Join our innovative team to build cutting-edge mobile applications. We\'re looking for an experienced Flutter developer to lead our mobile development efforts.',
          requirements: ['Flutter', 'Dart', 'REST APIs', 'Git'],
          type: 'Full-time',
        ),
        Job(
          id: '2',
          title: 'Mobile App Designer',
          company: 'DesignStudio',
          location: 'New York, NY',
          salary: '\$90k - \$110k',
          description:
              'Create beautiful and intuitive user experiences for our mobile applications. Work closely with developers to bring designs to life.',
          requirements: ['UI/UX', 'Figma', 'Prototyping', 'Design Systems'],
          type: 'Full-time',
        ),
        Job(
          id: '3',
          title: 'Backend Engineer',
          company: 'CloudTech',
          location: 'Remote',
          salary: '\$100k - \$130k',
          description:
              'Build scalable backend systems using modern technologies. Work on microservices architecture and cloud infrastructure.',
          requirements: ['Node.js', 'Python', 'AWS', 'Docker'],
          type: 'Full-time',
        ),
        Job(
          id: '4',
          title: 'Product Manager',
          company: 'StartupXYZ',
          location: 'Austin, TX',
          salary: '\$110k - \$140k',
          description:
              'Lead product strategy and work with cross-functional teams to deliver amazing products. Drive product vision and roadmap.',
          requirements: [
            'Product Strategy',
            'Agile',
            'Analytics',
            'Leadership',
          ],
          type: 'Full-time',
        ),
        Job(
          id: '5',
          title: 'DevOps Engineer',
          company: 'InfraSolutions',
          location: 'Seattle, WA',
          salary: '\$115k - \$145k',
          description:
              'Manage and optimize our cloud infrastructure. Implement CI/CD pipelines and ensure system reliability and scalability.',
          requirements: ['Kubernetes', 'Terraform', 'CI/CD', 'Monitoring'],
          type: 'Full-time',
        ),
        Job(
          id: '6',
          title: 'Data Scientist',
          company: 'DataInsights',
          location: 'Boston, MA',
          salary: '\$125k - \$160k',
          description:
              'Analyze complex datasets and build machine learning models. Help drive data-driven decision making across the organization.',
          requirements: ['Python', 'ML', 'SQL', 'Statistics'],
          type: 'Full-time',
        ),
      ];
    });
  }

  void _onSwipe(Job job, bool isLiked) {
    setState(() {
      // Remove the swiped job from the list
      _jobs.removeWhere((j) => j.id == job.id);

      if (isLiked) {
        _likedJobs.add(job);
      } else {
        _passedJobs.add(job);
      }
    });

    // Show feedback
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(
              isLiked ? Icons.favorite_rounded : Icons.check_circle_outline,
              color: Colors.white,
              size: 20,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                isLiked
                    ? 'Saved: ${job.title} at ${job.company}'
                    : 'Passed: ${job.title}',
                style: const TextStyle(fontWeight: FontWeight.w500),
              ),
            ),
          ],
        ),
        duration: const Duration(seconds: 2),
        backgroundColor:
            isLiked ? const Color(0xFF10B981) : const Color(0xFF6B7280),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        margin: const EdgeInsets.all(16),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: isDark ? const Color(0xFF202124) : Colors.white,
      appBar: AppBar(
        title: const Text('JobFinder'),
        elevation: 0,
        backgroundColor: isDark ? const Color(0xFF303134) : Colors.white,
        foregroundColor: isDark ? Colors.white : const Color(0xFF202124),
        surfaceTintColor: Colors.transparent,
        actions: [
          // Profile button
          IconButton(
            icon: Icon(
              _userProfile?.isEmpty ?? true
                  ? Icons.person_outline
                  : Icons.person,
              size: 24,
            ),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder:
                      (context) => UserInfoScreen(
                        initialProfile: _userProfile,
                        onSave: (profile) async {
                          setState(() {
                            _userProfile = profile;
                          });
                          // Save to Firestore via the callback
                          if (widget.onProfileUpdated != null) {
                            await widget.onProfileUpdated!(profile);
                          }
                        },
                      ),
                ),
              );
            },
            tooltip: 'Edit Profile',
          ),
          // Theme toggle button
          IconButton(
            icon: Icon(isDark ? Icons.light_mode : Icons.dark_mode, size: 20),
            onPressed: () {
              widget.onThemeToggle?.call();
            },
            tooltip: isDark ? 'Switch to light mode' : 'Switch to dark mode',
          ),
          Container(
            margin: const EdgeInsets.only(right: 8),
            child: IconButton(
              icon: Stack(
                clipBehavior: Clip.none,
                children: [
                  Icon(
                    Icons.bookmark_border,
                    color:
                        isDark ? Colors.grey.shade400 : const Color(0xFF5F6368),
                    size: 24,
                  ),
                  if (_likedJobs.isNotEmpty)
                    Positioned(
                      right: -6,
                      top: -6,
                      child: Container(
                        padding: const EdgeInsets.all(4),
                        decoration: const BoxDecoration(
                          color: Color(0xFFEA4335),
                          shape: BoxShape.circle,
                        ),
                        constraints: const BoxConstraints(
                          minWidth: 16,
                          minHeight: 16,
                        ),
                        child: Center(
                          child: Text(
                            '${_likedJobs.length}',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 10,
                              fontWeight: FontWeight.w500,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ),
                      ),
                    ),
                ],
              ),
              onPressed: () {
                // Show liked jobs
                showDialog(
                  context: context,
                  builder: (context) {
                    return AlertDialog(
                      backgroundColor:
                          isDark ? const Color(0xFF1E293B) : Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(20),
                      ),
                      title: Text(
                        'Saved Jobs',
                        style: TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 20,
                          color: isDark ? Colors.white : Colors.black87,
                        ),
                      ),
                      content:
                          _likedJobs.isEmpty
                              ? Padding(
                                padding: const EdgeInsets.symmetric(
                                  vertical: 20,
                                ),
                                child: Column(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(
                                      Icons.favorite_border,
                                      size: 48,
                                      color:
                                          isDark
                                              ? Colors.grey.shade500
                                              : Colors.grey.shade400,
                                    ),
                                    const SizedBox(height: 12),
                                    Text(
                                      'No saved jobs yet',
                                      style: TextStyle(
                                        color:
                                            isDark
                                                ? Colors.grey.shade400
                                                : Colors.grey.shade600,
                                        fontSize: 15,
                                      ),
                                    ),
                                  ],
                                ),
                              )
                              : SizedBox(
                                width: double.maxFinite,
                                child: ListView.builder(
                                  shrinkWrap: true,
                                  itemCount: _likedJobs.length,
                                  itemBuilder: (context, index) {
                                    final job = _likedJobs[index];
                                    return Container(
                                      margin: const EdgeInsets.only(bottom: 12),
                                      padding: const EdgeInsets.all(16),
                                      decoration: BoxDecoration(
                                        color:
                                            isDark
                                                ? const Color(0xFF334155)
                                                : Colors.grey.shade50,
                                        borderRadius: BorderRadius.circular(12),
                                        border: Border.all(
                                          color:
                                              isDark
                                                  ? Colors.grey.shade700
                                                  : Colors.grey.shade200,
                                        ),
                                      ),
                                      child: Row(
                                        children: [
                                          Container(
                                            width: 40,
                                            height: 40,
                                            decoration: BoxDecoration(
                                              color: const Color(
                                                0xFF6366F1,
                                              ).withOpacity(0.1),
                                              borderRadius:
                                                  BorderRadius.circular(10),
                                            ),
                                            child: const Icon(
                                              Icons.work_outline,
                                              color: Color(0xFF6366F1),
                                              size: 20,
                                            ),
                                          ),
                                          const SizedBox(width: 12),
                                          Expanded(
                                            child: Column(
                                              crossAxisAlignment:
                                                  CrossAxisAlignment.start,
                                              children: [
                                                Text(
                                                  job.title,
                                                  style: TextStyle(
                                                    fontWeight: FontWeight.w600,
                                                    fontSize: 15,
                                                    color:
                                                        isDark
                                                            ? Colors.white
                                                            : Colors.black87,
                                                  ),
                                                ),
                                                const SizedBox(height: 2),
                                                Text(
                                                  job.company,
                                                  style: TextStyle(
                                                    color:
                                                        isDark
                                                            ? Colors
                                                                .grey
                                                                .shade400
                                                            : Colors
                                                                .grey
                                                                .shade600,
                                                    fontSize: 13,
                                                  ),
                                                ),
                                              ],
                                            ),
                                          ),
                                        ],
                                      ),
                                    );
                                  },
                                ),
                              ),
                      actions: [
                        TextButton(
                          onPressed: () => Navigator.pop(context),
                          style: TextButton.styleFrom(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 24,
                              vertical: 12,
                            ),
                          ),
                          child: Text(
                            'Close',
                            style: TextStyle(
                              fontWeight: FontWeight.w600,
                              color:
                                  isDark
                                      ? Colors.grey.shade300
                                      : Colors.black87,
                            ),
                          ),
                        ),
                      ],
                    );
                  },
                );
              },
            ),
          ),
          // Sign out button
          IconButton(
            icon: const Icon(Icons.logout, size: 20),
            onPressed: () async {
              await AuthService().signOut();
            },
            tooltip: 'Sign Out',
          ),
          const SizedBox(width: 4),
        ],
      ),
      body: Column(
        children: [
          // Card stack area
          Expanded(
            child: SwipeableCardStack(
              key: _cardStackKey,
              jobs: _jobs,
              onSwipe: _onSwipe,
            ),
          ),
        ],
      ),
    );
  }
}
