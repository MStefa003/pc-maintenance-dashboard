"""
Browser cache and data cleanup module for PC Maintenance Dashboard.
Handles Chrome, Firefox, and Edge browser data cleaning.
"""

import os
import shutil
import sqlite3
from typing import List, Dict


class BrowserCleaner:
    """Handles browser cache and data cleanup."""
    
    def __init__(self):
        self.browsers = self._detect_browsers()
        self.cleaned_size = 0
        self.cleaned_files = 0
    
    def _detect_browsers(self) -> Dict[str, Dict[str, str]]:
        """Detect installed browsers and their data paths."""
        browsers = {}
        user_profile = os.environ.get('USERPROFILE', '')
        
        if not user_profile:
            return browsers
        
        # Chrome paths
        chrome_paths = {
            'cache': os.path.join(user_profile, 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'Cache'),
            'cookies': os.path.join(user_profile, 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'Cookies'),
            'history': os.path.join(user_profile, 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'History'),
            'downloads': os.path.join(user_profile, 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'History'),
            'temp': os.path.join(user_profile, 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'Local Storage')
        }
        
        if any(os.path.exists(path) for path in chrome_paths.values()):
            browsers['Chrome'] = chrome_paths
        
        # Firefox paths
        firefox_base = os.path.join(user_profile, 'AppData', 'Roaming', 'Mozilla', 'Firefox', 'Profiles')
        if os.path.exists(firefox_base):
            try:
                profiles = [d for d in os.listdir(firefox_base) if os.path.isdir(os.path.join(firefox_base, d))]
                if profiles:
                    profile_path = os.path.join(firefox_base, profiles[0])
                    firefox_paths = {
                        'cache': os.path.join(user_profile, 'AppData', 'Local', 'Mozilla', 'Firefox', 'Profiles', profiles[0], 'cache2'),
                        'cookies': os.path.join(profile_path, 'cookies.sqlite'),
                        'history': os.path.join(profile_path, 'places.sqlite'),
                        'downloads': os.path.join(profile_path, 'downloads.sqlite'),
                        'temp': os.path.join(profile_path, 'storage')
                    }
                    browsers['Firefox'] = firefox_paths
            except (OSError, PermissionError):
                pass
        
        # Edge paths
        edge_paths = {
            'cache': os.path.join(user_profile, 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data', 'Default', 'Cache'),
            'cookies': os.path.join(user_profile, 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data', 'Default', 'Cookies'),
            'history': os.path.join(user_profile, 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data', 'Default', 'History'),
            'downloads': os.path.join(user_profile, 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data', 'Default', 'History'),
            'temp': os.path.join(user_profile, 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data', 'Default', 'Local Storage')
        }
        
        if any(os.path.exists(path) for path in edge_paths.values()):
            browsers['Edge'] = edge_paths
        
        return browsers
    
    def get_browser_data_size(self) -> Dict[str, Dict[str, float]]:
        """Get size of browser data for each detected browser."""
        browser_sizes = {}
        
        for browser_name, paths in self.browsers.items():
            browser_sizes[browser_name] = {}
            total_size = 0
            
            for data_type, path in paths.items():
                size = self._get_path_size(path)
                browser_sizes[browser_name][data_type] = size / (1024**2)  # MB
                total_size += size
            
            browser_sizes[browser_name]['total'] = total_size / (1024**2)  # MB
        
        return browser_sizes
    
    def _get_path_size(self, path: str) -> int:
        """Get total size of files in a path."""
        total_size = 0
        
        try:
            if os.path.isfile(path):
                return os.path.getsize(path)
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            if os.path.exists(file_path):
                                total_size += os.path.getsize(file_path)
                        except (OSError, PermissionError):
                            continue
        except (OSError, PermissionError):
            pass
        
        return total_size
    
    def clean_browser_data(self, browser_name: str, data_types: List[str]) -> Dict[str, any]:
        """Clean specified browser data types."""
        if browser_name not in self.browsers:
            return {'success': False, 'error': f'{browser_name} not found'}
        
        self.cleaned_size = 0
        self.cleaned_files = 0
        errors = []
        cleaned_types = []
        
        browser_paths = self.browsers[browser_name]
        
        for data_type in data_types:
            if data_type not in browser_paths:
                continue
            
            path = browser_paths[data_type]
            
            try:
                if data_type in ['cookies', 'history', 'downloads'] and path.endswith('.sqlite'):
                    # Handle SQLite databases
                    if os.path.exists(path):
                        size = os.path.getsize(path)
                        self._clear_sqlite_database(path, data_type)
                        self.cleaned_size += size
                        self.cleaned_files += 1
                        cleaned_types.append(data_type)
                else:
                    # Handle directories and regular files
                    if os.path.exists(path):
                        if os.path.isdir(path):
                            self._clean_directory_browser(path, errors)
                        else:
                            size = os.path.getsize(path)
                            os.remove(path)
                            self.cleaned_size += size
                            self.cleaned_files += 1
                        cleaned_types.append(data_type)
            
            except Exception as e:
                errors.append(f"Error cleaning {browser_name} {data_type}: {str(e)}")
        
        return {
            'success': True,
            'browser': browser_name,
            'cleaned_types': cleaned_types,
            'size_freed_mb': self.cleaned_size / (1024**2),
            'files_deleted': self.cleaned_files,
            'errors': errors
        }
    
    def _clear_sqlite_database(self, db_path: str, data_type: str):
        """Clear specific tables in SQLite database."""
        try:
            # Create backup
            backup_path = db_path + '.backup'
            shutil.copy2(db_path, backup_path)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            if data_type == 'cookies':
                cursor.execute("DELETE FROM cookies")
            elif data_type == 'history':
                cursor.execute("DELETE FROM urls")
                cursor.execute("DELETE FROM visits")
            elif data_type == 'downloads':
                cursor.execute("DELETE FROM downloads")
            
            conn.commit()
            conn.close()
            
            # Remove backup if successful
            if os.path.exists(backup_path):
                os.remove(backup_path)
                
        except Exception as e:
            # Restore backup if something went wrong
            if os.path.exists(backup_path):
                shutil.move(backup_path, db_path)
            raise e
    
    def _clean_directory_browser(self, directory: str, errors: List[str]):
        """Clean files in a browser directory."""
        try:
            for root, dirs, files in os.walk(directory, topdown=False):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            self.cleaned_size += file_size
                            self.cleaned_files += 1
                    except (OSError, PermissionError) as e:
                        errors.append(f"Cannot delete {file_path}: {str(e)}")
                        continue
                
                # Remove empty directories
                for dir_name in dirs:
                    try:
                        dir_path = os.path.join(root, dir_name)
                        if os.path.exists(dir_path) and not os.listdir(dir_path):
                            os.rmdir(dir_path)
                    except (OSError, PermissionError):
                        continue
        except Exception as e:
            errors.append(f"Error accessing {directory}: {str(e)}")
    
    def clean_all_browsers(self, data_types: List[str]) -> Dict[str, any]:
        """Clean specified data types from all detected browsers."""
        results = []
        total_size_freed = 0
        total_files_deleted = 0
        all_errors = []
        
        for browser_name in self.browsers.keys():
            result = self.clean_browser_data(browser_name, data_types)
            if result['success']:
                results.append(result)
                total_size_freed += result['size_freed_mb']
                total_files_deleted += result['files_deleted']
                all_errors.extend(result['errors'])
        
        return {
            'success': True,
            'browsers_cleaned': len(results),
            'total_size_freed_mb': total_size_freed,
            'total_files_deleted': total_files_deleted,
            'results': results,
            'errors': all_errors
        }
    
    def get_detected_browsers(self) -> List[str]:
        """Get list of detected browser names."""
        return list(self.browsers.keys())
