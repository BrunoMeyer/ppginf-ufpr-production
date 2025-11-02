# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **DSpace HTTP Response Caching**: Fixed issue where metadata (author, title, summary) was lost when using cached responses. The application now properly caches HTTP response bodies and resolved URLs from DSpace API requests, ensuring that subsequent cached lookups contain complete metadata. This is critical for preserving publication information when the caching mechanism is enabled.
  - Added `cache_dspace_response()` and `get_cached_dspace_response()` methods to `ProcessingCache`
  - Updated `DSpaceClient` to cache HTTP responses with resolved URLs (e.g., after redirects)
  - Ensured backward compatibility: old cache entries without new fields gracefully fall back
  - Added comprehensive unit tests for caching behavior
