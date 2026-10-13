from setuptools import find_packages, setup
from pathlib import Path


data_files = [
    ("share/kylin-memory-bench", ["README.md", "LICENSE"]),
    ("share/kylin-memory-bench/kmb", ["kmb/scoring.py"]),
]
for folder in ("configs", "suites", "scripts"):
    groups = {}
    for path in sorted(Path(folder).rglob("*")):
        if path.is_file() and path.suffix in {".yaml", ".example", ".py"}:
            groups.setdefault(str(path.parent), []).append(str(path))
    data_files.extend(("share/kylin-memory-bench/" + parent, files) for parent, files in groups.items())


setup(
    name="kylin-memory-bench",
    version="0.2.4",
    description="Evidence-based long-term memory benchmark for AI agents",
    packages=find_packages(),
    package_data={"kmb": ["web/*.html", "web/*.js", "web/*.css"]},
    data_files=data_files,
    install_requires=["PyYAML>=6.0"],
    entry_points={"console_scripts": ["kmb=kmb.cli:main"]},
    python_requires=">=3.9",
)
