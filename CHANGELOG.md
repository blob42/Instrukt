# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Generate sphinx doc for online and offline reading from within the app. 
- wip: offline doc reader: jump to anchors (https://github.com/Textualize/textual/pull/2941)
- display common key bindings with `K` 
- Index Mgmt: added a local file system path selection UI
- UI: reusable action bar widget.

### Changed

- upgrade `textual` to `v0.30.0`
- upgrade `langchain` to `v0.0.235`
- upgrade `chromadb` to `v0.4.0`
- ChromaDB: no more manual call to `persist`

### Fixed

- Chroma: share a single client for all indexes
- Explicit dependency on `sentence-transofmers` library for local embeddings.

## [0.5.0] - 2023-07-18

### Added

- Github action for generating online sphinx documentation 

### Changed

- Bumped `textual` to version **v0.29.0**

### Fixed

- Index view broke after textual update

[unreleased]: https://github.com/blob42/Instrukt/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/blob42/Instrukt/compare/v0.4.0...v0.5.0
