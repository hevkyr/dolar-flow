from setuptools import setup, find_packages

setup(
    name="dolar-flow",
    version="1.0.0",
    description="Portfolio tracker focused on asset dollarization for Brazilian investors",
    author="hevkyr",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "dolar-flow=src.cli.cli:main",
        ],
    },
    python_requires=">=3.10",
)
