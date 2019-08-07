from setuptools import setup
from gcodepause import __version__

setup(
    name='gcodepause',
    version=__version__,
    description='A package to add pauses in 3D printing GCODE',
    author='Julien de la Bruère-Terreault',
    author_email='drgfreeman@tuta.io',
    url='https://github.com/DrGFreeman/GCode-Layer-Pause',
    license='MIT',
    python_requires='>=3.6',
    install_requires=['pyyaml'],
    py_modules=['gcodepause'],
)