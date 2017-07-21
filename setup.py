from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name = "keragen",
    version = "0.1.0a1",
    description = "A Keras-based neural net trainer.",
    long_description = long_description,
    url="https://github.com/fireyoshiqc/keragen",
    author="Félix Boulet",
    author_email="felix.boulet@polymtl.ca",
    license="MIT",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers, Researchers',
        'Topic :: Neural Networks :: FPGA :: Hardware :: Training',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python 3',
        'Programming Language :: Python 3.5',
        'Programming Language :: Python 3.6',
    ],

    keywords="neuralnetworks fpga hardware training",
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=['keras', 'numpy', 'python-mnist']
)