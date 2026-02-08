import 'dart:async';
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
  final List<String> savedJobIds;
  final Function(UserProfile)? onProfileUpdated;
  final Function(String jobId)? onJobSaved;

  const JobSwipeScreen({
    super.key,
    this.onThemeToggle,
    this.userProfile,
    this.savedJobIds = const [],
    this.onProfileUpdated,
    this.onJobSaved,
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
  String? _errorMessage;
  final GlobalKey<SwipeableCardStackState> _cardStackKey =
      GlobalKey<SwipeableCardStackState>();

  // Queue tracking
  final Map<String, QueueItem> _trackedQueueItems = {};
  final Map<String, String> _jobTitlesForQueue = {}; // docId -> job title
  Timer? _queueStatusTimer;
  StreamSubscription<List<QueueItem>>? _queueSubscription;

  @override
  void initState() {
    super.initState();
    _userProfile = widget.userProfile;
    _loadJobs();
    _setupQueueTracking();
  }

  @override
  void dispose() {
    _queueStatusTimer?.cancel();
    _queueSubscription?.cancel();
    super.dispose();
  }

  void _setupQueueTracking() {
    final currentUser = AuthService().currentUser;
    if (currentUser != null) {
      debugPrint('[Queue] Setting up queue tracking for user: ${currentUser.uid}');
      // Use Firestore stream for real-time updates
      _queueSubscription = QueueService.streamQueueItemsForUser(currentUser.uid)
          .listen((items) {
        debugPrint('[Queue] Received ${items.length} queue items from stream');
        setState(() {
          for (final item in items) {
            final oldItem = _trackedQueueItems[item.docId];
            _trackedQueueItems[item.docId] = item;

            // Log status changes
            if (oldItem == null) {
              debugPrint('[Queue] New item detected: ${item.docId} (status: ${item.status})');
            } else if (oldItem.status != item.status) {
              debugPrint('[Queue] Status changed for ${item.docId}: ${oldItem.status} → ${item.status}');
            }

            // Check if status changed to terminal state
            if (oldItem != null && !oldItem.isTerminal && item.isTerminal) {
              // Status just changed to completed or failed
              _showQueueStatusNotification(item);
              // Delete the entry from the queue after a short delay to allow UI to show final state
              _deleteQueueItemAfterDelay(item.docId);
            }
          }

          // Remove items that are no longer in the queue
          _trackedQueueItems.removeWhere((docId, item) =>
              !items.any((i) => i.docId == docId));
        });
      });
    } else {
      debugPrint('[Queue] No current user, skipping queue tracking setup');
    }
  }

  void _deleteQueueItemAfterDelay(String docId) {
    final jobTitle = _jobTitlesForQueue[docId] ?? 'Unknown job';
    debugPrint('[Queue] Scheduling deletion for $docId ($jobTitle) in 3 seconds...');
    // Wait 3 seconds to show the final status, then delete
    Future.delayed(const Duration(seconds: 3), () async {
      try {
        debugPrint('[Queue] Deleting queue item: $docId ($jobTitle)');
        await QueueService.removeFromQueueByDocId(docId);
        debugPrint('[Queue] ✓ Successfully deleted queue item: $docId');
        // Clean up local tracking
        setState(() {
          _trackedQueueItems.remove(docId);
          _jobTitlesForQueue.remove(docId);
        });
        debugPrint('[Queue] Cleaned up local tracking for: $docId');
      } catch (e) {
        debugPrint('[Queue] ✗ Failed to delete queue item $docId: $e');
      }
    });
  }

  void _showQueueStatusNotification(QueueItem item) {
    final jobTitle = _jobTitlesForQueue[item.docId] ?? 'Unknown job';
    if (item.isCompleted) {
      debugPrint('[Queue] ✓ Application COMPLETED: ${item.docId} ($jobTitle)');
    } else if (item.isFailed) {
      debugPrint('[Queue] ✗ Application FAILED: ${item.docId} ($jobTitle) - Error: ${item.error}');
    }
  }

  void _loadJobs() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final jobs = await JobService.fetchAllJobs();
      final savedIds = widget.savedJobIds.toSet();

      // Separate into previously saved jobs and unseen jobs
      final savedJobs = <Job>[];
      final unseenJobs = <Job>[];
      for (final job in jobs) {
        if (savedIds.contains(job.id)) {
          savedJobs.add(job);
        } else {
          unseenJobs.add(job);
        }
      }

      setState(() {
        _likedJobs = savedJobs;
        _jobs = unseenJobs;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to load jobs: $e';
        _isLoading = false;
      });
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
      // Remove the swiped job from the list
      _jobs.removeWhere((j) => j.id == job.id);

      if (isLiked) {
        _likedJobs.add(job);
      } else {
        _passedJobs.add(job);
      }
    });

    // Add to queue and save to Firestore if liked
    if (isLiked) {
      final currentUser = AuthService().currentUser;
      if (currentUser != null) {
        try {
          final docId = await QueueService.addToQueue(
            applicationId: job.id,
            applicantId: currentUser.uid,
          );
          // Track the job title for this queue item
          _jobTitlesForQueue[docId] = '${job.title} at ${job.company}';
          debugPrint('[Queue] Added job ${job.id} to queue for user ${currentUser.uid}, docId: $docId');
        } catch (e) {
          debugPrint('[Queue] Failed to add to queue: $e');
        }
      }
      // Save job ID to user's saved_jobs in Firestore
      widget.onJobSaved?.call(job.id);
    }
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
                                              ).withValues(alpha: 0.1),
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
      body: Stack(
        children: [
          _isLoading
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
                          ),
                        ),
                      ],
                    ),
          // Queue status notification overlay
          _buildQueueStatusOverlay(isDark),
        ],
      ),
    );
  }

  Widget _buildQueueStatusOverlay(bool isDark) {
    // Show all tracked queue items including terminal states
    final activeItems = _trackedQueueItems.values.toList();

    if (activeItems.isEmpty) {
      return const SizedBox.shrink();
    }

    return Positioned(
      left: 16,
      bottom: 16,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: activeItems.map((item) => _buildQueueItemCard(item, isDark)).toList(),
      ),
    );
  }

  Widget _buildQueueItemCard(QueueItem item, bool isDark) {
    final jobTitle = _jobTitlesForQueue[item.docId] ?? 'Job Application';

    IconData icon;
    Color color;
    String statusText;

    if (item.isProcessing) {
      icon = Icons.hourglass_empty;
      color = const Color(0xFF4285F4); // Blue
      statusText = 'Processing...';
    } else if (item.isCompleted) {
      icon = Icons.check_circle;
      color = const Color(0xFF10B981); // Green
      statusText = 'Completed';
    } else if (item.isFailed) {
      icon = Icons.error;
      color = const Color(0xFFEF4444); // Red
      statusText = 'Failed';
    } else {
      // pending
      icon = Icons.schedule;
      color = const Color(0xFFF59E0B); // Amber
      statusText = 'In Queue';
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      constraints: const BoxConstraints(maxWidth: 280),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF303134) : Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.15),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
        border: Border.all(
          color: isDark ? Colors.grey.shade700 : Colors.grey.shade200,
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (item.isPending || item.isProcessing)
            SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation<Color>(color),
              ),
            )
          else
            Icon(icon, color: color, size: 20),
          const SizedBox(width: 10),
          Flexible(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  jobTitle,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: isDark ? Colors.white : Colors.black87,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2),
                Text(
                  statusText,
                  style: TextStyle(
                    fontSize: 11,
                    color: color,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
