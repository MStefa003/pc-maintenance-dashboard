# 🖥️ PC Maintenance Dashboard

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://pypi.org/project/PyQt5/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/yourusername/pc-maintenance-dashboard)

A comprehensive, cross-platform desktop application for system maintenance and performance optimization. Built with PyQt5, this professional-grade tool provides real-time system monitoring, automated cleanup, and advanced performance benchmarking capabilities.

![PC Maintenance Dashboard](https://via.placeholder.com/800x500/2c3e50/ffffff?text=PC+Maintenance+Dashboard+Screenshot)

## ✨ Key Features

### 🔍 **Real-Time System Monitoring**
- Live CPU, RAM, and disk usage tracking with interactive graphs
- Network activity monitoring with upload/download speeds
- System uptime and active process counting
- Visual health indicators with color-coded status alerts

### 🧹 **Advanced Cleanup Tools**
- **Temporary Files**: Comprehensive cleanup of system temp files, browser caches, and prefetch data
- **Browser Cleanup**: Dedicated cleaning for Chrome, Firefox, Edge browser data
- **Duplicate Finder**: Intelligent duplicate file detection and removal
- **Registry Cleaner**: Safe Windows registry optimization with automatic backups

### 📊 **Performance Benchmarking**
- **CPU Benchmarks**: Prime number calculations and mathematical operations testing
- **RAM Speed Tests**: Memory allocation, bandwidth, and access pattern analysis  
- **Disk I/O Tests**: File read/write speeds and random access performance
- **Comprehensive Scoring**: Overall performance ratings with detailed metrics
- **Export Results**: Save benchmark data in multiple formats (JSON, TXT)

### ⚙️ **System Management**
- **Startup Manager**: Control which programs launch at system boot
- **Process Manager**: View and manage running applications and services
- **Network Monitor**: Real-time network connection and bandwidth analysis
- **System Reports**: Generate detailed system health and performance reports

### 🔧 **Advanced Tools**
- Memory optimization and garbage collection
- Disk defragmentation utilities
- Driver update checking
- Power management options
- Automated maintenance scheduling

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- Windows, macOS, or Linux operating system

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/pc-maintenance-dashboard.git
   cd pc-maintenance-dashboard
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

### Alternative: Standalone Executable
Download the latest pre-built executable from the [Releases](https://github.com/yourusername/pc-maintenance-dashboard/releases) page.

## 📋 System Requirements

- **Python**: 3.7+ (for source installation)
- **RAM**: 256MB minimum, 512MB recommended
- **Storage**: 50MB free space
- **OS**: Windows 7+, macOS 10.12+, or Linux with X11

## 🔧 Dependencies

```
PyQt5>=5.15.0
psutil>=5.8.0
```

## 🏗️ Building Executable

Create a standalone executable using PyInstaller:

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable (Windows)
pyinstaller --onefile --windowed --icon=icon.ico main.py

# Build executable (macOS/Linux)
pyinstaller --onefile --windowed main.py
```

The executable will be created in the `dist/` directory.

## 📸 Screenshots

### Main Dashboard
![Main Dashboard](https://via.placeholder.com/600x400/34495e/ffffff?text=Main+Dashboard+View)

### Performance Benchmark
![Performance Benchmark](https://via.placeholder.com/600x400/27ae60/ffffff?text=Performance+Benchmark+Tool)

### System Monitoring
![System Monitoring](https://via.placeholder.com/600x400/3498db/ffffff?text=Real-Time+System+Graphs)

## 🎯 Usage Examples

### Running a Performance Benchmark
1. Click "📊 Performance Benchmark" in the System Tools section
2. Select desired tests (CPU, RAM, Disk)
3. Choose test duration and parameters
4. Click "🚀 Start Benchmark"
5. Export results when complete

### Cleaning Temporary Files
1. Navigate to the File Cleanup section
2. Click "Clean Temporary Files"
3. Monitor progress in real-time
4. Review cleanup summary

### Managing Startup Programs
1. Click "🚀 Startup Programs"
2. Toggle programs on/off
3. Apply changes and restart system

## 🛠️ Development

### Project Structure
```
pc-maintenance-dashboard/
├── main.py                 # Application entry point
├── main_window_simple.py   # Main GUI implementation
├── performance_benchmark.py # Benchmark system
├── system_utils.py         # System monitoring utilities
├── browser_cleaner.py      # Browser cleanup functionality
├── duplicate_finder.py     # Duplicate file detection
├── themes.py              # UI theme management
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings for all functions and classes
- Include type hints where appropriate

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## 🙏 Acknowledgments

- Built with [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) for the GUI framework
- System monitoring powered by [psutil](https://github.com/giampaolo/psutil)
- Icons and emojis for enhanced user experience

## 📊 Statistics

![GitHub stars](https://img.shields.io/github/stars/yourusername/pc-maintenance-dashboard)
![GitHub forks](https://img.shields.io/github/forks/yourusername/pc-maintenance-dashboard)
![GitHub issues](https://img.shields.io/github/issues/yourusername/pc-maintenance-dashboard)
![GitHub downloads](https://img.shields.io/github/downloads/yourusername/pc-maintenance-dashboard/total)

---

**Made with ❤️**
