"""
Duplicate File Finder module for PC Maintenance Dashboard.
Finds and manages duplicate files using MD5 hashing.
"""

import os
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict


class DuplicateFinder:
    """Handles duplicate file detection and management."""
    
    def __init__(self):
        self.file_hashes = defaultdict(list)
        self.scanned_files = 0
        self.total_files = 0
        self.duplicates_found = {}
        self.total_duplicate_size = 0
        
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of a file with size limit."""
        hash_md5 = hashlib.md5()
        max_file_size = 100 * 1024 * 1024  # 100MB limit to prevent hanging
        
        try:
            file_size = os.path.getsize(file_path)
            if file_size > max_file_size:
                return None  # Skip very large files
                
            with open(file_path, "rb") as f:
                bytes_read = 0
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
                    bytes_read += len(chunk)
                    if bytes_read > max_file_size:  # Double check during reading
                        return None
            return hash_md5.hexdigest()
        except (OSError, PermissionError):
            return None
    
    def get_file_info(self, file_path: str) -> Dict[str, any]:
        """Get detailed file information."""
        try:
            stat = os.stat(file_path)
            return {
                'path': file_path,
                'size': stat.st_size,
                'modified': time.ctime(stat.st_mtime),
                'accessed': time.ctime(stat.st_atime),
                'created': time.ctime(stat.st_ctime),
                'size_mb': stat.st_size / (1024**2)
            }
        except (OSError, PermissionError):
            return None
    
    def count_files_in_directory(self, directory: str, extensions: Set[str] = None, 
                                min_size: int = 0) -> int:
        """Count total files to be scanned."""
        count = 0
        max_files = 10000  # Limit to prevent infinite scanning
        
        try:
            for root, dirs, files in os.walk(directory):
                # Skip system directories and limit depth
                dirs[:] = [d for d in dirs if not d.startswith('.') and 
                          d.lower() not in ['system volume information', '$recycle.bin', 
                                          'windows', 'program files', 'program files (x86)',
                                          'appdata\\local\\temp', 'temp']]
                
                for file in files:
                    if count >= max_files:  # Prevent excessive scanning
                        return max_files
                        
                    if file.startswith('.'):
                        continue
                        
                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size < min_size:
                            continue
                            
                        if extensions:
                            file_ext = Path(file_path).suffix.lower()
                            if file_ext not in extensions:
                                continue
                        
                        count += 1
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            pass
        
        return count
    
    def scan_directory(self, directory: str, extensions: Set[str] = None, 
                      min_size: int = 1024, progress_callback=None) -> Dict[str, List[Dict]]:
        """Scan directory for duplicate files."""
        self.file_hashes.clear()
        self.scanned_files = 0
        self.duplicates_found.clear()
        self.total_duplicate_size = 0
        
        # Count total files first (with limit)
        self.total_files = self.count_files_in_directory(directory, extensions, min_size)
        
        # Debug logging for file type filtering
        if extensions:
            print(f"Scanning for extensions: {extensions}")
            print(f"Total files found with filter: {self.total_files}")
        
        if self.total_files == 0:
            print(f"No files found matching criteria in {directory}")
            return {}
        
        max_scan_files = 10000  # Limit scanning to prevent freezing
        
        # Scan files and calculate hashes
        try:
            for root, dirs, files in os.walk(directory):
                # Skip system directories and limit depth
                dirs[:] = [d for d in dirs if not d.startswith('.') and 
                          d.lower() not in ['system volume information', '$recycle.bin',
                                          'windows', 'program files', 'program files (x86)',
                                          'appdata\\local\\temp', 'temp']]
                
                for file in files:
                    if self.scanned_files >= max_scan_files:  # Prevent excessive scanning
                        break
                        
                    if file.startswith('.'):
                        continue
                        
                    file_path = os.path.join(root, file)
                    
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size < min_size:
                            continue
                            
                        if extensions:
                            file_ext = Path(file_path).suffix.lower()
                            if file_ext not in extensions:
                                continue
                        
                        # Calculate hash
                        file_hash = self.calculate_file_hash(file_path)
                        if file_hash:
                            file_info = self.get_file_info(file_path)
                            if file_info:
                                self.file_hashes[file_hash].append(file_info)
                        
                        self.scanned_files += 1
                        
                        # Update progress more frequently
                        if progress_callback and self.scanned_files % 5 == 0:
                            progress = min(int((self.scanned_files / min(self.total_files, max_scan_files)) * 100), 100)
                            progress_callback(progress, file_path)
                            
                    except (OSError, PermissionError):
                        continue
                
                # Break outer loop if limit reached
                if self.scanned_files >= max_scan_files:
                    break
                        
        except (OSError, PermissionError):
            pass
        
        # Find duplicates
        duplicates = {}
        for file_hash, files in self.file_hashes.items():
            if len(files) > 1:
                # Sort by modification time (newest first)
                files.sort(key=lambda x: os.path.getmtime(x['path']), reverse=True)
                duplicates[file_hash] = files
                
                # Calculate duplicate size (all but the first file)
                for file_info in files[1:]:
                    self.total_duplicate_size += file_info['size']
        
        self.duplicates_found = duplicates
        return duplicates
    
    def get_duplicate_summary(self) -> Dict[str, any]:
        """Get summary of duplicate scan results."""
        if not self.duplicates_found:
            return {
                'total_duplicates': 0,
                'duplicate_groups': 0,
                'potential_savings_mb': 0,
                'potential_savings_gb': 0
            }
        
        total_duplicates = sum(len(files) - 1 for files in self.duplicates_found.values())
        duplicate_groups = len(self.duplicates_found)
        savings_mb = self.total_duplicate_size / (1024**2)
        savings_gb = self.total_duplicate_size / (1024**3)
        
        return {
            'total_duplicates': total_duplicates,
            'duplicate_groups': duplicate_groups,
            'potential_savings_mb': savings_mb,
            'potential_savings_gb': savings_gb,
            'scanned_files': self.scanned_files
        }
    
    def delete_selected_duplicates(self, selected_files: List[str]) -> Dict[str, any]:
        """Delete selected duplicate files."""
        deleted_files = 0
        deleted_size = 0
        errors = []
        
        for file_path in selected_files:
            try:
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    deleted_files += 1
                    deleted_size += file_size
            except (OSError, PermissionError) as e:
                errors.append(f"Cannot delete {file_path}: {str(e)}")
        
        return {
            'deleted_files': deleted_files,
            'deleted_size_mb': deleted_size / (1024**2),
            'errors': errors
        }
    
    def get_common_extensions(self) -> Set[str]:
        """Get common file extensions for filtering."""
        return {
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico',
            # Videos
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v',
            # Audio
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a',
            # Documents
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt',
            # Archives
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
            # Executables
            '.exe', '.msi', '.deb', '.rpm', '.dmg',
            # Other
            '.iso', '.bin', '.img'
        }
    
    def get_extension_categories(self) -> Dict[str, Set[str]]:
        """Get file extensions organized by category."""
        return {
            'Images': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico', '.svg'},
            'Videos': {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'},
            'Audio': {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus'},
            'Documents': {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt', '.ods', '.odp'},
            'Archives': {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'},
            'Executables': {'.exe', '.msi', '.deb', '.rpm', '.dmg', '.app'},
            'Other': {'.iso', '.bin', '.img', '.dll', '.so', '.dylib'}
        }
