# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Capture and redirect logging/output to Instrukt console widget.
- Generate sphinx doc for online and offline reading from within the app. 
- wip: offline doc reader: jump to anchors (https://github.com/Textualize/textual/pull/2941)
- Help screen for common keybindings with `?`
- UI: reusable action bar widget.

#### index management: 
- added a local file system path selection UI
- chromadb: save/restore used embedding function. You can have multiple indexes using
  different embedding functions.
- Choose to use local embeddings when creating index.
- TODO: detect local embeddings when loading an index.

### Changed

- Improved form validation
- Upgraded dependencies
- ChromaDB: no more manual call to `persist`

### Fixed

- improved iPython dev console: avoid term repaints until end of session.
- Fast preloading of messages when switching agent tab. 
- Chroma: share a single client for all indexes
- Explicit dependency on `sentence-transofmers` library for local embeddings.
- Many fixes related to dependency updates

## [0.5.0] - 2023-07-18

### Added

- Github action for generating online sphinx documentation 

### Changed

- Bumped `textual` to version **v0.29.0**

### Fixed

- Index view broke after textual update

[unreleased]: https://github.com/blob42/Instrukt/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/blob42/Instrukt/compare/v0.4.0...v0.5.0
