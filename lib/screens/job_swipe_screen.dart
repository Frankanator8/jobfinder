import 'package:flutter/material.dart';
import '../models/job.dart';
import '../models/user_profile.dart';
import '../services/auth_service.dart';
import '../services/job_service.dart';
import '../services/queue_service.dart';
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
  bool _isLoading = true;
  bool _isLoadingMore = false;
  String? _errorMessage;
  final Set<String> _seenJobIds = {};
  GlobalKey<SwipeableCardStackState> _cardStackKey =
      GlobalKey<SwipeableCardStackState>();

  @override
  void initState() {
    super.initState();
    _userProfile = widget.userProfile;
    _loadJobs();
  }

  /// The currently active category filter from user preferences.
  String? get _activeCategory {
    final cat = _userProfile?.category;
    return (cat != null && cat.isNotEmpty) ? cat : null;
  }

  /// The currently active location filter from user preferences.
  String? get _activeLocation {
    final loc = _userProfile?.searchLocation;
    return (loc != null && loc.isNotEmpty) ? loc : null;
  }

  /// The currently active max-age filter (hours) from user preferences.
  int? get _activeHoursOld {
    final h = _userProfile?.hoursOld;
    return (h != null && h > 0) ? h : null;
  }

  void _loadJobs() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      debugPrint('[_loadJobs] Filters → category: $_activeCategory, location: $_activeLocation, hoursOld: $_activeHoursOld');
      final jobs = await JobService.fetchAllJobs(
        category: _activeCategory,
        location: _activeLocation,
        hoursOld: _activeHoursOld,
      );
      debugPrint('[_loadJobs] Fetched ${jobs.length} jobs from Firestore (after filters)');
      // Filter out already-seen jobs
      final newJobs = jobs.where((j) => !_seenJobIds.contains(j.id)).toList();
      debugPrint('[_loadJobs] After dedup: ${newJobs.length} jobs (${_seenJobIds.length} seen)');
      setState(() {
        _jobs = newJobs;
        _isLoading = false;
        // Force card stack to rebuild with fresh data
        _cardStackKey = GlobalKey<SwipeableCardStackState>();
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to load jobs: $e';
        _isLoading = false;
      });
    }
  }

  /// Manually triggered by the user to scrape new jobs from the backend.
  Future<void> _scrapeMoreJobs() async {
    if (_isLoadingMore) return;

    setState(() {
      _isLoadingMore = true;
    });

    try {
      // Build scrape params from user preferences
      final profile = _userProfile;
      final category = _activeCategory ?? 'software_engineering';
      final location = (profile != null && profile.searchLocation.isNotEmpty)
          ? profile.searchLocation
          : 'New York, NY';
      final sites = (profile != null && profile.searchSites.isNotEmpty)
          ? profile.searchSites.join(',')
          : 'indeed,linkedin,zip_recruiter,google';
      final hoursOld = profile?.hoursOld ?? 72;

      // Ask the backend to scrape 20 new jobs
      final result = await JobService.scrapeJobs(
        category: category,
        location: location,
        sites: sites,
        hoursOld: hoursOld,
        resultsWanted: 20,
      );

      // Always reload from Firestore after scrape attempt —
      // even a "failed" scrape may have stored partial results.
      final jobs = await JobService.fetchAllJobsFromServer(
        category: _activeCategory,
        location: _activeLocation,
        hoursOld: _activeHoursOld,
      );
      final newJobs = jobs.where((j) => !_seenJobIds.contains(j.id)).toList();
      debugPrint('[Scrape] Reload complete: ${newJobs.length} unseen jobs');

      setState(() {
        _jobs = newJobs;
        _isLoadingMore = false;
        // Force the card stack to rebuild with the fresh job list
        _cardStackKey = GlobalKey<SwipeableCardStackState>();
      });

      if (mounted) {
        if (result != null) {
          final saved = result['jobs_saved'] ?? 0;
          final updated = result['jobs_updated'] ?? 0;
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Found $saved new jobs${updated > 0 ? ', updated $updated' : ''}'),
              backgroundColor: saved > 0 ? Colors.green.shade600 : Colors.orange.shade600,
              behavior: SnackBarBehavior.floating,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              margin: const EdgeInsets.all(16),
              duration: const Duration(seconds: 3),
            ),
          );
        }// else {
        //   ScaffoldMessenger.of(context).showSnackBar(
        //     SnackBar(
        //       content: const Text('Scrape failed — showing cached results. Is the backend running?'),
        //       backgroundColor: Colors.red.shade600,
        //       behavior: SnackBarBehavior.floating,
        //       shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        //       margin: const EdgeInsets.all(16),
        //     ),
        //   );
        // }
      }
    } catch (e) {
      debugPrint('[JobSwipeScreen] Scrape error: $e');
      setState(() {
        _isLoadingMore = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Scrape error: $e'),
            backgroundColor: Colors.red.shade600,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            margin: const EdgeInsets.all(16),
          ),
        );
      }
    }
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);

    if (difference.inDays == 0) {
      return 'Today';
    } else if (difference.inDays == 1) {
      return 'Yesterday';
    } else if (difference.inDays < 7) {
      return '${difference.inDays}d ago';
    } else if (difference.inDays < 30) {
      final weeks = (difference.inDays / 7).floor();
      return '${weeks}w ago';
    } else if (difference.inDays < 365) {
      final months = (difference.inDays / 30).floor();
      return '${months}mo ago';
    } else {
      final years = (difference.inDays / 365).floor();
      return '${years}y ago';
    }
  }

  void _onSwipe(Job job, bool isLiked) async {
    setState(() {
      // Track this job as seen so we don't show it again
      _seenJobIds.add(job.id);
      // Remove the swiped job from the list
      _jobs.removeWhere((j) => j.id == job.id);

      if (isLiked) {
        _likedJobs.add(job);
      } else {
        _passedJobs.add(job);
      }
    });

    // Add to queue if liked
    if (isLiked) {
      final currentUser = AuthService().currentUser;
      if (currentUser != null) {
        try {
          await QueueService.addToQueue(
            applicationId: job.id,
            applicantId: currentUser.uid,
          );
          debugPrint('[Queue] Added job ${job.id} to queue for user ${currentUser.uid}');
        } catch (e) {
          debugPrint('[Queue] Failed to add to queue: $e');
        }
      }
    }

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
                          final oldCategory = _userProfile?.category;
                          final oldSearchLocation = _userProfile?.searchLocation;
                          final oldSites = _userProfile?.searchSites.join(',');
                          final oldHoursOld = _userProfile?.hoursOld;

                          setState(() {
                            _userProfile = profile;
                          });
                          // Save to Firestore via the callback
                          if (widget.onProfileUpdated != null) {
                            await widget.onProfileUpdated!(profile);
                          }

                          // Check if search preferences changed — if so, reload jobs
                          final prefsChanged =
                              profile.category != oldCategory ||
                              profile.searchLocation != oldSearchLocation ||
                              profile.searchSites.join(',') != oldSites ||
                              profile.hoursOld != oldHoursOld;

                          if (prefsChanged) {
                            // Clear seen jobs so we get a fresh set for new preferences
                            _seenJobIds.clear();
                            _loadJobs();
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
                                            clipBehavior: Clip.antiAlias,
                                            child: job.logo != null && job.logo!.isNotEmpty
                                                ? Image.network(
                                                    job.logo!,
                                                    width: 40,
                                                    height: 40,
                                                    fit: BoxFit.cover,
                                                    errorBuilder: (context, error, stackTrace) =>
                                                        const Icon(
                                                          Icons.work_outline,
                                                          color: Color(0xFF6366F1),
                                                          size: 20,
                                                        ),
                                                  )
                                                : const Icon(
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
                                                if (job.type.isNotEmpty) ...[
                                                  const SizedBox(height: 4),
                                                  Container(
                                                    padding: const EdgeInsets.symmetric(
                                                      horizontal: 8,
                                                      vertical: 2,
                                                    ),
                                                    decoration: BoxDecoration(
                                                      color: isDark
                                                          ? Colors.grey.shade700
                                                          : Colors.grey.shade200,
                                                      borderRadius: BorderRadius.circular(8),
                                                    ),
                                                    child: Text(
                                                      job.type,
                                                      style: TextStyle(
                                                        fontSize: 11,
                                                        fontWeight: FontWeight.w500,
                                                        color: isDark
                                                            ? Colors.grey.shade300
                                                            : Colors.grey.shade700,
                                                      ),
                                                    ),
                                                  ),
                                                ],
                                              ],
                                            ),
                                          ),
                                          if (job.datePosted != null)
                                            Text(
                                              _formatDate(job.datePosted!),
                                              style: TextStyle(
                                                fontSize: 11,
                                                color: isDark
                                                    ? Colors.grey.shade500
                                                    : Colors.grey.shade500,
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
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.error_outline,
                        size: 48,
                        color: Colors.red.shade400,
                      ),
                      const SizedBox(height: 16),
                      Text(
                        _errorMessage!,
                        textAlign: TextAlign.center,
                        style: TextStyle(color: Colors.grey.shade600),
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadJobs,
                        child: const Text('Retry'),
                      ),
                    ],
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
                        onScrapeMore: _scrapeMoreJobs,
                        isScraping: _isLoadingMore,
                      ),
                    ),
                  ],
                ),
    );
  }
}
