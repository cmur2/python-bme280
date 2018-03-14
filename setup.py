from setuptools import setup

setup(name='bme280',
      version='1.0',
      url='https://github.com/cmur2/python-bme280',
      author='Christian Nicolai',
      description='A python library for accessing the BME280 combined humidity and pressure sensor from Bosch.',
      packages=['bme280'],
      long_description=open('README.md').read(),
      requires=['python (>= 2.7)', 'smbus (>= 0.4.1)'],
      install_requires=['smbus-cffi'])
