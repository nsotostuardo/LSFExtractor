from setuptools import setup, find_packages

with open('requirements.txt', encoding='UTF-16') as f:
    required = f.read().splitlines()

with open("README.md", "r") as f:
    description = f.read()

setup(
    name='LSFExtractor',
    version='0.0.1',
    description='A Python module to estimate the Line Spread Function',
    packages=find_packages(),
    install_requires=required,
    scripts=['LSFExtractor/Spectrum.py'],
    package_data={
        'LSFExtractor': ['*.py'],
    },
    long_description=description,
    long_description_content_type="text/markdown"
    )