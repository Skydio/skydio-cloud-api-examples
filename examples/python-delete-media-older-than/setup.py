from setuptools import setup, find_packages

setup(
    name="python_delete_media_older_than",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
    ],
)
