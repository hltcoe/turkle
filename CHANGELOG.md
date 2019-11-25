# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Bulk Batch activation/deactivation
- Support for turkle_site/local_settings.py
- Help page for workers

### Changed
- Access controls are now Batch-level instead of Project-level

### Removed
- No longer using django-dbbackup

## [2.1.0] - 2019-06-05
### Added
- Admin UI page with Batch-level Statistics
- Worker specific statistics page
- Bootstrap 4 support for the glyphicons from Bootstrap 3
- New results CSV column `Turkle.username`
- Toggle for unix line endings for batch results
- Added a check for input fields in templates (MTurk compatibility)
- Added template size limit (MTurk compatibility)
- Pass variables to task iframe (MTurk compatibility)
- Logging of user actions
- Versioning to code
- Admin About page that displays version #
- Release process instructions to README

### Changed
- Improved documentation
- Improved performance of index page
- Fixed several UI issues
- Fixed limit on csv field size
- Login page less fugly
- Docker compose setup now supports unicode characters in templates

### Removed
- Python 2.7 no longer supported
- Unused static resources like concrete.js and older bootstrap

## [2.0.1] - 2019-01-28
### Added
- CHANGELOG.md
- Support for running Dockerized Turkle with a URL prefix

### Changed
- In Task Assignment view, browser focus now starts in iframe
- In Task Assignment view, iframe height now dynamically resizes
  to fill entire screen instead of being fixed to 500px.  Resizing
  implemented using jQuery library
  [iframe-resizer](https://github.com/davidjbradshaw/iframe-resizer)
- `expire_abandoned_assignments` view moved into Turkle admin controller

## [2.0.0] - 2018-12-21
### Added
- Authentication support for multiple users using the
  `django.contrib.auth` framework
- Admin UI for creating and modifying Projects and Batches
- Support for multiple assignments per task (i.e. redundant
  annotations)
- Support for database backups using
  [django-dbbackup](https://django-dbbackup.readthedocs.io/en/stable/)

### Changed
- Almost every line of code. "Turkle 1.0" was a solid foundation, but
  the code base underwent extensive refactoring
- All Model names
- All routes
- Almost all View names
- Appearance of the UI
- Directory structure

### Removed
- `RANDOM_NEXT_HIT_ON_SUBMIT` setting no longer supported
