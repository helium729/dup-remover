# dup-remover
Remove duplicated files and replace them with links for better archive work.

## Description

A cross-platform Python tool to find duplicate files and replace them with links to save disk space:
- **Linux/Unix**: Creates soft links (symlinks)
- **Windows**: Creates hard links
- **Windows executable exclusion**: Optionally excludes executable files (.exe, .dll, .sys, etc.) from deduplication on Windows

## Features

- Fast duplicate detection using SHA256 hashing
- Cross-platform support (Windows, Linux, macOS)
- Platform-specific link creation (soft links on Unix, hard links on Windows)
- **Interactive confirmation** - Review duplicates before processing
- **Selective exclusion** - Exclude specific files from deduplication
- **Report generation** - Create a detailed report of duplicates
- Windows executable file exclusion option
- Dry-run mode to preview changes
- Auto-confirm mode for batch processing
- Human-readable space savings report

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only Python standard library)

## Installation

Clone this repository:

```bash
git clone https://github.com/helium729/dup-remover.git
cd dup-remover
```

Make the script executable (Linux/macOS):

```bash
chmod +x dup_remover.py
```

## Usage

### Interactive Mode (Default)

By default, the tool runs interactively, showing you all duplicates and asking for confirmation:

```bash
python dup_remover.py /path/to/directory
```

This will:
1. Scan for duplicates
2. Display all duplicate groups with file numbers
3. Ask for confirmation before proceeding
4. Allow you to exclude specific files (e.g., "1.2,3.1" excludes group 1 file 2 and group 3 file 1)
5. Process the remaining duplicates

### Auto-Confirm Mode

Skip confirmation prompts and process all duplicates automatically:

```bash
python dup_remover.py /path/to/directory --auto-confirm
```

### Generate Report

Create a detailed report without making any changes:

```bash
python dup_remover.py /path/to/directory --report duplicates.txt
```

### Dry Run Mode

Preview what would be done without making changes:

```bash
python dup_remover.py /path/to/directory --dry-run
```

### Exclude Windows Executables

On Windows, exclude executable files from deduplication:

```bash
python dup_remover.py C:\path\to\directory --exclude-executables
```

### Command-Line Options

```
positional arguments:
  directory             Directory to scan for duplicate files

optional arguments:
  -h, --help            Show this help message and exit
  --dry-run             Show what would be done without making any changes
  --exclude-executables Exclude Windows executable files from deduplication (Windows only)
  --auto-confirm        Skip confirmation prompts and process all duplicates automatically
  --report FILE         Generate a report of duplicates to a file instead of processing
```

## How It Works

1. **File Scanning**: Recursively scans the specified directory
2. **Hash Calculation**: Calculates SHA256 hash for each file
3. **Duplicate Detection**: Groups files with identical hashes
4. **Link Creation**: 
   - Keeps the first occurrence of each duplicate set
   - Replaces other duplicates with links to the original
   - On Windows: Creates hard links (same file, multiple directory entries)
   - On Linux/Unix: Creates soft links (symlinks pointing to original)
5. **Executable Handling**: On Windows, optionally skips .exe, .dll, .sys, .com, .bat, .cmd, .msi, .scr files

## Examples

### Example 1: Interactive mode with selective exclusion

```bash
$ python dup_remover.py ./test_data
Platform: Linux
Link type: Soft links (symlinks)

Scanning directory: ./test_data

Group 1 (hash: a1b2c3d4e5f6...):
  [0] ./test_data/file1.txt (KEEP)
  [1] ./test_data/copy1.txt (1.00 KB)
  [2] ./test_data/copy2.txt (1.00 KB)

Group 2 (hash: b2c3d4e5f6a7...):
  [0] ./test_data/file2.txt (KEEP)
  [1] ./test_data/copy3.txt (2.00 KB)

============================================================
Total duplicate files: 3
Potential space savings: 4.00 KB
============================================================

Proceed with deduplication? (y/n): y

============================================================
You can exclude specific files from deduplication.
Options:
  - Enter file numbers (e.g., '1.2,3.1' for group 1 file 2, group 3 file 1)
  - Press Enter to skip exclusions
============================================================

Enter files to exclude (or press Enter to continue): 1.1
Excluded: ./test_data/copy1.txt

Processing duplicates...
Created soft link: ./test_data/copy2.txt -> file1.txt
Created soft link: ./test_data/copy3.txt -> file2.txt

============================================================
Successfully processed 2 duplicate files
Space saved: 3.00 KB
Files excluded: 1
============================================================
```

### Example 2: Generate a report

```bash
$ python dup_remover.py ./test_data --report duplicates.txt
Platform: Linux
Link type: Soft links (symlinks)

Scanning directory: ./test_data

Group 1 (hash: a1b2c3d4e5f6...):
  [0] ./test_data/file1.txt (KEEP)
  [1] ./test_data/copy1.txt (1.00 KB)

Report generated: duplicates.txt
```

### Example 3: Auto-confirm mode for batch processing

```bash
$ python dup_remover.py ./test_data --auto-confirm
Platform: Linux
Link type: Soft links (symlinks)
...
Processing duplicates...
Successfully processed 3 duplicate files
Space saved: 4.00 KB
```

### Example 4: Dry run to preview changes

```bash
$ python dup_remover.py ./test_data --dry-run
Platform: Linux
Link type: Soft links (symlinks)

*** DRY RUN MODE - No changes will be made ***

Scanning directory: ./test_data

Group 1 (hash: a1b2c3d4e5f6...):
  [0] ./test_data/file1.txt (KEEP)
  [1] ./test_data/copy1.txt (1.00 KB)
...
```

## Safety Notes

- **Interactive by default**: The tool now requires confirmation before making changes
- **Selective exclusion**: You can exclude specific files from deduplication
- **Report generation**: Use `--report` to review duplicates without making changes
- The tool skips symbolic links to avoid circular references
- Always test with `--dry-run` first on important data
- Ensure you have write permissions in the target directory
- On Windows, hard links require files to be on the same volume
- Backup important data before running

## License

MIT License - see LICENSE file for details
