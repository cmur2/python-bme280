# python-bme280

[![Build Status](https://travis-ci.org/cmur2/python-bme280.svg?branch=master)](https://travis-ci.org/cmur2/python-bme280)

A Python library for accessing the [BME280 combined humidity and pressure](https://ae-bst.resource.bosch.com/media/_tech/media/datasheets/BST-BME280_DS001-11.pdf) from Bosch via `python-smbus` using the I2C interface.

Default settings are suitable for Raspberry Pi 2 and 3 and was successfully tested using a [breakout](https://github.com/watterott/BME280-Breakout).

I created this Python library in style of e.g. [python-veml6070](https://github.com/cmur2/python-veml6070) or [python-tsl2591](https://github.com/maxlklaxl/python-tsl2591) since I found only [python scripts](https://github.com/SWITCHSCIENCE/BME280) with limited functionality and minor bugs and the official driver from Bosch is only in C(++).

Although, it is heavily based on existing code from Bosch translated to Python and from [SWITCHSCIENCE](https://github.com/SWITCHSCIENCE/BME280).

## Usage

Consult the data sheet and see [demo.py](demo.py) for clues how to use this library.

Not all functions of the chip are supported since I focused on the *forced mode* but data readout and parameter setting should work in *normal mode*, too. Please send pull requests for improvements and bug fixes!

## License

Python files in this repository are released under the [MIT license](LICENSE) except those parts from other sources which are indicated where appropriate in the files.
