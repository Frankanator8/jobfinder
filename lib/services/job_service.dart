import 'dart:convert';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/job.dart';

class JobService {
  static final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  /// Base URL for the backend API (scraper endpoints).
  static const String _backendBaseUrl = 'http://localhost:8000';

  /// Fetch a single page of jobs from the Firebase 'jobs' collection.
  ///
  /// [limit] – number of jobs to fetch per page (default 20).
  /// [lastDocument] – the last document from the previous page for pagination.
  /// [category] – optional category filter (e.g. 'software_engineering').
  ///
  /// Returns a record containing the list of [Job] objects and the last document snapshot.
  static Future<({List<Job> jobs, DocumentSnapshot? lastDoc})> fetchJobsPage({
    int limit = 20,
    DocumentSnapshot? lastDocument,
    String? category,
  }) async {
    Query query = _firestore.collection('jobs');

    if (category != null && category.isNotEmpty) {
      query = query.where('category', isEqualTo: category);
    }

    query = query.limit(limit);

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

  /// Apply client-side filters for location and age that can't be done
  /// efficiently at the Firestore query level.
  ///
  /// [location] – if provided, only keep jobs whose location contains this
  ///              string (case-insensitive substring match).
  /// [hoursOld] – if provided, only keep jobs posted within this many hours.
  static List<Job> applyLocalFilters(
    List<Job> jobs, {
    String? location,
    int? hoursOld,
  }) {
    var filtered = jobs;

    if (location != null && location.isNotEmpty) {
      final loc = location.toLowerCase();
      filtered = filtered
          .where((j) => j.location.toLowerCase().contains(loc))
          .toList();
    }

    if (hoursOld != null && hoursOld > 0) {
      final cutoff = DateTime.now().subtract(Duration(hours: hoursOld));
      filtered = filtered.where((j) {
        if (j.datePosted == null) return true; // keep jobs with unknown date
        return j.datePosted!.isAfter(cutoff);
      }).toList();
    }

    return filtered;
  }

  /// Fetch ALL jobs from the Firebase 'jobs' collection.
  ///
  /// [category] – optional category filter.
  /// [batchSize] – number of jobs to fetch per request (default 100).
  ///
  /// Returns a list of all [Job] objects in the collection.
  static Future<List<Job>> fetchAllJobs({
    int batchSize = 100,
    String? category,
    String? location,
    int? hoursOld,
  }) async {
    final List<Job> allJobs = [];
    DocumentSnapshot? lastDoc;

    while (true) {
      final result = await fetchJobsPage(
        limit: batchSize,
        lastDocument: lastDoc,
        category: category,
      );

      allJobs.addAll(result.jobs);
      lastDoc = result.lastDoc;

      // If we got fewer jobs than the batch size, we've reached the end
      if (result.jobs.length < batchSize) {
        break;
      }
    }

    // Apply client-side location and age filters
    return applyLocalFilters(allJobs, location: location, hoursOld: hoursOld);
  }

  /// Fetch jobs with simple pagination (backwards compatible).
  static Future<List<Job>> fetchJobs({
    int limit = 20,
    DocumentSnapshot? lastDocument,
    String? category,
  }) async {
    final result = await fetchJobsPage(
      limit: limit,
      lastDocument: lastDocument,
      category: category,
    );
    return result.jobs;
  }

  /// Trigger the backend scraper to scrape new jobs and store them in Firebase.
  ///
  /// [category] – required category value (backend uses predefined search terms).
  /// [location] – job location (e.g. "New York, NY").
  /// [sites] – comma-separated site list (e.g. "indeed,linkedin").
  /// [hoursOld] – max age of postings in hours.
  /// [resultsWanted] – number of results to scrape (default 20).
  ///
  /// Returns a map with scrape details on success, or null on failure.
  /// Keys: 'jobs_found', 'jobs_saved', 'jobs_updated', 'jobs_skipped', 'message'.
  static Future<Map<String, dynamic>?> scrapeJobs({
    required String category,
    String location = 'New York, NY',
    String sites = 'indeed,linkedin,zip_recruiter,google',
    int hoursOld = 72,
    int resultsWanted = 20,
  }) async {
    try {
      final queryParams = {
        'category': category,
        'location': location,
        'site_name': sites,
        'hours_old': hoursOld.toString(),
        'results_wanted': resultsWanted.toString(),
      };

      final uri = Uri.parse('$_backendBaseUrl/scraper/scrape-jobs')
          .replace(queryParameters: queryParams);

      // Generous timeout: scraper now cycles through multiple search terms
      // and each can take 10-30 seconds.
      final response = await http.get(uri).timeout(
        const Duration(minutes: 5),
        onTimeout: () => http.Response('{"error": "timeout"}', 408),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final saved = data['jobs_saved_to_firebase'] ?? 0;
        final updated = data['jobs_updated'] ?? 0;
        debugPrint('[JobService] Scrape succeeded: $saved saved, $updated updated');
        return {
          'jobs_found': data['jobs_found'] ?? 0,
          'jobs_saved': saved,
          'jobs_updated': updated,
          'jobs_skipped': data['jobs_skipped'] ?? 0,
          'message': data['message'] ?? '',
        };
      } else {
        debugPrint('[JobService] Scrape failed: ${response.statusCode} - ${response.body}');
        return null;
      }
    } catch (e) {
      debugPrint('[JobService] Scrape error: $e');
      return null;
    }
  }

  /// Fetch ALL jobs, bypassing the local Firestore cache.
  /// Use after scraping to guarantee freshly written docs are visible.
  static Future<List<Job>> fetchAllJobsFromServer({
    int batchSize = 100,
    String? category,
    String? location,
    int? hoursOld,
  }) async {
    final List<Job> allJobs = [];
    DocumentSnapshot? lastDoc;

    while (true) {
      Query query = _firestore.collection('jobs');

      if (category != null && category.isNotEmpty) {
        query = query.where('category', isEqualTo: category);
      }

      query = query.limit(batchSize);

      if (lastDoc != null) {
        query = query.startAfterDocument(lastDoc);
      }

      // Force read from Firestore server, skip local cache
      final QuerySnapshot snapshot =
          await query.get(const GetOptions(source: Source.server));

      final jobs = snapshot.docs.map((doc) {
        final data = doc.data() as Map<String, dynamic>;
        return Job.fromJson({...data, 'id': doc.id});
      }).toList();

      allJobs.addAll(jobs);
      lastDoc = snapshot.docs.isNotEmpty ? snapshot.docs.last : null;

      if (jobs.length < batchSize) break;
    }

    return applyLocalFilters(allJobs, location: location, hoursOld: hoursOld);
  }
}
