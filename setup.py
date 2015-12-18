#from setuptools import setup, find_packages
from setuptools import *

description='DMB file parser for python'

setup(
    name='pydmb',
    version='0.1.1',
    description=description,
    long_description=description,
    url='https://github.com/baliame/pydmb',
    author='Baliame',
    author_email='akos.toth@cheppers.com',
    license='MIT',
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='byond dmb development library',
    install_requires=[],
    packages=find_packages(),
)
