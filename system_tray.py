"""
System tray integration for PC Maintenance Dashboard.
"""

import sys
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication, QMessageBox
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor
from system_utils import SystemMonitor, FileCleanup


class SystemTrayManager(QObject):
    """Manages system tray functionality."""
    
    show_window = pyqtSignal()
    exit_app = pyqtSignal()
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.monitor = SystemMonitor()
        self.cleanup = FileCleanup()
        
        # Create tray icon
        self.tray_icon = QSystemTrayIcon()
        self.create_tray_icon()
        self.create_tray_menu()
        
        # Setup monitoring timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.update_tray_status)
        self.monitor_timer.start(30000)  # Update every 30 seconds
        
        # Connect signals
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Initial status update
        self.update_tray_status()
    
    def create_tray_icon(self):
        """Create the system tray icon."""
        # Create a simple icon programmatically
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 123, 255))  # Blue background
        
        painter = QPainter(pixmap)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(8, 8, 16, 16)
        painter.end()
        
        icon = QIcon(pixmap)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("PC Maintenance Dashboard")
    
    def create_tray_menu(self):
        """Create the context menu for the tray icon."""
        menu = QMenu()
        
        # Show window action
        show_action = QAction("Show Dashboard", self)
        show_action.triggered.connect(self.show_window.emit)
        menu.addAction(show_action)
        
        menu.addSeparator()
        
        # Quick actions
        cleanup_action = QAction("Quick Cleanup", self)
        cleanup_action.triggered.connect(self.quick_cleanup)
        menu.addAction(cleanup_action)
        
        refresh_action = QAction("Refresh Status", self)
        refresh_action.triggered.connect(self.update_tray_status)
        menu.addAction(refresh_action)
        
        menu.addSeparator()
        
        # System info submenu
        info_menu = menu.addMenu("System Info")
        
        self.cpu_action = QAction("CPU: --", self)
        self.memory_action = QAction("Memory: --", self)
        self.disk_action = QAction("Disk: --", self)
        
        info_menu.addAction(self.cpu_action)
        info_menu.addAction(self.memory_action)
        info_menu.addAction(self.disk_action)
        
        menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_app.emit)
        menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(menu)
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window.emit()
    
    def update_tray_status(self):
        """Update system status in tray menu."""
        try:
            # Get system info
            cpu_usage = self.monitor.get_cpu_usage()
            memory_info = self.monitor.get_memory_usage()
            disk_info = self.monitor.get_disk_usage()
            
            # Update menu items
            self.cpu_action.setText(f"CPU: {cpu_usage:.1f}%")
            self.memory_action.setText(f"Memory: {memory_info['percent']:.1f}%")
            self.disk_action.setText(f"Disk: {disk_info['percent']:.1f}%")
            
            # Update tooltip with current status
            tooltip = (f"PC Maintenance Dashboard\n"
                      f"CPU: {cpu_usage:.1f}% | "
                      f"RAM: {memory_info['percent']:.1f}% | "
                      f"Disk: {disk_info['percent']:.1f}%")
            self.tray_icon.setToolTip(tooltip)
            
            # Show warning if resources are high
            if cpu_usage > 90 or memory_info['percent'] > 90 or disk_info['percent'] > 90:
                self.show_resource_warning(cpu_usage, memory_info['percent'], disk_info['percent'])
        
        except Exception as e:
            self.tray_icon.setToolTip(f"PC Maintenance Dashboard\nError: {str(e)}")
    
    def show_resource_warning(self, cpu, memory, disk):
        """Show warning for high resource usage."""
        if not hasattr(self, '_last_warning_time'):
            self._last_warning_time = 0
        
        import time
        current_time = time.time()
        
        # Only show warning every 5 minutes
        if current_time - self._last_warning_time > 300:
            warning_msg = "High resource usage detected:\n"
            if cpu > 90:
                warning_msg += f"• CPU: {cpu:.1f}%\n"
            if memory > 90:
                warning_msg += f"• Memory: {memory:.1f}%\n"
            if disk > 90:
                warning_msg += f"• Disk: {disk:.1f}%\n"
            
            self.tray_icon.showMessage(
                "PC Maintenance Alert",
                warning_msg,
                QSystemTrayIcon.Warning,
                5000
            )
            self._last_warning_time = current_time
    
    def quick_cleanup(self):
        """Perform quick cleanup from tray."""
        try:
            scan_result = self.cleanup.scan_temp_files()
            if scan_result['size_mb'] > 0:
                cleanup_result = self.cleanup.clean_temp_files()
                self.tray_icon.showMessage(
                    "Cleanup Complete",
                    f"Freed {cleanup_result['size_freed_mb']:.1f} MB of disk space!",
                    QSystemTrayIcon.Information,
                    3000
                )
            else:
                self.tray_icon.showMessage(
                    "Cleanup Complete",
                    "No temporary files found to clean.",
                    QSystemTrayIcon.Information,
                    2000
                )
        except Exception as e:
            self.tray_icon.showMessage(
                "Cleanup Error",
                f"Error during cleanup: {str(e)}",
                QSystemTrayIcon.Critical,
                3000
            )
    
    def show(self):
        """Show the tray icon."""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.show()
            return True
        return False
    
    def hide(self):
        """Hide the tray icon."""
        self.tray_icon.hide()
    
    def is_visible(self):
        """Check if tray icon is visible."""
        return self.tray_icon.isVisible()
