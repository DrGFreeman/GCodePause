from setuptools import setup, find_packages

setup(
    name='gcodepause',
    version='0.1.0',
    description='A package to add pauses in 3D printing GCODE',
    author='Julien de la Bruère-Terreault',
    author_email='drgfreeman@tuta.io',
    url='https://github.com/DrGFreeman/GCode-Layer-Pause',
    license='MIT',
    python_requires='>=3.6',
    install_requires=['pyyaml'],
    packages=find_packages(),
)
