import 'package:cloud_firestore/cloud_firestore.dart';

class QueueService {
  static final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  /// Add a job to the queue collection.
  ///
  /// [applicationId] – the ID of the job application.
  /// [applicantId] – the ID of the current user/applicant.
  ///
  /// Returns the document ID of the created queue entry.
  static Future<String> addToQueue({
    required String applicationId,
    required String applicantId,
  }) async {
    final docRef = await _firestore.collection('queue').add({
      'application_id': applicationId,
      'applicant_id': applicantId,
      'created_at': FieldValue.serverTimestamp(),
    });
    return docRef.id;
  }

  /// Remove a job from the queue collection.
  ///
  /// [applicationId] – the ID of the job application.
  /// [applicantId] – the ID of the current user/applicant.
  static Future<void> removeFromQueue({
    required String applicationId,
    required String applicantId,
  }) async {
    final snapshot = await _firestore
        .collection('queue')
        .where('application_id', isEqualTo: applicationId)
        .where('applicant_id', isEqualTo: applicantId)
        .get();

    for (final doc in snapshot.docs) {
      await doc.reference.delete();
    }
  }

  /// Check if a job is already in the queue for the user.
  static Future<bool> isInQueue({
    required String applicationId,
    required String applicantId,
  }) async {
    final snapshot = await _firestore
        .collection('queue')
        .where('application_id', isEqualTo: applicationId)
        .where('applicant_id', isEqualTo: applicantId)
        .limit(1)
        .get();

    return snapshot.docs.isNotEmpty;
  }
}
