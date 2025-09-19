"""
Scheduler system for automatic maintenance tasks.
"""

import json
import os
from datetime import datetime, timedelta
from PyQt5.QtCore import QTimer, QObject, pyqtSignal
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QSpinBox, QCheckBox, QPushButton,
                             QGroupBox, QTimeEdit, QListWidget, QMessageBox, QWidget)
from PyQt5.QtCore import QTime, QSettings
from system_utils import FileCleanup


class MaintenanceScheduler(QObject):
    """Handles scheduled maintenance tasks."""
    
    maintenance_triggered = pyqtSignal(str)  # Emits task type
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings('PCMaintenance', 'Scheduler')
        self.timers = {}
        self.load_schedules()
    
    def load_schedules(self):
        """Load scheduled tasks from settings."""
        schedules = self.settings.value('schedules', {})
        
        if isinstance(schedules, str):
            try:
                schedules = json.loads(schedules)
            except:
                schedules = {}
        
        for task_id, schedule in schedules.items():
            if schedule.get('enabled', False):
                self.create_timer(task_id, schedule)
    
    def save_schedules(self):
        """Save schedules to settings."""
        schedules = {}
        for task_id, timer_info in self.timers.items():
            schedules[task_id] = timer_info['schedule']
        
        self.settings.setValue('schedules', json.dumps(schedules))
    
    def create_timer(self, task_id, schedule):
        """Create a timer for a scheduled task."""
        if task_id in self.timers:
            self.timers[task_id]['timer'].stop()
        
        timer = QTimer()
        interval = self.calculate_interval(schedule)
        
        if interval > 0:
            timer.timeout.connect(lambda: self.execute_task(task_id, schedule))
            timer.start(interval)
            
            self.timers[task_id] = {
                'timer': timer,
                'schedule': schedule,
                'next_run': datetime.now() + timedelta(milliseconds=interval)
            }
    
    def calculate_interval(self, schedule):
        """Calculate timer interval in milliseconds."""
        frequency = schedule.get('frequency', 'daily')
        
        if frequency == 'hourly':
            return 60 * 60 * 1000  # 1 hour
        elif frequency == 'daily':
            return 24 * 60 * 60 * 1000  # 24 hours
        elif frequency == 'weekly':
            return 7 * 24 * 60 * 60 * 1000  # 7 days
        elif frequency == 'custom':
            hours = schedule.get('custom_hours', 24)
            return hours * 60 * 60 * 1000
        
        return 0
    
    def execute_task(self, task_id, schedule):
        """Execute a scheduled task."""
        task_type = schedule.get('task_type', 'cleanup')
        
        try:
            if task_type == 'cleanup':
                self.maintenance_triggered.emit('cleanup')
            elif task_type == 'full_maintenance':
                self.maintenance_triggered.emit('full_maintenance')
            
            # Update next run time
            if task_id in self.timers:
                interval = self.calculate_interval(schedule)
                self.timers[task_id]['next_run'] = datetime.now() + timedelta(milliseconds=interval)
        
        except Exception as e:
            print(f"Error executing scheduled task {task_id}: {e}")
    
    def add_schedule(self, task_id, schedule):
        """Add a new scheduled task."""
        self.create_timer(task_id, schedule)
        self.save_schedules()
    
    def remove_schedule(self, task_id):
        """Remove a scheduled task."""
        if task_id in self.timers:
            self.timers[task_id]['timer'].stop()
            del self.timers[task_id]
            self.save_schedules()
    
    def get_schedules(self):
        """Get all current schedules."""
        schedules = {}
        for task_id, timer_info in self.timers.items():
            schedule = timer_info['schedule'].copy()
            schedule['next_run'] = timer_info['next_run'].strftime('%Y-%m-%d %H:%M:%S')
            schedules[task_id] = schedule
        return schedules


class SchedulerDialog(QDialog):
    """Dialog for managing scheduled maintenance tasks."""
    
    def __init__(self, scheduler, parent=None):
        super().__init__(parent)
        self.scheduler = scheduler
        self.setup_ui()
        self.load_schedules()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Maintenance Scheduler")
        self.setGeometry(200, 200, 500, 400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Current schedules
        schedules_group = QGroupBox("Current Schedules")
        schedules_layout = QVBoxLayout()
        
        self.schedules_list = QListWidget()
        schedules_layout.addWidget(self.schedules_list)
        
        # Schedule controls
        controls_layout = QHBoxLayout()
        
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.edit_schedule)
        controls_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_schedule)
        controls_layout.addWidget(self.delete_btn)
        
        schedules_layout.addLayout(controls_layout)
        schedules_group.setLayout(schedules_layout)
        layout.addWidget(schedules_group)
        
        # New schedule
        new_schedule_group = QGroupBox("Add New Schedule")
        new_layout = QVBoxLayout()
        
        # Task type
        task_layout = QHBoxLayout()
        task_layout.addWidget(QLabel("Task:"))
        self.task_combo = QComboBox()
        self.task_combo.addItems(["Temporary File Cleanup", "Full Maintenance"])
        task_layout.addWidget(self.task_combo)
        new_layout.addLayout(task_layout)
        
        # Frequency
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("Frequency:"))
        self.freq_combo = QComboBox()
        self.freq_combo.addItems(["Hourly", "Daily", "Weekly", "Custom"])
        self.freq_combo.currentTextChanged.connect(self.frequency_changed)
        freq_layout.addWidget(self.freq_combo)
        new_layout.addLayout(freq_layout)
        
        # Custom hours (initially hidden)
        self.custom_widget = QWidget()
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("Every"))
        self.custom_hours = QSpinBox()
        self.custom_hours.setRange(1, 168)  # 1 hour to 1 week
        self.custom_hours.setValue(24)
        custom_layout.addWidget(self.custom_hours)
        custom_layout.addWidget(QLabel("hours"))
        self.custom_widget.setLayout(custom_layout)
        new_layout.addWidget(self.custom_widget)
        self.custom_widget.setVisible(False)
        
        # Start time
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Start Time:"))
        self.start_time = QTimeEdit()
        self.start_time.setTime(QTime.currentTime())
        time_layout.addWidget(self.start_time)
        new_layout.addLayout(time_layout)
        
        # Enabled checkbox
        self.enabled_check = QCheckBox("Enable this schedule")
        self.enabled_check.setChecked(True)
        new_layout.addWidget(self.enabled_check)
        
        # Add button
        self.add_btn = QPushButton("Add Schedule")
        self.add_btn.clicked.connect(self.add_schedule)
        new_layout.addWidget(self.add_btn)
        
        new_schedule_group.setLayout(new_layout)
        layout.addWidget(new_schedule_group)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def frequency_changed(self, frequency):
        """Handle frequency selection change."""
        self.custom_widget.setVisible(frequency == "Custom")
    
    def load_schedules(self):
        """Load and display current schedules."""
        self.schedules_list.clear()
        schedules = self.scheduler.get_schedules()
        
        for task_id, schedule in schedules.items():
            task_type = "Cleanup" if schedule['task_type'] == 'cleanup' else "Full Maintenance"
            frequency = schedule['frequency'].title()
            next_run = schedule['next_run']
            
            item_text = f"{task_type} - {frequency} - Next: {next_run}"
            self.schedules_list.addItem(item_text)
    
    def add_schedule(self):
        """Add a new schedule."""
        task_type = 'cleanup' if self.task_combo.currentIndex() == 0 else 'full_maintenance'
        frequency = self.freq_combo.currentText().lower()
        
        schedule = {
            'task_type': task_type,
            'frequency': frequency,
            'start_time': self.start_time.time().toString(),
            'enabled': self.enabled_check.isChecked()
        }
        
        if frequency == 'custom':
            schedule['custom_hours'] = self.custom_hours.value()
        
        # Generate unique task ID
        import uuid
        task_id = str(uuid.uuid4())[:8]
        
        self.scheduler.add_schedule(task_id, schedule)
        self.load_schedules()
        
        QMessageBox.information(self, "Schedule Added", 
                               f"New {task_type.replace('_', ' ')} schedule added successfully!")
    
    def edit_schedule(self):
        """Edit selected schedule."""
        current_row = self.schedules_list.currentRow()
        if current_row >= 0:
            QMessageBox.information(self, "Edit Schedule", 
                                   "Schedule editing will be available in a future update.")
    
    def delete_schedule(self):
        """Delete selected schedule."""
        current_row = self.schedules_list.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(self, "Delete Schedule",
                                       "Are you sure you want to delete this schedule?",
                                       QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # Get task ID (this is simplified - in a real implementation, 
                # you'd store task IDs with list items)
                schedules = list(self.scheduler.get_schedules().keys())
                if current_row < len(schedules):
                    task_id = schedules[current_row]
                    self.scheduler.remove_schedule(task_id)
                    self.load_schedules()
                    QMessageBox.information(self, "Schedule Deleted", 
                                           "Schedule deleted successfully!")
