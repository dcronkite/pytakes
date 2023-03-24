# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Reference

Types of changes:

* `Added`: for new features.
* `Changed`: for changes in existing functionality.
* `Deprecated`: for soon-to-be removed features.
* `Removed`: for now removed features.
* `Fixed`: for any bug fixes.
* `Security`: in case of vulnerabilities.

## [Unreleased]

## 1.2.0

### Fixed

* Updated homepage, version, description in `pyproject.toml`

### Removed

* `setup.py` in favor of `pyproject.toml`

## 1.1.3

### Fixed

* `publish-to-pypi` workflow: `module` to `name`

## 1.1.2

### Fixed

* `publish-to-pypi` workflow: need to quote around python version >= '3.10'

## 1.1.1

### Fixed

* `publish-to-pypi` workflow
  * Python 3.10 as build target
  * reference released versions
* Fixed `pyproject.toml` to use `[project]`

## 1.1.0

### Added

* Option in schema to specify `include_extension` and `exclude_extension` to limit files included from a directory

### Changed

* Migrated from `os` to `pathlib`
* In config, changed `corpus.directories` from an array of string (i.e., directory paths) to array of objects (i.e., directory with metadata).
