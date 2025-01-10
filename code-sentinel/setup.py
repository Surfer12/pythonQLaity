from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="code-sentinel",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A static analysis tool for code quality and security",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/code-sentinel",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "hydra-core>=1.1.0",
        "sqlalchemy>=1.4.0",
        "alembic>=1.7.0",
        "pyyaml>=5.4.0",
        "rich>=10.0.0",
        "pathlib>=1.0.1",
        "typing-extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.12.0",
            "black>=21.5b2",
            "isort>=5.9.0",
            "flake8>=3.9.0",
            "mypy>=0.910",
            "pre-commit>=2.15.0",
            "sphinx>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "code-sentinel=cli.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
