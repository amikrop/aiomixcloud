import re
from pathlib import Path

from setuptools import setup


init_path = Path('aiomixcloud') / '__init__.py'
with init_path.open() as f:
    version = re.search(r'__version__ = \'(.*?)\'', f.read()).group(1)

with open('README.rst') as f:
    long_description = f.read()


setup(
    name='aiomixcloud',
    version=version,
    description='Mixcloud API wrapper for Python and Async IO',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author='Aristotelis Mikropoulos',
    author_email='amikrop@gmail.com',
    url='https://github.com/amikrop/aiomixcloud',
    packages=['aiomixcloud'],
    license='MIT',
    install_requires=[
        'aiohttp',
        'python-dateutil',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: AsyncIO',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
