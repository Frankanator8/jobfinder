import 'package:flutter/material.dart';
import '../models/job.dart';
import '../models/user_profile.dart';
import '../services/job_service.dart';
import '../widgets/swipeable_card_stack.dart';
import 'user_info_screen.dart';

class JobSwipeScreen extends StatefulWidget {
  final VoidCallback? onThemeToggle;
  
  const JobSwipeScreen({super.key, this.onThemeToggle});

  @override
  State<JobSwipeScreen> createState() => _JobSwipeScreenState();
}

class _JobSwipeScreenState extends State<JobSwipeScreen> {
  List<Job> _jobs = [];
  List<Job> _likedJobs = [];
  List<Job> _passedJobs = [];
  final Set<String> _seenJobIds = {};
  UserProfile? _userProfile;
  bool _isLoading = true;
  bool _isLoadingMore = false;
  bool _allJobsExhausted = false;
  String? _errorMessage;
  int _offset = 0;
  static const int _batchSize = 10;
  final GlobalKey<SwipeableCardStackState> _cardStackKey =
      GlobalKey<SwipeableCardStackState>();

  @override
  void initState() {
    super.initState();
    _loadJobs();
  }

  Future<void> _loadJobs() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final jobs = await JobService.fetchJobs(limit: _batchSize, offset: 0);
      final newJobs = jobs.where((j) => !_seenJobIds.contains(j.id)).toList();
      setState(() {
        _jobs = newJobs;
        _seenJobIds.addAll(newJobs.map((j) => j.id));
        _offset = jobs.length;
        _allJobsExhausted = jobs.isEmpty;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _errorMessage = 'Could not load jobs. Is the backend running?';
      });
    }
  }

  Future<void> _loadMoreJobs() async {
    setState(() {
      _isLoadingMore = true;
    });

    try {
      final moreJobs = await JobService.fetchJobs(limit: _batchSize, offset: _offset);
      final newJobs = moreJobs.where((j) => !_seenJobIds.contains(j.id)).toList();
      setState(() {
        _offset += moreJobs.length;
        if (moreJobs.isEmpty) {
          _allJobsExhausted = true;
        } else {
          _jobs = newJobs;
          _seenJobIds.addAll(newJobs.map((j) => j.id));
          // If every returned job was already seen, we're also exhausted
          if (newJobs.isEmpty) _allJobsExhausted = true;
        }
        _isLoadingMore = false;
      });
    } catch (e) {
      setState(() {
        _isLoadingMore = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('Failed to load more jobs'),
            backgroundColor: Colors.red.shade400,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            margin: const EdgeInsets.all(16),
          ),
        );
      }
    }
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
                style: const TextStyle(
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ],
        ),
        duration: const Duration(seconds: 2),
        backgroundColor: isLiked ? const Color(0xFF10B981) : const Color(0xFF6B7280),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
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
                  builder: (context) => UserInfoScreen(
                    initialProfile: _userProfile,
                    onSave: (profile) {
                      setState(() {
                        _userProfile = profile;
                      });
                    },
                  ),
                ),
              );
            },
            tooltip: 'Edit Profile',
          ),
          // Theme toggle button
          IconButton(
            icon: Icon(
              isDark ? Icons.light_mode : Icons.dark_mode,
              size: 20,
            ),
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
                    color: isDark
                        ? Colors.grey.shade400
                        : const Color(0xFF5F6368),
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
                      backgroundColor: isDark ? const Color(0xFF1E293B) : Colors.white,
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
                      content: _likedJobs.isEmpty
                          ? Padding(
                              padding: const EdgeInsets.symmetric(vertical: 20),
                              child: Column(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(
                                    Icons.favorite_border,
                                    size: 48,
                                    color: isDark
                                        ? Colors.grey.shade500
                                        : Colors.grey.shade400,
                                  ),
                                  const SizedBox(height: 12),
                                  Text(
                                    'No saved jobs yet',
                                    style: TextStyle(
                                      color: isDark
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
                                      color: isDark
                                          ? const Color(0xFF334155)
                                          : Colors.grey.shade50,
                                      borderRadius: BorderRadius.circular(12),
                                      border: Border.all(
                                        color: isDark
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
                                            color: const Color(0xFF6366F1)
                                                .withOpacity(0.1),
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
                                                  color: isDark
                                                      ? Colors.white
                                                      : Colors.black87,
                                                ),
                                              ),
                                              const SizedBox(height: 2),
                                              Text(
                                                job.company,
                                                style: TextStyle(
                                                  color: isDark
                                                      ? Colors.grey.shade400
                                                      : Colors.grey.shade600,
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
                              color: isDark
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
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(32),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.cloud_off_rounded,
                          size: 64,
                          color: isDark ? Colors.grey.shade500 : Colors.grey.shade400,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          _errorMessage!,
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: isDark ? Colors.grey.shade400 : Colors.grey.shade600,
                            fontSize: 16,
                          ),
                        ),
                        const SizedBox(height: 24),
                        ElevatedButton.icon(
                          onPressed: _loadJobs,
                          icon: const Icon(Icons.refresh),
                          label: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                )
              : Column(
                  children: [
                    // Card stack area
                    Expanded(
                      child: SwipeableCardStack(
                        key: _cardStackKey,
                        jobs: _jobs,
                        onSwipe: _onSwipe,
                        onLoadMore: _allJobsExhausted ? null : _loadMoreJobs,
                        isLoadingMore: _isLoadingMore,
                        allJobsExhausted: _allJobsExhausted,
                      ),
                    ),
                  ],
                ),
    );
  }
}


