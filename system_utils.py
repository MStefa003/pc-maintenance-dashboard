"""
System utilities module for PC Maintenance Dashboard.
Handles system monitoring, file cleanup, and startup management.
"""

import os
import sys
import shutil
import tempfile
import psutil
import platform
import socket
import subprocess
import sqlite3
import json
import time
import stat
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta


class SystemMonitor:
    """Handles system resource monitoring."""
    
    @staticmethod
    def get_cpu_usage() -> float:
        """Get current CPU usage percentage."""
        return psutil.cpu_percent(interval=1)
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get memory usage information."""
        memory = psutil.virtual_memory()
        return {
            'total': memory.total / (1024**3),  # GB
            'used': memory.used / (1024**3),    # GB
            'available': memory.available / (1024**3),  # GB
            'percent': memory.percent
        }
    
    @staticmethod
    def get_disk_usage(path: str = None) -> Dict[str, float]:
        """Get disk usage for specified path or system root."""
        if path is None:
            if platform.system() == "Windows":
                path = "C:\\"
            else:
                path = "/"
        
        usage = shutil.disk_usage(path)
        total = usage.total / (1024**3)  # GB
        used = usage.used / (1024**3)    # GB
        free = usage.free / (1024**3)    # GB
        
        return {
            'total': total,
            'used': used,
            'free': free,
            'percent': (used / total) * 100
        }
    
    @staticmethod
    def get_network_info() -> Dict[str, any]:
        """Get network interface information."""
        try:
            interfaces = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            io_counters = psutil.net_io_counters(pernic=True)
            
            network_info = {
                'interfaces': [],
                'total_sent': 0,
                'total_received': 0
            }
            
            for interface, addresses in interfaces.items():
                if interface in stats:
                    interface_info = {
                        'name': interface,
                        'is_up': stats[interface].isup,
                        'speed': stats[interface].speed,
                        'addresses': []
                    }
                    
                    for addr in addresses:
                        if addr.family == socket.AF_INET:
                            interface_info['addresses'].append({
                                'type': 'IPv4',
                                'address': addr.address,
                                'netmask': addr.netmask
                            })
                    
                    if interface in io_counters:
                        interface_info['bytes_sent'] = io_counters[interface].bytes_sent
                        interface_info['bytes_recv'] = io_counters[interface].bytes_recv
                        network_info['total_sent'] += io_counters[interface].bytes_sent
                        network_info['total_received'] += io_counters[interface].bytes_recv
                    
                    network_info['interfaces'].append(interface_info)
            
            return network_info
        except Exception:
            return {'interfaces': [], 'total_sent': 0, 'total_received': 0}
    
    @staticmethod
    def get_process_info(limit: int = 10) -> List[Dict[str, any]]:
        """Get top processes by CPU usage."""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] is None:
                        proc_info['cpu_percent'] = 0.0
                    processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage and return top processes
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            return processes[:limit]
        except Exception:
            return []
    
    @staticmethod
    def get_system_temperature() -> Dict[str, float]:
        """Get system temperature information (if available)."""
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                temp_info = {}
                for name, entries in temps.items():
                    if entries:
                        temp_info[name] = entries[0].current
                return temp_info
            return {}
        except (AttributeError, OSError):
            # Temperature sensors not available on this system
            return {}
    
    @staticmethod
    def get_boot_time() -> str:
        """Get system boot time."""
        try:
            import datetime
            boot_time = psutil.boot_time()
            return datetime.datetime.fromtimestamp(boot_time).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return 'Unknown'


class FileCleanup:
    """Handles temporary file and cache cleanup."""
    
    def __init__(self, min_file_age_hours: float = 1.0):
        self.temp_dirs = self._get_temp_directories()
        self.cleaned_size = 0
        self.cleaned_files = 0
        self.skipped_files = 0
        self.permission_errors = 0
        self.in_use_errors = 0
        self.min_file_age_hours = min_file_age_hours  # Configurable minimum file age
    
    def _get_temp_directories(self) -> List[str]:
        """Get list of temporary directories to clean."""
        temp_dirs = []
        
        # System temp directory
        temp_dirs.append(tempfile.gettempdir())
        
        if platform.system() == "Windows":
            # Windows-specific temp directories
            user_profile = os.environ.get('USERPROFILE', '')
            if user_profile:
                temp_dirs.extend([
                    os.path.join(user_profile, 'AppData', 'Local', 'Temp'),
                    os.path.join(user_profile, 'AppData', 'Local', 'Microsoft', 'Windows', 'Temporary Internet Files'),
                    os.path.join(user_profile, 'AppData', 'Local', 'Microsoft', 'Windows', 'INetCache'),
                ])
            
            # System temp directories
            temp_dirs.extend([
                'C:\\Windows\\Temp',
                'C:\\Windows\\Prefetch',
            ])
        
        elif platform.system() == "Darwin":  # macOS
            user_home = os.path.expanduser('~')
            temp_dirs.extend([
                os.path.join(user_home, 'Library', 'Caches'),
                '/tmp',
                '/var/tmp'
            ])
        
        else:  # Linux
            user_home = os.path.expanduser('~')
            temp_dirs.extend([
                os.path.join(user_home, '.cache'),
                '/tmp',
                '/var/tmp'
            ])
        
        # Filter existing directories
        return [d for d in temp_dirs if os.path.exists(d)]
    
    def scan_temp_files(self) -> Dict[str, int]:
        """Scan temporary directories and return file count and size."""
        total_size = 0
        total_files = 0
        
        for temp_dir in self.temp_dirs:
            try:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            if os.path.exists(file_path):
                                total_size += os.path.getsize(file_path)
                                total_files += 1
                        except (OSError, PermissionError):
                            continue
            except (OSError, PermissionError):
                continue
        
        return {
            'size_mb': total_size / (1024**2),
            'file_count': total_files
        }
    
    def clean_temp_files(self) -> Dict[str, any]:
        """Clean temporary files and return cleanup statistics."""
        self.cleaned_size = 0
        self.cleaned_files = 0
        self.skipped_files = 0
        self.permission_errors = 0
        self.in_use_errors = 0
        errors = []
        
        for temp_dir in self.temp_dirs:
            try:
                self._clean_directory_smart(temp_dir, errors)
            except Exception as e:
                errors.append(f"Error cleaning {temp_dir}: {str(e)}")
        
        return {
            'size_freed_mb': self.cleaned_size / (1024**2),
            'files_deleted': self.cleaned_files,
            'skipped_files': self.skipped_files,
            'permission_errors': self.permission_errors,
            'in_use_errors': self.in_use_errors,
            'errors': errors,
            'summary': self._generate_cleanup_summary()
        }
    
    def _generate_cleanup_summary(self) -> str:
        """Generate a human-readable cleanup summary."""
        if self.cleaned_files == 0:
            if self.skipped_files > 0:
                return f"No files cleaned. {self.skipped_files} files were skipped (too recent or protected)."
            else:
                return "No temporary files found to clean."
        
        summary = f"Successfully cleaned {self.cleaned_files} files, freed {self.cleaned_size / (1024**2):.1f} MB."
        
        if self.skipped_files > 0:
            summary += f" {self.skipped_files} files skipped."
        
        if self.in_use_errors > 0:
            summary += f" {self.in_use_errors} files were in use by other processes."
        
        return summary
    
    def _clean_directory_smart(self, directory: str, errors: List[str]):
        """Smart directory cleaning with age filtering and better error handling."""
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    try:
                        if not os.path.exists(file_path):
                            continue
                            
                        # Check file age - skip recently created files
                        if not self._is_file_old_enough(file_path):
                            self.skipped_files += 1
                            continue
                            
                        # Skip system critical files
                        if self._is_system_critical_file(file_path):
                            self.skipped_files += 1
                            continue
                            
                        file_size = os.path.getsize(file_path)
                        
                        # Try to delete with retry mechanism
                        if self._delete_file_with_retry(file_path):
                            self.cleaned_size += file_size
                            self.cleaned_files += 1
                        else:
                            self.skipped_files += 1
                            
                    except PermissionError as e:
                        self.permission_errors += 1
                        if "WinError 32" in str(e) or "being used by another process" in str(e):
                            self.in_use_errors += 1
                        # Only log first few permission errors to avoid spam
                        if len(errors) < 5:
                            errors.append(f"Cannot delete {file_path}: {str(e)}")
                    except (OSError, FileNotFoundError):
                        # File might have been deleted by another process
                        continue
                    except Exception as e:
                        if len(errors) < 10:
                            errors.append(f"Unexpected error with {file_path}: {str(e)}")
                
                # Try to remove empty directories (less aggressively)
                self._cleanup_empty_directories(root, dirs)
                
        except Exception as e:
            errors.append(f"Error accessing {directory}: {str(e)}")
    
    def _is_file_old_enough(self, file_path: str) -> bool:
        """Check if file is old enough to be safely deleted."""
        try:
            file_stat = os.stat(file_path)
            file_age = datetime.now() - datetime.fromtimestamp(file_stat.st_mtime)
            return file_age > timedelta(hours=self.min_file_age_hours)
        except (OSError, ValueError):
            return False
    
    def _is_system_critical_file(self, file_path: str) -> bool:
        """Check if file is system critical and should not be deleted."""
        filename = os.path.basename(file_path).lower()
        
        # Skip files that are likely system critical
        critical_patterns = [
            'desktop.ini',
            'thumbs.db',
            '.sys',
            '.dll',
            '.exe',
            'hiberfil.sys',
            'pagefile.sys',
            'swapfile.sys'
        ]
        
        # Skip files with certain extensions that are likely important
        important_extensions = ['.log', '.ini', '.cfg', '.config']
        
        for pattern in critical_patterns:
            if pattern in filename:
                return True
        
        # Check if file is in a critical system directory
        critical_dirs = ['system32', 'syswow64', 'windows\system', 'program files']
        file_path_lower = file_path.lower()
        for critical_dir in critical_dirs:
            if critical_dir in file_path_lower:
                return True
                
        return False
    
    def _delete_file_with_retry(self, file_path: str, max_retries: int = 3) -> bool:
        """Try to delete file with retry mechanism for locked files."""
        for attempt in range(max_retries):
            try:
                # Try to change file permissions if needed
                if platform.system() == "Windows":
                    try:
                        # Make file writable
                        os.chmod(file_path, stat.S_IWRITE)
                    except (OSError, PermissionError):
                        pass
                
                os.remove(file_path)
                return True
                
            except PermissionError as e:
                if "WinError 32" in str(e) or "being used by another process" in str(e):
                    # File is in use - try again after a short delay
                    if attempt < max_retries - 1:
                        time.sleep(0.2 * (attempt + 1))  # Increasing delay
                        continue
                raise e
            except (OSError, FileNotFoundError):
                # File was deleted by another process or doesn't exist
                return False
            except Exception:
                # Unexpected error - don't retry
                return False
                
        return False
    
    def _cleanup_empty_directories(self, root: str, dirs: List[str]):
        """Safely cleanup empty directories."""
        for dir_name in dirs:
            try:
                dir_path = os.path.join(root, dir_name)
                if os.path.exists(dir_path) and not os.listdir(dir_path):
                    # Only remove if it's clearly a temp directory
                    if any(temp_indicator in dir_path.lower() for temp_indicator in ['temp', 'tmp', 'cache']):
                        os.rmdir(dir_path)
            except (OSError, PermissionError):
                continue


class StartupManager:
    """Handles startup application management."""
    
    def __init__(self):
        self.system = platform.system()
    
    def get_startup_programs(self) -> List[Dict[str, str]]:
        """Get list of startup programs."""
        if self.system == "Windows":
            return self._get_windows_startup_programs()
        elif self.system == "Darwin":
            return self._get_macos_startup_programs()
        else:
            return self._get_linux_startup_programs()
    
    def _get_windows_startup_programs(self) -> List[Dict[str, str]]:
        """Get Windows startup programs from registry."""
        startup_programs = []
        
        try:
            import winreg
            
            # Registry keys to check
            registry_keys = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
            ]
            
            for hkey, subkey in registry_keys:
                try:
                    with winreg.OpenKey(hkey, subkey) as key:
                        i = 0
                        while True:
                            try:
                                name, value, _ = winreg.EnumValue(key, i)
                                startup_programs.append({
                                    'name': name,
                                    'path': value,
                                    'enabled': True,
                                    'location': f"{hkey}\\{subkey}"
                                })
                                i += 1
                            except WindowsError:
                                break
                except WindowsError:
                    continue
        
        except ImportError:
            # winreg not available (non-Windows system)
            pass
        
        return startup_programs
    
    def _get_macos_startup_programs(self) -> List[Dict[str, str]]:
        """Get macOS startup programs."""
        startup_programs = []
        
        # LaunchAgents directories
        launch_dirs = [
            os.path.expanduser('~/Library/LaunchAgents'),
            '/Library/LaunchAgents',
            '/System/Library/LaunchAgents'
        ]
        
        for launch_dir in launch_dirs:
            if os.path.exists(launch_dir):
                try:
                    for file in os.listdir(launch_dir):
                        if file.endswith('.plist'):
                            startup_programs.append({
                                'name': file.replace('.plist', ''),
                                'path': os.path.join(launch_dir, file),
                                'enabled': True,
                                'location': launch_dir
                            })
                except PermissionError:
                    continue
        
        return startup_programs
    
    def _get_linux_startup_programs(self) -> List[Dict[str, str]]:
        """Get Linux startup programs."""
        startup_programs = []
        
        # Autostart directories
        autostart_dirs = [
            os.path.expanduser('~/.config/autostart'),
            '/etc/xdg/autostart'
        ]
        
        for autostart_dir in autostart_dirs:
            if os.path.exists(autostart_dir):
                try:
                    for file in os.listdir(autostart_dir):
                        if file.endswith('.desktop'):
                            startup_programs.append({
                                'name': file.replace('.desktop', ''),
                                'path': os.path.join(autostart_dir, file),
                                'enabled': True,
                                'location': autostart_dir
                            })
                except PermissionError:
                    continue
        
        return startup_programs
    
    def toggle_startup_program(self, program: Dict[str, str], enable: bool) -> bool:
        """Enable or disable a startup program."""
        if self.system == "Windows":
            return self._toggle_windows_startup(program, enable)
        elif self.system == "Darwin":
            return self._toggle_macos_startup(program, enable)
        else:
            return self._toggle_linux_startup(program, enable)
    
    def _toggle_windows_startup(self, program: Dict[str, str], enable: bool) -> bool:
        """Toggle Windows startup program."""
        try:
            import winreg
            
            # Parse location to get registry key
            location_parts = program['location'].split('\\')
            if len(location_parts) < 2:
                return False
            
            hkey_name = location_parts[0]
            subkey = '\\'.join(location_parts[1:])
            
            # Convert string to registry key
            hkey_map = {
                'HKEY_CURRENT_USER': winreg.HKEY_CURRENT_USER,
                'HKEY_LOCAL_MACHINE': winreg.HKEY_LOCAL_MACHINE
            }
            
            hkey = hkey_map.get(hkey_name)
            if not hkey:
                return False
            
            with winreg.OpenKey(hkey, subkey, 0, winreg.KEY_SET_VALUE) as key:
                if enable:
                    winreg.SetValueEx(key, program['name'], 0, winreg.REG_SZ, program['path'])
                else:
                    try:
                        winreg.DeleteValue(key, program['name'])
                    except WindowsError:
                        pass
            
            return True
        
        except Exception:
            return False
    
    def _toggle_macos_startup(self, program: Dict[str, str], enable: bool) -> bool:
        """Toggle macOS startup program."""
        try:
            if enable:
                # Re-enable by ensuring file exists
                return os.path.exists(program['path'])
            else:
                # Disable by moving to disabled location
                disabled_path = program['path'] + '.disabled'
                if os.path.exists(program['path']):
                    os.rename(program['path'], disabled_path)
                return True
        except Exception:
            return False
    
    def _toggle_linux_startup(self, program: Dict[str, str], enable: bool) -> bool:
        """Toggle Linux startup program."""
        try:
            if enable:
                # Re-enable by ensuring file exists and removing Hidden=true
                if os.path.exists(program['path']):
                    with open(program['path'], 'r') as f:
                        content = f.read()
                    
                    # Remove Hidden=true line if present
                    lines = content.split('\n')
                    lines = [line for line in lines if not line.startswith('Hidden=')]
                    
                    with open(program['path'], 'w') as f:
                        f.write('\n'.join(lines))
                return True
            else:
                # Disable by adding Hidden=true
                if os.path.exists(program['path']):
                    with open(program['path'], 'r') as f:
                        content = f.read()
                    
                    if 'Hidden=true' not in content:
                        content += '\nHidden=true'
                        with open(program['path'], 'w') as f:
                            f.write(content)
                return True
        except Exception:
            return False
