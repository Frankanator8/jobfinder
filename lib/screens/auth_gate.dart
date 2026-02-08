import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../services/firestore_service.dart';
import '../models/user_profile.dart';
import 'sign_in_screen.dart';
import 'user_info_screen.dart';
import 'job_swipe_screen.dart';

/// AuthGate manages the authentication flow:
/// 1. Not signed in → SignInScreen (email/password)
/// 2. Signed in but no profile → UserInfoScreen (must complete profile)
/// 3. Signed in with profile → JobSwipeScreen (main app)
class AuthGate extends StatefulWidget {
  final VoidCallback? onThemeToggle;

  const AuthGate({super.key, this.onThemeToggle});

  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  final AuthService _authService = AuthService();
  final FirestoreService _firestoreService = FirestoreService();

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<User?>(
      stream: _authService.authStateChanges,
      builder: (context, snapshot) {
        // Show loading while checking auth state
        if (snapshot.connectionState == ConnectionState.waiting) {
          return _buildLoadingScreen();
        }

        // Not signed in → show sign-in screen
        if (!snapshot.hasData || snapshot.data == null) {
          return const SignInScreen();
        }

        // Signed in → check if profile is complete
        final user = snapshot.data!;
        return FutureBuilder<bool>(
          future: _firestoreService.hasCompletedProfile(user.uid),
          builder: (context, profileSnapshot) {
            if (profileSnapshot.connectionState == ConnectionState.waiting) {
              return _buildLoadingScreen();
            }

            final hasProfile = profileSnapshot.data ?? false;

            if (!hasProfile) {
              // Profile not complete → show profile setup screen
              return _buildProfileSetupScreen(user);
            }

            // Profile complete → show main app
            return _buildMainApp(user);
          },
        );
      },
    );
  }

  Widget _buildLoadingScreen() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Scaffold(
      backgroundColor: isDark ? const Color(0xFF202124) : Colors.white,
      body: const Center(
        child: CircularProgressIndicator(color: Color(0xFF4285F4)),
      ),
    );
  }

  Widget _buildProfileSetupScreen(User user) {
    // Pre-fill with account email
    final initialProfile = UserProfile(email: user.email ?? '');

    return UserInfoScreen(
      initialProfile: initialProfile,
      isInitialSetup: true,
      onSave: (profile) async {
        await _firestoreService.saveUserProfile(user.uid, profile);
        if (mounted) {
          setState(() {}); // Trigger rebuild to move to main app
        }
      },
    );
  }

  Widget _buildMainApp(User user) {
    return _MainAppWithProfile(
      user: user,
      firestoreService: _firestoreService,
      onThemeToggle: widget.onThemeToggle,
    );
  }
}

/// Loads the user profile from Firestore and passes it to JobSwipeScreen
class _MainAppWithProfile extends StatefulWidget {
  final User user;
  final FirestoreService firestoreService;
  final VoidCallback? onThemeToggle;

  const _MainAppWithProfile({
    required this.user,
    required this.firestoreService,
    this.onThemeToggle,
  });

  @override
  State<_MainAppWithProfile> createState() => _MainAppWithProfileState();
}

class _MainAppWithProfileState extends State<_MainAppWithProfile> {
  UserProfile? _userProfile;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    final profile = await widget.firestoreService.getUserProfile(
      widget.user.uid,
    );
    if (mounted) {
      setState(() {
        _userProfile = profile;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      final isDark = Theme.of(context).brightness == Brightness.dark;
      return Scaffold(
        backgroundColor: isDark ? const Color(0xFF202124) : Colors.white,
        body: const Center(
          child: CircularProgressIndicator(color: Color(0xFF4285F4)),
        ),
      );
    }

    return JobSwipeScreen(
      onThemeToggle: widget.onThemeToggle,
      userProfile: _userProfile,
      onProfileUpdated: (profile) async {
        await widget.firestoreService.saveUserProfile(widget.user.uid, profile);
        setState(() {
          _userProfile = profile;
        });
      },
    );
  }
}
