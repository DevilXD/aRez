from setuptools import setup, find_packages

import arez

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name="aRez",
    version=arez.__version__,
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
