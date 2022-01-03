import time

import smbus  # pylint: disable=import-error

ADDR = 0x76  # 7bit address of the BME280 for SDO=0, else 0x77

REGISTER_ID = 0xD0
REGISTER_RESET = 0xE0
REGISTER_CTRL_HUM = 0xF2
REGISTER_STATUS = 0xF3
REGISTER_CTRL_MEAS = 0xF4
REGISTER_CONFIG = 0xF5

HO_SKIPPED = 0x00
HO_1 = 0x01
HO_2 = 0x02
HO_4 = 0x03
HO_8 = 0x04
HO_16 = 0x05  # and all higher

PO_SKIPPED = 0x00
PO_1 = 0x01
PO_2 = 0x02
PO_4 = 0x03
PO_8 = 0x04
PO_16 = 0x05  # and all higher

TO_SKIPPED = 0x00
TO_1 = 0x01
TO_2 = 0x02
TO_4 = 0x03
TO_8 = 0x04
TO_16 = 0x05  # and all higher

MODE_SLEEP = 0x00
MODE_FORCED = 0x01  # and 0x02
MODE_NORMAL = 0x03

TSTANDBY_0_5 = 0x00
TSTANDBY_62_5 = 0x01
TSTANDBY_125 = 0x02
TSTANDBY_250 = 0x03
TSTANDBY_500 = 0x04
TSTANDBY_1000 = 0x05
TSTANDBY_10 = 0x06
TSTANDBY_20 = 0x07

FILTER_OFF = 0x00
FILTER_2 = 0x01
FILTER_4 = 0x02
FILTER_8 = 0x03
FILTER_16 = 0x04  # and all higher


class Bme280():

    def __init__(self, i2c_bus=1, sensor_address=ADDR):
        self.bus = smbus.SMBus(i2c_bus)
        self.sensor_address = sensor_address
        self.ho = HO_1
        self.po = PO_1
        self.to = TO_1
        self.mode = MODE_SLEEP
        self.tstandy = TSTANDBY_1000
        self.filter = FILTER_OFF

        self.read_calibration_parameters()

        # initialize once
        self.bus.write_byte_data(self.sensor_address, REGISTER_CTRL_HUM, self.get_reg_ctrl_hum())
        self.bus.write_byte_data(self.sensor_address, REGISTER_CTRL_MEAS, self.get_reg_ctrl_meas())
        self.bus.write_byte_data(self.sensor_address, REGISTER_CONFIG, self.get_reg_config())

    def get_chip_id(self):
        return self.bus.read_byte_data(self.sensor_address, REGISTER_ID)

    def reset(self):
        self.bus.write_byte_data(self.sensor_address, REGISTER_RESET, 0xB6)

    def is_status_measuring(self):
        return (self.bus.read_byte_data(self.sensor_address, REGISTER_STATUS) & 0x08) != 0x00

    def is_status_image_register_updating(self):
        return (self.bus.read_byte_data(self.sensor_address, REGISTER_STATUS) & 0x01) != 0x00

    def set_humidity_oversampling(self, ho):
        self.ho = ho
        self.bus.write_byte_data(self.sensor_address, REGISTER_CTRL_HUM, self.get_reg_ctrl_hum())
        # flush (unchanged) CTRL_MEAS to make CTRL_HUM effective!
        self.bus.write_byte_data(self.sensor_address, REGISTER_CTRL_MEAS, self.get_reg_ctrl_meas())

    def get_humidity_oversampling(self):
        return self.ho

    def set_temperature_oversampling(self, to):
        self.to = to
        self.bus.write_byte_data(self.sensor_address, REGISTER_CTRL_MEAS, self.get_reg_ctrl_meas())

    def get_temperature_oversampling(self):
        return self.to

    def set_pressure_oversampling(self, po):
        self.po = po
        self.bus.write_byte_data(self.sensor_address, REGISTER_CTRL_MEAS, self.get_reg_ctrl_meas())

    def get_pressure_oversampling(self):
        return self.po

    def set_mode(self, mode):
        self.mode = mode
        self.bus.write_byte_data(self.sensor_address, REGISTER_CTRL_MEAS, self.get_reg_ctrl_meas())

    def get_mode(self):
        return self.mode

    def set_tstandy(self, tstandy):
        self.tstandy = tstandy
        self.bus.write_byte_data(self.sensor_address, REGISTER_CONFIG, self.get_reg_config())

    def get_tstandy(self):
        return self.tstandy

    def set_filter(self, fil):
        self.filter = fil
        self.bus.write_byte_data(self.sensor_address, REGISTER_CONFIG, self.get_reg_config())

    def get_filter(self):
        return self.filter

    def get_data(self):
        if self.get_mode() == MODE_FORCED:
            t_measure_max = 1.25 + (2.3 * self.to) + (2.3 * self.po + 0.575) + (2.3 * self.ho + 0.575)
            time.sleep(t_measure_max / 1000.0)

        data = []
        for i in range(0xF7, 0xF7 + 8):
            data.append(self.bus.read_byte_data(self.sensor_address, i))

        pressure_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        temperature_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        humidity_raw = (data[6] << 8) | data[7]
        t_fine = self.calc_t_fine(temperature_raw)
        t = self.calc_compensated_temperature(t_fine)
        p = self.calc_compensated_pressure(t_fine, pressure_raw)
        h = self.calc_compensated_humidity(t_fine, humidity_raw)

        if self.get_mode() == MODE_FORCED:
            # chip returns to sleep after data readout automatically, mirror it
            self.mode = MODE_SLEEP

        return (t, p, h)

    def get_reg_ctrl_hum(self):
        """
        returns the bit pattern for CTRL_HUM corresponding to the desired state of this class
        """
        return self.ho & 0x07

    def get_reg_ctrl_meas(self):
        """
        returns the bit pattern for CTRL_MEAS corresponding to the desired state of this class
        """
        return ((self.to & 0x07) << 5) | ((self.po & 0x07) << 2) | self.mode

    def get_reg_config(self):
        """
        returns the bit pattern for CONFIG corresponding to the desired state of this class
        """
        # SPI permanently disabled
        return ((self.tstandy & 0x07) << 5) | ((self.filter & 0x07) << 2) | 0x00

    # Bug-fixed code, originally from https://github.com/SWITCHSCIENCE/BME280

    def read_calibration_parameters(self):
        # read all calibration registers from chip NVM
        calibration_regs = []
        for i in range(0x88, 0x88 + 24):
            calibration_regs.append(self.bus.read_byte_data(self.sensor_address, i))
        calibration_regs.append(self.bus.read_byte_data(self.sensor_address, 0xA1))
        for i in range(0xE1, 0xE1 + 7):
            calibration_regs.append(self.bus.read_byte_data(self.sensor_address, i))

        # pylint: disable=bad-option-value,bad-whitespace

        # reorganize 8-bit words into compensation words (without correct sign)
        self.digT = []
        self.digT.append((calibration_regs[1] << 8) | calibration_regs[0])
        self.digT.append((calibration_regs[3] << 8) | calibration_regs[2])
        self.digT.append((calibration_regs[5] << 8) | calibration_regs[4])

        self.digP = []
        self.digP.append((calibration_regs[7] << 8) | calibration_regs[6])
        self.digP.append((calibration_regs[9] << 8) | calibration_regs[8])
        self.digP.append((calibration_regs[11] << 8) | calibration_regs[10])
        self.digP.append((calibration_regs[13] << 8) | calibration_regs[12])
        self.digP.append((calibration_regs[15] << 8) | calibration_regs[14])
        self.digP.append((calibration_regs[17] << 8) | calibration_regs[16])
        self.digP.append((calibration_regs[19] << 8) | calibration_regs[18])
        self.digP.append((calibration_regs[21] << 8) | calibration_regs[20])
        self.digP.append((calibration_regs[23] << 8) | calibration_regs[22])

        self.digH = []
        self.digH.append(calibration_regs[24])
        self.digH.append((calibration_regs[26] << 8) | calibration_regs[25])
        self.digH.append(calibration_regs[27])
        self.digH.append((calibration_regs[28] << 4) | (0x0F & calibration_regs[29]))
        self.digH.append((calibration_regs[30] << 4) | ((calibration_regs[29] >> 4) & 0x0F))
        self.digH.append(calibration_regs[31])

        # fix sign for integers in two's complement
        for i in [1, 2]:
            if self.digT[i] & 0x8000:
                self.digT[i] = (-self.digT[i] ^ 0xFFFF) + 1

        for i in [1, 2, 3, 4, 5, 6, 7, 8]:
            if self.digP[i] & 0x8000:
                self.digP[i] = (-self.digP[i] ^ 0xFFFF) + 1

        for i in [1]:
            if self.digH[i] & 0x8000:
                self.digH[i] = (-self.digH[i] ^ 0xFFFF) + 1
        for i in [3, 4]:
            if self.digH[i] & 0x0800:
                self.digH[i] = (-self.digH[i] ^ 0x0FFF) + 1
        for i in [5]:
            if self.digH[i] & 0x0080:
                self.digH[i] = (-self.digH[i] ^ 0x00FF) + 1

    # Code from Bosch datasheet translated to Python

    def calc_t_fine(self, adc_T):
        var1 = (adc_T / 16384.0 - self.digT[0] / 1024.0) * self.digT[1]
        var2 = (adc_T / 131072.0 - self.digT[0] / 8192.0) * (adc_T / 131072.0 - self.digT[0] / 8192.0) * self.digT[2]
        return var1 + var2

    @staticmethod
    def calc_compensated_temperature(t_fine):
        return t_fine / 5120.0

    def calc_compensated_pressure(self, t_fine, adc_P):
        var1 = (t_fine / 2.0) - 64000.0
        var2 = var1 * var1 * (self.digP[5]) / 32768.0
        var2 = var2 + var1 * (self.digP[4]) * 2.0
        var2 = (var2 / 4.0) + (self.digP[3] * 65536.0)
        var1 = (self.digP[2] * var1 * var1 / 524288.0 + self.digP[1] * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.digP[0]
        if var1 == 0.0:
            return 0  # avoid exception caused by division by zero
        p = 1048576.0 - adc_P
        p = (p - (var2 / 4096.0)) * 6250.0 / var1
        var1 = self.digP[8] * p * p / 2147483648.0
        var2 = p * self.digP[7] / 32768.0
        return p + (var1 + var2 + self.digP[6]) / 16.0

    def calc_compensated_humidity(self, t_fine, adc_H):
        var_H = t_fine - 76800.0
        # yapf: disable
        # pylint: disable=line-too-long
        var_H = (adc_H - (self.digH[3] * 64.0 + self.digH[4] / 16384.0 * var_H)) * (self.digH[1] / 65536.0 * (1.0 + self.digH[5] / 67108864.0 * var_H * (1.0 + self.digH[2] / 67108864.0 * var_H)))
        # yapf: enable
        var_H = var_H * (1.0 - self.digH[0] * var_H / 524288.0)
        if var_H > 100.0:
            var_H = 100.0
        elif var_H < 0.0:
            var_H = 0.0
        return var_H
