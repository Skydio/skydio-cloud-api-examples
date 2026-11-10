from setuptools import find_packages, setup

setup(
    name="python_operations",
    version="0.1.0",
    packages=find_packages(),
    py_modules=["skydio_api_client", "skydio_operations"],
    install_requires=["requests", "python-dateutil", "plotly"],
    python_requires=">=3.8",
)
