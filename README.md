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
- Windows executable file exclusion option
- Dry-run mode to preview changes
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

### Basic Usage

Scan a directory for duplicates and replace them with links:

```bash
python dup_remover.py /path/to/directory
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

### Example 1: Dry run to see what would happen

```bash
$ python dup_remover.py ./test_data --dry-run
Platform: Linux
Link type: Soft links (symlinks)

*** DRY RUN MODE - No changes will be made ***

Scanning directory: ./test_data
Found 2 duplicate file groups with 3 duplicate files.

Duplicate set (hash: a1b2c3d4e5f6...):
  Original: ./test_data/file1.txt
  Would replace: ./test_data/copy1.txt (1024 bytes)
  Would replace: ./test_data/copy2.txt (1024 bytes)
...
```

### Example 2: Process duplicates on Windows, excluding executables

```bash
C:\> python dup_remover.py C:\MyFiles --exclude-executables
Platform: Windows
Link type: Hard links
Executable files: Excluded from deduplication
...
```

## Safety Notes

- The tool skips symbolic links to avoid circular references
- Always test with `--dry-run` first on important data
- Ensure you have write permissions in the target directory
- On Windows, hard links require files to be on the same volume
- Backup important data before running

## License

MIT License - see LICENSE file for details
