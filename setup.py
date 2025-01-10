from setuptools import setup, find_packages

setup(
    name="code-sentinel-demo",
    version="0.1.0",
    description="Code Sentinel integration with Anthropic Computer Use Demo",
    author="Anthropic",
    author_email="info@anthropic.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "pytest>=8.0.0",
        "pyyaml>=6.0.0",
        "jsonschema>=4.0.0",
        "omegaconf>=2.3.0",
        "antlr4-python3-runtime>=4.9.3",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
            "black",
            "isort",
            "flake8",
            "mypy",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
)
