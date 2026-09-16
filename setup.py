from setuptools import find_packages, setup


setup(
    name="kylin-memory-bench",
    version="0.2.0",
    description="Evidence-based long-term memory benchmark for AI agents",
    packages=find_packages(),
    package_data={"kmb": ["web/*.html", "web/*.js", "web/*.css"]},
    install_requires=["PyYAML>=6.0"],
    entry_points={"console_scripts": ["kmb=kmb.cli:main"]},
    python_requires=">=3.9",
)
