"""
Version information for PC Maintenance Dashboard
"""

__version__ = "2.0.0"
__author__ = "MStefa003"
__email__ = "your.email@example.com"
__description__ = "A comprehensive system maintenance and performance optimization tool"
__url__ = "https://github.com/yourusername/pc-maintenance-dashboard"

# Version history
VERSION_INFO = {
    "major": 2,
    "minor": 0,
    "patch": 0,
    "pre_release": None,
    "build": None
}

def get_version():
    """Get the current version string."""
    version = f"{VERSION_INFO['major']}.{VERSION_INFO['minor']}.{VERSION_INFO['patch']}"
    if VERSION_INFO['pre_release']:
        version += f"-{VERSION_INFO['pre_release']}"
    if VERSION_INFO['build']:
        version += f"+{VERSION_INFO['build']}"
    return version

def get_version_info():
    """Get detailed version information."""
    return {
        "version": get_version(),
        "author": __author__,
        "description": __description__,
        "url": __url__
    }
