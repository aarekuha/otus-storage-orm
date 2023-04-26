from io import open
from setuptools import setup

"""
:authors: aarekuha
:license: Apache License, Version 2.0
:copyright: (c) 2022 aarekuha
"""

version = '1.0.0'

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='storage_orm',
    version=version,

    author='aarekuha',
    author_email='aarekuha@gmail.ru',

    description=(
        u'Python for using in-memory storage with ORM'
    ),
    long_description=long_description,
    long_description_content_type='text/markdown',

    url='https://github.com/aarekuha/otus-storage-orm',

    license='Apache License, Version 2.0',

    packages=['storage_orm', 'storage_orm.redis_impl'],
    install_requires=['redis'],

    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: Implementation :: CPython',
    ]
)
