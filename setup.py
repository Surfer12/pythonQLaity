"""Setup script for the anthropic package."""

from setuptools import setup, find_packages

setup(
    name="anthropic",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "jsonschema",
        "omegaconf",
        "pyyaml",
        "pytest",
    ],
    python_requires=">=3.7",
)
