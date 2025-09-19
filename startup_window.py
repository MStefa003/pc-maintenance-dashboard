"""
Startup manager window for PC Maintenance Dashboard.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QMessageBox,
                             QHeaderView, QCheckBox, QWidget, QProgressBar,
                             QStatusBar, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from system_utils import StartupManager


class StartupLoadWorker(QThread):
    """Worker thread for loading startup programs."""
    
    finished = pyqtSignal(list)
    progress = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.startup_manager = StartupManager()
    
    def run(self):
        """Load startup programs."""
        self.progress.emit("Loading startup programs...")
        programs = self.startup_manager.get_startup_programs()
        self.finished.emit(programs)


class StartupToggleWorker(QThread):
    """Worker thread for toggling startup programs."""
    
    finished = pyqtSignal(bool, str)
    
    def __init__(self, startup_manager, program, enable):
        super().__init__()
        self.startup_manager = startup_manager
        self.program = program
        self.enable = enable
    
    def run(self):
        """Toggle startup program."""
        try:
            success = self.startup_manager.toggle_startup_program(self.program, self.enable)
            action = "enabled" if self.enable else "disabled"
            message = f"Successfully {action} {self.program['name']}"
            self.finished.emit(success, message)
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")


class StartupWindow(QDialog):
    """Startup manager window."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.startup_manager = StartupManager()
        self.startup_programs = []
        self.load_worker = None
        self.toggle_worker = None
        self.setup_ui()
        self.load_startup_programs()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Startup Program Manager")
        self.setGeometry(150, 150, 800, 500)
        self.setModal(False)
        
        # Set window style
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
            QTableWidget {
                gridline-color: #dee2e6;
                background-color: #ffffff;
                alternate-background-color: #f8f9fa;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                padding: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)
        
        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Startup Program Manager")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.load_startup_programs)
        header_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # Info label
        info_label = QLabel("Manage programs that start automatically when your computer boots up. "
                           "Disabling unnecessary startup programs can improve boot time.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #6c757d; margin: 10px 0;")
        main_layout.addWidget(info_label)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Program Name", "Path", "Status", "Action"])
        
        # Configure table
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        
        main_layout.addWidget(self.table)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        self.enable_all_btn = QPushButton("✅ Enable All")
        self.enable_all_btn.clicked.connect(self.enable_all_programs)
        button_layout.addWidget(self.enable_all_btn)
        
        self.disable_all_btn = QPushButton("❌ Disable All")
        self.disable_all_btn.clicked.connect(self.disable_all_programs)
        button_layout.addWidget(self.disable_all_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(button_layout)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #6c757d; padding: 5px;")
        main_layout.addWidget(self.status_label)
    
    def load_startup_programs(self):
        """Load startup programs in a separate thread."""
        if self.load_worker and self.load_worker.isRunning():
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.refresh_btn.setEnabled(False)
        self.status_label.setText("Loading startup programs...")
        
        self.load_worker = StartupLoadWorker()
        self.load_worker.progress.connect(self.update_status)
        self.load_worker.finished.connect(self.programs_loaded)
        self.load_worker.start()
    
    def update_status(self, message: str):
        """Update status message."""
        self.status_label.setText(message)
    
    def programs_loaded(self, programs: list):
        """Handle loaded startup programs."""
        self.startup_programs = programs
        self.populate_table()
        
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
        self.status_label.setText(f"Loaded {len(programs)} startup programs")
    
    def populate_table(self):
        """Populate the table with startup programs."""
        self.table.setRowCount(len(self.startup_programs))
        
        for row, program in enumerate(self.startup_programs):
            # Program name
            name_item = QTableWidgetItem(program['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            
            # Program path
            path_item = QTableWidgetItem(program['path'])
            path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
            path_item.setToolTip(program['path'])  # Show full path on hover
            self.table.setItem(row, 1, path_item)
            
            # Status
            status = "Enabled" if program['enabled'] else "Disabled"
            status_item = QTableWidgetItem(status)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            
            if program['enabled']:
                status_item.setBackground(Qt.green)
            else:
                status_item.setBackground(Qt.red)
            
            self.table.setItem(row, 2, status_item)
            
            # Action button
            toggle_btn = QPushButton("Disable" if program['enabled'] else "Enable")
            toggle_btn.clicked.connect(lambda checked, r=row: self.toggle_program(r))
            
            if program['enabled']:
                toggle_btn.setStyleSheet("background-color: #dc3545;")  # Red for disable
            else:
                toggle_btn.setStyleSheet("background-color: #28a745;")  # Green for enable
            
            self.table.setCellWidget(row, 3, toggle_btn)
    
    def toggle_program(self, row: int):
        """Toggle a startup program."""
        if row >= len(self.startup_programs):
            return
        
        program = self.startup_programs[row]
        new_state = not program['enabled']
        
        # Confirm action
        action = "enable" if new_state else "disable"
        reply = QMessageBox.question(self, f"Confirm Action",
                                   f"Are you sure you want to {action} '{program['name']}'?",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply != QMessageBox.Yes:
            return
        
        # Disable the button during operation
        button = self.table.cellWidget(row, 3)
        button.setEnabled(False)
        button.setText("Working...")
        
        self.status_label.setText(f"{'Enabling' if new_state else 'Disabling'} {program['name']}...")
        
        # Start toggle operation
        self.toggle_worker = StartupToggleWorker(self.startup_manager, program, new_state)
        self.toggle_worker.finished.connect(lambda success, msg, r=row: self.toggle_finished(success, msg, r))
        self.toggle_worker.start()
    
    def toggle_finished(self, success: bool, message: str, row: int):
        """Handle toggle operation completion."""
        self.status_label.setText(message)
        
        if success and row < len(self.startup_programs):
            # Update program state
            self.startup_programs[row]['enabled'] = not self.startup_programs[row]['enabled']
            
            # Update table
            program = self.startup_programs[row]
            
            # Update status column
            status = "Enabled" if program['enabled'] else "Disabled"
            status_item = self.table.item(row, 2)
            status_item.setText(status)
            
            if program['enabled']:
                status_item.setBackground(Qt.green)
            else:
                status_item.setBackground(Qt.red)
            
            # Update button
            button = self.table.cellWidget(row, 3)
            button.setText("Disable" if program['enabled'] else "Enable")
            button.setEnabled(True)
            
            if program['enabled']:
                button.setStyleSheet("background-color: #dc3545;")  # Red for disable
            else:
                button.setStyleSheet("background-color: #28a745;")  # Green for enable
        else:
            # Re-enable button on failure
            button = self.table.cellWidget(row, 3)
            button.setText("Disable" if self.startup_programs[row]['enabled'] else "Enable")
            button.setEnabled(True)
            
            if not success:
                QMessageBox.warning(self, "Operation Failed", message)
    
    def enable_all_programs(self):
        """Enable all startup programs."""
        reply = QMessageBox.question(self, "Confirm Action",
                                   "Are you sure you want to enable ALL startup programs?\n"
                                   "This may slow down your computer's boot time.",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.batch_toggle_programs(True)
    
    def disable_all_programs(self):
        """Disable all startup programs."""
        reply = QMessageBox.question(self, "Confirm Action",
                                   "Are you sure you want to disable ALL startup programs?\n"
                                   "Some programs may be important for system functionality.",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.batch_toggle_programs(False)
    
    def batch_toggle_programs(self, enable: bool):
        """Enable or disable all programs."""
        action = "Enabling" if enable else "Disabling"
        self.status_label.setText(f"{action} all programs...")
        
        # Disable all buttons
        for row in range(self.table.rowCount()):
            button = self.table.cellWidget(row, 3)
            if button:
                button.setEnabled(False)
        
        self.enable_all_btn.setEnabled(False)
        self.disable_all_btn.setEnabled(False)
        
        # Process each program
        success_count = 0
        for i, program in enumerate(self.startup_programs):
            if program['enabled'] != enable:
                try:
                    if self.startup_manager.toggle_startup_program(program, enable):
                        program['enabled'] = enable
                        success_count += 1
                except Exception:
                    pass
        
        # Update table
        self.populate_table()
        
        # Re-enable buttons
        self.enable_all_btn.setEnabled(True)
        self.disable_all_btn.setEnabled(True)
        
        action_past = "enabled" if enable else "disabled"
        self.status_label.setText(f"Successfully {action_past} {success_count} programs")
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.load_worker and self.load_worker.isRunning():
            self.load_worker.terminate()
        
        if self.toggle_worker and self.toggle_worker.isRunning():
            self.toggle_worker.terminate()
        
        event.accept()
