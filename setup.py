#!/usr/bin/env python3
"""
Setup script for YOLOv11e PII Detection Pipeline.

This package provides a comprehensive solution for detecting and blurring
Personally Identifiable Information (PII) in images and videos using
YOLOv11e (YOLOE) open-vocabulary object detection.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="yoloe-pii-detector",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="YOLOv11e-based PII detection and blurring pipeline",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/techjam_catgpt_2025",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/techjam_catgpt_2025/issues",
        "Source": "https://github.com/yourusername/techjam_catgpt_2025",
        "Documentation": "https://github.com/yourusername/techjam_catgpt_2025#readme",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Multimedia :: Video",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
            "myst-parser>=0.15",
        ],
    },
    entry_points={
        "console_scripts": [
            "pii-detector=pii_detector:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.yaml", "*.yml"],
    },
    keywords=[
        "pii",
        "privacy",
        "yolo",
        "yoloe",
        "object-detection",
        "computer-vision",
        "image-processing",
        "video-processing",
        "blur",
        "anonymization",
    ],
    license="MIT",
    zip_safe=False,
)
