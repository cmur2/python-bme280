
import bme280

if __name__ == '__main__':
  bme = bme280.Bme280()
  bme.set_mode(bme280.MODE_FORCED)
  t, p, h = bme.get_data()
  print "Temperature: %f °C" % t
  print "Pressure: %f P" % p
  print "Humidity: %f %" % h
