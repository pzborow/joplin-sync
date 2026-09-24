from setuptools import find_packages, setup


setup(
    name="joplin-sync",
    version="0.1.1",
    package_dir={"": "src"},
    packages=find_packages("src"),
    entry_points={"console_scripts": ["joplin-sync=joplin_sync.cli:main"]},
    python_requires=">=3.10",
)