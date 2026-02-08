import 'package:flutter/material.dart';
import '../models/job.dart';
import '../models/user_profile.dart';

class JobCard extends StatelessWidget {
  final Job job;
  final double angle;
  final bool isFront;

  const JobCard({
    super.key,
    required this.job,
    this.angle = 0,
    this.isFront = false,
  });

  Color _getCompanyColor(String company) {
    final hash = company.hashCode;
    final colors = [
      const Color(0xFF4285F4), // Google Blue
      const Color(0xFF34A853), // Google Green
      const Color(0xFFEA4335), // Google Red
      const Color(0xFFFBBC04), // Google Yellow
      const Color(0xFF9AA0A6), // Google Gray
      const Color(0xFF1A73E8), // Google Blue Dark
    ];
    return colors[hash.abs() % colors.length];
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

  Widget _buildLogo(Color companyColor) {
    if (job.logo == null || job.logo!.isEmpty) {
      debugPrint('[JobCard] No logo URL for ${job.company}: logo=${job.logo}');
      return Icon(
        Icons.business_outlined,
        color: companyColor,
        size: 24,
      );
    }

    final logoUrl = job.logo!;
    debugPrint('[JobCard] Attempting to load logo for ${job.company}');
    debugPrint('[JobCard] URL: $logoUrl');

    return Image.network(
      logoUrl,
      width: 48,
      height: 48,
      fit: BoxFit.cover,
      loadingBuilder: (context, child, loadingProgress) {
        if (loadingProgress == null) {
          debugPrint('[JobCard] ✓ Logo loaded successfully for ${job.company}');
          return child;
        }
        final progress = loadingProgress.expectedTotalBytes != null
            ? (loadingProgress.cumulativeBytesLoaded / loadingProgress.expectedTotalBytes! * 100).toStringAsFixed(0)
            : '?';
        debugPrint('[JobCard] Loading ${job.company} logo: $progress%');
        return Center(
          child: CircularProgressIndicator(
            strokeWidth: 2,
            value: loadingProgress.expectedTotalBytes != null
                ? loadingProgress.cumulativeBytesLoaded / loadingProgress.expectedTotalBytes!
                : null,
          ),
        );
      },
      errorBuilder: (context, error, stackTrace) {
        debugPrint('[JobCard] ✗ Logo FAILED for ${job.company}');
        debugPrint('[JobCard]   URL: $logoUrl');
        debugPrint('[JobCard]   Error type: ${error.runtimeType}');
        debugPrint('[JobCard]   Error: $error');
        if (error.toString().contains('CORS') ||
            error.toString().contains('XMLHttpRequest') ||
            error.toString().contains('NetworkError')) {
          debugPrint('[JobCard]   ⚠️  This appears to be a CORS error. Try running with:');
          debugPrint('[JobCard]       flutter run -d chrome --web-browser-flag "--disable-web-security"');
        }
        return Icon(
          Icons.business_outlined,
          color: companyColor,
          size: 24,
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final companyColor = _getCompanyColor(job.company);
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Transform.rotate(
      angle: angle,
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        decoration: BoxDecoration(
          color: isDark ? const Color(0xFF303134) : Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isDark
                ? Colors.grey.shade800
                : Colors.grey.shade300,
            width: 1,
          ),
          boxShadow: [
            BoxShadow(
              color: isDark
                  ? Colors.black.withOpacity(0.2)
                  : Colors.black.withOpacity(0.04),
              blurRadius: 8,
              spreadRadius: 0,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header section with company branding
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 24, 24, 16),
              child: Row(
                children: [
                  // Company logo
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      color: companyColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    clipBehavior: Clip.antiAlias,
                    child: _buildLogo(companyColor),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          job.company,
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w400,
                            color: isDark
                                ? Colors.grey.shade300
                                : const Color(0xFF5F6368),
                            letterSpacing: 0,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          job.type,
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w400,
                            color: isDark
                                ? Colors.grey.shade500
                                : const Color(0xFF80868B),
                            letterSpacing: 0,
                          ),
                        ),
                      ],
                    ),
                  ),
                  // Date posted
                  if (job.datePosted != null)
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        color: isDark
                            ? Colors.grey.shade800.withOpacity(0.5)
                            : Colors.grey.shade100,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        _formatDate(job.datePosted!),
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w500,
                          color: isDark
                              ? Colors.grey.shade400
                              : const Color(0xFF5F6368),
                          letterSpacing: 0,
                        ),
                      ),
                    ),
                ],
              ),
            ),
            // Job details
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Job title
                  Text(
                    job.title,
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.w400,
                      color: isDark
                          ? Colors.white
                          : const Color(0xFF202124),
                      letterSpacing: 0,
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 16),
                  // Location and salary row
                  Wrap(
                    spacing: 16,
                    runSpacing: 12,
                    children: [
                      _InfoChip(
                        icon: Icons.location_on_outlined,
                        text: job.location,
                        color: isDark
                            ? Colors.grey.shade400
                            : const Color(0xFF5F6368),
                      ),
                      _InfoChip(
                        icon: Icons.attach_money_outlined,
                        text: job.salary,
                        color: const Color(0xFF34A853),
                        isHighlighted: true,
                      ),
                      if (job.category != null && job.category!.isNotEmpty)
                        _InfoChip(
                          icon: Icons.category_outlined,
                          text: UserProfile.categoryLabel(job.category!),
                          color: const Color(0xFF4285F4),
                        ),
                    ],
                  ),
                  const SizedBox(height: 20),
                  // Description
                  Text(
                    job.description,
                    style: TextStyle(
                      fontSize: 14,
                      color: isDark
                          ? Colors.grey.shade400
                          : const Color(0xFF5F6368),
                      height: 1.5,
                      letterSpacing: 0,
                    ),
                    maxLines: 3,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 20),
                  // Requirements tags
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: job.requirements.take(4).map((req) {
                      return Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          color: isDark
                              ? Colors.grey.shade800.withOpacity(0.5)
                              : Colors.grey.shade100,
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: Text(
                          req,
                          style: TextStyle(
                            fontSize: 12,
                            color: isDark
                                ? Colors.grey.shade300
                                : const Color(0xFF5F6368),
                            fontWeight: FontWeight.w400,
                            letterSpacing: 0,
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _InfoChip extends StatelessWidget {
  final IconData icon;
  final String text;
  final Color color;
  final bool isHighlighted;

  const _InfoChip({
    required this.icon,
    required this.text,
    required this.color,
    this.isHighlighted = false,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          icon,
          size: 18,
          color: color,
        ),
        const SizedBox(width: 8),
        Flexible(
          child: Text(
            text,
            style: TextStyle(
              fontSize: 14,
              color: color,
              fontWeight: FontWeight.w400,
              letterSpacing: 0,
            ),
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }
}

