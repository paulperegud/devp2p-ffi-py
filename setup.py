#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
    from rust_ext import build_rust_cmdclass, install_lib_including_rust
except ImportError:
    from distutils.core import setup

readme = open('README.md').read()
history = open('HISTORY.md').read().replace('.. :changelog:', '')

install_requires = set(x.strip() for x in open('requirements.txt'))
install_requires_replacements = {
}
install_requires = [install_requires_replacements.get(r, r) for r in install_requires]

test_requirements = [
    'pytest==2.9.0',
    'pytest-catchlog==1.2.2',
    'pytest-timeout==1.0.0'
]

# *IMPORTANT*: Don't manually change the version here. Use the 'bumpversion' utility.
# see: https://github.com/ethereum/pyethapp/wiki/Development:-Versions-and-Releases
version = '0.0.1'

setup(
    name='devp2p_ffi_py',
    version=version,
    description='Python binding to Parity\s DevP2P implementation',
    long_description=readme + '\n\n' + history,
    author='pepesza',
    author_email='paulperegud@gmail.com',
    url='https://github.com/paulperegud/devp2p-ffi-py',
    # packages=find_packages(exclude='devp2p_ffi_py.tests'),
    packages=find_packages(),
    package_dir={'devp2p_ffi_py': 'devp2p_ffi_py'},
    # include_package_data=False,
    install_requires=install_requires,
    license="GPLv3.0",
    keywords='devp2p',
    cffi_modules=[
        "devp2p_ffi_py/cffi_builder.py:ffi"
    ],
    cmdclass={
        # This enables 'setup.py build_rust', and makes it run
        # 'cargo extensions/cargo.toml' before building your package.
        'build_rust': build_rust_cmdclass('devp2p-ffi/Cargo.toml', True),
        # This causes your rust binary to be automatically installed
        # with the package when install_lib runs (including when you
        # run 'setup.py install'.
        'install_lib': install_lib_including_rust
    },
    zip_safe=False,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPLv3.0',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7'
    ],
    setup_requires=['pytest-runner>2.0,<3', 'rust_ext'],
    tests_require=test_requirements
)
