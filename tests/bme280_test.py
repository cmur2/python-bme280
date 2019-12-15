# import unittest
import sys
import time

import mock

import snapshottest

# Note: prepare globally mocked modules first and then load our module
MOCKED_SMBUS_MODULE = mock.Mock()
sys.modules['smbus'] = MOCKED_SMBUS_MODULE
time.sleep = lambda s: None
import bme280  # pylint: disable=wrong-import-position


# inspired by https://github.com/adafruit/Adafruit_Python_GPIO/blob/master/Adafruit_GPIO/I2C.py
class MockSMBus():
    def __init__(self, initial_read=None):
        self._log = []
        self.initial_read = initial_read or {}

    def read_byte(self, addr):
        val = self.initial_read.get(addr).pop(0)
        self._log.append(('r', addr, val))
        return val

    def write_byte(self, addr, val):
        self._log.append(('w', addr, val))

    def read_byte_data(self, addr, cmd):
        val = self.initial_read.get(addr).pop(0)
        self._log.append(('w', addr, cmd))
        self._log.append(('r', addr, val))
        return val

    def write_byte_data(self, addr, cmd, val):
        self._log.append(('w', addr, cmd))
        self._log.append(('w', addr, val))


def setup_mockbus(**kwargs):
    mockbus = MockSMBus(**kwargs)
    MOCKED_SMBUS_MODULE.SMBus.return_value = mockbus
    return mockbus


def calibration_read():
    return [0x00] * (24 + 1 + 7)


# pylint: disable=protected-access
class TestBme280(snapshottest.TestCase):
    def test_setup(self):
        mockbus = setup_mockbus(initial_read={0x76: calibration_read()})
        bme = bme280.Bme280()
        MOCKED_SMBUS_MODULE.SMBus.assert_called_with(1)
        self.assertIsNotNone(bme)
        self.assertMatchSnapshot(mockbus._log)

    def test_chip_id(self):
        mockbus = setup_mockbus(initial_read={0x76: calibration_read() + [0x23]})
        bme = bme280.Bme280()
        self.assertEqual(bme.get_chip_id(), 0x23)
        self.assertMatchSnapshot(mockbus._log)

    def test_reset(self):
        mockbus = setup_mockbus(initial_read={0x76: calibration_read()})
        bme = bme280.Bme280()
        bme.reset()
        self.assertMatchSnapshot(mockbus._log)

    def test_status(self):
        mockbus = setup_mockbus(initial_read={0x76: calibration_read() + [0x08, 0x00, 0x01, 0x00]})
        bme = bme280.Bme280()
        self.assertTrue(bme.is_status_measuring())
        self.assertFalse(bme.is_status_measuring())
        self.assertTrue(bme.is_status_image_register_updating())
        self.assertFalse(bme.is_status_image_register_updating())
        self.assertMatchSnapshot(mockbus._log)

    def test_oversampling(self):
        mockbus = setup_mockbus(initial_read={0x76: calibration_read()})
        bme = bme280.Bme280()
        self.assertEqual(bme.get_humidity_oversampling(), bme280.HO_1)
        bme.set_humidity_oversampling(bme280.HO_16)
        self.assertEqual(bme.get_humidity_oversampling(), bme280.HO_16)
        self.assertEqual(bme.get_temperature_oversampling(), bme280.TO_1)
        bme.set_temperature_oversampling(bme280.TO_16)
        self.assertEqual(bme.get_temperature_oversampling(), bme280.TO_16)
        self.assertEqual(bme.get_pressure_oversampling(), bme280.PO_1)
        bme.set_pressure_oversampling(bme280.PO_16)
        self.assertEqual(bme.get_pressure_oversampling(), bme280.PO_16)
        self.assertMatchSnapshot(mockbus._log)

    def test_mode(self):
        mockbus = setup_mockbus(initial_read={0x76: calibration_read()})
        bme = bme280.Bme280()
        self.assertEqual(bme.get_mode(), bme280.MODE_SLEEP)
        bme.set_mode(bme280.MODE_FORCED)
        self.assertEqual(bme.get_mode(), bme280.MODE_FORCED)
        self.assertMatchSnapshot(mockbus._log)

    def test_config(self):
        mockbus = setup_mockbus(initial_read={0x76: calibration_read()})
        bme = bme280.Bme280()
        self.assertEqual(bme.get_tstandy(), bme280.TSTANDBY_1000)
        bme.set_tstandy(bme280.TSTANDBY_20)
        self.assertEqual(bme.get_tstandy(), bme280.TSTANDBY_20)
        self.assertEqual(bme.get_filter(), bme280.FILTER_OFF)
        bme.set_filter(bme280.FILTER_16)
        self.assertEqual(bme.get_filter(), bme280.FILTER_16)
        self.assertMatchSnapshot(mockbus._log)

    def test_data(self):
        mockbus = setup_mockbus(initial_read={0x76: calibration_read() + [0x00] * 8})
        bme = bme280.Bme280()
        bme.set_mode(bme280.MODE_FORCED)
        t, p, h = bme.get_data()  # pylint: disable=unused-variable
        # self.assertEqual(t, 0x00)
        self.assertMatchSnapshot(mockbus._log)
