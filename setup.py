#!/usr/bin/env python3
"""
Setup script for HFT-PacketFilter

High-Frequency Trading Network Analysis Package
"""

from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize
import os
import sys
import platform
import numpy

# Read version from package
def get_version():
    """Get version from package __init__.py"""
    version_file = os.path.join(os.path.dirname(__file__), 'hft_packetfilter', '__init__.py')
    with open(version_file, 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return "0.1.0"

# Read long description from README
def get_long_description():
    """Get long description from README.md"""
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "High-Frequency Trading Network Analysis Package"

# Read requirements
def get_requirements():
    """Get requirements from requirements.txt"""
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(req_path):
        with open(req_path, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

# Platform-specific requirements
def get_platform_requirements():
    """Get platform-specific requirements"""
    requirements = get_requirements()
    
    # Add platform-specific packages
    if sys.platform.startswith('linux'):
        requirements.extend([
            'netfilterqueue>=1.0.0',
            'python-iptables>=1.0.0'
        ])
    
    return requirements

# Performance-critical C extensions
extensions = [
    Extension(
        "hft_packetfilter.core.c_extensions.fast_parser",
        sources=["hft_packetfilter/core/c_extensions/fast_parser.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=["-O3", "-ffast-math", "-march=native"],
        extra_link_args=["-O3"],
        language="c",
    ),
    Extension(
        "hft_packetfilter.core.c_extensions.latency_tracker", 
        sources=["hft_packetfilter/core/c_extensions/latency_tracker.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=["-O3", "-ffast-math", "-march=native"],
        extra_link_args=["-O3"],
        language="c",
    ),
    Extension(
        "hft_packetfilter.core.c_extensions.memory_pool",
        sources=["hft_packetfilter/core/c_extensions/memory_pool.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=["-O3", "-ffast-math", "-march=native"],
        extra_link_args=["-O3"],
        language="c",
    ),
    Extension(
        "hft_packetfilter.core.c_extensions.lock_free_queue",
        sources=["hft_packetfilter/core/c_extensions/lock_free_queue.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=["-O3", "-ffast-math", "-march=native"],
        extra_link_args=["-O3"],
        language="c",
    ),
]

# Platform-specific optimizations
if platform.system() == "Linux":
    for ext in extensions:
        ext.extra_compile_args.extend(["-DLINUX", "-D_GNU_SOURCE"])
elif platform.system() == "Darwin":
    for ext in extensions:
        ext.extra_compile_args.extend(["-DMACOS"])

setup(
    # Basic package information
    name="hft-packetfilter",
    version=get_version(),
    description="High-Frequency Trading Network Analysis Package",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    
    # Author and contact information
    author="HFT-PacketFilter Development Team",
    author_email="dev@hft-packetfilter.com",
    maintainer="HFT-PacketFilter Team",
    maintainer_email="support@hft-packetfilter.com",
    
    # URLs and links
    url="https://github.com/hft-packetfilter/hft-packetfilter",
    project_urls={
        "Documentation": "https://hft-packetfilter.readthedocs.io/",
        "Source Code": "https://github.com/hft-packetfilter/hft-packetfilter",
        "Bug Tracker": "https://github.com/hft-packetfilter/hft-packetfilter/issues",
        "Changelog": "https://github.com/hft-packetfilter/hft-packetfilter/blob/main/CHANGELOG.md",
        "Funding": "https://github.com/sponsors/hft-packetfilter",
    },
    
    # Package discovery and structure
    packages=find_packages(exclude=['tests*', 'benchmarks*', 'examples*']),
    package_data={
        'hft_packetfilter': [
            'config/*.yaml',
            'config/*.json',
            'static/css/*.css',
            'static/js/*.js',
            'templates/*.html',
            'schemas/*.json',
        ],
    },
    include_package_data=True,
    
    # C extensions for performance
    ext_modules=cythonize(extensions, compiler_directives={
        'language_level': 3,
        'boundscheck': False,
        'wraparound': False,
        'cdivision': True,
        'profile': False,
        'linetrace': False,
    }),
    
    # Dependencies
    install_requires=get_platform_requirements(),
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'pytest-mock>=3.10.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
            'sphinx>=6.0.0',
            'sphinx-rtd-theme>=1.2.0',
        ],
        'performance': [
            'cython>=3.0.7,<4.0',
            'numpy>=1.24.0',
            'psutil>=5.9.0',
            'atomics>=1.0.2',
        ],
        'ml': [
            'scikit-learn>=1.2.0',
            'tensorflow>=2.10.0',
            'torch>=1.13.0',
        ],
        'dashboard': [
            'flask>=2.2.0',
            'flask-cors>=4.0.0',
            'plotly>=5.12.0',
            'dash>=2.7.0',
        ],
        'compliance': [
            'cryptography>=38.0.0',
            'pycryptodome>=3.16.0',
        ],
        'cloud': [
            'boto3>=1.26.0',  # AWS
            'google-cloud-storage>=2.7.0',  # GCP
            'azure-storage-blob>=12.14.0',  # Azure
        ],
        'monitoring': [
            'prometheus-client>=0.15.0',
            'influxdb-client>=1.35.0',
            'grafana-api>=1.0.3',
        ],
        'linux': get_platform_requirements(),
        'all': (
            get_platform_requirements() +
            ['cython>=3.0.7,<4.0', 'numpy>=1.24.0', 'psutil>=5.9.0', 'atomics>=1.0.2']
        ),
    },
    
    # Entry points for command-line tools
    entry_points={
        'console_scripts': [
            'hft-monitor=hft_packetfilter.tools.monitor:main',
            'hft-analyze=hft_packetfilter.tools.analyzer:main',
            'hft-config=hft_packetfilter.tools.config:main',
            'hft-benchmark=hft_packetfilter.tools.benchmark:main',
            'hft-export=hft_packetfilter.tools.export:main',
            'hft-dashboard=hft_packetfilter.tools.dashboard:main',
        ],
    },
    
    # Python version requirements
    python_requires=">=3.9",
    
    # Package classification
    classifiers=[
        # Development Status
        "Development Status :: 4 - Beta",
        
        # Intended Audience
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        
        # Topic
        "Topic :: Office/Business :: Financial",
        "Topic :: System :: Networking :: Monitoring",
        "Topic :: System :: Systems Administration",
        "Topic :: Software Development :: Libraries :: Python Modules",
        
        # License
        "License :: OSI Approved :: Apache Software License",
        
        # Programming Language
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: CPython",
        
        # Operating System
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        
        # Environment
        "Environment :: Console",
        "Environment :: Web Environment",
        
        # Natural Language
        "Natural Language :: English",
    ],
    
    # Keywords for PyPI search
    keywords=[
        "hft", "high-frequency-trading", "packet-filtering", "network-analysis",
        "latency-monitoring", "trading", "finance", "market-data", "fix-protocol",
        "arbitrage", "compliance", "risk-management", "real-time", "microsecond",
        "exchange", "trading-infrastructure", "market-microstructure"
    ],
    
    # License
    license="Apache License 2.0",
    
    # Platform requirements
    platforms=["Linux", "macOS", "Windows"],
    
    # Zip safety
    zip_safe=False,
) 