import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../models/job.dart';

class JobService {
  // Use 10.0.2.2 for Android emulator, localhost for others
  static String get _baseUrl {
    if (Platform.isAndroid) {
      return 'http://10.0.2.2:8000';
    }
    return 'http://127.0.0.1:8000';
  }

  /// Fetch jobs from the backend API with pagination.
  ///
  /// [limit] – number of jobs to fetch (default 10).
  /// [offset] – starting index (default 0).
  ///
  /// Returns a list of [Job] objects.  
  /// Throws on network / server errors.
  static Future<List<Job>> fetchJobs({int limit = 20, int offset = 0}) async {
    final uri = Uri.parse(
      '$_baseUrl/scraper/get-jobs?limit=$limit&offset=$offset',
    );

    try {
      final response = await http.get(uri).timeout(
        const Duration(seconds: 10),
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> body = json.decode(response.body);

        // The API wraps the response: {"success": true, "data": {"jobs": [...]}}
        final Map<String, dynamic> data = body['data'] ?? body;
        final List<dynamic> jobsJson = data['jobs'] ?? [];
        return jobsJson.map((j) => Job.fromJson(j as Map<String, dynamic>)).toList();
      } else {
        throw HttpException(
          'Failed to load jobs – status ${response.statusCode}',
        );
      }
    } on Exception {
      rethrow;
    }
  }
}
