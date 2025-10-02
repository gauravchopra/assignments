from setuptools import setup, find_packages

setup(
    name="real-estate-analyzer",
    version="1.0.0",
    description="Real estate data analysis tool for filtering properties by price per square foot",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "pandas>=1.5.0",
        "numpy>=1.21.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
        ],
        "viz": [
            "matplotlib>=3.5.0",
            "seaborn>=0.11.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "real-estate-analyzer=real_estate_analyzer:main",
        ],
    },
    author="Test Assignment",
    author_email="test@example.com",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)