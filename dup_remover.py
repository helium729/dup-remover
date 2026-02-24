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


def display_duplicates(duplicates, show_detail=True):
    """
    Display duplicate files to the user.
    
    Args:
        duplicates: Dictionary mapping file hashes to lists of file paths
        show_detail: If True, show all files; if False, show summary only
    
    Returns:
        Total number of duplicate files and potential space savings
    """
    total_duplicates = 0
    potential_savings = 0
    group_num = 1
    
    for file_hash, file_paths in duplicates.items():
        file_paths_sorted = sorted(file_paths, key=lambda p: len(p))
        original = file_paths_sorted[0]
        duplicates_list = file_paths_sorted[1:]
        
        if show_detail:
            print(f"\nGroup {group_num} (hash: {file_hash[:16]}...):")
            print(f"  [0] {original} (KEEP)")
            for idx, duplicate in enumerate(duplicates_list, 1):
                file_size = os.path.getsize(duplicate)
                print(f"  [{idx}] {duplicate} ({format_size(file_size)})")
                potential_savings += file_size
        
        total_duplicates += len(duplicates_list)
        group_num += 1
    
    if not show_detail:
        for file_paths in duplicates.values():
            file_paths_sorted = sorted(file_paths, key=lambda p: len(p))
            for duplicate in file_paths_sorted[1:]:
                potential_savings += os.path.getsize(duplicate)
    
    return total_duplicates, potential_savings


def get_user_confirmation(total_duplicates, potential_savings):
    """
    Ask user for confirmation before proceeding.
    
    Args:
        total_duplicates: Number of duplicate files
        potential_savings: Space that would be saved
    
    Returns:
        True if user confirms, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"Total duplicate files: {total_duplicates}")
    print(f"Potential space savings: {format_size(potential_savings)}")
    print(f"{'='*60}")
    
    while True:
        response = input("\nProceed with deduplication? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'")


def get_excluded_files(duplicates):
    """
    Allow user to exclude specific files from deduplication.
    
    Args:
        duplicates: Dictionary mapping file hashes to lists of file paths
    
    Returns:
        Set of file paths to exclude
    """
    excluded = set()
    
    print("\n" + "="*60)
    print("You can exclude specific files from deduplication.")
    print("Options:")
    print("  - Enter file numbers (e.g., '1.2,3.1' for group 1 file 2, group 3 file 1)")
    print("  - Press Enter to skip exclusions")
    print("="*60)
    
    response = input("\nEnter files to exclude (or press Enter to continue): ").strip()
    
    if not response:
        return excluded
    
    # Parse the response
    group_list = list(duplicates.items())
    
    for item in response.split(','):
        item = item.strip()
        if '.' in item:
            try:
                group_idx, file_idx = item.split('.')
                group_idx = int(group_idx) - 1
                file_idx = int(file_idx)
                
                if 0 <= group_idx < len(group_list):
                    file_hash, file_paths = group_list[group_idx]
                    file_paths_sorted = sorted(file_paths, key=lambda p: len(p))
                    
                    if 1 <= file_idx < len(file_paths_sorted):
                        excluded.add(file_paths_sorted[file_idx])
                        print(f"Excluded: {file_paths_sorted[file_idx]}")
            except (ValueError, IndexError):
                print(f"Invalid entry: {item}")
    
    return excluded


def process_duplicates(duplicates, dry_run=False, excluded_files=None):
    """
    Process duplicate files by replacing them with links.
    
    Args:
        duplicates: Dictionary mapping file hashes to lists of file paths
        dry_run: If True, only show what would be done without making changes
        excluded_files: Set of file paths to exclude from processing
    
    Returns:
        Tuple of (number of files processed, space saved in bytes)
    """
    if excluded_files is None:
        excluded_files = set()
    
    files_processed = 0
    space_saved = 0
    
    for file_hash, file_paths in duplicates.items():
        # Sort by path length and keep the shortest path as original
        # This minimizes the chance of broken links if files are moved
        file_paths_sorted = sorted(file_paths, key=lambda p: len(p))
        original = file_paths_sorted[0]
        duplicates_list = file_paths_sorted[1:]
        
        for duplicate in duplicates_list:
            # Skip excluded files
            if duplicate in excluded_files:
                continue
            
            file_size = os.path.getsize(duplicate)
            
            if dry_run:
                print(f"  Would replace: {duplicate} ({format_size(file_size)})")
            else:
                if create_link(original, duplicate):
                    files_processed += 1
                    space_saved += file_size
    
    return files_processed, space_saved


def generate_report(filename, duplicates, total_duplicates, potential_savings):
    """
    Generate a report file listing all duplicates.
    
    Args:
        filename: Path to the report file
        duplicates: Dictionary mapping file hashes to lists of file paths
        total_duplicates: Total number of duplicate files
        potential_savings: Total space that could be saved
    """
    try:
        with open(filename, 'w') as f:
            f.write("="*70 + "\n")
            f.write("DUPLICATE FILES REPORT\n")
            f.write("="*70 + "\n\n")
            f.write(f"Total duplicate file groups: {len(duplicates)}\n")
            f.write(f"Total duplicate files: {total_duplicates}\n")
            f.write(f"Potential space savings: {format_size(potential_savings)}\n\n")
            f.write("="*70 + "\n\n")
            
            group_num = 1
            for file_hash, file_paths in duplicates.items():
                file_paths_sorted = sorted(file_paths, key=lambda p: len(p))
                original = file_paths_sorted[0]
                duplicates_list = file_paths_sorted[1:]
                
                f.write(f"Group {group_num} (hash: {file_hash})\n")
                f.write(f"  [0] {original} (KEEP)\n")
                
                for idx, duplicate in enumerate(duplicates_list, 1):
                    file_size = os.path.getsize(duplicate)
                    f.write(f"  [{idx}] {duplicate} ({format_size(file_size)})\n")
                
                f.write("\n")
                group_num += 1
            
            f.write("="*70 + "\n")
            f.write("End of report\n")
    except (IOError, OSError) as e:
        print(f"Error writing report to {filename}: {e}", file=sys.stderr)
        sys.exit(1)


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
  %(prog)s /path/to/directory --auto-confirm

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
    
    parser.add_argument(
        '--auto-confirm',
        action='store_true',
        help='Skip confirmation prompts and process all duplicates automatically'
    )
    
    parser.add_argument(
        '--report',
        metavar='FILE',
        help='Generate a report of duplicates to a file instead of processing'
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
    print(f"\nScanning directory: {args.directory}")
    duplicates = find_duplicates(args.directory, args.exclude_executables)
    
    if not duplicates:
        print("\nNo duplicate files found.")
        return
    
    # Display duplicates
    total_duplicates, potential_savings = display_duplicates(duplicates, show_detail=True)
    
    # Generate report if requested
    if args.report:
        generate_report(args.report, duplicates, total_duplicates, potential_savings)
        print(f"\nReport generated: {args.report}")
        return
    
    # In dry-run mode, just show what would happen
    if args.dry_run:
        print(f"\n{'='*60}")
        print(f"Would process {total_duplicates} duplicate files")
        print(f"Potential space savings: {format_size(potential_savings)}")
        print(f"{'='*60}")
        return
    
    # Get user confirmation unless auto-confirm is set
    if not args.auto_confirm:
        if not get_user_confirmation(total_duplicates, potential_savings):
            print("\nOperation cancelled by user.")
            return
        
        # Allow user to exclude specific files
        excluded_files = get_excluded_files(duplicates)
    else:
        excluded_files = set()
    
    # Process duplicates
    print("\nProcessing duplicates...")
    files_processed, space_saved = process_duplicates(duplicates, False, excluded_files)
    
    # Show final summary
    print("\n" + "="*60)
    print(f"Successfully processed {files_processed} duplicate files")
    print(f"Space saved: {format_size(space_saved)}")
    if excluded_files:
        print(f"Files excluded: {len(excluded_files)}")
    print("="*60)


if __name__ == '__main__':
    main()
