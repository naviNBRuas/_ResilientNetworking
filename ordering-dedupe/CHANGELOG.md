# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-07-13

### Fixed
- `test_concurrency_deduplicator` keyed entries by `threading.get_ident()`, which is only unique among threads alive at the same instant; a finished worker's native thread ID could be recycled by a later one, causing key collisions and a flaky failure under CI scheduling. Now keys by an explicit worker index.

## [1.0.0] - 2026-07-13

### Added
- Initial stable release. Ordering, sequencing, and deduplication helpers.
- Test suite covering the package's core behavior.
