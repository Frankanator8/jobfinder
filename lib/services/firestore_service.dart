import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/user_profile.dart';

class FirestoreService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  /// Save a user profile to Firestore under the user's UID
  Future<void> saveUserProfile(String uid, UserProfile profile) async {
    await _db
        .collection('users')
        .doc(uid)
        .set(profile.toMap(), SetOptions(merge: true));
  }

  /// Load a user profile from Firestore by UID
  Future<UserProfile?> getUserProfile(String uid) async {
    final doc = await _db.collection('users').doc(uid).get();
    if (doc.exists && doc.data() != null) {
      return UserProfile.fromMap(doc.data()!);
    }
    return null;
  }

  /// Check if a user has completed their profile
  Future<bool> hasCompletedProfile(String uid) async {
    final profile = await getUserProfile(uid);
    if (profile == null) return false;
    // A profile is considered complete if at least name and email are filled
    return profile.name.isNotEmpty && profile.email.isNotEmpty;
  }
}
