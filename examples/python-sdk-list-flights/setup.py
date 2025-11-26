from setuptools import setup, find_packages

setup(
    name="python_sdk_list_flights",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "pytz",
        "timezonefinder",
    ],
)
