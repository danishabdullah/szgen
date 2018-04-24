from __future__ import print_function, unicode_literals

from setuptools import setup, find_packages

__author__ = "danishabdullah"

with open("requirements.txt", 'r') as file:
    requirements = file.readlines()

with open("readme.md", 'r') as file:
    readme = file.read()

with open("LICENSE", 'r') as file:
    license = file.read()

setup(
    name='szgen',
    version='0.1',
    packages=find_packages(),
    url='https://github.com/danishabdullah/szgen',
    install_requires=requirements,
    license=license,
    zip_safe=False,
    author='Danish Abdullah',
    author_email='dev@danishabdullah.com',
    description='szgen',
    keywords='szgen subzerocloud model generation',
    package_data={
        '': ['requirements.txt', 'readme.md', 'LICENSE']
    },
    entry_points={
        'console_scripts': ['szgen=szgen.scripts.cli:cli']
    },
    long_description=readme,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
