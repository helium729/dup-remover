#!/usr/bin/env python3
"""
Duplicate File Remover
A cross-platform tool to find duplicate files and replace them with links to save space.
- On Linux: Creates soft links (symlinks)
- On Windows: Creates hard links
- Excludes executable files on Windows from deduplication
"""

import os
import sys
import hashlib
import argparse
from pathlib import Path
from collections import defaultdict
import platform


def calculate_file_hash(filepath, chunk_size=8192):
    """
    Calculate SHA256 hash of a file.
    
    Args:
        filepath: Path to the file
        chunk_size: Size of chunks to read (default 8KB)
    
    Returns:
        SHA256 hash as hexadecimal string
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        print(f"Error reading file {filepath}: {e}", file=sys.stderr)
        return None


def is_windows_executable(filepath):
    """
    Check if a file is a Windows executable.
    
    Args:
        filepath: Path to the file
    
    Returns:
        True if file is a Windows executable, False otherwise
    """
    executable_extensions = {'.exe', '.dll', '.sys', '.com', '.bat', '.cmd', '.msi', '.scr'}
    return Path(filepath).suffix.lower() in executable_extensions


def find_duplicates(directory, exclude_executables=False):
    """
    Find duplicate files in a directory.
    
    Args:
        directory: Directory to scan for duplicates
        exclude_executables: If True, exclude Windows executables (only on Windows)
    
    Returns:
        Dictionary mapping file hashes to lists of file paths
    """
    file_hashes = defaultdict(list)
    is_windows = platform.system() == 'Windows'
    
    print(f"Scanning directory: {directory}")
    
    for root, dirs, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            
            # Skip if it's a symbolic link to avoid issues
            if os.path.islink(filepath):
                continue
            
            # On Windows, skip executables if requested
            if is_windows and exclude_executables and is_windows_executable(filepath):
                continue
            
            file_hash = calculate_file_hash(filepath)
            if file_hash:
                file_hashes[file_hash].append(filepath)
    
    # Filter to only keep hashes with duplicates
    duplicates = {h: paths for h, paths in file_hashes.items() if len(paths) > 1}
    
    return duplicates


def create_link(source, target):
    """
    Create a link from target to source.
    On Linux: Creates a soft link (symlink)
    On Windows: Creates a hard link
    
    Args:
        source: The original file to keep
        target: The duplicate file to replace with a link
    
    Returns:
        True if successful, False otherwise
    """
    is_windows = platform.system() == 'Windows'
    
    try:
        # Remove the target file first
        os.remove(target)
        
        if is_windows:
            # Create hard link on Windows (requires absolute paths)
            os.link(source, target)
            print(f"Created hard link: {target} -> {source}")
        else:
            # Create soft link on Linux/Unix using relative path
            # Calculate relative path from target to source
            target_dir = os.path.dirname(os.path.abspath(target))
            source_abs = os.path.abspath(source)
            rel_path = os.path.relpath(source_abs, target_dir)
            os.symlink(rel_path, target)
            print(f"Created soft link: {target} -> {rel_path}")
        
        return True
    except (IOError, OSError) as e:
        print(f"Error creating link from {target} to {source}: {e}", file=sys.stderr)
        return False


def process_duplicates(duplicates, dry_run=False):
    """
    Process duplicate files by replacing them with links.
    
    Args:
        duplicates: Dictionary mapping file hashes to lists of file paths
        dry_run: If True, only show what would be done without making changes
    
    Returns:
        Tuple of (number of files processed, space saved in bytes)
    """
    files_processed = 0
    space_saved = 0
    
    for file_hash, file_paths in duplicates.items():
        # Sort by path length and keep the shortest path as original
        # This minimizes the chance of broken links if files are moved
        file_paths_sorted = sorted(file_paths, key=lambda p: len(p))
        original = file_paths_sorted[0]
        duplicates_list = file_paths_sorted[1:]
        
        print(f"\nDuplicate set (hash: {file_hash[:16]}...):")
        print(f"  Original: {original}")
        
        for duplicate in duplicates_list:
            file_size = os.path.getsize(duplicate)
            
            if dry_run:
                print(f"  Would replace: {duplicate} ({file_size} bytes)")
            else:
                print(f"  Replacing: {duplicate} ({file_size} bytes)")
                if create_link(original, duplicate):
                    files_processed += 1
                    space_saved += file_size
    
    return files_processed, space_saved


def format_size(bytes_size):
    """
    Format bytes into human-readable size.
    
    Args:
        bytes_size: Size in bytes
    
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if bytes_size < 1024.0 or unit == 'PB':
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0


def main():
    """Main function to run the duplicate file remover."""
    parser = argparse.ArgumentParser(
        description='Find and remove duplicate files by replacing them with links.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/directory
  %(prog)s /path/to/directory --dry-run
  %(prog)s /path/to/directory --exclude-executables

On Linux/Unix: Creates soft links (symlinks)
On Windows: Creates hard links, optionally excluding executable files
        """
    )
    
    parser.add_argument(
        'directory',
        help='Directory to scan for duplicate files'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making any changes'
    )
    
    parser.add_argument(
        '--exclude-executables',
        action='store_true',
        help='Exclude Windows executable files from deduplication (Windows only)'
    )
    
    args = parser.parse_args()
    
    # Validate directory
    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory", file=sys.stderr)
        sys.exit(1)
    
    # Show platform and mode information
    print(f"Platform: {platform.system()}")
    if platform.system() == 'Windows':
        print("Link type: Hard links")
        if args.exclude_executables:
            print("Executable files: Excluded from deduplication")
        else:
            print("Executable files: Included in deduplication")
    else:
        print("Link type: Soft links (symlinks)")
    
    if args.dry_run:
        print("\n*** DRY RUN MODE - No changes will be made ***\n")
    
    # Find duplicates
    duplicates = find_duplicates(args.directory, args.exclude_executables)
    
    if not duplicates:
        print("\nNo duplicate files found.")
        return
    
    # Show summary
    total_duplicates = sum(len(paths) - 1 for paths in duplicates.values())
    print(f"\nFound {len(duplicates)} duplicate file groups with {total_duplicates} duplicate files.")
    
    # Process duplicates
    files_processed, space_saved = process_duplicates(duplicates, args.dry_run)
    
    # Show final summary
    print("\n" + "="*60)
    if args.dry_run:
        print(f"Would process {total_duplicates} duplicate files")
        potential_savings = sum(
            sum(os.path.getsize(p) for p in paths[1:])
            for paths in duplicates.values()
        )
        print(f"Potential space savings: {format_size(potential_savings)}")
    else:
        print(f"Successfully processed {files_processed} duplicate files")
        print(f"Space saved: {format_size(space_saved)}")
    print("="*60)


if __name__ == '__main__':
    main()
