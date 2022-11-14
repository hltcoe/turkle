# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Changed
- Upgrade to Django 3.2

## [2.7.0] - 2022-11-01
### Changed
 - Upgrade to Django 3.1
 - Upgrade dependencies
 - Made Turkle an installable package
### Fixed
 - postgres database support fixed

## [2.6.2] - 2022-03-28
### Added
 - Adds `TURKLE_ANONYMOUS_TASKS` flag to turn off anonymous tasks

## [2.6.1] - 2022-02-24
### Fixed
 - Display of password validation errors
### Added
 - Configurable metatags
 - Hook in login template for consent banner
 - Documentation for configuring email behind reverse proxy

## [2.6.0] - 2022-02-03
### Fixed
- Cron job for docker-compose MySQL setup works now.
- Turkle logging sent to console in docker images.
### Added
- Adds a favicon.
### Changed
- Switching to Debian based images for Docker due to RedHat dropping CentOS.

## [2.5.0] - 2021-10-05
### Added
- Add "Activity Calendar Heatmap" visualization to Batch Stats and
  Project Stats admin views and User Stats view.  Visualization shows
  how many Task Assignments were completed for each day of the past
  year.
- Add "Active Projects" admin view that uses the "Activity Calendar
  Heatmap" visualization to show activity on all projects active
  in last N days.
- Add "Active Users" admin view that lists all users active in last
  N days.
### Changed
- Users with Staff privileges can now access User Stats view for
  any User.  The User table on the User Admin changelist page now
  includes a link to the Stats page for each User.

## [2.4.1] - 2021-04-29
### Fixed
- Project Statistics page now includes data about all Batches for
  the Project, not just Batches with at least one completed Task
  Assignment

## [2.4.0] - 2021-04-20
### Added
- Added allotted_assignment_time field to Projects that is used as
  the default allotted_assignment_time for new Batches created
  for the Project
- Added statistics about not-yet-completed Task Assignments to
  Project Stats page.
- Banner for the preview page added to warn users that any work
  won't be saved.
- Batch Statistics page now includes table of Unsubmitted Assignments
- Tables on Batch Stats and Project Stats pages are now sortable
  by clicking on column headings
- Turkle now creates a "Turkle User Admin" Group that has:
  - Add/Change/View (but not Delete) permissions for Users
  - Add/Change/View (but not Delete) permissions for Groups
  - View permissions for Batches
  - View permissions for Projects

### Changed
- Deprecate support for (EOL) Python 3.5, add support for
  Python 3.9.
- On the Add/Change Batch and Add/Change Project forms, changes made
  to Group and User permissions while editing the form are now saved
  even if the "Restrict access" checkbox is unchecked (hiding the
  form widgets for selecting Groups and Users) when the form is
  submitted
- On the Add/Change User admin forms, the ability to assign superuser
  status or grant model-level permission privileges to Users is now
  restricted to superusers
- On the Change User admin form, the "Last login" and "Date joined"
  fields are now read-only
- Permission to work on a Batch can now be restricted to specific Users.
  Previously, Batch access could only be restricted at the Group level,
  which in practice lead to the creation of many single-User Groups.
- Reorganized Add/Change Project forms to more clearly identify which
  Project-level settings are only used as defaults for new Batches.
  Reorganized Add/Change Batch forms to match field order on Add/Change
  Project forms.
- Updated to use Django 2 style URLs.

### Fixed
- Fixed a race condition in task assignment.
- Task Assignments from inactive Batches and/or Projects are no
  longer included in the list of "Abandoned Tasks" shown to
  Users on the Turkle index page.
- Users can no longer accept Task Assignments for inactive
  Projects.

## [2.3.0] - 2021-02-15
### Added
- Added `Batch.completed` flag. Batch Admin page now supports
  filtering by completion status.
- Added additional configuration options for the Docker images.
- Batch activation and deactivation of user accounts added.
- Turkle version displayed in new admin footer.
- Added additional filters and display columns for Batch admin.

### Fixed
- Task assignment expiration date only set now upon creation.
- Fixed display of expiration time left to include days remaining.

## [2.2.0] - 2020-09-08
### Added
- Admin page with Project-level Statistics.  Page shows tasks
  completed during time intervals.  Page also links to Batch-level
  Statistics pages for each Batch associated with the Project.
- Batch Admin page displays green checkmark icon for completed batches
- Bulk Batch activation/deactivation admin UI actions
- Bulk Project activation/deactivation admin UI actions
- Support for turkle_site/local_settings.py
- Help page for workers
- Batches on Batch Admin page can now be filtered by Active flag,
  Batch Name, Batch Creator, and Project Name
- Projects on Project Admin page can now be filtered by Active flag,
  Project Creator, Project Name

### Changed
- Access controls are now Batch-level instead of Project-level
- CSV field size limit now computed with Windows-compatible metric
- Index page performance improvements.
- Updated Django from 1.11 to 2.2

### Fixed
- On Task Assignment page, JavaScript countdown timer now handles
  timezones correctly.

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
