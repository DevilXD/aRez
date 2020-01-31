from setuptools import setup, find_packages

import arez

setup(
    name="aRez",
    version=arez.__version__,
    description="Async Python HiRez API wrapper",
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
    packages=find_packages(include=["arez"]),
    install_requires=[
        "aiohttp>=2.0",
    ],
    python_requires=">=3.8",
)
