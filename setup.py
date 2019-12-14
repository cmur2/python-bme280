from setuptools import setup

setup(name='bme280',
      version='1.0.0',
      packages=['bme280'],

      install_requires=['smbus2'],
      python_requires='>=2.7',

      url='https://dev.mycrobase.de/gitea/cn/python-bme280',
      author='Christian Nicolai',
      description='A python library for accessing the BME280 combined humidity and pressure sensor from Bosch.',
      long_description=open('README.md').read())
