from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ks-infrastructure",
    version="1.0.0",
    author="KS Team",
    author_email="ks-team@example.com",
    description="KS Infrastructure - A unified infrastructure service module",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ks-team/ks-infrastructure",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "mysql-connector-python>=8.0.0",
        "boto3>=1.26.0",
        "qdrant-client>=1.1.0",
        "openai>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.9",
        ],
    },
    package_data={
        "ks_infrastructure": [
            "configs/*.py",
            "README.md",
        ],
    },
    include_package_data=True,
)