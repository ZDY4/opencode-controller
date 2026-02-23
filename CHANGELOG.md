# Changelog

All notable changes to the OpenCode Controller Skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-02-23

### Added
- **Dynamic polling intervals** - Monitor now uses exponential backoff:
  - First 2 checks: every 30 seconds
  - Checks 3-5: every 1 minute
  - Checks 6-10: every 2 minutes
  - After 10: every 3 minutes
- **Dual task completion detection** - Combines session status (idle) + message analysis
- **Multi-path configuration lookup** - Searches for `.env` in multiple locations:
  - Current working directory
  - OpenClaw project directory
  - Relative paths from script location
- **Manual .env parser** - No longer requires `python-dotenv` package
- **Max duration limit** - Auto-stop monitoring after 1 hour (configurable)
- **Improved Telegram notifications** - Shows task duration and message count
- **Better error handling** - Graceful degradation when Telegram is not configured
- **Keyboard interrupt support** - Clean exit on Ctrl+C

### Changed
- **Removed hardcoded Windows path** - `working_dir` now defaults to current directory
- **Removed hardcoded Telegram token** - Now requires proper environment configuration
- **Replaced print statements with logging** - Uses standard Python logging module
- **Updated shell script** - Supports new `--max-no-change` and `--max-duration` parameters
- **Improved log format** - Tabular output showing message count, status, and next check time

### Fixed
- **Duplicate code at end of file** - Removed unreachable test code after `return process.pid`
- **Configuration loading** - Now properly loads from project `.env` files
- **Cross-platform compatibility** - Works on Mac, Linux, and Windows

### Security
- **Removed hardcoded bot token** - Token must now be provided via environment or `.env` file
- **No default sensitive values** - All credentials must be explicitly configured

## [1.0.0] - 2026-02-12

### Added
- Initial release
- HTTP Server API client for OpenCode
- Session management (create, delete, list)
- Message sending and retrieval
- Server auto-start functionality
- Basic task monitoring with Telegram notifications
- PowerShell support for Windows
- Background process monitoring

### Features
- Synchronous and asynchronous message sending
- Session status polling
- Message parsing and extraction
- File diff retrieval
- Context manager support
