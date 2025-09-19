"""
Setup script for PC Maintenance Dashboard
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read version from version.py
version_dict = {}
with open(os.path.join(this_directory, 'version.py')) as f:
    exec(f.read(), version_dict)

setup(
    name="pc-maintenance-dashboard",
    version=version_dict['__version__'],
    author=version_dict['__author__'],
    author_email=version_dict['__email__'],
    description=version_dict['__description__'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=version_dict['__url__'],
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Topic :: System :: Systems Administration",
        "Topic :: System :: Monitoring",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: Qt",
    ],
    python_requires=">=3.7",
    install_requires=[
        "PyQt5>=5.15.0",
        "psutil>=5.8.0",
    ],
    extras_require={
        "dev": [
            "pyinstaller>=6.0.0",
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
        "build": [
            "pyinstaller>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pc-maintenance=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
    keywords=[
        "system maintenance",
        "performance monitoring",
        "disk cleanup",
        "system optimization",
        "benchmark",
        "system tools",
        "desktop application",
        "PyQt5",
    ],
    project_urls={
        "Bug Reports": "https://github.com/yourusername/pc-maintenance-dashboard/issues",
        "Source": "https://github.com/yourusername/pc-maintenance-dashboard",
        "Documentation": "https://github.com/yourusername/pc-maintenance-dashboard/wiki",
    },
)
