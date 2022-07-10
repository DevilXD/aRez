from __future__ import annotations

import re
from setuptools import setup, find_packages


# Parse the version string out of the init file
version: str | None = None
with open("arez/__init__.py", 'r', encoding="utf8") as f:
    match = re.search(r'__version__ = "(\d+\.\d+\.\d+(?:\.dev\d+)?)"', f.read())
    if match:
        version = match.group(1)
if not version:
    raise RuntimeError("Unable to parse version!")

with open("README.md", 'r') as f:
    long_description = f.read()


setup(
    name="aRez",
    version=version,
    description="Async Python HiRez API wrapper",
    long_description=long_description,
    long_description_content_type="text/markdown; charset=UTF-8; variant=GFM",
    url="https://github.com/DevilXD/aRez",
    author="DevilXD",
    license='GPLv3',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
    project_urls={
        "Source": "https://github.com/DevilXD/aRez",
        "Documentation": "https://arez.readthedocs.io/en/latest/",
    },
    packages=find_packages(include=["arez"]),
    install_requires=[
        "aiohttp>=2.0",
    ],
    python_requires=">=3.8",
    package_data={
        "arez": ["py.typed"],
    },
)
