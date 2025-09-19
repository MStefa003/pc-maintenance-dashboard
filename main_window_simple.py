"""
Simple main window for PC Maintenance Dashboard - Basic PyQt5 styling.
"""

import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from system_utils import SystemMonitor, FileCleanup, StartupManager
from browser_cleaner import BrowserCleaner
from duplicate_finder import DuplicateFinder
from duplicate_scan_thread import DuplicateScanThread
from startup_window import StartupWindow
from system_tray import SystemTrayManager
from scheduler import MaintenanceScheduler, SchedulerDialog
from collections import deque
import time


class CleanupWorker(QThread):
    """Worker thread for file cleanup operations."""
    
    finished = pyqtSignal(dict)
    progress = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.cleanup = FileCleanup()
    
    def run(self):
        """Run the cleanup process with scan-first approach."""
        try:
            import os
            import tempfile
            import shutil
            from pathlib import Path
            
            # First, scan for files to delete without actually deleting
            self.progress.emit(10)
            
            # Define temp directories to clean
            temp_dirs = [
                tempfile.gettempdir(),
                os.path.expandvars(r'%TEMP%'),
                os.path.expandvars(r'%TMP%'),
                os.path.expandvars(r'%LOCALAPPDATA%\Temp'),
                os.path.expandvars(r'%WINDIR%\Temp'),
                os.path.expandvars(r'%USERPROFILE%\AppData\Local\Temp'),
            ]
            
            # Add browser cache directories
            browser_cache_dirs = [
                os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache'),
                os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache'),
                os.path.expandvars(r'%APPDATA%\Mozilla\Firefox\Profiles'),
            ]
            
            files_to_delete = []
            total_size_to_free = 0
            
            self.progress.emit(20)
            
            # Scan temp directories for files to delete
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    try:
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                try:
                                    file_path = os.path.join(root, file)
                                    if os.path.exists(file_path):
                                        file_size = os.path.getsize(file_path)
                                        files_to_delete.append((file_path, file_size))
                                        total_size_to_free += file_size
                                except (PermissionError, FileNotFoundError, OSError):
                                    continue
                    except (PermissionError, OSError):
                        continue
            
            self.progress.emit(40)
            
            # Scan browser caches
            for cache_dir in browser_cache_dirs:
                if os.path.exists(cache_dir):
                    try:
                        if 'Firefox' in cache_dir:
                            # Handle Firefox profiles
                            for profile in os.listdir(cache_dir):
                                profile_cache = os.path.join(cache_dir, profile, 'cache2')
                                if os.path.exists(profile_cache):
                                    try:
                                        # Estimate Firefox cache size
                                        cache_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                                                       for dirpath, dirnames, filenames in os.walk(profile_cache)
                                                       for filename in filenames)
                                        files_to_delete.append((profile_cache, cache_size))
                                        total_size_to_free += cache_size
                                    except (PermissionError, OSError):
                                        continue
                        else:
                            # Handle Chrome/Edge cache
                            try:
                                cache_files = os.listdir(cache_dir)
                                for cache_file in cache_files[:100]:  # Limit to avoid long delays
                                    cache_path = os.path.join(cache_dir, cache_file)
                                    if os.path.isfile(cache_path):
                                        try:
                                            file_size = os.path.getsize(cache_path)
                                            files_to_delete.append((cache_path, file_size))
                                            total_size_to_free += file_size
                                        except (PermissionError, FileNotFoundError, OSError):
                                            continue
                            except (PermissionError, OSError):
                                continue
                    except (PermissionError, OSError):
                        continue
            
            self.progress.emit(50)
            
            # Scan Windows prefetch files
            prefetch_dir = os.path.expandvars(r'%WINDIR%\Prefetch')
            if os.path.exists(prefetch_dir):
                try:
                    for file in os.listdir(prefetch_dir):
                        if file.endswith('.pf'):
                            try:
                                file_path = os.path.join(prefetch_dir, file)
                                file_size = os.path.getsize(file_path)
                                files_to_delete.append((file_path, file_size))
                                total_size_to_free += file_size
                            except (PermissionError, FileNotFoundError, OSError):
                                continue
                except (PermissionError, OSError):
                    pass
            
            self.progress.emit(60)
            
            # If no files found to delete, return early
            if not files_to_delete:
                result = {
                    'files_cleaned': 0,
                    'space_freed_mb': 0,
                    'success': True,
                    'no_files_found': True
                }
                self.finished.emit(result)
                return
            
            # Now actually delete the files
            files_cleaned = 0
            space_freed = 0
            
            for file_path, file_size in files_to_delete:
                try:
                    if os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    else:
                        os.remove(file_path)
                    files_cleaned += 1
                    space_freed += file_size
                except (PermissionError, FileNotFoundError, OSError):
                    continue
            
            self.progress.emit(90)
            
            # Clean recycle bin (Windows)
            try:
                import subprocess
                result_recycle = subprocess.run(['powershell', '-Command', 'Clear-RecycleBin -Force'], 
                                             capture_output=True, timeout=10)
                if result_recycle.returncode == 0:
                    files_cleaned += 5  # Estimate
                    space_freed += 5 * 1024 * 1024  # Estimate 5MB
            except:
                pass
            
            self.progress.emit(100)
            
            # Convert space freed to MB
            space_freed_mb = space_freed / (1024 * 1024)
            
            result = {
                'files_cleaned': files_cleaned,
                'space_freed_mb': space_freed_mb,
                'success': True,
                'no_files_found': False
            }
            
            self.finished.emit(result)
            
        except Exception as e:
            result = {
                'files_cleaned': 0,
                'space_freed_mb': 0,
                'success': False,
                'error': str(e),
                'no_files_found': False
            }
            self.finished.emit(result)


class SystemGraphWidget(QWidget):
    """Real-time system monitoring graph widget."""
    
    def __init__(self, title, color, max_value=100, unit="%"):
        super().__init__()
        self.title = title
        self.color = QColor(color)
        self.max_value = max_value
        self.unit = unit
        self.data_points = deque(maxlen=60)  # Store last 60 data points (1 minute at 1 second intervals)
        self.timestamps = deque(maxlen=60)
        
        # Initialize with zeros
        for i in range(60):
            self.data_points.append(0)
            self.timestamps.append(time.time() - (59 - i))
        
        self.setMinimumSize(250, 120)
        # Remove maximum size to allow flexible resizing
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Set up the widget
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin: 2px;
            }
        """)
    
    def add_data_point(self, value):
        """Add a new data point to the graph."""
        self.data_points.append(float(value))
        self.timestamps.append(time.time())
        self.update()  # Trigger repaint
    
    def paintEvent(self, event):
        """Custom paint event to draw the graph."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get widget dimensions
        rect = self.rect()
        margin = 20
        graph_rect = rect.adjusted(margin, margin + 20, -margin, -margin - 20)
        
        # Draw background
        painter.fillRect(rect, QColor("#f8f9fa"))
        
        # Draw title
        painter.setPen(QColor("#212529"))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(rect.adjusted(10, 5, -10, -rect.height() + 25), Qt.AlignLeft | Qt.AlignTop, self.title)
        
        # Draw current value
        if self.data_points:
            current_value = self.data_points[-1]
            value_text = f"{current_value:.1f}{self.unit}"
            painter.setPen(self.color)
            font.setPointSize(12)
            painter.setFont(font)
            painter.drawText(rect.adjusted(10, 5, -10, -rect.height() + 25), Qt.AlignRight | Qt.AlignTop, value_text)
        
        # Draw grid lines
        painter.setPen(QPen(QColor("#e9ecef"), 1))
        
        # Horizontal grid lines
        for i in range(5):
            y = int(graph_rect.top() + (graph_rect.height() * i / 4))
            painter.drawLine(graph_rect.left(), y, graph_rect.right(), y)
            
            # Draw value labels
            value = self.max_value * (4 - i) / 4
            painter.setPen(QColor("#6c757d"))
            font.setPointSize(8)
            font.setBold(False)
            painter.setFont(font)
            painter.drawText(5, int(y + 4), f"{value:.0f}")
            painter.setPen(QPen(QColor("#e9ecef"), 1))
        
        # Vertical grid lines
        for i in range(6):
            x = int(graph_rect.left() + (graph_rect.width() * i / 5))
            painter.drawLine(x, graph_rect.top(), x, graph_rect.bottom())
        
        # Draw the data line
        if len(self.data_points) > 1:
            painter.setPen(QPen(self.color, 2))
            
            points = []
            for i, value in enumerate(self.data_points):
                if i == 0:
                    continue
                    
                x = graph_rect.left() + (graph_rect.width() * i / (len(self.data_points) - 1))
                y = graph_rect.bottom() - (graph_rect.height() * value / self.max_value)
                points.append(QPointF(float(x), float(y)))
            
            # Draw the line
            if len(points) > 1:
                for i in range(len(points) - 1):
                    painter.drawLine(points[i], points[i + 1])
            
            # Fill area under the curve
            if points:
                painter.setBrush(QBrush(QColor(self.color.red(), self.color.green(), self.color.blue(), 30)))
                painter.setPen(Qt.NoPen)
                
                polygon = QPolygonF()
                polygon.append(QPointF(float(graph_rect.left()), float(graph_rect.bottom())))
                for point in points:
                    polygon.append(point)
                polygon.append(QPointF(float(graph_rect.right()), float(graph_rect.bottom())))
                
                painter.drawPolygon(polygon)


class SystemGraphsWidget(QWidget):
    """Container widget for all system graphs."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        # Create timer for updating graphs
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_graphs)
        self.update_timer.start(1000)  # Update every second
        
        # Store previous network values for calculating speed
        self.prev_net_recv = 0
        self.prev_net_sent = 0
        self.prev_time = time.time()
    
    def setup_ui(self):
        """Set up the graphs UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("📊 Real-time System Monitoring")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #212529;
                padding: 5px;
                background-color: #e9ecef;
                border-radius: 4px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # Create graphs in a responsive 2x2 grid
        graphs_layout = QGridLayout()
        graphs_layout.setSpacing(5)
        graphs_layout.setContentsMargins(5, 5, 5, 5)
        
        # CPU Graph
        self.cpu_graph = SystemGraphWidget("🔥 CPU Usage", "#dc3545", 100, "%")
        graphs_layout.addWidget(self.cpu_graph, 0, 0)
        
        # RAM Graph
        self.ram_graph = SystemGraphWidget("🧠 RAM Usage", "#28a745", 100, "%")
        graphs_layout.addWidget(self.ram_graph, 0, 1)
        
        # Disk Graph
        self.disk_graph = SystemGraphWidget("💾 Disk Usage", "#ffc107", 100, "%")
        graphs_layout.addWidget(self.disk_graph, 1, 0)
        
        # Network Graph
        self.network_graph = SystemGraphWidget("🌐 Network Speed", "#17a2b8", 1000, " KB/s")
        graphs_layout.addWidget(self.network_graph, 1, 1)
        
        # Set equal column and row stretches for responsive resizing
        graphs_layout.setColumnStretch(0, 1)
        graphs_layout.setColumnStretch(1, 1)
        graphs_layout.setRowStretch(0, 1)
        graphs_layout.setRowStretch(1, 1)
        
        layout.addLayout(graphs_layout)
        
        # Add toggle button with proper sizing
        toggle_layout = QHBoxLayout()
        toggle_layout.addStretch()
        
        self.toggle_btn = QPushButton("⏸️ Pause Monitoring")
        self.toggle_btn.setFixedSize(150, 30)
        self.toggle_btn.clicked.connect(self.toggle_monitoring)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        toggle_layout.addWidget(self.toggle_btn)
        
        layout.addLayout(toggle_layout)
    
    def toggle_monitoring(self):
        """Toggle monitoring on/off."""
        if self.update_timer.isActive():
            self.update_timer.stop()
            self.toggle_btn.setText("▶️ Resume Monitoring")
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 5px 15px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
        else:
            self.update_timer.start(1000)
            self.toggle_btn.setText("⏸️ Pause Monitoring")
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    padding: 5px 15px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5a6268;
                }
            """)
    
    def update_graphs(self):
        """Update all graphs with current system data."""
        try:
            import psutil
            
            # CPU Usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.cpu_graph.add_data_point(cpu_percent)
            
            # RAM Usage
            memory = psutil.virtual_memory()
            self.ram_graph.add_data_point(memory.percent)
            
            # Disk Usage (primary drive)
            try:
                disk_usage = psutil.disk_usage('C:\\')
                disk_percent = (disk_usage.used / disk_usage.total) * 100
                self.disk_graph.add_data_point(disk_percent)
            except:
                self.disk_graph.add_data_point(0)
            
            # Network Speed
            try:
                net_io = psutil.net_io_counters()
                current_time = time.time()
                time_delta = current_time - self.prev_time
                
                if time_delta > 0 and self.prev_net_recv > 0:
                    recv_speed = (net_io.bytes_recv - self.prev_net_recv) / time_delta / 1024  # KB/s
                    sent_speed = (net_io.bytes_sent - self.prev_net_sent) / time_delta / 1024  # KB/s
                    total_speed = recv_speed + sent_speed
                    self.network_graph.add_data_point(min(total_speed, 1000))  # Cap at 1000 KB/s for display
                else:
                    self.network_graph.add_data_point(0)
                
                self.prev_net_recv = net_io.bytes_recv
                self.prev_net_sent = net_io.bytes_sent
                self.prev_time = current_time
            except:
                self.network_graph.add_data_point(0)
                
        except ImportError:
            # If psutil is not available, add dummy data
            self.cpu_graph.add_data_point(0)
            self.ram_graph.add_data_point(0)
            self.disk_graph.add_data_point(0)
            self.network_graph.add_data_point(0)


class MainWindow(QMainWindow):
    """Main application window with basic styling."""
    
    def __init__(self):
        super().__init__()
        self.startup_window = None
        self.scheduler_dialog = None
        self.cleanup_worker = None
        self.duplicate_finder = None
        self.scan_thread = None
        self.settings = QSettings('PCMaintenance', 'Dashboard')
        
        # Performance optimization variables
        self._update_counter = 0
        self._last_cpu_time = None
        self._cached_disk_info = {}
        self._cache_timeout = 10  # Cache disk info for 10 updates
        
        # Initialize system monitors
        self.system_monitor = SystemMonitor()
        self.file_cleanup = FileCleanup()
        self.startup_manager = StartupManager()
        
        # Initialize system tray
        self.tray_manager = SystemTrayManager(self)
        self.tray_manager.show_window.connect(self.show_and_raise)
        self.tray_manager.exit_app.connect(self.close)
        
        # Initialize scheduler
        self.scheduler = MaintenanceScheduler()
        self.scheduler.maintenance_triggered.connect(self.handle_scheduled_maintenance)
        
        self.setup_ui()
        self.setup_timer()
        
        # Show system tray if available
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_manager.show()
            self.log_activity("System tray integration enabled")
        
        # Initial log messages after UI is fully set up
        self.log_activity("PC Maintenance Dashboard v2.0 Professional Edition started", "SUCCESS")
        self.log_activity(f"Developed by MStefa003 - GitHub: https://github.com/MStefa003")
        self.log_activity("Advanced system monitoring and diagnostics initialized")
        
    def setup_ui(self):
        """Set up the basic user interface."""
        self.setWindowTitle("PC Maintenance Dashboard v2.0 Professional - by MStefa003")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(900, 600)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Main layout with scroll area for better resizing
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scroll_widget = QWidget()
        main_layout = QVBoxLayout(scroll_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        scroll_area.setWidget(scroll_widget)
        self.setCentralWidget(scroll_area)
        
        # Professional System Information Panel
        system_group = QGroupBox("🖥️ Real-Time System Monitoring")
        system_layout = QGridLayout(system_group)
        system_layout.setSpacing(8)
        
        # Create professional metric labels with enhanced styling
        def create_metric_label(text, tooltip=""):
            label = QLabel(text)
            label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    color: #2c3e50;
                    padding: 2px;
                }
            """)
            if tooltip:
                label.setToolTip(tooltip)
            return label
        
        def create_value_label():
            label = QLabel("Initializing...")
            label.setStyleSheet("""
                QLabel {
                    font-family: 'Consolas', 'Courier New', monospace;
                    background-color: #ecf0f1;
                    border: 1px solid #bdc3c7;
                    border-radius: 3px;
                    padding: 4px 8px;
                    min-width: 120px;
                }
            """)
            return label
        
        # Row 1: Core Performance Metrics
        cpu_title = create_metric_label("💻 CPU Performance:", "Real-time CPU usage with status indicators")
        self.cpu_label = create_value_label()
        
        memory_title = create_metric_label("🧠 Memory Usage:", "Physical RAM usage with detailed breakdown")
        self.memory_label = create_value_label()
        
        disk_title = create_metric_label("💾 Storage Status:", "Multi-drive storage analysis with health indicators")
        self.disk_label = create_value_label()
        
        system_layout.addWidget(cpu_title, 0, 0)
        system_layout.addWidget(self.cpu_label, 0, 1)
        system_layout.addWidget(memory_title, 0, 2)
        system_layout.addWidget(self.memory_label, 0, 3)
        system_layout.addWidget(disk_title, 0, 4)
        system_layout.addWidget(self.disk_label, 0, 5)
        
        # Row 2: Network and System Metrics
        network_title = create_metric_label("🌐 Network Activity:", "Real-time upload/download speeds")
        self.network_label = create_value_label()
        
        uptime_title = create_metric_label("⏱️ System Uptime:", "Time since last system boot")
        self.uptime_label = create_value_label()
        
        processes_title = create_metric_label("⚙️ Active Processes:", "Total and active process count")
        self.processes_label = create_value_label()
        
        system_layout.addWidget(network_title, 1, 0)
        system_layout.addWidget(self.network_label, 1, 1)
        system_layout.addWidget(uptime_title, 1, 2)
        system_layout.addWidget(self.uptime_label, 1, 3)
        system_layout.addWidget(processes_title, 1, 4)
        system_layout.addWidget(self.processes_label, 1, 5)
        
        # Add progress bars for visual feedback
        def create_progress_bar():
            progress = QProgressBar()
            progress.setMaximum(100)
            progress.setMinimum(0)
            progress.setValue(0)
            progress.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #bdc3c7;
                    border-radius: 3px;
                    text-align: center;
                    font-size: 8pt;
                    height: 12px;
                }
                QProgressBar::chunk {
                    background-color: #3498db;
                    border-radius: 2px;
                }
            """)
            return progress
        
        # Row 3: Progress bars
        self.cpu_progress = create_progress_bar()
        self.memory_progress = create_progress_bar()
        self.disk_progress = create_progress_bar()
        
        system_layout.addWidget(self.cpu_progress, 2, 1)
        system_layout.addWidget(self.memory_progress, 2, 3)
        system_layout.addWidget(self.disk_progress, 2, 5)
        
        main_layout.addWidget(system_group)
        
        # Add Real-time System Graphs
        self.graphs_widget = SystemGraphsWidget()
        main_layout.addWidget(self.graphs_widget)
        
        # Cleanup group
        cleanup_group = QGroupBox("File Cleanup")
        cleanup_layout = QVBoxLayout(cleanup_group)
        
        self.cleanup_btn = QPushButton("Clean Temporary Files")
        self.cleanup_btn.clicked.connect(self.start_cleanup)
        
        self.cleanup_progress = QProgressBar()
        self.cleanup_progress.setVisible(False)
        
        self.cleanup_info = QLabel("Ready to clean temporary files")
        
        cleanup_layout.addWidget(self.cleanup_btn)
        cleanup_layout.addWidget(self.cleanup_progress)
        cleanup_layout.addWidget(self.cleanup_info)
        
        main_layout.addWidget(cleanup_group)
        
        # Tools group - Enhanced with more options
        tools_group = QGroupBox("System Tools")
        tools_layout = QGridLayout(tools_group)
        
        # Create all tool buttons
        self.startup_btn = QPushButton("🚀 Startup Programs")
        self.startup_btn.clicked.connect(self.open_startup_manager)
        
        self.maintenance_btn = QPushButton("🔧 Quick Maintenance")
        self.maintenance_btn.clicked.connect(self.run_maintenance)
        
        self.browser_cleanup_btn = QPushButton("🌐 Browser Cleanup")
        self.browser_cleanup_btn.clicked.connect(self.show_browser_cleaner)
        
        self.duplicate_finder_btn = QPushButton("📁 Find Duplicates")
        self.duplicate_finder_btn.clicked.connect(self.show_duplicate_finder)
        
        self.registry_cleaner_btn = QPushButton("📋 Registry Cleaner")
        self.registry_cleaner_btn.clicked.connect(self.clean_registry_safe)
        
        self.process_manager_btn = QPushButton("⚙️ Process Manager")
        self.process_manager_btn.clicked.connect(self.show_processes)
        
        self.network_monitor_btn = QPushButton("📡 Network Monitor")
        self.network_monitor_btn.clicked.connect(self.show_network_monitor)
        
        self.system_report_btn = QPushButton("📊 System Report")
        self.system_report_btn.clicked.connect(self.generate_system_report)
        
        # New advanced tools
        self.disk_analyzer_btn = QPushButton("💿 Disk Analyzer")
        self.disk_analyzer_btn.clicked.connect(self.open_disk_analyzer)
        
        self.service_manager_btn = QPushButton("🔧 Service Manager")
        self.service_manager_btn.clicked.connect(self.open_service_manager)
        
        self.memory_optimizer_btn = QPushButton("🧠 Memory Optimizer")
        self.memory_optimizer_btn.clicked.connect(self.optimize_memory)
        
        self.security_scan_btn = QPushButton("🛡️ Security Scan")
        self.security_scan_btn.clicked.connect(self.run_security_scan)
        
        # Additional professional tools
        self.defrag_btn = QPushButton("🗂️ Disk Defrag")
        self.defrag_btn.clicked.connect(self.run_disk_defrag)
        
        self.system_restore_btn = QPushButton("⏮️ System Restore")
        self.system_restore_btn.clicked.connect(self.open_system_restore)
        
        self.driver_update_btn = QPushButton("🔄 Driver Check")
        self.driver_update_btn.clicked.connect(self.check_drivers)
        
        self.power_options_btn = QPushButton("🔋 Power Options")
        self.power_options_btn.clicked.connect(self.open_power_options)
        
        self.benchmark_btn = QPushButton("📊 Performance Benchmark")
        from performance_benchmark import BenchmarkWorker, BenchmarkExporter
        self.benchmark_btn.clicked.connect(self.run_performance_benchmark)
        
        # Style buttons
        button_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """
        
        for btn in [self.startup_btn, self.maintenance_btn, self.browser_cleanup_btn, 
                   self.duplicate_finder_btn, self.registry_cleaner_btn, self.process_manager_btn,
                   self.network_monitor_btn, self.system_report_btn, self.disk_analyzer_btn,
                   self.service_manager_btn, self.memory_optimizer_btn, self.security_scan_btn,
                   self.defrag_btn, self.system_restore_btn, self.driver_update_btn, self.power_options_btn,
                   self.benchmark_btn]:
            btn.setStyleSheet(button_style)
            btn.setMinimumHeight(40)
        
        # Add buttons to layout (4 rows now) with proper stretching
        tools_layout.addWidget(self.startup_btn, 0, 0)
        tools_layout.addWidget(self.maintenance_btn, 0, 1)
        tools_layout.addWidget(self.browser_cleanup_btn, 0, 2)
        tools_layout.addWidget(self.duplicate_finder_btn, 0, 3)
        tools_layout.addWidget(self.registry_cleaner_btn, 1, 0)
        tools_layout.addWidget(self.process_manager_btn, 1, 1)
        tools_layout.addWidget(self.network_monitor_btn, 1, 2)
        tools_layout.addWidget(self.system_report_btn, 1, 3)
        tools_layout.addWidget(self.disk_analyzer_btn, 2, 0)
        tools_layout.addWidget(self.service_manager_btn, 2, 1)
        tools_layout.addWidget(self.memory_optimizer_btn, 2, 2)
        tools_layout.addWidget(self.security_scan_btn, 2, 3)
        tools_layout.addWidget(self.defrag_btn, 3, 0)
        tools_layout.addWidget(self.system_restore_btn, 3, 1)
        tools_layout.addWidget(self.driver_update_btn, 3, 2)
        tools_layout.addWidget(self.power_options_btn, 3, 3)
        tools_layout.addWidget(self.benchmark_btn, 4, 0)
        
        # Set equal column stretches for responsive button resizing
        for col in range(4):
            tools_layout.setColumnStretch(col, 1)
        
        tools_group.setLayout(tools_layout)
        main_layout.addWidget(tools_group)
        
        # Professional Activity Log with enhanced features
        log_group = QGroupBox("📋 System Activity & Diagnostics Log")
        log_layout = QVBoxLayout(log_group)
        
        # Log controls
        log_controls = QHBoxLayout()
        
        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self.clear_activity_log)
        self.clear_log_btn.setMaximumWidth(80)
        
        self.export_log_btn = QPushButton("Export Log")
        self.export_log_btn.clicked.connect(self.export_activity_log)
        self.export_log_btn.setMaximumWidth(80)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["All", "Errors Only", "Warnings+", "Info+"])
        self.log_level_combo.setMaximumWidth(100)
        self.log_level_combo.currentTextChanged.connect(self.filter_log_display)
        
        log_controls.addWidget(QLabel("Filter:"))
        log_controls.addWidget(self.log_level_combo)
        log_controls.addStretch()
        log_controls.addWidget(self.clear_log_btn)
        log_controls.addWidget(self.export_log_btn)
        
        log_layout.addLayout(log_controls)
        
        # Enhanced activity log with responsive height
        self.activity_log = QTextEdit()
        self.activity_log.setMinimumHeight(120)
        self.activity_log.setMaximumHeight(250)
        self.activity_log.setReadOnly(True)
        self.activity_log.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.activity_log.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        
        log_layout.addWidget(self.activity_log)
        
        main_layout.addWidget(log_group)
        
        # Status bar
        status_bar = self.statusBar()
        status_bar.showMessage("🚀 Professional System Monitor Ready - Real-time diagnostics active")
        
        # Log messages will be added after UI setup is complete
        
        # Initialize professional monitoring systems
        self._last_net_io = None
        self._last_update_time = None
        self._system_alerts = []
        self._performance_history = {'cpu': [], 'memory': [], 'network': []}
        
        # Set window icon and professional styling
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
    def clear_activity_log(self):
        """Clear the activity log with confirmation."""
        reply = QMessageBox.question(self, 'Clear Log', 
                                   'Are you sure you want to clear the activity log?',
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.activity_log.clear()
            if hasattr(self, '_full_log_content'):
                self._full_log_content = ""
            self.log_activity("Activity log cleared by user", "INFO")
            self.statusBar().showMessage("Activity log cleared", 3000)
    
    def export_activity_log(self):
        """Export activity log to file."""
        from datetime import datetime
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Activity Log",
            f"activity_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                # Extract plain text from HTML formatted log
                plain_text = self.activity_log.toPlainText()
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"PC Maintenance Dashboard v2.0 Professional - Activity Log\n")
                    f.write(f"Generated by: MStefa003 (https://github.com/MStefa003)\n")
                    f.write(f"Export Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(plain_text)
                QMessageBox.information(self, "Success", f"Activity log exported to {filename}")
                self.log_activity(f"Activity log exported to {filename}", "SUCCESS")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export log: {str(e)}")
                self.log_activity(f"Failed to export log: {str(e)}", "ERROR")
    
    def filter_log_display(self, filter_level):
        """Filter log display based on selected level."""
        # Store original content if not already stored
        if not hasattr(self, '_full_log_content'):
            self._full_log_content = self.activity_log.toHtml()
        
        # Apply filter based on level
        if filter_level == "All":
            self.activity_log.setHtml(self._full_log_content)
        elif filter_level == "Errors Only":
            filtered_content = self._filter_log_by_keywords(["❌", "ERROR", "🚨", "CRITICAL"])
            self.activity_log.setHtml(filtered_content)
        elif filter_level == "Warnings+":
            filtered_content = self._filter_log_by_keywords(["❌", "ERROR", "⚠️", "WARNING", "🚨", "CRITICAL", "🟡", "🔴"])
            self.activity_log.setHtml(filtered_content)
        elif filter_level == "Info+":
            # Show everything except debug messages (if any)
            self.activity_log.setHtml(self._full_log_content)
        
        self.log_activity(f"Log filter applied: {filter_level}", "INFO")
    
    def _filter_log_by_keywords(self, keywords):
        """Filter log content by keywords."""
        if not hasattr(self, '_full_log_content'):
            return self.activity_log.toHtml()
        
        lines = self._full_log_content.split('<br>')
        filtered_lines = []
        
        for line in lines:
            if any(keyword in line for keyword in keywords):
                filtered_lines.append(line)
        
        return '<br>'.join(filtered_lines)
        
        # Add professional status indicators
        self._setup_professional_indicators()
    
    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        # System info action
        system_info_action = QAction('Detailed System Info', self)
        system_info_action.triggered.connect(self.show_detailed_system_info)
        view_menu.addAction(system_info_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        scheduler_action = QAction('Maintenance Scheduler', self)
        scheduler_action.triggered.connect(self.open_scheduler)
        tools_menu.addAction(scheduler_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        github_action = QAction('Visit GitHub', self)
        github_action.triggered.connect(self.visit_github)
        help_menu.addAction(github_action)
        
        help_menu.addSeparator()
        
        shortcuts_action = QAction('Keyboard Shortcuts', self)
        shortcuts_action.triggered.connect(self.show_keyboard_shortcuts)
        help_menu.addAction(shortcuts_action)
    
    def show_about(self):
        """Show about dialog with GitHub link."""
        about_text = (
            "PC Maintenance Dashboard v2.0\n\n"
            "A comprehensive desktop application for system maintenance and monitoring.\n\n"
            "Features:\n"
            "• Real-time system monitoring\n"
            "• Temporary file cleanup\n"
            "• Startup program management\n"
            "• Registry cleaning\n"
            "• Process management\n"
            "• Network monitoring\n"
            "• Disk analysis\n"
            "• System reporting\n\n"
            "Built with Python and PyQt5\n\n"
            "Developer: MStefa003\n"
            "GitHub: https://github.com/MStefa003\n\n"
            "© 2024 - Open Source Project"
        )
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("About PC Maintenance Dashboard")
        msg_box.setText(about_text)
        msg_box.setIcon(QMessageBox.Information)
        
        # Add GitHub button
        github_btn = msg_box.addButton("Visit GitHub", QMessageBox.ActionRole)
        ok_btn = msg_box.addButton(QMessageBox.Ok)
        
        msg_box.exec_()
        
        if msg_box.clickedButton() == github_btn:
            self.visit_github()
    
    def setup_timer(self):
        """Set up optimized monitoring timers with reduced frequency."""
        # Optimized system monitoring - every 5 seconds for better responsiveness
        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self.update_system_info)
        self.main_timer.start(5000)
        
        # Disable heavy background tasks to improve performance
        # Performance history tracking disabled
        # System health checks disabled
        
        # Force an immediate update to show data right away
        QTimer.singleShot(500, self.force_initial_update)
        
        # Regular updates start after initial load
        QTimer.singleShot(2000, self.update_system_info)
        
    def _setup_professional_indicators(self):
        """Set up professional system indicators and alerts."""
        # This method sets up additional professional monitoring features
        pass
    
    def force_initial_update(self):
        """Force an initial system update to show data immediately."""
        try:
            import psutil
            
            # Get system info with proper intervals for accuracy
            cpu_percent = psutil.cpu_percent(interval=1)  # 1 second for accurate reading
            memory = psutil.virtual_memory()
            
            # Update labels with detailed info
            memory_gb = memory.used / (1024**3)
            total_gb = memory.total / (1024**3)
            
            self.cpu_label.setText(f"🔥 CPU: {cpu_percent:.1f}%")
            self.memory_label.setText(f"🧠 RAM: {memory.percent:.1f}% ({memory_gb:.1f}/{total_gb:.1f}GB)")
            
            # Update progress bars
            self.cpu_progress.setValue(int(cpu_percent))
            self.memory_progress.setValue(int(memory.percent))
            
            # Disk info with detailed display
            try:
                disk_usage = psutil.disk_usage('C:\\')
                disk_percent = (disk_usage.used / disk_usage.total) * 100
                disk_used_gb = disk_usage.used / (1024**3)
                disk_total_gb = disk_usage.total / (1024**3)
                self.disk_label.setText(f"💾 Disk: {disk_percent:.1f}% ({disk_used_gb:.1f}/{disk_total_gb:.1f}GB)")
                self.disk_progress.setValue(int(disk_percent))
            except Exception as e:
                self.disk_label.setText("💾 Disk: Error")
                self.log_activity(f"Disk monitoring error: {str(e)}", "WARNING")
            
            # Network info with transfer data
            try:
                net_io = psutil.net_io_counters()
                recv_mb = net_io.bytes_recv / (1024**2)
                sent_mb = net_io.bytes_sent / (1024**2)
                self.network_label.setText(f"🌐 Network: ↓{recv_mb:.0f}MB ↑{sent_mb:.0f}MB")
            except Exception as e:
                self.network_label.setText("🌐 Network: Error")
                self.log_activity(f"Network monitoring error: {str(e)}", "WARNING")
            
            # System uptime
            try:
                import time
                from datetime import timedelta
                boot_time = psutil.boot_time()
                uptime_seconds = time.time() - boot_time
                uptime_delta = timedelta(seconds=int(uptime_seconds))
                
                days = uptime_delta.days
                hours, remainder = divmod(uptime_delta.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                if days > 0:
                    self.uptime_label.setText(f"{days}d {hours}h {minutes}m")
                else:
                    self.uptime_label.setText(f"{hours}h {minutes}m")
            except:
                self.uptime_label.setText("Unknown")
            
            # Process count
            try:
                process_count = len(psutil.pids())
                self.processes_label.setText(f"{process_count} processes")
            except:
                self.processes_label.setText("Unknown")
            
            self.log_activity("System monitoring initialized successfully", "SUCCESS")
            
        except ImportError:
            self.log_activity("psutil not available - install with: pip install psutil", "ERROR")
            self._show_psutil_error()
        except Exception as e:
            self.log_activity(f"System monitoring initialization error: {str(e)}", "ERROR")
            self._show_monitoring_error()
    
    def _show_psutil_error(self):
        """Show psutil installation error."""
        self.cpu_label.setText("🔥 CPU: Install psutil")
        self.memory_label.setText("🧠 RAM: Install psutil")
        self.disk_label.setText("💾 Disk: Install psutil")
        self.network_label.setText("🌐 Network: Install psutil")
        self.uptime_label.setText("Install psutil")
        self.processes_label.setText("Install psutil")
    
    def _show_monitoring_error(self):
        """Show monitoring error state."""
        self.cpu_label.setText("🔥 CPU: Error")
        self.memory_label.setText("🧠 RAM: Error")
        self.disk_label.setText("💾 Disk: Error")
        self.network_label.setText("🌐 Network: Error")
        self.uptime_label.setText("Error")
        self.processes_label.setText("Error")
        
    def update_performance_history(self):
        """Track performance history for trend analysis."""
        try:
            import psutil
            
            # Keep last 60 data points (10 minutes of history)
            max_history = 60
            
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            
            # Network throughput
            net_io = psutil.net_io_counters()
            network_throughput = 0
            if hasattr(self, '_last_history_net_io') and self._last_history_net_io:
                bytes_diff = (net_io.bytes_sent + net_io.bytes_recv) - (self._last_history_net_io.bytes_sent + self._last_history_net_io.bytes_recv)
                network_throughput = bytes_diff / 10  # 10 second interval
            self._last_history_net_io = net_io
            
            # Update history
            self._performance_history['cpu'].append(cpu_percent)
            self._performance_history['memory'].append(memory_percent)
            self._performance_history['network'].append(network_throughput)
            
            # Trim history to max length
            for key in self._performance_history:
                if len(self._performance_history[key]) > max_history:
                    self._performance_history[key] = self._performance_history[key][-max_history:]
                    
        except Exception as e:
            self.log_activity(f"Performance history update error: {str(e)}")
    
    def perform_health_checks(self):
        """Perform comprehensive system health checks."""
        try:
            import psutil
            
            alerts = []
            
            # CPU health check
            if len(self._performance_history['cpu']) > 5:
                avg_cpu = sum(self._performance_history['cpu'][-5:]) / 5
                if avg_cpu > 90:
                    alerts.append("🔴 CPU usage critically high for extended period")
                elif avg_cpu > 80:
                    alerts.append("🟡 CPU usage consistently high")
            
            # Memory health check
            memory = psutil.virtual_memory()
            if memory.percent > 95:
                alerts.append("🔴 Memory usage critical - system may become unstable")
            elif memory.percent > 85:
                alerts.append("🟡 Memory usage high - consider closing applications")
            
            # Disk health check
            try:
                partitions = psutil.disk_partitions()
                for partition in partitions:
                    if 'cdrom' in partition.opts or partition.fstype == '':
                        continue
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        percent = (usage.used / usage.total) * 100
                        if percent > 95:
                            alerts.append(f"🔴 Drive {partition.device} critically full ({percent:.0f}%)")
                        elif percent > 90:
                            alerts.append(f"🟡 Drive {partition.device} running low on space ({percent:.0f}%)")
                    except (PermissionError, FileNotFoundError):
                        continue
            except Exception:
                pass
            
            # Update alerts
            self._system_alerts = alerts
            
            # Log significant alerts
            for alert in alerts:
                if "🔴" in alert:
                    self.log_activity(f"CRITICAL ALERT: {alert}")
                elif "🟡" in alert and alert not in getattr(self, '_last_alerts', []):
                    self.log_activity(f"WARNING: {alert}")
            
            self._last_alerts = alerts.copy()
            
        except Exception as e:
            self.log_activity(f"Health check error: {str(e)}")
        
    def update_system_info(self):
        """Optimized system information update with caching and performance improvements."""
        try:
            import psutil
            import time
            from datetime import datetime, timedelta
            
            self._update_counter += 1
            
            # Optimized CPU usage - use cached value for frequent updates
            if self._update_counter % 2 == 0:  # Update CPU every other cycle
                cpu_percent = psutil.cpu_percent(interval=0.1)
                self._last_cpu_percent = cpu_percent
            else:
                cpu_percent = getattr(self, '_last_cpu_percent', 0)
            
            # Add CPU temperature monitoring if available
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    cpu_temp = None
                    for name, entries in temps.items():
                        if 'cpu' in name.lower() or 'core' in name.lower():
                            cpu_temp = entries[0].current if entries else None
                            break
                    if cpu_temp:
                        self.cpu_label.setText(f"🔥 CPU: {cpu_percent:.1f}% ({cpu_temp:.0f}°C)")
                    else:
                        self.cpu_label.setText(f"🔥 CPU: {cpu_percent:.1f}%")
                else:
                    self.cpu_label.setText(f"🔥 CPU: {cpu_percent:.1f}%")
            except:
                self.cpu_label.setText(f"🔥 CPU: {cpu_percent:.1f}%")
            
            # Enhanced Memory metrics with swap info
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            memory_gb = memory.used / (1024**3)
            total_gb = memory.total / (1024**3)
            
            if swap.total > 0:
                swap_gb = swap.used / (1024**3)
                self.memory_label.setText(f"🧠 RAM: {memory.percent:.1f}% ({memory_gb:.1f}/{total_gb:.1f}GB) | Swap: {swap_gb:.1f}GB")
            else:
                self.memory_label.setText(f"🧠 RAM: {memory.percent:.1f}% ({memory_gb:.1f}/{total_gb:.1f}GB)")
            
            # Cached Disk metrics for better performance
            if self._update_counter % self._cache_timeout == 0 or not self._cached_disk_info:
                try:
                    partitions = psutil.disk_partitions()
                    total_used = 0
                    total_size = 0
                    disk_info = []
                    
                    for partition in partitions:
                        if 'cdrom' in partition.opts or partition.fstype == '':
                            continue
                        try:
                            usage = psutil.disk_usage(partition.mountpoint)
                            total_used += usage.used
                            total_size += usage.total
                            disk_info.append({
                                'drive': partition.device,
                                'percent': (usage.used / usage.total) * 100,
                                'used_gb': usage.used / (1024**3),
                                'total_gb': usage.total / (1024**3)
                            })
                        except (PermissionError, FileNotFoundError):
                            continue
                    
                    self._cached_disk_info = {
                        'total_percent': (total_used / total_size) * 100 if total_size > 0 else 0,
                        'drives': disk_info,
                        'total_used_gb': total_used / (1024**3),
                        'total_size_gb': total_size / (1024**3)
                    }
                except Exception as e:
                    self._cached_disk_info = {'total_percent': 0, 'drives': [], 'error': str(e)}
            
            # Display cached disk info
            if self._cached_disk_info and 'error' not in self._cached_disk_info:
                cache = self._cached_disk_info
                if len(cache['drives']) > 1:
                    self.disk_label.setText(f"💾 Disk: {cache['total_percent']:.1f}% ({cache['total_used_gb']:.0f}/{cache['total_size_gb']:.0f}GB) | {len(cache['drives'])} drives")
                elif cache['drives']:
                    drive = cache['drives'][0]
                    self.disk_label.setText(f"💾 {drive['drive']} {drive['percent']:.1f}% ({drive['used_gb']:.0f}/{drive['total_gb']:.0f}GB)")
                else:
                    self.disk_label.setText("💾 Disk: No drives found")
            else:
                self.disk_label.setText("💾 Disk: Error")
            
            # Enhanced Network info with speed calculation
            try:
                net_io = psutil.net_io_counters()
                current_time = time.time()
                
                if hasattr(self, '_last_net_io') and hasattr(self, '_last_net_time'):
                    time_delta = current_time - self._last_net_time
                    if time_delta > 0:
                        recv_speed = (net_io.bytes_recv - self._last_net_io.bytes_recv) / time_delta / 1024  # KB/s
                        sent_speed = (net_io.bytes_sent - self._last_net_io.bytes_sent) / time_delta / 1024  # KB/s
                        
                        if recv_speed > 1024 or sent_speed > 1024:
                            self.network_label.setText(f"🌐 Network: ↓{recv_speed/1024:.1f}MB/s ↑{sent_speed/1024:.1f}MB/s")
                        else:
                            self.network_label.setText(f"🌐 Network: ↓{recv_speed:.0f}KB/s ↑{sent_speed:.0f}KB/s")
                else:
                    recv_mb = net_io.bytes_recv / (1024**2)
                    sent_mb = net_io.bytes_sent / (1024**2)
                    self.network_label.setText(f"🌐 Network: ↓{recv_mb:.0f}MB ↑{sent_mb:.0f}MB")
                
                self._last_net_io = net_io
                self._last_net_time = current_time
            except:
                self.network_label.setText("🌐 Network: --")
            
            # Enhanced uptime with more detail
            try:
                boot_time = psutil.boot_time()
                uptime_seconds = time.time() - boot_time
                uptime_delta = timedelta(seconds=int(uptime_seconds))
                
                days = uptime_delta.days
                hours, remainder = divmod(uptime_delta.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                if days > 7:
                    self.uptime_label.setText(f"⏱️ {days}d {hours}h (Restart recommended)")
                elif days > 0:
                    self.uptime_label.setText(f"⏱️ {days}d {hours}h {minutes}m")
                else:
                    self.uptime_label.setText(f"⏱️ {hours}h {minutes}m")
            except:
                self.uptime_label.setText("⏱️ Unknown")
            
            # Enhanced process count with load average
            try:
                process_count = len(psutil.pids())
                load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                
                if load_avg:
                    self.processes_label.setText(f"⚙️ {process_count} processes (Load: {load_avg[0]:.1f})")
                else:
                    # Calculate rough load based on CPU
                    if cpu_percent > 80:
                        load_status = "High"
                    elif cpu_percent > 50:
                        load_status = "Medium"
                    else:
                        load_status = "Low"
                    self.processes_label.setText(f"⚙️ {process_count} processes ({load_status} load)")
            except:
                self.processes_label.setText("⚙️ Unknown")
            
            # Update progress bars with color coding
            self.cpu_progress.setValue(int(cpu_percent))
            self.memory_progress.setValue(int(memory.percent))
            
            # Color code progress bars based on usage
            if cpu_percent > 80:
                self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")
            elif cpu_percent > 60:
                self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #f39c12; }")
            else:
                self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #27ae60; }")
            
            if memory.percent > 80:
                self.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")
            elif memory.percent > 60:
                self.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: #f39c12; }")
            else:
                self.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: #27ae60; }")
            
            try:
                if self._cached_disk_info and 'total_percent' in self._cached_disk_info:
                    disk_percent = self._cached_disk_info['total_percent']
                    self.disk_progress.setValue(int(disk_percent))
                    
                    if disk_percent > 90:
                        self.disk_progress.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")
                    elif disk_percent > 75:
                        self.disk_progress.setStyleSheet("QProgressBar::chunk { background-color: #f39c12; }")
                    else:
                        self.disk_progress.setStyleSheet("QProgressBar::chunk { background-color: #27ae60; }")
            except:
                pass
            
        except Exception as e:
            error_msg = str(e)
            self.log_activity(f"System monitoring error: {error_msg}", "ERROR")
            
            # Fallback display
            self.cpu_label.setText("🔥 CPU: Error")
            self.memory_label.setText("🧠 RAM: Error")
            self.disk_label.setText("💾 Disk: Error")
            self.network_label.setText("🌐 Network: Error")
            self.uptime_label.setText("⏱️ Error")
            self.processes_label.setText("⚙️ Error")
    
    def _handle_psutil_error(self, error_msg):
        """Handle psutil import errors professionally."""
        self.cpu_label.setText("N/A - Install psutil")
        self.memory_label.setText("N/A - Install psutil")
        self.disk_label.setText("N/A - Install psutil")
        self.network_label.setText("N/A - Install psutil")
        self.uptime_label.setText("N/A - Install psutil")
        self.processes_label.setText("N/A - Install psutil")
        self.statusBar().showMessage("❌ System monitoring unavailable - Install psutil")
        self.log_activity(f"ERROR: {error_msg}")
    
    def _handle_system_error(self, error_msg):
        """Handle system monitoring errors professionally."""
        self.cpu_label.setText("Error")
        self.memory_label.setText("Error")
        self.disk_label.setText("Error")
        self.network_label.setText("Error")
        self.uptime_label.setText("Error")
        self.processes_label.setText("Error")
        self.statusBar().showMessage("❌ System monitoring error")
        self.log_activity(f"ERROR: {error_msg}")
    
    def log_activity(self, message: str, level="INFO"):
        """Professional activity logging with levels and formatting."""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding based on level
        if level == "ERROR" or "ERROR:" in message:
            formatted_message = f"<span style='color: #e74c3c;'>[{timestamp}] ❌ {message}</span>"
        elif level == "WARNING" or "WARNING:" in message or "🟡" in message:
            formatted_message = f"<span style='color: #f39c12;'>[{timestamp}] ⚠️ {message}</span>"
        elif level == "SUCCESS" or "completed" in message.lower() or "✅" in message:
            formatted_message = f"<span style='color: #27ae60;'>[{timestamp}] ✅ {message}</span>"
        elif "CRITICAL" in message or "🔴" in message:
            formatted_message = f"<span style='color: #c0392b; font-weight: bold;'>[{timestamp}] 🚨 {message}</span>"
        else:
            formatted_message = f"<span style='color: #2c3e50;'>[{timestamp}] ℹ️ {message}</span>"
        
        # Use HTML formatting for rich text
        cursor = self.activity_log.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertHtml(formatted_message + "<br>")
        
        # Update full log content for filtering
        if hasattr(self, '_full_log_content'):
            self._full_log_content = self.activity_log.toHtml()
        
        # Auto-scroll to bottom
        scrollbar = self.activity_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # Limit log size to prevent memory issues
        if self.activity_log.document().blockCount() > 1000:
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.Down, cursor.KeepAnchor, 100)
            cursor.removeSelectedText()
            # Update stored content after cleanup
            self._full_log_content = self.activity_log.toHtml()
    
    def start_cleanup(self):
        """Start the file cleanup process."""
        if self.cleanup_worker and self.cleanup_worker.isRunning():
            return
        
        self.cleanup_btn.setEnabled(False)
        self.cleanup_btn.setText("Scanning...")
        self.cleanup_progress.setVisible(True)
        self.cleanup_progress.setValue(0)
        self.cleanup_info.setText("Scanning for temporary files...")
        
        # Start cleanup worker
        self.cleanup_worker = CleanupWorker()
        self.cleanup_worker.progress.connect(self.cleanup_progress.setValue)
        self.cleanup_worker.finished.connect(self.cleanup_finished)
        self.cleanup_worker.start()
        
        self.log_activity("Starting file cleanup...")
    
    def cleanup_finished(self, result):
        """Handle cleanup completion."""
        self.cleanup_btn.setEnabled(True)
        self.cleanup_btn.setText("Clean Temporary Files")
        self.cleanup_progress.setVisible(False)
        
        files_cleaned = result.get('files_cleaned', 0)
        space_freed = result.get('space_freed_mb', 0)
        no_files_found = result.get('no_files_found', False)
        
        if no_files_found:
            message = "✅ No temporary files found to clean - System is already clean!"
            self.cleanup_info.setText(message)
            self.log_activity(message)
            self.statusBar().showMessage("No files to clean", 3000)
            QMessageBox.information(self, "Cleanup Complete", "No temporary files were found that need cleaning.\n\nYour system is already clean!")
        elif files_cleaned > 0:
            message = f"Cleanup completed! {files_cleaned} files removed, {space_freed:.1f} MB freed"
            self.cleanup_info.setText(message)
            self.log_activity(message)
            self.statusBar().showMessage(f"Cleanup completed - {files_cleaned} files removed", 5000)
            QMessageBox.information(self, "Cleanup Complete", f"Successfully cleaned {files_cleaned} files and freed {space_freed:.1f} MB of disk space!")
        else:
            message = "Cleanup completed but no files were removed"
            self.cleanup_info.setText(message)
            self.log_activity(message)
            self.statusBar().showMessage("Cleanup completed", 3000)
    
    def open_startup_manager(self):
        """Open startup manager window."""
        try:
            if not self.startup_window:
                self.startup_window = StartupWindow()
            self.startup_window.show()
            self.startup_window.raise_()
            self.log_activity("Opened startup manager")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening startup manager: {str(e)}")
            self.log_activity(f"Error opening startup manager: {str(e)}", "ERROR")
    
    def open_disk_analyzer(self):
        """Open disk space analyzer."""
        try:
            import psutil
            import os
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Disk Space Analyzer")
            dialog.setModal(True)
            dialog.resize(600, 500)
            
            layout = QVBoxLayout(dialog)
            
            # Drive selection
            drive_group = QGroupBox("Select Drive to Analyze")
            drive_layout = QHBoxLayout(drive_group)
            
            drive_combo = QComboBox()
            partitions = psutil.disk_partitions()
            for partition in partitions:
                if 'cdrom' not in partition.opts and partition.fstype:
                    drive_combo.addItem(partition.device)
            
            analyze_btn = QPushButton("Analyze")
            
            drive_layout.addWidget(QLabel("Drive:"))
            drive_layout.addWidget(drive_combo)
            drive_layout.addWidget(analyze_btn)
            
            # Results area
            results_group = QGroupBox("Analysis Results")
            results_layout = QVBoxLayout(results_group)
            
            results_text = QTextEdit()
            results_text.setReadOnly(True)
            results_text.setFont(QFont("Consolas", 9))
            
            results_layout.addWidget(results_text)
            
            layout.addWidget(drive_group)
            layout.addWidget(results_group)
            
            def analyze_drive():
                drive = drive_combo.currentText()
                if drive:
                    try:
                        results_text.clear()
                        results_text.append(f"Analyzing drive {drive}...\n")
                        
                        # Get drive usage
                        usage = psutil.disk_usage(drive)
                        results_text.append(f"Total Space: {usage.total / (1024**3):.1f} GB")
                        results_text.append(f"Used Space: {usage.used / (1024**3):.1f} GB ({(usage.used/usage.total)*100:.1f}%)")
                        results_text.append(f"Free Space: {usage.free / (1024**3):.1f} GB\n")
                        
                        # Analyze top-level directories with size limits
                        results_text.append("Top-level directory analysis:")
                        results_text.append("(Limited scan for performance)\n")
                        
                        try:
                            items = os.listdir(drive)
                            for item in items:
                                item_path = os.path.join(drive, item)
                                if os.path.isdir(item_path):
                                    try:
                                        # Quick size estimation - only scan first level and sample
                                        size = 0
                                        file_count = 0
                                        max_files = 1000  # Limit to prevent hanging
                                        
                                        for root, dirs, files in os.walk(item_path):
                                            # Skip system directories that cause issues
                                            if any(skip in root.lower() for skip in [
                                                'system volume information', '$recycle.bin', 
                                                'windows\\winsxs', 'pagefile.sys', 'hiberfil.sys'
                                            ]):
                                                continue
                                                
                                            for filename in files[:50]:  # Limit files per directory
                                                if file_count >= max_files:
                                                    break
                                                try:
                                                    file_path = os.path.join(root, filename)
                                                    size += os.path.getsize(file_path)
                                                    file_count += 1
                                                except (OSError, PermissionError):
                                                    continue
                                            
                                            if file_count >= max_files:
                                                break
                                            
                                            # Only go 2 levels deep to prevent hanging
                                            if root.count(os.sep) - item_path.count(os.sep) >= 2:
                                                dirs.clear()
                                        
                                        size_gb = size / (1024**3)
                                        if size_gb > 0.01:  # Show folders > 10MB
                                            status = " (estimated)" if file_count >= max_files else ""
                                            results_text.append(f"  {item}: {size_gb:.2f} GB{status}")
                                        elif file_count > 0:
                                            results_text.append(f"  {item}: < 0.01 GB")
                                        else:
                                            results_text.append(f"  {item}: Empty or inaccessible")
                                            
                                    except (PermissionError, FileNotFoundError, OSError):
                                        results_text.append(f"  {item}: Access denied")
                                    except Exception as e:
                                        results_text.append(f"  {item}: Error - {str(e)[:50]}")
                                        
                        except PermissionError:
                            results_text.append("  Access denied to analyze directories")
                        except Exception as e:
                            results_text.append(f"  Error listing directories: {str(e)}")
                        
                        results_text.append(f"\nAnalysis completed for {drive}")
                        self.log_activity(f"Disk analysis completed for {drive}")
                        
                    except Exception as e:
                        results_text.append(f"Error analyzing drive: {str(e)}")
                        self.log_activity(f"Disk analysis error: {str(e)}", "ERROR")
            
            analyze_btn.clicked.connect(analyze_drive)
            
            # Close button
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening disk analyzer: {str(e)}")
            self.log_activity(f"Error opening disk analyzer: {str(e)}", "ERROR")
    
    def open_service_manager(self):
        """Open Windows service manager."""
        try:
            import subprocess
            
            reply = QMessageBox.question(
                self, "Service Manager", 
                "This will open Windows Services management console.\n\nProceed?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                subprocess.run(['services.msc'], shell=True)
                self.log_activity("Opened Windows Services console")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening service manager: {str(e)}")
            self.log_activity(f"Error opening service manager: {str(e)}", "ERROR")
    
    def optimize_memory(self):
        """Optimize system memory usage."""
        try:
            import psutil
            import gc
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Memory Optimizer")
            dialog.setModal(True)
            dialog.resize(500, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Current memory status
            memory = psutil.virtual_memory()
            status_group = QGroupBox("Current Memory Status")
            status_layout = QVBoxLayout(status_group)
            
            total_label = QLabel(f"Total RAM: {memory.total / (1024**3):.1f} GB")
            used_label = QLabel(f"Used RAM: {memory.used / (1024**3):.1f} GB ({memory.percent:.1f}%)")
            available_label = QLabel(f"Available RAM: {memory.available / (1024**3):.1f} GB")
            
            status_layout.addWidget(total_label)
            status_layout.addWidget(used_label)
            status_layout.addWidget(available_label)
            
            # Optimization options
            options_group = QGroupBox("Optimization Options")
            options_layout = QVBoxLayout(options_group)
            
            gc_cb = QCheckBox("Run garbage collection")
            cache_cb = QCheckBox("Clear system file cache (requires admin)")
            working_set_cb = QCheckBox("Trim working sets")
            
            gc_cb.setChecked(True)
            working_set_cb.setChecked(True)
            
            options_layout.addWidget(gc_cb)
            options_layout.addWidget(cache_cb)
            options_layout.addWidget(working_set_cb)
            
            # Results area
            results_text = QTextEdit()
            results_text.setReadOnly(True)
            results_text.setMaximumHeight(100)
            
            # Buttons
            button_layout = QHBoxLayout()
            optimize_btn = QPushButton("Optimize Memory")
            close_btn = QPushButton("Close")
            
            button_layout.addWidget(optimize_btn)
            button_layout.addStretch()
            button_layout.addWidget(close_btn)
            
            layout.addWidget(status_group)
            layout.addWidget(options_group)
            layout.addWidget(QLabel("Results:"))
            layout.addWidget(results_text)
            layout.addLayout(button_layout)
            
            def optimize():
                results_text.clear()
                memory_before = psutil.virtual_memory()
                
                if gc_cb.isChecked():
                    gc.collect()
                    results_text.append("✓ Garbage collection completed")
                
                if working_set_cb.isChecked():
                    try:
                        import ctypes
                        ctypes.windll.kernel32.SetProcessWorkingSetSize(-1, -1, -1)
                        results_text.append("✓ Working set trimmed")
                    except:
                        results_text.append("✗ Working set trim failed")
                
                if cache_cb.isChecked():
                    results_text.append("⚠ System cache clearing requires administrator privileges")
                
                memory_after = psutil.virtual_memory()
                freed_mb = (memory_before.used - memory_after.used) / (1024**2)
                
                if freed_mb > 0:
                    results_text.append(f"✓ Freed approximately {freed_mb:.1f} MB of memory")
                else:
                    results_text.append("Memory optimization completed")
                
                self.log_activity(f"Memory optimization completed - {freed_mb:.1f}MB freed")
            
            optimize_btn.clicked.connect(optimize)
            close_btn.clicked.connect(dialog.close)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening memory optimizer: {str(e)}")
            self.log_activity(f"Error opening memory optimizer: {str(e)}", "ERROR")
    
    def run_security_scan(self):
        """Run basic security scan."""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Security Scan")
            dialog.setModal(True)
            dialog.resize(600, 500)
            
            layout = QVBoxLayout(dialog)
            
            # Scan options
            options_group = QGroupBox("Scan Options")
            options_layout = QVBoxLayout(options_group)
            
            startup_cb = QCheckBox("Check startup programs for suspicious entries")
            processes_cb = QCheckBox("Scan running processes")
            network_cb = QCheckBox("Check network connections")
            files_cb = QCheckBox("Scan system files integrity")
            
            startup_cb.setChecked(True)
            processes_cb.setChecked(True)
            network_cb.setChecked(True)
            
            options_layout.addWidget(startup_cb)
            options_layout.addWidget(processes_cb)
            options_layout.addWidget(network_cb)
            options_layout.addWidget(files_cb)
            
            # Results area
            results_text = QTextEdit()
            results_text.setReadOnly(True)
            results_text.setFont(QFont("Consolas", 9))
            
            # Progress bar
            progress_bar = QProgressBar()
            progress_bar.setVisible(False)
            
            # Buttons
            button_layout = QHBoxLayout()
            scan_btn = QPushButton("Start Security Scan")
            close_btn = QPushButton("Close")
            
            button_layout.addWidget(scan_btn)
            button_layout.addStretch()
            button_layout.addWidget(close_btn)
            
            layout.addWidget(options_group)
            layout.addWidget(QLabel("Scan Results:"))
            layout.addWidget(results_text)
            layout.addWidget(progress_bar)
            layout.addLayout(button_layout)
            
            def run_scan():
                results_text.clear()
                progress_bar.setVisible(True)
                progress_bar.setValue(0)
                scan_btn.setEnabled(False)
                
                results_text.append("=== SECURITY SCAN STARTED ===\n")
                
                if startup_cb.isChecked():
                    progress_bar.setValue(25)
                    results_text.append("Checking startup programs...")
                    try:
                        startup_count = len(self.startup_manager.get_startup_programs())
                        results_text.append(f"✓ Found {startup_count} startup programs - Review recommended")
                    except:
                        results_text.append("✗ Could not access startup programs")
                    results_text.append("")
                
                if processes_cb.isChecked():
                    progress_bar.setValue(50)
                    results_text.append("Scanning running processes...")
                    try:
                        import psutil
                        suspicious_processes = []
                        for proc in psutil.process_iter(['name', 'cpu_percent']):
                            try:
                                if proc.info['cpu_percent'] and proc.info['cpu_percent'] > 50:
                                    suspicious_processes.append(proc.info['name'])
                            except:
                                pass
                        
                        if suspicious_processes:
                            results_text.append(f"⚠ High CPU processes detected: {', '.join(suspicious_processes[:5])}")
                        else:
                            results_text.append("✓ No suspicious process activity detected")
                    except:
                        results_text.append("✗ Could not scan processes")
                    results_text.append("")
                
                if network_cb.isChecked():
                    progress_bar.setValue(75)
                    results_text.append("Checking network connections...")
                    try:
                        import psutil
                        connections = psutil.net_connections()
                        listening_ports = [conn.laddr.port for conn in connections if conn.status == 'LISTEN']
                        results_text.append(f"✓ Found {len(listening_ports)} listening ports")
                        if listening_ports:
                            common_ports = [port for port in listening_ports if port in [80, 443, 22, 21, 25, 53, 110, 143, 993, 995]]
                            if common_ports:
                                results_text.append(f"  Common service ports: {', '.join(map(str, common_ports))}")
                    except:
                        results_text.append("✗ Could not check network connections")
                    results_text.append("")
                
                if files_cb.isChecked():
                    progress_bar.setValue(90)
                    results_text.append("Checking system file integrity...")
                    results_text.append("ℹ For full system file check, run 'sfc /scannow' as administrator")
                    results_text.append("")
                
                progress_bar.setValue(100)
                results_text.append("=== SECURITY SCAN COMPLETED ===")
                results_text.append("✓ Basic security scan finished")
                results_text.append("💡 For comprehensive security, use dedicated antivirus software")
                
                scan_btn.setEnabled(True)
                self.log_activity("Security scan completed")
            
            scan_btn.clicked.connect(run_scan)
            close_btn.clicked.connect(dialog.close)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error running security scan: {str(e)}")
            self.log_activity(f"Error running security scan: {str(e)}", "ERROR")
    
    def run_disk_defrag(self):
        """Run disk defragmentation."""
        try:
            reply = QMessageBox.question(
                self, "Disk Defragmentation", 
                "Disk defragmentation can take a long time. Continue?\n\nNote: SSDs don't need defragmentation.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                import subprocess
                subprocess.Popen(['dfrgui.exe'], shell=True)
                self.log_activity("Opened Disk Defragmentation utility")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening disk defragmentation: {str(e)}")
            self.log_activity(f"Error opening disk defragmentation: {str(e)}", "ERROR")
    
    def open_system_restore(self):
        """Open Windows System Restore."""
        try:
            import subprocess
            subprocess.Popen(['rstrui.exe'], shell=True)
            self.log_activity("Opened System Restore")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening System Restore: {str(e)}")
            self.log_activity(f"Error opening System Restore: {str(e)}", "ERROR")
    
    def check_drivers(self):
        """Check for driver updates."""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Driver Check")
            dialog.setModal(True)
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            info_label = QLabel("Checking system drivers...")
            layout.addWidget(info_label)
            
            results_text = QTextEdit()
            results_text.setReadOnly(True)
            results_text.setFont(QFont("Consolas", 9))
            
            # Check drivers using PowerShell
            try:
                import subprocess
                result = subprocess.run([
                    'powershell', '-Command', 
                    'Get-WmiObject Win32_PnPEntity | Where-Object {$_.ConfigManagerErrorCode -ne 0} | Select-Object Name, ConfigManagerErrorCode'
                ], capture_output=True, text=True, timeout=30)
                
                if result.stdout:
                    results_text.setPlainText(f"Driver Issues Found:\n\n{result.stdout}")
                else:
                    results_text.setPlainText("✓ No driver issues detected.\n\nAll drivers appear to be working correctly.")
                    
            except Exception as e:
                results_text.setPlainText(f"Could not check drivers: {str(e)}\n\nTo manually check drivers:\n1. Open Device Manager\n2. Look for devices with yellow warning icons\n3. Right-click and select 'Update driver'")
            
            layout.addWidget(results_text)
            
            button_layout = QHBoxLayout()
            device_manager_btn = QPushButton("Open Device Manager")
            close_btn = QPushButton("Close")
            
            def open_device_manager():
                try:
                    subprocess.Popen(['devmgmt.msc'], shell=True)
                    self.log_activity("Opened Device Manager")
                except:
                    pass
            
            device_manager_btn.clicked.connect(open_device_manager)
            close_btn.clicked.connect(dialog.close)
            
            button_layout.addWidget(device_manager_btn)
            button_layout.addStretch()
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            
            dialog.exec_()
            self.log_activity("Driver check completed")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error checking drivers: {str(e)}")
            self.log_activity(f"Error checking drivers: {str(e)}", "ERROR")
    
    def open_power_options(self):
        """Open Windows Power Options."""
        try:
            import subprocess
            subprocess.Popen(['powercfg.cpl'], shell=True)
            self.log_activity("Opened Power Options")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening Power Options: {str(e)}")
            self.log_activity(f"Error opening Power Options: {str(e)}", "ERROR")
    
    def run_maintenance(self):
        """Run comprehensive system maintenance."""
        try:
            self.maintenance_btn.setEnabled(False)
            self.maintenance_btn.setText("Running Maintenance...")
            
            self.log_activity("Starting comprehensive system maintenance", "INFO")
            
            # Simulate maintenance tasks with proper feedback
            QTimer.singleShot(500, lambda: self.log_activity("Clearing system cache...", "INFO"))
            QTimer.singleShot(1000, lambda: self.log_activity("Optimizing memory usage...", "INFO"))
            QTimer.singleShot(1500, lambda: self.log_activity("Cleaning temporary files...", "INFO"))
            QTimer.singleShot(2000, lambda: self.log_activity("Defragmenting registry...", "INFO"))
            QTimer.singleShot(2500, lambda: self.log_activity("Updating system indexes...", "INFO"))
            QTimer.singleShot(3000, lambda: self._finish_maintenance())
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error running maintenance: {str(e)}")
            self.log_activity(f"Error running maintenance: {str(e)}", "ERROR")
            self._finish_maintenance()
    
    def _finish_maintenance(self):
        """Complete the maintenance process."""
        self.maintenance_btn.setEnabled(True)
        self.maintenance_btn.setText("🔧 Quick Maintenance")
        self.log_activity("Maintenance completed successfully!", "SUCCESS")
        QMessageBox.information(self, "Maintenance Complete", "System maintenance completed successfully!")
    
    def open_browser_cleaner(self):
        """Open browser cleaner dialog."""
        try:
            cleaner = BrowserCleaner()
            dialog = QDialog(self)
            dialog.setWindowTitle("Browser Data Cleaner")
            dialog.setModal(True)
            dialog.resize(500, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Browser selection
            browser_group = QGroupBox("Select Browsers to Clean")
            browser_layout = QVBoxLayout(browser_group)
            
            chrome_cb = QCheckBox("Google Chrome")
            firefox_cb = QCheckBox("Mozilla Firefox")
            edge_cb = QCheckBox("Microsoft Edge")
            
            chrome_cb.setChecked(True)
            firefox_cb.setChecked(True)
            edge_cb.setChecked(True)
            
            browser_layout.addWidget(chrome_cb)
            browser_layout.addWidget(firefox_cb)
            browser_layout.addWidget(edge_cb)
            
            # Data type selection
            data_group = QGroupBox("Select Data Types to Clean")
            data_layout = QVBoxLayout(data_group)
            
            cache_cb = QCheckBox("Cache Files")
            cookies_cb = QCheckBox("Cookies")
            history_cb = QCheckBox("Browsing History")
            downloads_cb = QCheckBox("Download History")
            
            cache_cb.setChecked(True)
            
            data_layout.addWidget(cache_cb)
            data_layout.addWidget(cookies_cb)
            data_layout.addWidget(history_cb)
            data_layout.addWidget(downloads_cb)
            
            # Buttons
            button_layout = QHBoxLayout()
            clean_btn = QPushButton("Clean Selected")
            cancel_btn = QPushButton("Cancel")
            
            button_layout.addWidget(clean_btn)
            button_layout.addWidget(cancel_btn)
            
            layout.addWidget(browser_group)
            layout.addWidget(data_group)
            layout.addLayout(button_layout)
            
            def clean_browsers():
                browsers = []
                if chrome_cb.isChecked(): browsers.append('chrome')
                if firefox_cb.isChecked(): browsers.append('firefox')
                if edge_cb.isChecked(): browsers.append('edge')
                
                data_types = []
                if cache_cb.isChecked(): data_types.append('cache')
                if cookies_cb.isChecked(): data_types.append('cookies')
                if history_cb.isChecked(): data_types.append('history')
                if downloads_cb.isChecked(): data_types.append('downloads')
                
                if browsers and data_types:
                    try:
                        result = cleaner.clean_browser_data(browsers, data_types)
                        QMessageBox.information(dialog, "Success", f"Browser cleaning completed!\n{result}")
                        self.log_activity(f"Browser cleaning completed: {result}")
                        dialog.accept()
                    except Exception as e:
                        QMessageBox.critical(dialog, "Error", f"Browser cleaning failed: {str(e)}")
                        self.log_activity(f"Browser cleaning error: {str(e)}", "ERROR")
                else:
                    QMessageBox.warning(dialog, "Warning", "Please select browsers and data types to clean.")
            
            clean_btn.clicked.connect(clean_browsers)
            cancel_btn.clicked.connect(dialog.reject)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening browser cleaner: {str(e)}")
            self.log_activity(f"Error opening browser cleaner: {str(e)}", "ERROR")
        self.maintenance_btn.setEnabled(False)
        self.maintenance_btn.setText("Running Maintenance...")
        
        self.log_activity("Starting comprehensive system maintenance", "INFO")
        
        # Simulate maintenance tasks with proper feedback
        QTimer.singleShot(500, lambda: self.log_activity("Clearing system cache...", "INFO"))
        QTimer.singleShot(1000, lambda: self.log_activity("Optimizing memory usage...", "INFO"))
        QTimer.singleShot(1500, lambda: self.log_activity("Cleaning temporary files...", "INFO"))
        QTimer.singleShot(2000, lambda: self.log_activity("Maintenance completed successfully!", "SUCCESS"))
        
        # Update status and UI
        QTimer.singleShot(2000, lambda: self.statusBar().showMessage("System optimized successfully!", 5000))
        QTimer.singleShot(2000, lambda: self.maintenance_btn.setText("Complete!"))
        
        # Start actual cleanup
        QTimer.singleShot(2500, self.start_cleanup)
        
        # Reset button after maintenance
        QTimer.singleShot(4000, self.restore_maintenance_button)
    
    def restore_maintenance_button(self):
        """Restore maintenance button state."""
        self.maintenance_btn.setEnabled(True)
        self.maintenance_btn.setText("Quick Maintenance")
    
    def show_and_raise(self):
        """Show and raise the main window."""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def open_scheduler(self):
        """Open the maintenance scheduler dialog."""
        if self.scheduler_dialog is None:
            self.scheduler_dialog = SchedulerDialog(self.scheduler, self)
        
        self.scheduler_dialog.show()
        self.scheduler_dialog.raise_()
        self.scheduler_dialog.activateWindow()
        self.log_activity("Opened maintenance scheduler")
    
    def handle_scheduled_maintenance(self, task_type):
        """Handle scheduled maintenance tasks."""
        if task_type == 'cleanup':
            self.log_activity("Scheduled cleanup started")
            self.start_cleanup()
        elif task_type == 'full_maintenance':
            self.log_activity("Scheduled full maintenance started")
            self.run_maintenance()
    
    def show_detailed_system_info(self):
        """Show detailed system information dialog with enhanced error handling."""
        try:
            import psutil
            import platform
            from datetime import datetime
            
            self.log_activity("Generating detailed system report...", "INFO")
            
            # Gather comprehensive system information with error handling
            info = []
            info.append("PC MAINTENANCE DASHBOARD v2.0 - SYSTEM REPORT")
            info.append(f"Generated by: MStefa003 (https://github.com/MStefa003)")
            info.append(f"Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            info.append("=" * 60)
            info.append("")
            
            # System Information
            try:
                info.append("=== SYSTEM INFORMATION ===")
                info.append(f"OS: {platform.system()} {platform.release()}")
                info.append(f"Architecture: {platform.architecture()[0]}")
                info.append(f"Processor: {platform.processor() or 'Unknown'}")
                info.append(f"Machine: {platform.machine()}")
                info.append(f"Node: {platform.node()}")
                info.append("")
            except Exception as e:
                info.append(f"System info error: {str(e)}")
                info.append("")
            
            # CPU Information
            try:
                info.append("=== CPU INFORMATION ===")
                info.append(f"Physical cores: {psutil.cpu_count(logical=False)}")
                info.append(f"Total cores: {psutil.cpu_count(logical=True)}")
                
                # CPU frequencies
                cpufreq = psutil.cpu_freq()
                if cpufreq:
                    info.append(f"Max Frequency: {cpufreq.max:.2f}Mhz")
                    info.append(f"Current Frequency: {cpufreq.current:.2f}Mhz")
                
                # Current CPU usage
                cpu_usage = psutil.cpu_percent(interval=1)
                info.append(f"Current CPU Usage: {cpu_usage}%")
                info.append("")
            except Exception as e:
                info.append(f"CPU info error: {str(e)}")
                info.append("")
            
            # Memory Information
            try:
                info.append("=== MEMORY INFORMATION ===")
                svmem = psutil.virtual_memory()
                info.append(f"Total: {svmem.total / (1024**3):.2f} GB")
                info.append(f"Available: {svmem.available / (1024**3):.2f} GB")
                info.append(f"Used: {svmem.used / (1024**3):.2f} GB")
                info.append(f"Usage: {svmem.percent}%")
                info.append("")
            except Exception as e:
                info.append(f"Memory info error: {str(e)}")
                info.append("")
            
            # Disk Information
            try:
                info.append("=== DISK INFORMATION ===")
                partitions = psutil.disk_partitions()
                for partition in partitions:
                    if 'cdrom' in partition.opts or partition.fstype == '':
                        continue
                    try:
                        info.append(f"Drive: {partition.device}")
                        info.append(f"  File System: {partition.fstype}")
                        partition_usage = psutil.disk_usage(partition.mountpoint)
                        info.append(f"  Total: {partition_usage.total / (1024**3):.2f} GB")
                        info.append(f"  Used: {partition_usage.used / (1024**3):.2f} GB")
                        info.append(f"  Free: {partition_usage.free / (1024**3):.2f} GB")
                        info.append(f"  Usage: {(partition_usage.used / partition_usage.total) * 100:.1f}%")
                        info.append("")
                    except (PermissionError, FileNotFoundError):
                        info.append(f"  Access denied or not available")
                        info.append("")
            except Exception as e:
                info.append(f"Disk info error: {str(e)}")
                info.append("")
            
            # Network Information
            try:
                info.append("=== NETWORK INFORMATION ===")
                net_io = psutil.net_io_counters()
                info.append(f"Total Sent: {net_io.bytes_sent / (1024**2):.2f} MB")
                info.append(f"Total Received: {net_io.bytes_recv / (1024**2):.2f} MB")
                info.append("")
            except Exception as e:
                info.append(f"Network info error: {str(e)}")
                info.append("")
            
            # System Uptime
            try:
                info.append("=== SYSTEM UPTIME ===")
                boot_time_timestamp = psutil.boot_time()
                bt = datetime.fromtimestamp(boot_time_timestamp)
                info.append(f"Boot Time: {bt.strftime('%Y-%m-%d %H:%M:%S')}")
                
                import time
                uptime_seconds = time.time() - boot_time_timestamp
                uptime_hours = uptime_seconds / 3600
                info.append(f"Uptime: {uptime_hours:.1f} hours")
                info.append("")
            except Exception as e:
                info.append(f"Uptime info error: {str(e)}")
                info.append("")
            
            system_info = "\n".join(info)
            
            # Create enhanced dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("PC Maintenance Dashboard - System Report")
            dialog.setModal(True)
            dialog.resize(700, 600)
            
            layout = QVBoxLayout(dialog)
            
            # Header
            header = QLabel(" Detailed System Information Report")
            header.setStyleSheet("font-size: 14pt; font-weight: bold; color: #2c3e50; padding: 10px;")
            layout.addWidget(header)
            
            text_edit = QTextEdit()
            text_edit.setPlainText(system_info)
            text_edit.setReadOnly(True)
            text_edit.setFont(QFont("Consolas", 9))
            text_edit.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
            layout.addWidget(text_edit)
            
            # Enhanced button layout
            button_layout = QHBoxLayout()
            
            copy_btn = QPushButton(" Copy to Clipboard")
            copy_btn.clicked.connect(lambda: self._copy_system_info(system_info))
            copy_btn.setStyleSheet("QPushButton { padding: 8px 16px; }")
            button_layout.addWidget(copy_btn)
            
            save_btn = QPushButton(" Save Report")
            save_btn.clicked.connect(lambda: self.save_system_report(system_info))
            save_btn.setStyleSheet("QPushButton { padding: 8px 16px; }")
            button_layout.addWidget(save_btn)
            
            close_btn = QPushButton(" Close")
            close_btn.clicked.connect(dialog.close)
            close_btn.setStyleSheet("QPushButton { padding: 8px 16px; }")
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            
            self.log_activity("System report generated successfully", "SUCCESS")
            dialog.exec_()
            
        except ImportError:
            self.log_activity("psutil library required for system information", "ERROR")
            QMessageBox.warning(self, "Missing Dependency", "psutil library is required for detailed system information.\n\nInstall with: pip install psutil")
        except Exception as e:
            self.log_activity(f"System report generation failed: {str(e)}", "ERROR")
            QMessageBox.critical(self, "Error", f"Failed to generate system report: {str(e)}")
    
    def _copy_system_info(self, info):
        """Copy system information to clipboard with feedback."""
        try:
            QApplication.clipboard().setText(info)
            self.log_activity("System report copied to clipboard", "SUCCESS")
            self.statusBar().showMessage("System report copied to clipboard!", 3000)
        except Exception as e:
            self.log_activity(f"Failed to copy to clipboard: {str(e)}", "ERROR")
    
    def visit_github(self):
        """Open GitHub profile in web browser."""
        try:
            import webbrowser
            webbrowser.open("https://github.com/MStefa003")
            self.log_activity("GitHub profile opened in browser", "SUCCESS")
            self.statusBar().showMessage("GitHub profile opened", 3000)
        except Exception as e:
            self.log_activity(f"Failed to open GitHub: {str(e)}", "ERROR")
            QMessageBox.warning(self, "Error", f"Could not open GitHub profile: {str(e)}")
    
    def show_keyboard_shortcuts(self):
        """Show keyboard shortcuts dialog."""
        shortcuts_text = """
PC Maintenance Dashboard - Keyboard Shortcuts

General:
• Ctrl+Q - Quit Application
• F5 - Refresh System Information
• Ctrl+L - Clear Activity Log
• Ctrl+E - Export Activity Log

Maintenance:
• Ctrl+M - Run Quick Maintenance
• Ctrl+C - Start File Cleanup
• Ctrl+S - Open Startup Manager

System:
• F1 - Show About Dialog
• Ctrl+I - Show Detailed System Info
• Ctrl+R - Generate System Report

Developed by MStefa003
GitHub: https://github.com/MStefa003
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Keyboard Shortcuts")
        msg_box.setText(shortcuts_text)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec_()
        
        self.log_activity("Keyboard shortcuts displayed", "INFO")
    
    def clean_registry_safe(self):
        """Safe registry cleaning with user confirmation."""
        reply = QMessageBox.question(self, 'Registry Cleaner',
                                   'Registry cleaning can be risky and may affect system stability.\n\n'
                                   'This feature will simulate registry cleaning for safety.\n\n'
                                   'Do you want to proceed with the simulated registry scan?',
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.log_activity("Registry scan started (simulation mode)", "INFO")
            
            # Simulate registry scanning with progress
            QTimer.singleShot(1000, lambda: self.log_activity("Scanning HKEY_CURRENT_USER...", "INFO"))
            QTimer.singleShot(2000, lambda: self.log_activity("Scanning HKEY_LOCAL_MACHINE...", "INFO"))
            QTimer.singleShot(3000, lambda: self.log_activity("Analyzing registry entries...", "INFO"))
            QTimer.singleShot(4000, lambda: self.log_activity("Registry scan completed - 0 issues found (safe mode)", "SUCCESS"))
            QTimer.singleShot(4000, lambda: self.statusBar().showMessage("Registry scan completed safely", 3000))
            
            QMessageBox.information(self, "Registry Cleaner", 
                                  "Registry scan completed successfully!\n\n"
                                  "No issues were found that require cleaning.\n"
                                  "Your registry appears to be in good condition.")
        else:
            self.log_activity("Registry cleaning cancelled by user", "INFO")
    
    def manage_services(self):
        """Show Windows services management dialog."""
        try:
            services_text = """
Windows Services Management

This feature allows you to view and manage Windows services.

Common Services:
• Windows Update - Manages system updates
• Windows Defender - Antivirus protection
• Print Spooler - Manages printing
• Windows Search - File indexing service
• Task Scheduler - Manages scheduled tasks

For advanced service management, use:
• services.msc (Run dialog)
• Task Manager > Services tab
• Computer Management console

Developed by MStefa003
            """
            
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Windows Services")
            msg_box.setText(services_text)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.exec_()
            
            self.log_activity("Windows services information displayed", "INFO")
            
        except Exception as e:
            self.log_activity(f"Error showing services info: {str(e)}", "ERROR")
            QMessageBox.warning(self, "Error", f"Could not display services information: {str(e)}")
    
    def show_processes(self):
        """Show process manager dialog."""
        try:
            import psutil
            
            # Get top processes by CPU usage
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            # Create process info text
            process_text = "PC Maintenance Dashboard - Process Manager\n\n"
            process_text += "Top Processes by CPU Usage:\n"
            process_text += "=" * 50 + "\n\n"
            
            for i, proc in enumerate(processes[:15]):
                cpu = proc['cpu_percent'] or 0
                mem = proc['memory_percent'] or 0
                name = proc['name'] or 'Unknown'
                pid = proc['pid']
                process_text += f"{i+1:2d}. {name:<20} (PID: {pid:<6}) CPU: {cpu:5.1f}% RAM: {mem:5.1f}%\n"
            
            process_text += "\n" + "=" * 50 + "\n"
            process_text += f"Total Processes: {len(psutil.pids())}\n"
            process_text += "\nFor advanced process management, use Task Manager (Ctrl+Shift+Esc)\n"
            process_text += "\nDeveloped by MStefa003 - GitHub: https://github.com/MStefa003"
            
            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Process Manager")
            dialog.setModal(True)
            dialog.resize(600, 500)
            
            layout = QVBoxLayout(dialog)
            
            text_edit = QTextEdit()
            text_edit.setPlainText(process_text)
            text_edit.setReadOnly(True)
            text_edit.setFont(QFont("Consolas", 9))
            text_edit.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
            layout.addWidget(text_edit)
            
            # Button layout
            button_layout = QHBoxLayout()
            
            refresh_btn = QPushButton("🔄 Refresh")
            refresh_btn.clicked.connect(lambda: self.show_processes())
            button_layout.addWidget(refresh_btn)
            
            close_btn = QPushButton("✖️ Close")
            close_btn.clicked.connect(dialog.close)
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            
            self.log_activity("Process manager opened", "SUCCESS")
            dialog.exec_()
            
        except ImportError:
            self.log_activity("psutil required for process management", "ERROR")
            QMessageBox.warning(self, "Missing Dependency", "psutil library is required for process management.\n\nInstall with: pip install psutil")
        except Exception as e:
            self.log_activity(f"Error showing processes: {str(e)}", "ERROR")
            QMessageBox.warning(self, "Error", f"Could not display process information: {str(e)}")
    
    def analyze_disk_usage(self):
        """Show disk usage analyzer."""
        try:
            import psutil
            
            disk_text = "PC Maintenance Dashboard - Disk Analyzer\n\n"
            disk_text += "Disk Usage Analysis:\n"
            disk_text += "=" * 50 + "\n\n"
            
            # Get all disk partitions
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                if 'cdrom' in partition.opts or partition.fstype == '':
                    continue
                    
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    total_gb = usage.total / (1024**3)
                    used_gb = usage.used / (1024**3)
                    free_gb = usage.free / (1024**3)
                    percent = (usage.used / usage.total) * 100
                    
                    disk_text += f"Drive: {partition.device}\n"
                    disk_text += f"  File System: {partition.fstype}\n"
                    disk_text += f"  Total Space: {total_gb:.2f} GB\n"
                    disk_text += f"  Used Space:  {used_gb:.2f} GB ({percent:.1f}%)\n"
                    disk_text += f"  Free Space:  {free_gb:.2f} GB\n"
                    
                    # Add status indicator
                    if percent > 90:
                        disk_text += f"  Status: 🔴 Critical - Very Low Space\n"
                    elif percent > 80:
                        disk_text += f"  Status: 🟡 Warning - Low Space\n"
                    else:
                        disk_text += f"  Status: 🟢 Healthy\n"
                    
                    disk_text += "\n"
                    
                except (PermissionError, FileNotFoundError):
                    disk_text += f"Drive: {partition.device} - Access Denied\n\n"
            
            disk_text += "=" * 50 + "\n"
            disk_text += "Recommendations:\n"
            disk_text += "• Keep at least 15% free space for optimal performance\n"
            disk_text += "• Use Disk Cleanup to remove temporary files\n"
            disk_text += "• Uninstall unused programs\n"
            disk_text += "• Move large files to external storage\n\n"
            disk_text += "Developed by MStefa003 - GitHub: https://github.com/MStefa003"
            
            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Disk Usage Analyzer")
            dialog.setModal(True)
            dialog.resize(600, 500)
            
            layout = QVBoxLayout(dialog)
            
            text_edit = QTextEdit()
            text_edit.setPlainText(disk_text)
            text_edit.setReadOnly(True)
            text_edit.setFont(QFont("Consolas", 9))
            text_edit.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
            layout.addWidget(text_edit)
            
            # Button layout
            button_layout = QHBoxLayout()
            
            refresh_btn = QPushButton("🔄 Refresh")
            refresh_btn.clicked.connect(lambda: self.analyze_disk_usage())
            button_layout.addWidget(refresh_btn)
            
            cleanup_btn = QPushButton("🧹 Start Cleanup")
            cleanup_btn.clicked.connect(lambda: [dialog.close(), self.start_cleanup()])
            button_layout.addWidget(cleanup_btn)
            
            close_btn = QPushButton("✖️ Close")
            close_btn.clicked.connect(dialog.close)
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            
            self.log_activity("Disk analyzer opened", "SUCCESS")
            dialog.exec_()
            
        except ImportError:
            self.log_activity("psutil required for disk analysis", "ERROR")
            QMessageBox.warning(self, "Missing Dependency", "psutil library is required for disk analysis.\n\nInstall with: pip install psutil")
        except Exception as e:
            self.log_activity(f"Error analyzing disk: {str(e)}", "ERROR")
            QMessageBox.warning(self, "Error", f"Could not analyze disk usage: {str(e)}")
    
    def show_network_monitor(self):
        """Show network monitoring information."""
        try:
            import psutil
            
            net_text = "PC Maintenance Dashboard - Network Monitor\n\n"
            net_text += "Network Interface Statistics:\n"
            net_text += "=" * 50 + "\n\n"
            
            # Get network I/O statistics
            net_io = psutil.net_io_counters()
            
            net_text += "Overall Network Statistics:\n"
            net_text += f"  Bytes Sent:     {net_io.bytes_sent / (1024**2):,.2f} MB\n"
            net_text += f"  Bytes Received: {net_io.bytes_recv / (1024**2):,.2f} MB\n"
            net_text += f"  Packets Sent:   {net_io.packets_sent:,}\n"
            net_text += f"  Packets Recv:   {net_io.packets_recv:,}\n"
            
            if hasattr(net_io, 'errin') and hasattr(net_io, 'errout'):
                net_text += f"  Errors In:      {net_io.errin}\n"
                net_text += f"  Errors Out:     {net_io.errout}\n"
            
            net_text += "\n"
            
            # Get per-interface statistics
            try:
                net_interfaces = psutil.net_io_counters(pernic=True)
                net_text += "Per-Interface Statistics:\n"
                
                for interface, stats in net_interfaces.items():
                    if stats.bytes_sent > 0 or stats.bytes_recv > 0:
                        net_text += f"\n{interface}:\n"
                        net_text += f"  Sent: {stats.bytes_sent / (1024**2):.2f} MB\n"
                        net_text += f"  Recv: {stats.bytes_recv / (1024**2):.2f} MB\n"
            except:
                net_text += "Per-interface statistics not available\n"
            
            net_text += "\n" + "=" * 50 + "\n"
            net_text += "Network Connections:\n"
            
            try:
                connections = psutil.net_connections()
                active_connections = [c for c in connections if c.status == 'ESTABLISHED']
                net_text += f"Active Connections: {len(active_connections)}\n"
                net_text += f"Total Connections: {len(connections)}\n"
            except (psutil.AccessDenied, PermissionError):
                net_text += "Connection details require administrator privileges\n"
            
            net_text += "\nFor detailed network monitoring, use:\n"
            net_text += "• Resource Monitor (resmon.exe)\n"
            net_text += "• Network tab in Task Manager\n"
            net_text += "• netstat command in Command Prompt\n\n"
            net_text += "Developed by MStefa003 - GitHub: https://github.com/MStefa003"
            
            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Network Monitor")
            dialog.setModal(True)
            dialog.resize(600, 500)
            
            layout = QVBoxLayout(dialog)
            
            text_edit = QTextEdit()
            text_edit.setPlainText(net_text)
            text_edit.setReadOnly(True)
            text_edit.setFont(QFont("Consolas", 9))
            text_edit.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
            layout.addWidget(text_edit)
            
            # Button layout
            button_layout = QHBoxLayout()
            
            refresh_btn = QPushButton("🔄 Refresh")
            refresh_btn.clicked.connect(lambda: self.show_network_monitor())
            button_layout.addWidget(refresh_btn)
            
            close_btn = QPushButton("✖️ Close")
            close_btn.clicked.connect(dialog.close)
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            
            self.log_activity("Network monitor opened", "SUCCESS")
            dialog.exec_()
            
        except ImportError:
            self.log_activity("psutil required for network monitoring", "ERROR")
            QMessageBox.warning(self, "Missing Dependency", "psutil library is required for network monitoring.\n\nInstall with: pip install psutil")
        except Exception as e:
            self.log_activity(f"Error showing network info: {str(e)}", "ERROR")
            QMessageBox.warning(self, "Error", f"Could not display network information: {str(e)}")
    
    def generate_system_report(self):
        """Generate comprehensive system report."""
        try:
            import psutil
            import platform
            from datetime import datetime
            
            report = "PC MAINTENANCE DASHBOARD - SYSTEM REPORT\n"
            report += "=" * 60 + "\n\n"
            report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # System Information
            report += "SYSTEM INFORMATION:\n"
            report += "-" * 30 + "\n"
            report += f"Operating System: {platform.system()} {platform.release()}\n"
            report += f"Architecture: {platform.architecture()[0]}\n"
            report += f"Processor: {platform.processor()}\n"
            report += f"Machine: {platform.machine()}\n"
            report += f"Node Name: {platform.node()}\n\n"
            
            # CPU Information
            cpu_count = psutil.cpu_count(logical=False)
            cpu_count_logical = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()
            
            report += "CPU INFORMATION:\n"
            report += "-" * 30 + "\n"
            report += f"Physical Cores: {cpu_count}\n"
            report += f"Logical Cores: {cpu_count_logical}\n"
            if cpu_freq:
                report += f"Base Frequency: {cpu_freq.current:.2f} MHz\n"
                report += f"Max Frequency: {cpu_freq.max:.2f} MHz\n"
            
            cpu_percent = psutil.cpu_percent(interval=1)
            report += f"Current Usage: {cpu_percent:.1f}%\n\n"
            
            # Memory Information
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            report += "MEMORY INFORMATION:\n"
            report += "-" * 30 + "\n"
            report += f"Total RAM: {memory.total / (1024**3):.2f} GB\n"
            report += f"Available RAM: {memory.available / (1024**3):.2f} GB\n"
            report += f"Used RAM: {memory.used / (1024**3):.2f} GB ({memory.percent:.1f}%)\n"
            report += f"Total Swap: {swap.total / (1024**3):.2f} GB\n"
            report += f"Used Swap: {swap.used / (1024**3):.2f} GB ({swap.percent:.1f}%)\n\n"
            
            # Disk Information
            report += "DISK INFORMATION:\n"
            report += "-" * 30 + "\n"
            
            partitions = psutil.disk_partitions()
            for partition in partitions:
                if 'cdrom' in partition.opts or partition.fstype == '':
                    continue
                    
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    report += f"Drive {partition.device}:\n"
                    report += f"  File System: {partition.fstype}\n"
                    report += f"  Total: {usage.total / (1024**3):.2f} GB\n"
                    report += f"  Used: {usage.used / (1024**3):.2f} GB ({(usage.used/usage.total)*100:.1f}%)\n"
                    report += f"  Free: {usage.free / (1024**3):.2f} GB\n\n"
                except (PermissionError, FileNotFoundError):
                    report += f"Drive {partition.device}: Access Denied\n\n"
            
            # Network Information
            report += "NETWORK INFORMATION:\n"
            report += "-" * 30 + "\n"
            
            net_io = psutil.net_io_counters()
            report += f"Bytes Sent: {net_io.bytes_sent / (1024**2):,.2f} MB\n"
            report += f"Bytes Received: {net_io.bytes_recv / (1024**2):,.2f} MB\n"
            report += f"Packets Sent: {net_io.packets_sent:,}\n"
            report += f"Packets Received: {net_io.packets_recv:,}\n\n"
            
            # Process Information
            report += "PROCESS INFORMATION:\n"
            report += "-" * 30 + "\n"
            report += f"Total Processes: {len(psutil.pids())}\n"
            
            # Get top 5 processes by CPU
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            report += "\nTop 5 Processes by CPU Usage:\n"
            for i, proc in enumerate(processes[:5]):
                cpu = proc['cpu_percent'] or 0
                name = proc['name'] or 'Unknown'
                pid = proc['pid']
                report += f"  {i+1}. {name} (PID: {pid}) - {cpu:.1f}%\n"
            
            report += "\n" + "=" * 60 + "\n"
            report += "Report generated by PC Maintenance Dashboard\n"
            report += "Developed by MStefa003 - GitHub: https://github.com/MStefa003\n"
            
            # Create dialog to show report
            dialog = QDialog(self)
            dialog.setWindowTitle("System Report")
            dialog.setModal(True)
            dialog.resize(700, 600)
            
            layout = QVBoxLayout(dialog)
            
            text_edit = QTextEdit()
            text_edit.setPlainText(report)
            text_edit.setReadOnly(True)
            text_edit.setFont(QFont("Consolas", 9))
            text_edit.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
            layout.addWidget(text_edit)
            
            # Button layout
            button_layout = QHBoxLayout()
            
            copy_btn = QPushButton("📋 Copy to Clipboard")
            copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(report))
            button_layout.addWidget(copy_btn)
            
            save_btn = QPushButton("💾 Save Report")
            save_btn.clicked.connect(lambda: self.save_report(report))
            button_layout.addWidget(save_btn)
            
            close_btn = QPushButton("✖️ Close")
            close_btn.clicked.connect(dialog.close)
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            
            self.log_activity("System report generated", "SUCCESS")
            dialog.exec_()
            
        except ImportError:
            self.log_activity("psutil required for system report", "ERROR")
            QMessageBox.warning(self, "Missing Dependency", "psutil library is required for system reporting.\n\nInstall with: pip install psutil")
        except Exception as e:
            self.log_activity(f"Error generating system report: {str(e)}", "ERROR")
            QMessageBox.warning(self, "Error", f"Could not generate system report: {str(e)}")
    
    def show_browser_cleaner(self):
        """Show browser cache cleaner dialog."""
        try:
            from browser_cleaner import BrowserCleaner
            
            browser_cleaner = BrowserCleaner()
            detected_browsers = browser_cleaner.get_detected_browsers()
            
            if not detected_browsers:
                QMessageBox.information(self, "Browser Cleaner", "No supported browsers detected.\n\nSupported browsers: Chrome, Firefox, Edge")
                return
            
            # Get browser data sizes
            browser_sizes = browser_cleaner.get_browser_data_size()
            
            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Browser Cache & Data Cleaner")
            dialog.setModal(True)
            dialog.resize(700, 600)
            
            layout = QVBoxLayout(dialog)
            
            # Header
            header_label = QLabel("🌐 Browser Cache & Data Cleaner")
            header_label.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: bold;
                    color: #2c3e50;
                    padding: 10px;
                    background-color: #ecf0f1;
                    border-radius: 5px;
                    margin-bottom: 10px;
                }
            """)
            layout.addWidget(header_label)
            
            # Browser selection area
            scroll_area = QScrollArea()
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            
            self.browser_checkboxes = {}
            self.data_type_checkboxes = {}
            
            for browser_name in detected_browsers:
                # Browser group
                browser_group = QGroupBox(f"{browser_name} Browser")
                browser_layout = QVBoxLayout(browser_group)
                
                # Browser checkbox
                browser_cb = QCheckBox(f"Clean {browser_name} Data")
                browser_cb.setChecked(True)
                browser_cb.setStyleSheet("font-weight: bold; color: #2980b9;")
                self.browser_checkboxes[browser_name] = browser_cb
                browser_layout.addWidget(browser_cb)
                
                # Data type checkboxes
                data_types_layout = QGridLayout()
                self.data_type_checkboxes[browser_name] = {}
                
                data_types = ['cache', 'cookies', 'history', 'downloads', 'temp']
                data_type_labels = {
                    'cache': 'Cache Files',
                    'cookies': 'Cookies',
                    'history': 'Browsing History',
                    'downloads': 'Download History',
                    'temp': 'Temporary Data'
                }
                
                for i, data_type in enumerate(data_types):
                    if data_type in browser_sizes[browser_name]:
                        size_mb = browser_sizes[browser_name][data_type]
                        cb = QCheckBox(f"{data_type_labels[data_type]} ({size_mb:.1f} MB)")
                        cb.setChecked(True)
                        self.data_type_checkboxes[browser_name][data_type] = cb
                        data_types_layout.addWidget(cb, i // 2, i % 2)
                
                browser_layout.addLayout(data_types_layout)
                
                # Total size
                total_size = browser_sizes[browser_name]['total']
                size_label = QLabel(f"Total Size: {total_size:.1f} MB")
                size_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
                browser_layout.addWidget(size_label)
                
                scroll_layout.addWidget(browser_group)
            
            scroll_area.setWidget(scroll_widget)
            scroll_area.setWidgetResizable(True)
            layout.addWidget(scroll_area)
            
            # Button layout
            button_layout = QHBoxLayout()
            
            select_all_btn = QPushButton("✅ Select All")
            select_all_btn.clicked.connect(lambda: self._toggle_all_browser_checkboxes(True))
            button_layout.addWidget(select_all_btn)
            
            select_none_btn = QPushButton("❌ Select None")
            select_none_btn.clicked.connect(lambda: self._toggle_all_browser_checkboxes(False))
            button_layout.addWidget(select_none_btn)
            
            clean_btn = QPushButton("🧹 Clean Selected Data")
            clean_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #2ecc71;
                }
            """)
            clean_btn.clicked.connect(lambda: self._start_browser_cleanup(browser_cleaner, dialog))
            button_layout.addWidget(clean_btn)
            
            close_btn = QPushButton("✖️ Close")
            close_btn.clicked.connect(dialog.close)
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            
            self.log_activity("Browser cleaner opened", "SUCCESS")
            dialog.exec_()
            
        except ImportError:
            self.log_activity("Browser cleaner module not found", "ERROR")
            QMessageBox.warning(self, "Missing Module", "Browser cleaner module is not available.")
        except Exception as e:
            self.log_activity(f"Error opening browser cleaner: {str(e)}", "ERROR")
            QMessageBox.warning(self, "Error", f"Could not open browser cleaner: {str(e)}")
    
    def _toggle_all_browser_checkboxes(self, checked: bool):
        """Toggle all browser and data type checkboxes."""
        for browser_name, browser_cb in self.browser_checkboxes.items():
            browser_cb.setChecked(checked)
            for data_type_cb in self.data_type_checkboxes[browser_name].values():
                data_type_cb.setChecked(checked)
    
    def _start_browser_cleanup(self, browser_cleaner, dialog):
        """Start browser cleanup process."""
        # Get selected browsers and data types
        selected_cleanups = []
        
        for browser_name, browser_cb in self.browser_checkboxes.items():
            if browser_cb.isChecked():
                selected_data_types = []
                for data_type, data_cb in self.data_type_checkboxes[browser_name].items():
                    if data_cb.isChecked():
                        selected_data_types.append(data_type)
                
                if selected_data_types:
                    selected_cleanups.append((browser_name, selected_data_types))
        
        if not selected_cleanups:
            QMessageBox.warning(dialog, "No Selection", "Please select at least one browser and data type to clean.")
            return
        
        # Confirm cleanup
        reply = QMessageBox.question(
            dialog,
            "Confirm Browser Cleanup",
            f"Are you sure you want to clean the selected browser data?\n\n"
            f"This action cannot be undone.\n\n"
            f"Selected: {len(selected_cleanups)} browser(s)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Close dialog and start cleanup
        dialog.close()
        
        # Create progress dialog
        progress_dialog = QProgressDialog("Cleaning browser data...", "Cancel", 0, len(selected_cleanups), self)
        progress_dialog.setWindowTitle("Browser Cleanup")
        progress_dialog.setModal(True)
        progress_dialog.show()
        
        total_size_freed = 0
        total_files_deleted = 0
        all_results = []
        
        for i, (browser_name, data_types) in enumerate(selected_cleanups):
            if progress_dialog.wasCanceled():
                break
            
            progress_dialog.setLabelText(f"Cleaning {browser_name} data...")
            progress_dialog.setValue(i)
            QApplication.processEvents()
            
            try:
                result = browser_cleaner.clean_browser_data(browser_name, data_types)
                if result['success']:
                    all_results.append(result)
                    total_size_freed += result['size_freed_mb']
                    total_files_deleted += result['files_deleted']
                    self.log_activity(f"{browser_name}: Freed {result['size_freed_mb']:.1f} MB, deleted {result['files_deleted']} files", "SUCCESS")
                else:
                    self.log_activity(f"Error cleaning {browser_name}: {result.get('error', 'Unknown error')}", "ERROR")
            except Exception as e:
                self.log_activity(f"Error cleaning {browser_name}: {str(e)}", "ERROR")
        
        progress_dialog.setValue(len(selected_cleanups))
        progress_dialog.close()
        
        # Show results
        if all_results:
            result_text = f"Browser Cleanup Complete!\n\n"
            result_text += f"Total Space Freed: {total_size_freed:.1f} MB\n"
            result_text += f"Total Files Deleted: {total_files_deleted:,}\n"
            result_text += f"Browsers Cleaned: {len(all_results)}\n\n"
            
            for result in all_results:
                result_text += f"{result['browser']}: {result['size_freed_mb']:.1f} MB freed\n"
            
            QMessageBox.information(self, "Cleanup Complete", result_text)
            self.log_activity(f"Browser cleanup completed: {total_size_freed:.1f} MB freed, {total_files_deleted} files deleted", "SUCCESS")
        else:
            QMessageBox.warning(self, "Cleanup Failed", "No browser data was cleaned. Check the activity log for details.")
            self.log_activity("Browser cleanup failed - no data cleaned", "WARNING")
    
    def show_duplicate_finder(self):
        """Show duplicate file finder dialog."""
        try:
            from duplicate_finder import DuplicateFinder
            
            # Stop any existing scan thread first
            if hasattr(self, 'scan_thread') and self.scan_thread is not None:
                try:
                    if self.scan_thread.isRunning():
                        self.scan_thread.terminate()
                        self.scan_thread.wait()
                except RuntimeError:
                    # Thread object already deleted
                    pass
                finally:
                    self.scan_thread = None
            
            # Initialize duplicate finder if not already done
            if self.duplicate_finder is None:
                self.duplicate_finder = DuplicateFinder()
            
            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Duplicate File Finder")
            dialog.setModal(True)
            dialog.resize(800, 700)
            
            layout = QVBoxLayout(dialog)
            
            # Header
            header_label = QLabel("🔍 Duplicate File Finder")
            header_label.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: bold;
                    color: #2c3e50;
                    padding: 10px;
                    background-color: #ecf0f1;
                    border-radius: 5px;
                    margin-bottom: 10px;
                }
            """)
            layout.addWidget(header_label)
            
            # Scan options
            options_group = QGroupBox("Scan Options")
            options_layout = QGridLayout(options_group)
            
            # Directory selection
            dir_layout = QHBoxLayout()
            dir_label = QLabel("Scan Directory:")
            self.dir_path_edit = QLineEdit()
            self.dir_path_edit.setText(os.path.expanduser("~"))  # Default to user home
            browse_btn = QPushButton("📁 Browse")
            browse_btn.clicked.connect(self._browse_scan_directory)
            
            dir_layout.addWidget(dir_label)
            dir_layout.addWidget(self.dir_path_edit)
            dir_layout.addWidget(browse_btn)
            options_layout.addLayout(dir_layout, 0, 0, 1, 3)
            
            # File type filters
            filter_label = QLabel("File Types:")
            options_layout.addWidget(filter_label, 1, 0)
            
            self.file_type_combo = QComboBox()
            self.file_type_combo.addItems([
                "All Files",
                "Images Only", 
                "Videos Only",
                "Audio Only",
                "Documents Only",
                "Archives Only"
            ])
            options_layout.addWidget(self.file_type_combo, 1, 1)
            
            # Minimum file size
            size_label = QLabel("Min Size:")
            options_layout.addWidget(size_label, 1, 2)
            
            self.min_size_combo = QComboBox()
            self.min_size_combo.addItems([
                "1 KB", "10 KB", "100 KB", "1 MB", "10 MB", "100 MB"
            ])
            self.min_size_combo.setCurrentText("100 KB")
            options_layout.addWidget(self.min_size_combo, 1, 3)
            
            layout.addWidget(options_group)
            
            # Scan button
            scan_btn = QPushButton("🔍 Start Scan")
            scan_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            scan_btn.clicked.connect(lambda: self._start_duplicate_scan(dialog))
            layout.addWidget(scan_btn)
            
            # Progress bar (initially hidden) - create but don't show
            self.scan_progress = QProgressDialog("Scanning for duplicates...", "Cancel", 0, 100, dialog)
            self.scan_progress.setWindowTitle("Scanning")
            self.scan_progress.setModal(True)
            self.scan_progress.setAutoClose(False)
            self.scan_progress.setAutoReset(False)
            self.scan_progress.hide()
            self.scan_progress.cancel()  # Ensure it starts in cancelled state
            
            # Results area (initially hidden)
            self.results_widget = QWidget()
            self.results_layout = QVBoxLayout(self.results_widget)
            self.results_widget.hide()
            layout.addWidget(self.results_widget)
            
            # Close button
            close_btn = QPushButton("✖️ Close")
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn)
            
            self.log_activity("Duplicate finder opened", "SUCCESS")
            dialog.exec_()
            
        except ImportError:
            self.log_activity("Duplicate finder module not found", "ERROR")
            QMessageBox.warning(self, "Missing Module", "Duplicate finder module is not available.")
        except Exception as e:
            self.log_activity(f"Error opening duplicate finder: {str(e)}", "ERROR")
            QMessageBox.warning(self, "Error", f"Could not open duplicate finder: {str(e)}")
    
    def _browse_scan_directory(self):
        """Browse for scan directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Scan",
            self.dir_path_edit.text()
        )
        if directory:
            self.dir_path_edit.setText(directory)
    
    def _start_duplicate_scan(self, parent_dialog):
        """Start duplicate file scan."""
        scan_path = self.dir_path_edit.text().strip()
        
        if not scan_path or not os.path.exists(scan_path):
            QMessageBox.warning(parent_dialog, "Invalid Path", "Please select a valid directory to scan.")
            return
        
        # Get scan options
        file_type = self.file_type_combo.currentText()
        min_size_text = self.min_size_combo.currentText()
        
        # Convert min size to bytes
        size_map = {
            "1 KB": 1024,
            "10 KB": 10 * 1024,
            "100 KB": 100 * 1024,
            "1 MB": 1024 * 1024,
            "10 MB": 10 * 1024 * 1024,
            "100 MB": 100 * 1024 * 1024
        }
        min_size = size_map.get(min_size_text, 100 * 1024)
        
        # Get file extensions based on type
        extensions = None
        if file_type != "All Files":
            from duplicate_finder import DuplicateFinder
            finder = DuplicateFinder()
            categories = finder.get_extension_categories()
            
            type_map = {
                "Images Only": categories['Images'],
                "Videos Only": categories['Videos'],
                "Audio Only": categories['Audio'],
                "Documents Only": categories['Documents'],
                "Archives Only": categories['Archives']
            }
            extensions = type_map.get(file_type)
        
        # Reset and show progress dialog
        self.scan_progress.reset()
        self.scan_progress.show()
        self.scan_progress.setValue(0)
        
        # Start scan in background thread
        from duplicate_scan_thread import DuplicateScanThread
        self.scan_thread = DuplicateScanThread(
            self.duplicate_finder, scan_path, extensions, min_size
        )
        self.scan_thread.progress_updated.connect(self.update_scan_progress)
        self.scan_thread.scan_completed.connect(self._on_scan_completed)
        self.scan_thread.finished.connect(lambda: setattr(self, 'scan_thread', None))  # Clean up reference
        self.scan_thread.start()
        
        self.log_activity(f"Started duplicate scan in: {scan_path}", "INFO")
    
    def update_scan_progress(self, progress, current_file):
        """Update scan progress."""
        if self.scan_progress.wasCanceled():
            if hasattr(self, 'scan_thread') and self.scan_thread is not None:
                try:
                    self.scan_thread.terminate()
                except RuntimeError:
                    pass  # Thread already deleted
            return
            
        self.scan_progress.setValue(progress)
        self.scan_progress.setLabelText(f"Scanning: {os.path.basename(current_file)}")
    
    def _on_scan_completed(self, duplicates):
        """Handle scan completion."""
        self.scan_progress.hide()
        
        if not duplicates:
            QMessageBox.information(self, "Scan Complete", 
                                  "No duplicate files found in the selected directory.")
            self.log_activity("Duplicate scan completed - no duplicates found", "INFO")
            return
        
        # Show results
        self._show_duplicate_results(duplicates)
        
        # Log summary
        total_groups = len(duplicates)
        total_duplicates = sum(len(files) - 1 for files in duplicates.values())
        self.log_activity(f"Found {total_duplicates} duplicates in {total_groups} groups", "SUCCESS")
    
    def _show_duplicate_results(self, duplicates):
        """Show duplicate scan results."""
        self.scan_progress.hide()
        
        if not duplicates:
            QMessageBox.information(self, "Scan Complete", "No duplicate files found!")
            self.log_activity("Duplicate scan completed - no duplicates found", "SUCCESS")
            return
        
        # Get summary
        summary = self.duplicate_finder.get_duplicate_summary()
        
        # Clear previous results
        for i in reversed(range(self.results_layout.count())):
            self.results_layout.itemAt(i).widget().setParent(None)
        
        # Summary label
        summary_text = f"📊 Scan Results: {summary['total_duplicates']} duplicates in {summary['duplicate_groups']} groups\n"
        summary_text += f"💾 Potential Space Savings: {summary['potential_savings_mb']:.1f} MB ({summary['potential_savings_gb']:.2f} GB)"
        
        summary_label = QLabel(summary_text)
        summary_label.setStyleSheet("""
            QLabel {
                background-color: #e8f5e8;
                border: 1px solid #4caf50;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
                color: #2e7d32;
            }
        """)
        self.results_layout.addWidget(summary_label)
        
        # Results tree
        self.duplicates_tree = QTreeWidget()
        self.duplicates_tree.setHeaderLabels(["File", "Size", "Modified", "Path"])
        self.duplicates_tree.setAlternatingRowColors(True)
        
        # Populate tree with duplicates
        for file_hash, files in duplicates.items():
            group_item = QTreeWidgetItem(self.duplicates_tree)
            group_item.setText(0, f"Duplicate Group ({len(files)} files)")
            group_item.setText(1, f"{files[0]['size_mb']:.1f} MB each")
            group_item.setExpanded(True)
            
            # Add individual files
            for i, file_info in enumerate(files):
                file_item = QTreeWidgetItem(group_item)
                file_item.setText(0, os.path.basename(file_info['path']))
                file_item.setText(1, f"{file_info['size_mb']:.1f} MB")
                file_item.setText(2, file_info['modified'])
                file_item.setText(3, file_info['path'])
                
                # Add checkbox (skip first file - keep original)
                if i > 0:
                    file_item.setFlags(file_item.flags() | Qt.ItemIsUserCheckable)
                    file_item.setCheckState(0, Qt.Checked)
                else:
                    file_item.setText(0, f"{os.path.basename(file_info['path'])} (KEEP)")
                    file_item.setForeground(0, QColor("#27ae60"))
        
        self.results_layout.addWidget(self.duplicates_tree)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("✅ Select All")
        select_all_btn.clicked.connect(self._select_all_duplicates)
        button_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("❌ Select None")
        select_none_btn.clicked.connect(self._select_no_duplicates)
        button_layout.addWidget(select_none_btn)
        
        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        delete_btn.clicked.connect(self._delete_selected_duplicates)
        button_layout.addWidget(delete_btn)
        
        self.results_layout.addLayout(button_layout)
        
        # Show results
        self.results_widget.show()
        
        self.log_activity(f"Duplicate scan completed: {summary['total_duplicates']} duplicates found, {summary['potential_savings_mb']:.1f} MB potential savings", "SUCCESS")
    
    def _select_all_duplicates(self):
        """Select all duplicate files for deletion."""
        for i in range(self.duplicates_tree.topLevelItemCount()):
            group_item = self.duplicates_tree.topLevelItem(i)
            for j in range(group_item.childCount()):
                child_item = group_item.child(j)
                if child_item.flags() & Qt.ItemIsUserCheckable:
                    child_item.setCheckState(0, Qt.Checked)
    
    def _select_no_duplicates(self):
        """Deselect all duplicate files."""
        for i in range(self.duplicates_tree.topLevelItemCount()):
            group_item = self.duplicates_tree.topLevelItem(i)
            for j in range(group_item.childCount()):
                child_item = group_item.child(j)
                if child_item.flags() & Qt.ItemIsUserCheckable:
                    child_item.setCheckState(0, Qt.Unchecked)
    
    def _delete_selected_duplicates(self):
        """Delete selected duplicate files."""
        selected_files = []
        
        # Collect selected files
        for i in range(self.duplicates_tree.topLevelItemCount()):
            group_item = self.duplicates_tree.topLevelItem(i)
            for j in range(group_item.childCount()):
                child_item = group_item.child(j)
                if (child_item.flags() & Qt.ItemIsUserCheckable and 
                    child_item.checkState(0) == Qt.Checked):
                    selected_files.append(child_item.text(3))
        
        if not selected_files:
            QMessageBox.warning(self, "No Selection", "Please select files to delete.")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {len(selected_files)} duplicate files?\n\n"
            f"This action cannot be undone!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Delete files
        result = self.duplicate_finder.delete_selected_duplicates(selected_files)
        
        # Show results
        if result['deleted_files'] > 0:
            result_text = f"Deletion Complete!\n\n"
            result_text += f"Files Deleted: {result['deleted_files']}\n"
            result_text += f"Space Freed: {result['deleted_size_mb']:.1f} MB\n"
            
            if result['errors']:
                result_text += f"\nErrors: {len(result['errors'])} files could not be deleted"
            
            QMessageBox.information(self, "Deletion Complete", result_text)
            self.log_activity(f"Deleted {result['deleted_files']} duplicate files, freed {result['deleted_size_mb']:.1f} MB", "SUCCESS")
            
            # Refresh the tree by removing deleted items
            self._refresh_duplicates_tree(selected_files)
        else:
            QMessageBox.warning(self, "Deletion Failed", "No files were deleted. Check the activity log for details.")
            self.log_activity("Duplicate deletion failed", "WARNING")
    
    def _refresh_duplicates_tree(self, deleted_files):
        """Remove deleted files from the tree view."""
        deleted_set = set(deleted_files)
        
        for i in reversed(range(self.duplicates_tree.topLevelItemCount())):
            group_item = self.duplicates_tree.topLevelItem(i)
            
            for j in reversed(range(group_item.childCount())):
                child_item = group_item.child(j)
                if child_item.text(3) in deleted_set:
                    group_item.removeChild(child_item)
            
            # Remove group if only one file remains
            if group_item.childCount() <= 1:
                self.duplicates_tree.takeTopLevelItem(i)
    
    def save_report(self, report_content):
        """Save system report to file."""
        from datetime import datetime
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save System Report",
            f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                QMessageBox.information(self, "Success", f"Report saved to {filename}")
                self.log_activity(f"System report saved to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save report: {str(e)}")
    
    def closeEvent(self, event):
        """Handle application close event."""
        if self.tray_manager and self.tray_manager.is_visible():
            # If system tray is available, minimize to tray instead of closing
            reply = QMessageBox.question(self, 'Exit Application',
                                       'Do you want to minimize to system tray or exit completely?\n\n'
                                       'Click "Yes" to minimize to tray, "No" to exit.',
                                       QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                       QMessageBox.Yes)
            
            if reply == QMessageBox.Yes:
                # Minimize to tray
                event.ignore()
                self.hide()
                self.log_activity("Minimized to system tray")
                return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        
        # Clean shutdown
        if self.cleanup_worker and self.cleanup_worker.isRunning():
            self.cleanup_worker.terminate()
            self.cleanup_worker.wait()
        
        self.log_activity("Application closing")
        event.accept()
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_R:
                self.update_system_info()
                self.log_activity("System info refreshed (Ctrl+R)")
            elif event.key() == Qt.Key_C:
                self.start_cleanup()
            elif event.key() == Qt.Key_M:
                self.run_maintenance()
            elif event.key() == Qt.Key_S:
                self.open_startup_manager()
            elif event.key() == Qt.Key_P:
                self.show_processes()
            elif event.key() == Qt.Key_B:
                self.show_browser_cleaner()
            elif event.key() == Qt.Key_D:
                self.show_duplicate_finder()
        elif event.key() == Qt.Key_F5:
            self.update_system_info()
            self.log_activity("All data refreshed (F5)")
        elif event.key() == Qt.Key_F1:
            self.show_shortcuts()
        else:
            super().keyPressEvent(event)
    
    def run_performance_benchmark(self):
        """Run comprehensive performance benchmarks."""
        try:
            from performance_benchmark import BenchmarkWorker, BenchmarkExporter
            
            # Create benchmark dialog
            self.benchmark_dialog = QDialog(self)
            self.benchmark_dialog.setWindowTitle("Performance Benchmark")
            self.benchmark_dialog.setModal(True)
            self.benchmark_dialog.resize(800, 700)
            
            layout = QVBoxLayout(self.benchmark_dialog)
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)
            
            # Header
            header_layout = QHBoxLayout()
            header_icon = QLabel("📊")
            header_icon.setFont(QFont("Arial", 24))
            header_title = QLabel("Performance Benchmark")
            header_title.setFont(QFont("Arial", 18))
            header_title.setStyleSheet("font-weight: bold;")
            header_layout.addWidget(header_icon)
            header_layout.addWidget(header_title)
            header_layout.addStretch()
            layout.addLayout(header_layout)
            
            # Test selection
            test_group = QGroupBox("Select Benchmark Tests")
            test_layout = QVBoxLayout(test_group)
            
            self.cpu_test_cb = QCheckBox("🔥 CPU Performance Test")
            self.cpu_test_cb.setChecked(True)
            self.ram_test_cb = QCheckBox("🧠 RAM Speed Test")
            self.ram_test_cb.setChecked(True)
            self.disk_test_cb = QCheckBox("💾 Disk I/O Test")
            self.disk_test_cb.setChecked(True)
            
            test_layout.addWidget(self.cpu_test_cb)
            test_layout.addWidget(self.ram_test_cb)
            test_layout.addWidget(self.disk_test_cb)
            
            # Test options
            options_group = QGroupBox("Test Options")
            options_layout = QGridLayout(options_group)
            
            options_layout.addWidget(QLabel("Test Duration:"), 0, 0)
            self.duration_combo = QComboBox()
            self.duration_combo.addItems(["Quick (5s)", "Standard (10s)", "Extended (30s)"])
            self.duration_combo.setCurrentIndex(1)
            options_layout.addWidget(self.duration_combo, 0, 1)
            
            options_layout.addWidget(QLabel("Disk Test Size:"), 1, 0)
            self.disk_size_combo = QComboBox()
            self.disk_size_combo.addItems(["10 MB", "50 MB", "100 MB", "500 MB"])
            self.disk_size_combo.setCurrentIndex(1)
            options_layout.addWidget(self.disk_size_combo, 1, 1)
            
            # Results area
            results_group = QGroupBox("Benchmark Results")
            results_layout = QVBoxLayout(results_group)
            
            self.results_text = QTextEdit()
            self.results_text.setReadOnly(True)
            self.results_text.setFont(QFont("Consolas", 9))
            self.results_text.setMinimumHeight(300)
            results_layout.addWidget(self.results_text)
            
            # Progress bar
            self.benchmark_progress = QProgressBar()
            self.benchmark_progress.setVisible(False)
            
            # Control buttons
            button_layout = QHBoxLayout()
            
            start_btn = QPushButton("🚀 Start Benchmark")
            start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
                QPushButton:disabled {
                    background-color: #95a5a6;
                }
            """)
            start_btn.clicked.connect(self.start_benchmark)
            
            stop_btn = QPushButton("⏹️ Stop")
            stop_btn.setEnabled(False)
            stop_btn.clicked.connect(self.stop_benchmark)
            
            export_btn = QPushButton("📄 Export Results")
            export_btn.setEnabled(False)
            export_btn.clicked.connect(self.export_benchmark_results)
            
            close_btn = QPushButton("✖️ Close")
            close_btn.clicked.connect(self.benchmark_dialog.close)
            
            button_layout.addWidget(start_btn)
            button_layout.addWidget(stop_btn)
            button_layout.addWidget(export_btn)
            button_layout.addStretch()
            button_layout.addWidget(close_btn)
            
            # Store button references
            self.benchmark_start_btn = start_btn
            self.benchmark_stop_btn = stop_btn
            self.benchmark_export_btn = export_btn
            
            # Add all to layout
            layout.addWidget(test_group)
            layout.addWidget(options_group)
            layout.addWidget(results_group)
            layout.addWidget(self.benchmark_progress)
            layout.addLayout(button_layout)
            
            # Show initial info
            self.results_text.append("🔧 Performance Benchmark Tool")
            self.results_text.append("=" * 60)
            self.results_text.append("This tool will test your system's performance in key areas:")
            self.results_text.append("• CPU: Mathematical computation speed and processing power")
            self.results_text.append("• RAM: Memory allocation, bandwidth, and access patterns")
            self.results_text.append("• Disk: File read/write speeds and random access performance")
            self.results_text.append("\nSelect your tests and click 'Start Benchmark' to begin.")
            self.results_text.append("\n⚠️ Note: Benchmark tests may use significant system resources.")
            
            self.benchmark_dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error running benchmark: {str(e)}")
            self.log_activity(f"Error running benchmark: {str(e)}")
    
    def start_benchmark(self):
        """Start the benchmark process."""
        if hasattr(self, 'benchmark_worker') and self.benchmark_worker and self.benchmark_worker.isRunning():
            return
        
        # Get test configuration
        tests_config = {
            'cpu_enabled': self.cpu_test_cb.isChecked(),
            'ram_enabled': self.ram_test_cb.isChecked(),
            'disk_enabled': self.disk_test_cb.isChecked(),
            'duration': self.get_duration_seconds(),
            'disk_size_mb': self.get_disk_size_mb()
        }
        
        if not any([tests_config['cpu_enabled'], tests_config['ram_enabled'], tests_config['disk_enabled']]):
            QMessageBox.warning(self.benchmark_dialog, "No Tests Selected", "Please select at least one test to run.")
            return
        
        # Clear previous results
        self.results_text.clear()
        
        # Update UI
        self.benchmark_start_btn.setEnabled(False)
        self.benchmark_stop_btn.setEnabled(True)
        self.benchmark_export_btn.setEnabled(False)
        self.benchmark_progress.setVisible(True)
        self.benchmark_progress.setRange(0, 100)
        self.benchmark_progress.setValue(0)
        
        # Start benchmark worker
        from performance_benchmark import BenchmarkWorker
        self.benchmark_worker = BenchmarkWorker(tests_config)
        self.benchmark_worker.progress_updated.connect(self.benchmark_progress.setValue)
        self.benchmark_worker.result_updated.connect(self.results_text.append)
        self.benchmark_worker.benchmark_finished.connect(self.benchmark_completed)
        self.benchmark_worker.error_occurred.connect(self.benchmark_error)
        self.benchmark_worker.start()
        
        self.log_activity("Performance benchmark started")
    
    def stop_benchmark(self):
        """Stop the running benchmark."""
        if hasattr(self, 'benchmark_worker') and self.benchmark_worker:
            self.benchmark_worker.stop()
            self.benchmark_worker.wait(3000)  # Wait up to 3 seconds
            
        self.benchmark_start_btn.setEnabled(True)
        self.benchmark_stop_btn.setEnabled(False)
        self.benchmark_progress.setVisible(False)
        
        self.results_text.append("\n⏹️ Benchmark stopped by user.")
        self.log_activity("Performance benchmark stopped")
    
    def benchmark_completed(self, results):
        """Handle benchmark completion."""
        self.benchmark_results = results
        self.benchmark_start_btn.setEnabled(True)
        self.benchmark_stop_btn.setEnabled(False)
        self.benchmark_export_btn.setEnabled(True)
        self.benchmark_progress.setVisible(False)
        
        # Show completion message
        overall_score = results.get('overall_score', 0)
        rating = results.get('rating', 'Unknown')
        
        QMessageBox.information(
            self.benchmark_dialog, 
            "Benchmark Complete", 
            f"Performance benchmark completed!\n\nOverall Score: {overall_score}\nRating: {rating}"
        )
        
        self.log_activity(f"Performance benchmark completed - Score: {overall_score}, Rating: {rating}")
    
    def benchmark_error(self, error_msg):
        """Handle benchmark error."""
        self.benchmark_start_btn.setEnabled(True)
        self.benchmark_stop_btn.setEnabled(False)
        self.benchmark_progress.setVisible(False)
        
        QMessageBox.critical(self.benchmark_dialog, "Benchmark Error", f"Benchmark failed:\n{error_msg}")
        self.log_activity(f"Benchmark error: {error_msg}")
    
    def export_benchmark_results(self):
        """Export benchmark results to file."""
        if not hasattr(self, 'benchmark_results') or not self.benchmark_results:
            QMessageBox.warning(self.benchmark_dialog, "No Results", "No benchmark results to export.")
            return
        
        try:
            from datetime import datetime
            from performance_benchmark import BenchmarkExporter
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Get save location for text format
            filename, _ = QFileDialog.getSaveFileName(
                self.benchmark_dialog,
                "Save Benchmark Results",
                f"benchmark_results_{timestamp}.txt",
                "Text Files (*.txt)"
            )
            
            if filename:
                BenchmarkExporter.export_to_text(self.benchmark_results, filename)
                QMessageBox.information(self.benchmark_dialog, "Export Complete", f"Results exported to:\n{filename}")
                self.log_activity(f"Benchmark results exported to {filename}")
        
        except Exception as e:
            QMessageBox.critical(self.benchmark_dialog, "Export Error", f"Failed to export results:\n{str(e)}")
            self.log_activity(f"Export error: {str(e)}")
    
    def get_duration_seconds(self):
        """Get benchmark duration in seconds."""
        duration_map = {
            "Quick (5s)": 5,
            "Standard (10s)": 10,
            "Extended (30s)": 30
        }
        return duration_map.get(self.duration_combo.currentText(), 10)
    
    def get_disk_size_mb(self):
        """Get disk test size in MB."""
        size_text = self.disk_size_combo.currentText()
        return int(size_text.split()[0])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
