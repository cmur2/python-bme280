#!/usr/bin/env python

import bme280


def main():
    bme = bme280.Bme280()
    bme.set_mode(bme280.MODE_FORCED)
    t, p, h = bme.get_data()
    print("Temperature: %f °C" % t)
    print("Pressure: %f P" % p)
    print("Humidity: %f %%" % h)


if __name__ == '__main__':
    main()
