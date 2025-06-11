# setup.py
"""
Setup para instalação do Qualia Core
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="qualia-core",
    version="0.1.0",
    author="Seu Nome",
    author_email="seu.email@example.com",
    description="Framework bare metal para análise qualitativa",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mrlnlms/qualia",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0",
        "rich>=13.0",
        "pyyaml>=6.0",
        "pydantic>=2.0",
        "nltk>=3.8",
        "numpy",
        "pandas",
    ],
    entry_points={
        "console_scripts": [
            "qualia=qualia.cli:cli",
        ],
    },
    include_package_data=True,
)