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

  /// Add a job ID to the user's saved_jobs array
  Future<void> saveJob(String uid, String jobId) async {
    await _db.collection('users').doc(uid).set({
      'saved_jobs': FieldValue.arrayUnion([jobId]),
    }, SetOptions(merge: true));
  }

  /// Remove a job ID from the user's saved_jobs array
  Future<void> unsaveJob(String uid, String jobId) async {
    await _db.collection('users').doc(uid).update({
      'saved_jobs': FieldValue.arrayRemove([jobId]),
    });
  }

  /// Get the list of saved job IDs for a user
  Future<List<String>> getSavedJobs(String uid) async {
    final doc = await _db.collection('users').doc(uid).get();
    if (doc.exists && doc.data() != null) {
      final data = doc.data()!;
      return List<String>.from(data['saved_jobs'] as List? ?? []);
    }
    return [];
  }
}
