import 'package:flutter/material.dart';
import '../models/job.dart';
import 'job_card.dart';

class SwipeableCardStack extends StatefulWidget {
  final List<Job> jobs;
  final Function(Job job, bool isLiked)? onSwipe;
  final VoidCallback? onScrapeMore;
  final bool isScraping;

  const SwipeableCardStack({
    super.key,
    required this.jobs,
    this.onSwipe,
    this.onScrapeMore,
    this.isScraping = false,
  });

  @override
  State<SwipeableCardStack> createState() => SwipeableCardStackState();
}

class SwipeableCardStackState extends State<SwipeableCardStack>
    with TickerProviderStateMixin {
  late List<Job> _remainingJobs;
  Offset _position = Offset.zero;
  double _angle = 0;
  bool _isDragging = false;
  
  late AnimationController _swipeController;
  late AnimationController _resetController;
  late Animation<Offset> _swipeAnimation;
  late Animation<double> _swipeRotationAnimation;
  late Animation<double> _swipeOpacityAnimation;
  
  Offset _resetStartPosition = Offset.zero;
  double _resetStartAngle = 0;

  @override
  void initState() {
    super.initState();
    _remainingJobs = List.from(widget.jobs);
    
    // Swipe animation controller
    _swipeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    
    // Reset animation controller with spring physics
    _resetController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 500),
    );
    
    // Swipe animations
    _swipeAnimation = Tween<Offset>(
      begin: Offset.zero,
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _swipeController,
      curve: Curves.easeOutCubic,
    ));
    
    _swipeRotationAnimation = Tween<double>(
      begin: 0,
      end: 0,
    ).animate(CurvedAnimation(
      parent: _swipeController,
      curve: Curves.easeOutCubic,
    ));
    
    _swipeOpacityAnimation = Tween<double>(
      begin: 1.0,
      end: 0.0,
    ).animate(CurvedAnimation(
      parent: _swipeController,
      curve: Curves.easeOut,
    ));
    
    // Reset animation
    _resetController.addListener(() {
      if (_resetController.isAnimating) {
        setState(() {
          final progress = Curves.easeOutCubic.transform(_resetController.value);
          _position = Offset.lerp(_resetStartPosition, Offset.zero, progress)!;
          _angle = _resetStartAngle * (1 - progress);
        });
      }
    });
  }
  
  @override
  void dispose() {
    _swipeController.dispose();
    _resetController.dispose();
    super.dispose();
  }

  void swipeLeft() {
    if (_remainingJobs.isEmpty) return;
    
    _swipeAnimation = Tween<Offset>(
      begin: _position,
      end: const Offset(-600, 0),
    ).animate(CurvedAnimation(
      parent: _swipeController,
      curve: Curves.easeOutCubic,
    ));
    
    _swipeRotationAnimation = Tween<double>(
      begin: _angle,
      end: -25,
    ).animate(CurvedAnimation(
      parent: _swipeController,
      curve: Curves.easeOutCubic,
    ));
    
    _swipeController.forward().then((_) {
      _swipeCard(false);
    });
  }

  void swipeRight() {
    if (_remainingJobs.isEmpty) return;
    
    _swipeAnimation = Tween<Offset>(
      begin: _position,
      end: const Offset(600, 0),
    ).animate(CurvedAnimation(
      parent: _swipeController,
      curve: Curves.easeOutCubic,
    ));
    
    _swipeRotationAnimation = Tween<double>(
      begin: _angle,
      end: 25,
    ).animate(CurvedAnimation(
      parent: _swipeController,
      curve: Curves.easeOutCubic,
    ));
    
    _swipeController.forward().then((_) {
      _swipeCard(true);
    });
  }

  @override
  void didUpdateWidget(SwipeableCardStack oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.jobs != oldWidget.jobs) {
      _remainingJobs = List.from(widget.jobs);
      _position = Offset.zero;
      _angle = 0;
    }
  }

  void _onPanUpdate(DragUpdateDetails details) {
    if (_swipeController.isAnimating || _resetController.isAnimating) return;
    
    setState(() {
      _position += details.delta;
      _angle = _position.dx / 20;
      _isDragging = true;
    });
  }

  void _onPanEnd(DragEndDetails details) {
    if (_swipeController.isAnimating || _resetController.isAnimating) return;
    
    final swipeThreshold = 100.0;
    final isRightSwipe = _position.dx > swipeThreshold;
    final isLeftSwipe = _position.dx < -swipeThreshold;
    final velocity = details.velocity.pixelsPerSecond.dx;

    if (isRightSwipe || (velocity > 500 && _position.dx > 0)) {
      swipeRight();
    } else if (isLeftSwipe || (velocity < -500 && _position.dx < 0)) {
      swipeLeft();
    } else {
      _resetCard();
    }
  }

  void _swipeCard(bool isLiked) {
    if (_remainingJobs.isEmpty) return;

    final swipedJob = _remainingJobs.first;
    widget.onSwipe?.call(swipedJob, isLiked);

    setState(() {
      _remainingJobs.removeAt(0);
      _position = Offset.zero;
      _angle = 0;
      _isDragging = false;
    });
    
    _swipeController.reset();
  }

  void _resetCard() {
    _resetStartPosition = _position;
    _resetStartAngle = _angle;
    _resetController.forward().then((_) {
      setState(() {
        _position = Offset.zero;
        _angle = 0;
        _isDragging = false;
      });
      _resetController.reset();
    });
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    if (_remainingJobs.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 120,
                height: 120,
                decoration: BoxDecoration(
                  color: isDark
                      ? const Color(0xFF334155)
                      : const Color(0xFFF3F4F6),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.search_off_rounded,
                  size: 56,
                  color: isDark
                      ? Colors.grey.shade500
                      : Colors.grey.shade400,
                ),
              ),
              const SizedBox(height: 24),
              Text(
                'No jobs found',
                style: TextStyle(
                  fontSize: 24,
                  color: isDark
                      ? Colors.white
                      : Colors.grey.shade900,
                  fontWeight: FontWeight.w700,
                  letterSpacing: -0.5,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'No jobs match your current preferences.\nTry updating your search settings or scrape for new listings.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 15,
                  color: isDark
                      ? Colors.grey.shade400
                      : Colors.grey.shade600,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 28),
              if (widget.onScrapeMore != null)
                SizedBox(
                  width: 220,
                  height: 48,
                  child: ElevatedButton.icon(
                    onPressed: widget.isScraping ? null : widget.onScrapeMore,
                    icon: widget.isScraping
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(Icons.search, size: 20),
                    label: Text(
                      widget.isScraping ? 'Scraping...' : 'Scrape More Jobs',
                      style: const TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 15,
                      ),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF4285F4),
                      foregroundColor: Colors.white,
                      disabledBackgroundColor: const Color(0xFF4285F4).withOpacity(0.6),
                      disabledForegroundColor: Colors.white70,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(24),
                      ),
                      elevation: 0,
                    ),
                  ),
                ),
            ],
          ),
        ),
      );
    }

    return Stack(
      children: [
        // Background cards - completely hidden to avoid distracting effects
        // Front card (draggable)
        if (_remainingJobs.isNotEmpty)
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: GestureDetector(
              onPanUpdate: _onPanUpdate,
              onPanEnd: _onPanEnd,
              child: AnimatedBuilder(
                animation: Listenable.merge([
                  _swipeController,
                  _resetController,
                ]),
                builder: (context, child) {
                  final currentPosition = _swipeController.isAnimating
                      ? _swipeAnimation.value
                      : _position;
                  final currentAngle = _swipeController.isAnimating
                      ? _swipeRotationAnimation.value
                      : _angle;
                  final currentOpacity = _swipeController.isAnimating
                      ? _swipeOpacityAnimation.value
                      : (_isDragging ? 0.95 : 1.0);
                  
                  return Transform.translate(
                    offset: currentPosition,
                    child: Transform.rotate(
                      angle: currentAngle * 0.0174533, // Convert to radians
                      child: Opacity(
                        opacity: currentOpacity,
                        child: JobCard(
                          job: _remainingJobs.first,
                          angle: currentAngle * 0.0174533,
                          isFront: true,
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
          ),
        // Swipe indicators with cool effects
        if (_isDragging && _remainingJobs.isNotEmpty && !_swipeController.isAnimating)
          Positioned.fill(
            child: Stack(
              children: [
                // Background overlay for like (right)
                if (_position.dx > 0)
                  Positioned.fill(
                    child: Container(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.centerRight,
                          end: Alignment.centerLeft,
                          colors: [
                            const Color(0xFF34A853).withOpacity(
                              (_position.dx / 200).clamp(0.0, 0.12),
                            ),
                            Colors.transparent,
                          ],
                        ),
                      ),
                    ),
                  ),
                // Background overlay for pass (left)
                if (_position.dx < 0)
                  Positioned.fill(
                    child: Container(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.centerLeft,
                          end: Alignment.centerRight,
                          colors: [
                            const Color(0xFFEA4335).withOpacity(
                              (_position.dx.abs() / 200).clamp(0.0, 0.12),
                            ),
                            Colors.transparent,
                          ],
                        ),
                      ),
                    ),
                  ),
                // Like indicator (right) with animated scale and glow
                if (_position.dx > 0)
                  Positioned(
                    top: 60,
                    right: 24,
                    child: Builder(
                      builder: (context) {
                        final value = (_position.dx / 100).clamp(0.0, 1.0);
                        return Transform.scale(
                          scale: 0.8 + (value * 0.2),
                          child: Transform.rotate(
                            angle: -_angle * 0.0174533,
                            child: Opacity(
                              opacity: value.clamp(0.0, 1.0),
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 28,
                                  vertical: 14,
                                ),
                                decoration: BoxDecoration(
                                  color: const Color(0xFF34A853),
                                  borderRadius: BorderRadius.circular(28),
                                  boxShadow: [
                                    BoxShadow(
                                      color: const Color(0xFF34A853)
                                          .withOpacity(0.4 * value),
                                      blurRadius: 12 * value,
                                      spreadRadius: 2 * value,
                                    ),
                                  ],
                                ),
                                child: Icon(
                                  Icons.check,
                                  color: Colors.white,
                                  size: 28 + (value * 4),
                                ),
                              ),
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                // Pass indicator (left) with animated scale and glow
                if (_position.dx < 0)
                  Positioned(
                    top: 60,
                    left: 24,
                    child: Builder(
                      builder: (context) {
                        final value = (_position.dx.abs() / 100).clamp(0.0, 1.0);
                        return Transform.scale(
                          scale: 0.8 + (value * 0.2),
                          child: Transform.rotate(
                            angle: -_angle * 0.0174533,
                            child: Opacity(
                              opacity: value.clamp(0.0, 1.0),
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 28,
                                  vertical: 14,
                                ),
                                decoration: BoxDecoration(
                                  color: const Color(0xFFEA4335),
                                  borderRadius: BorderRadius.circular(28),
                                  boxShadow: [
                                    BoxShadow(
                                      color: const Color(0xFFEA4335)
                                          .withOpacity(0.4 * value),
                                      blurRadius: 12 * value,
                                      spreadRadius: 2 * value,
                                    ),
                                  ],
                                ),
                                child: Icon(
                                  Icons.close,
                                  color: Colors.white,
                                  size: 28 + (value * 4),
                                ),
                              ),
                            ),
                          ),
                        );
                      },
                    ),
                  ),
              ],
            ),
          ),
      ],
    );
  }
}

