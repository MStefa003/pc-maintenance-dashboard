"""
Enhanced theme management for PC Maintenance Dashboard.
"""

class ThemeManager:
    """Manages application themes with modern design."""
    
    @staticmethod
    def get_light_theme():
        """Get modern theme with glassmorphism design."""
        return f"""
            /* Main Application - Fancy Background */
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:0.25 #764ba2, stop:0.5 #f093fb, 
                    stop:0.75 #f5576c, stop:1 #4facfe);
                color: #ffffff;
                font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            }}
            
            QDialog {{
                background-color: #ffffff;
                color: #1e293b;
            }}
            
            /* Fancy Gradient Buttons */
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff6b6b, stop:0.5 #4ecdc4, stop:1 #45b7d1);
                color: white;
                border: none;
                border-radius: 15px;
                padding: 16px 32px;
                font-size: 15px;
                font-weight: 700;
                min-height: 24px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff5252, stop:0.5 #26d0ce, stop:1 #1e88e5);
            }}
            
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e53e3e, stop:0.5 #319795, stop:1 #2b6cb0);
            }}
            
            QPushButton:disabled {{
                background-color: #bdc3c7;
                color: #7f8c8d;
            }}
            
            /* Fancy Labels with Glow */
            QLabel {{
                color: #ffffff;
                font-size: 15px;
                font-weight: 600;
            }}
            
            QLabel[objectName="CardTitle"] {{
                color: #0f172a;
                font-size: 18px;
                font-weight: 700;
                margin-bottom: 8px;
            }}
            
            QLabel[objectName="CardSubtitle"] {{
                color: #64748b;
                font-size: 13px;
                font-weight: 400;
                margin-bottom: 16px;
            }}
            
            /* Fancy Animated Progress Bars */
            QProgressBar {{
                border: none;
                border-radius: 12px;
                text-align: center;
                font-weight: 600;
                font-size: 13px;
                color: #ffffff;
                background: rgba(255, 255, 255, 0.2);
                min-height: 16px;
            }}
            
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff6b6b, stop:0.5 #4ecdc4, stop:1 #45b7d1);
                border-radius: 12px;
            }}
            
            /* Enhanced Card-style Frames */
            QFrame {{
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.8);
                border-radius: 20px;
                padding: 24px;
            }}
            
            /* Fancy Glassmorphism Cards */
            QFrame {{
                background: rgba(255, 255, 255, 0.15);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 20px;
                padding: 28px;
                margin: 16px;
            }}
            
            QFrame:hover {{
                background: rgba(255, 255, 255, 0.25);
                border: 2px solid rgba(255, 255, 255, 0.4);
            }}
            
            QFrame[objectName="ActionCard"]:hover {{
                background: #f8fafc;
                border: 2px solid #cbd5e1;
            }}
            
            /* Professional Group Boxes */
            QGroupBox {{
                font-weight: 600;
                font-size: 16px;
                color: #374151;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: #ffffff;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                background-color: #ffffff;
            }}
            
            /* Fancy Glass Text Areas */
            QTextEdit {{
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 15px;
                padding: 20px;
                font-family: 'Inter', 'Segoe UI', monospace;
                font-size: 14px;
                color: #ffffff;
                font-weight: 500;
                selection-background-color: rgba(255, 255, 255, 0.3);
            }}
            
            QTextEdit:focus {{
                border-color: #3498db;
            }}
            
            /* Fancy Glass Menu Bar */
            QMenuBar {{
                background: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                border-bottom: 2px solid rgba(255, 255, 255, 0.2);
                padding: 12px 0px;
                font-weight: 600;
            }}
            
            QMenuBar::item {{
                background: transparent;
                padding: 10px 20px;
                margin: 0px 6px;
                border-radius: 10px;
            }}
            
            QMenuBar::item:selected {{
                background: rgba(255, 255, 255, 0.2);
                color: #ffffff;
            }}
            
            QMenu {{
                background: rgba(15, 15, 35, 0.98);
                color: #e8eaed;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                padding: 8px;
            }}
            
            QMenu::item {{
                padding: 12px 24px;
                border-radius: 8px;
                margin: 2px;
            }}
            
            QMenu::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border-radius: 8px;
            }}
            
            /* Modern Glassmorphism Card Styles */
            QFrame#SystemInfoCard {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 20px;
                padding: 24px;
            }}
            
            QFrame#ActionCard {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 20px;
                padding: 24px;
            }}
            
            QFrame#ActionCard:hover {{
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
            
            QFrame#HeaderCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
                border-radius: 16px;
                border: none;
            }}
            
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            
            QWidget#MainBackground {{
                background: transparent;
            }}
            
            QPushButton#PrimaryButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 16px 28px;
                border-radius: 14px;
                font-size: 14px;
                font-weight: 600;
                min-height: 48px;
                max-height: 52px;
                margin: 4px;
            }}
            
            QPushButton#PrimaryButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c8df0, stop:1 #8a5fb8);
            }}
            
            QPushButton#PrimaryButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a6fd8, stop:1 #6b4190);
            }}
            
            QPushButton#SecondaryButton {{
                background: rgba(255, 255, 255, 0.1);
                color: #e8eaed;
                border: 1px solid rgba(255, 255, 255, 0.2);
                padding: 14px 26px;
                border-radius: 14px;
                font-size: 14px;
                font-weight: 500;
                min-height: 48px;
                max-height: 52px;
                margin: 4px;
            }}
            
            QPushButton#SecondaryButton:hover {{
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
            
            QPushButton#SecondaryButton:pressed {{
                background: rgba(255, 255, 255, 0.08);
            }}
            
            QLabel#CardTitle {{
                color: #ffffff;
                font-weight: 700;
                font-size: 18px;
            }}
            
            QLabel#CardSubtitle {{
                color: rgba(255, 255, 255, 0.7);
                font-weight: 500;
                font-size: 13px;
            }}
            
            QStatusBar {{
                background: rgba(255, 255, 255, 0.05);
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.8);
                font-size: 12px;
                padding: 8px;
            }}
            
            QTextEdit {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                color: #e8eaed;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                padding: 12px;
            }}
            
            QProgressBar {{
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 8px;
                text-align: center;
                color: white;
                font-weight: 600;
            }}
            
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 8px;
            }}
        """

    @staticmethod
    def get_dark_theme():
        """Get modern dark theme stylesheet with enhanced design."""
        return """
            /* Main Window - Enhanced Dark Theme */
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f0f23, stop:0.3 #1a1a2e, stop:0.7 #16213e, stop:1 #0f3460);
                color: #e8eaed;
                font-family: 'Segoe UI', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
            }
            
            QDialog {
                background-color: #2c3e50;
                color: #ecf0f1;
            }
            
            /* Modern Enhanced Dark Buttons */
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
                color: white;
                border: none;
                padding: 16px 32px;
                border-radius: 16px;
                font-size: 14px;
                font-weight: 600;
                min-height: 24px;
                font-family: 'Segoe UI', sans-serif;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c8df0, stop:0.5 #8a5fb8, stop:1 #f5a3ff);
            }
            
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a6fd8, stop:0.5 #6b4190, stop:1 #d67bff);
            }
            
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
            
            /* Enhanced Dark Labels */
            QLabel {
                color: #e8eaed;
                font-weight: 500;
                font-family: 'Segoe UI', sans-serif;
            }
            
            /* Enhanced Dark Progress Bars */
            QProgressBar {
                border: none;
                border-radius: 12px;
                text-align: center;
                background: rgba(255, 255, 255, 0.1);
                color: #e8eaed;
                font-weight: 600;
                height: 24px;
                font-family: 'Segoe UI', sans-serif;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
                border-radius: 12px;
                margin: 2px;
            }
            
            /* Enhanced Dark Card Frames */
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 20px;
                padding: 24px;
            }
            
            /* Enhanced Dark Group Boxes */
            QGroupBox {
                font-weight: 600;
                font-size: 16px;
                color: #e8eaed;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 16px;
                margin-top: 15px;
                padding-top: 15px;
                background: rgba(255, 255, 255, 0.05);
                font-family: 'Segoe UI', sans-serif;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                background: rgba(255, 255, 255, 0.05);
            }
            
            /* Enhanced Dark Text Areas */
            QTextEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                padding: 16px;
                color: #e8eaed;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                selection-background-color: rgba(102, 126, 234, 0.5);
            }
            
            QTextEdit:focus {
                border: 1px solid rgba(102, 126, 234, 0.6);
            }
            
            /* Enhanced Dark Tables */
            QTableWidget {
                gridline-color: rgba(255, 255, 255, 0.1);
                background: rgba(255, 255, 255, 0.05);
                alternate-background-color: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                color: #e8eaed;
                selection-background-color: rgba(102, 126, 234, 0.3);
            }
            
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                padding: 12px;
                border: none;
                font-weight: 600;
            }
            /* Enhanced Dark Menu Bar */
            QMenuBar {
                background: rgba(255, 255, 255, 0.05);
                color: #e8eaed;
                border: none;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                padding: 8px;
                font-size: 13px;
                font-weight: 500;
                font-family: 'Segoe UI', sans-serif;
            }
            
            QMenuBar::item {
                background: transparent;
                padding: 10px 16px;
                border-radius: 8px;
                margin: 2px;
            }
            
            QMenuBar::item:selected {
                background: rgba(255, 255, 255, 0.1);
            }
            
            QMenu {
                background: rgba(15, 15, 35, 0.98);
                color: #e8eaed;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                padding: 8px;
            }
            
            QMenu::item {
                padding: 12px 24px;
                border-radius: 8px;
                margin: 2px;
            }
            
            QMenu::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border-radius: 8px;
            }
            
            /* Modern Glassmorphism Card Styles */
            QFrame#SystemInfoCard {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 20px;
                padding: 24px;
            }
            
            QFrame#ActionCard {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 20px;
                padding: 24px;
            }
            
            QFrame#ActionCard:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            
            QFrame#HeaderCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
                border-radius: 16px;
                border: none;
            }
            
            QScrollArea {
                border: none;
                background: transparent;
            }
            
            QWidget#MainBackground {
                background: transparent;
            }
            
            QPushButton#PrimaryButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 16px 28px;
                border-radius: 14px;
                font-size: 14px;
                font-weight: 600;
                min-height: 48px;
                max-height: 52px;
                margin: 4px;
            }
            
            QPushButton#PrimaryButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c8df0, stop:1 #8a5fb8);
            }
            
            QPushButton#PrimaryButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a6fd8, stop:1 #6b4190);
            }
            
            QPushButton#SecondaryButton {
                background: rgba(255, 255, 255, 0.1);
                color: #e8eaed;
                border: 1px solid rgba(255, 255, 255, 0.2);
                padding: 14px 26px;
                border-radius: 14px;
                font-size: 14px;
                font-weight: 500;
                min-height: 48px;
                max-height: 52px;
                margin: 4px;
            }
            
            QPushButton#SecondaryButton:hover {
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            
            QPushButton#SecondaryButton:pressed {
                background: rgba(255, 255, 255, 0.08);
            }
            
            QLabel#CardTitle {
                color: #ffffff;
                font-weight: 700;
                font-size: 18px;
            }
            
            QLabel#CardSubtitle {
                color: rgba(255, 255, 255, 0.7);
                font-weight: 500;
                font-size: 13px;
            }
            
            QStatusBar {
                background: rgba(255, 255, 255, 0.05);
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.8);
                font-size: 12px;
                padding: 8px;
            }
            
            QTextEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                color: #e8eaed;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                padding: 12px;
            }
            
            QProgressBar {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 8px;
                text-align: center;
                color: white;
                font-weight: 600;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 8px;
            }
        """
