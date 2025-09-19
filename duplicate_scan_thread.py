"""
Thread class for duplicate file scanning to keep UI responsive.
"""

from PyQt5.QtCore import QThread, pyqtSignal


class DuplicateScanThread(QThread):
    """Worker thread for duplicate file scanning."""
    
    progress_updated = pyqtSignal(int, str)  # progress, current_file
    scan_completed = pyqtSignal(dict)  # duplicates found
    
    def __init__(self, duplicate_finder, scan_path, extensions, min_size):
        super().__init__()
        self.duplicate_finder = duplicate_finder
        self.scan_path = scan_path
        self.extensions = extensions
        self.min_size = min_size
    
    def run(self):
        """Run the duplicate scan in background thread."""
        def progress_callback(progress, current_file):
            self.progress_updated.emit(progress, current_file)
        
        duplicates = self.duplicate_finder.scan_directory(
            self.scan_path, 
            self.extensions, 
            self.min_size, 
            progress_callback
        )
        
        self.scan_completed.emit(duplicates)
