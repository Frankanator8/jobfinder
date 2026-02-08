import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/job.dart';

class JobService {
  static final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  /// Fetch a single page of jobs from the Firebase 'jobs' collection.
  ///
  /// [limit] – number of jobs to fetch per page (default 20).
  /// [lastDocument] – the last document from the previous page for pagination.
  ///
  /// Returns a record containing the list of [Job] objects and the last document snapshot.
  static Future<({List<Job> jobs, DocumentSnapshot? lastDoc})> fetchJobsPage({
    int limit = 20,
    DocumentSnapshot? lastDocument,
  }) async {
    Query query = _firestore.collection('jobs').limit(limit);

    if (lastDocument != null) {
      query = query.startAfterDocument(lastDocument);
    }

    final QuerySnapshot snapshot = await query.get();

    final jobs = snapshot.docs.map((doc) {
      final data = doc.data() as Map<String, dynamic>;
      return Job.fromJson({...data, 'id': doc.id});
    }).toList();

    final lastDoc = snapshot.docs.isNotEmpty ? snapshot.docs.last : null;

    return (jobs: jobs, lastDoc: lastDoc);
  }

  /// Fetch ALL jobs from the Firebase 'jobs' collection.
  ///
  /// This method keeps making requests until the collection is exhausted.
  /// [batchSize] – number of jobs to fetch per request (default 100).
  ///
  /// Returns a list of all [Job] objects in the collection.
  static Future<List<Job>> fetchAllJobs({int batchSize = 100}) async {
    final List<Job> allJobs = [];
    DocumentSnapshot? lastDoc;

    while (true) {
      final result = await fetchJobsPage(
        limit: batchSize,
        lastDocument: lastDoc,
      );

      allJobs.addAll(result.jobs);
      lastDoc = result.lastDoc;

      // If we got fewer jobs than the batch size, we've reached the end
      if (result.jobs.length < batchSize) {
        break;
      }
    }

    return allJobs;
  }

  /// Fetch jobs with simple pagination (backwards compatible).
  static Future<List<Job>> fetchJobs({
    int limit = 20,
    DocumentSnapshot? lastDocument,
  }) async {
    final result = await fetchJobsPage(limit: limit, lastDocument: lastDocument);
    return result.jobs;
  }
}
