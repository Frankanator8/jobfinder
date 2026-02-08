import 'package:cloud_firestore/cloud_firestore.dart';

/// Represents a queue item with its status
class QueueItem {
  final String docId;
  final String applicationId;
  final String applicantId;
  final String status;
  final String? error;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  QueueItem({
    required this.docId,
    required this.applicationId,
    required this.applicantId,
    required this.status,
    this.error,
    this.createdAt,
    this.updatedAt,
  });

  factory QueueItem.fromFirestore(String docId, Map<String, dynamic> data) {
    return QueueItem(
      docId: docId,
      applicationId: data['application_id'] ?? '',
      applicantId: data['applicant_id'] ?? '',
      status: data['status'] ?? 'pending',
      error: data['error'],
      createdAt: (data['created_at'] as Timestamp?)?.toDate(),
      updatedAt: (data['updated_at'] as Timestamp?)?.toDate(),
    );
  }

  bool get isPending => status == 'pending';
  bool get isProcessing => status == 'processing';
  bool get isCompleted => status == 'completed';
  bool get isFailed => status == 'failed';
  bool get isTerminal => isCompleted || isFailed;
}

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
      'status': 'pending',
      'created_at': FieldValue.serverTimestamp(),
    });
    return docRef.id;
  }

  /// Get a queue item by document ID
  static Future<QueueItem?> getQueueItem(String docId) async {
    final doc = await _firestore.collection('queue').doc(docId).get();
    if (doc.exists && doc.data() != null) {
      return QueueItem.fromFirestore(doc.id, doc.data()!);
    }
    return null;
  }

  /// Get all queue items for a user
  static Future<List<QueueItem>> getQueueItemsForUser(String applicantId) async {
    final snapshot = await _firestore
        .collection('queue')
        .where('applicant_id', isEqualTo: applicantId)
        .get();

    final items = snapshot.docs
        .map((doc) => QueueItem.fromFirestore(doc.id, doc.data()))
        .toList();

    // Sort by created_at descending (newest first) in Dart to avoid needing a composite index
    items.sort((a, b) {
      if (a.createdAt == null && b.createdAt == null) return 0;
      if (a.createdAt == null) return 1;
      if (b.createdAt == null) return -1;
      return b.createdAt!.compareTo(a.createdAt!);
    });

    return items;
  }

  /// Stream queue items for a user (for real-time updates)
  static Stream<List<QueueItem>> streamQueueItemsForUser(String applicantId) {
    return _firestore
        .collection('queue')
        .where('applicant_id', isEqualTo: applicantId)
        .snapshots()
        .map((snapshot) {
          final items = snapshot.docs
              .map((doc) => QueueItem.fromFirestore(doc.id, doc.data()))
              .toList();

          // Sort by created_at descending (newest first) in Dart to avoid needing a composite index
          items.sort((a, b) {
            if (a.createdAt == null && b.createdAt == null) return 0;
            if (a.createdAt == null) return 1;
            if (b.createdAt == null) return -1;
            return b.createdAt!.compareTo(a.createdAt!);
          });

          return items;
        });
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

  /// Remove a queue item by document ID.
  static Future<void> removeFromQueueByDocId(String docId) async {
    await _firestore.collection('queue').doc(docId).delete();
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
