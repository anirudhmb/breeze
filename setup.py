"""
Breeze Trading Client - Setup Configuration
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="breeze-trader-client",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A trader-friendly Python wrapper for ICICI Direct's Breeze API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/breeze-trader-client",
    packages=find_packages(exclude=["tests", "tests.*", "scripts", "scripts.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "breeze-connect>=1.0.39",
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
        ],
        "analysis": [
            "pandas>=2.0.0",
            "numpy>=1.24.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "breeze-login=scripts.login:main",
            "breeze-status=scripts.session_status:main",
            "breeze-test=scripts.test_connection:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

