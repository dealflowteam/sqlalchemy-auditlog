import os

from setuptools import setup

import auditlog

# Readme as long description
with open(os.path.join(os.path.dirname(__file__), "README.md"), "r") as readme_file:
    long_description = readme_file.read()

setup(
    name='sqlalchemy-auditlog',
    version=auditlog.__version__,
    packages=['sqlalchemy_auditlog'],
    include_package_data=True,
    url='https://github.com/dealflowteam/sqlalchemy-auditlog',
    license='MIT',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'sqlalchemy==1.3.23',
        'elasticsearch-dsl==7.3.0',
    ],
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: MIT License',
    ],
)