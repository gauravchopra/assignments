from setuptools import setup, find_packages

setup(
    name="rbcapp1-monitoring",
    version="1.0.0",
    description="Monitoring system for rbcapp1 application and its dependencies",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "Flask>=2.3.0",
        "elasticsearch>=8.0.0",
        "requests>=2.31.0",
        "dataclasses-json>=0.6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-mock>=3.11.0",
            "requests-mock>=1.11.0",
            "coverage>=7.3.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "rbcapp1-monitor=monitor.service_monitor:main",
            "rbcapp1-api=api.app:main",
        ],
    },
)