#!/usr/bin/env python

"""
Created by Ralf Zimmermann (mail@ralfzimmermann.de) in 2020.
This code and its documentation can be found on: https://github.com/RalfZim/venus.dbus-fronius-smartmeter
Used https://github.com/victronenergy/velib_python/blob/master/dbusdummyservice.py as basis for this service.
Reading information from the Fronius Smart Meter via http REST API and puts the info on dbus.
"""
try:
  import gobject  # Python 2.x
except:
  from gi.repository import GLib as gobject # Python 3.x
import platform
import logging
import sys
import os
import requests # for http GET
try:
  import thread   # for daemon = True  / Python 2.x
except:
  import _thread as thread   # for daemon = True  / Python 3.x

# our own packages
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '../ext/velib_python'))
from vedbus import VeDbusService

path_UpdateIndex = '/UpdateIndex'


class DbusDummyService:
  def __init__(self, servicename, deviceinstance, paths, productname='Discovergy Smart Meter', connection='Discovergy Smart Meter service'):
    self._dbusservice = VeDbusService(servicename)
    self._paths = paths

    logging.debug("%s /DeviceInstance = %d" % (servicename, deviceinstance))

    # Create the management objects, as specified in the ccgx dbus-api document
    self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
    self._dbusservice.add_path('/Mgmt/ProcessVersion', 'Unkown version, and running on Python ' + platform.python_version())
    self._dbusservice.add_path('/Mgmt/Connection', connection)

    # Create the mandatory objects
    self._dbusservice.add_path('/DeviceInstance', deviceinstance)
    self._dbusservice.add_path('/ProductId', 16) # value used in ac_sensor_bridge.cpp of dbus-cgwacs
    self._dbusservice.add_path('/ProductName', productname)
    self._dbusservice.add_path('/FirmwareVersion', 0.1)
    self._dbusservice.add_path('/HardwareVersion', 0)
    self._dbusservice.add_path('/Connected', 1)
    self._dbusservice.add_path('/Position', 0) #neu hinzugefügt

    for path, settings in self._paths.items():
      self._dbusservice.add_path(
        path, settings['initial'], writeable=True, onchangecallback=self._handlechangedvalue)

    gobject.timeout_add(15000, self._update) # pause 200ms before the next request

  def _update(self):
    try:
#      meter_url = "http://10.194.65.143/solar_api/v1/GetMeterRealtimeData.cgi?"\
#                  "Scope=Device&DeviceId=0&DataCollection=MeterRealtimeData"
#      meter_r = requests.get(url=meter_url) # request data from the Fronius PV inverter
#      meter_data = meter_r.json() # convert JSON data
      meter_url = "https://benutzername:Password@api.discovergy.com/public/v1/last_reading?meterId=MeterID des eigenen Meters"
      meter_data = requests.get(meter_url).json() # convert JSON data
      meter_consumption = round(meter_data['values']['power']/1000,2)
      self._dbusservice['/Ac/Power'] = meter_consumption # positive: consumption, negative: feed into grid
      self._dbusservice['/Ac/L1/Voltage'] = round(meter_data['values']['voltage1']/1000)
      self._dbusservice['/Ac/L2/Voltage'] = round(meter_data['values']['voltage2']/1000)
      self._dbusservice['/Ac/L3/Voltage'] = round(meter_data['values']['voltage3']/1000)
      self._dbusservice['/Ac/L1/Current'] = round(meter_data['values']['power1']/meter_data['values']['voltage1'],2)
      self._dbusservice['/Ac/L2/Current'] = round(meter_data['values']['power2']/meter_data['values']['voltage2'],2)
      self._dbusservice['/Ac/L3/Current'] = round(meter_data['values']['power3']/meter_data['values']['voltage3'],2)
      self._dbusservice['/Ac/L1/Power'] = round(float(meter_data['values']['power1'])/1000,2)
      self._dbusservice['/Ac/L2/Power'] = round(float(meter_data['values']['power2'])/1000,2)
      self._dbusservice['/Ac/L3/Power'] = round(float(meter_data['values']['power3'])/1000,2)
      self._dbusservice['/Ac/Energy/Forward'] = round(float(meter_data['values']['power'])/1000,2)
#      self._dbusservice['/Ac/Energy/Reverse'] = float(meter_data['values']['EnergyReal_WAC_Sum_Produced'])/1000
      logging.info("House Consumption: {:.0f}".format(meter_consumption))
    except:
      logging.info("WARNING: Could not read from Discovergy Smart Meter")
      self._dbusservice['/Ac/Power'] = 0  # TODO: any better idea to signal an issue?
    # increment UpdateIndex - to show that new data is available
    index = self._dbusservice[path_UpdateIndex] + 1  # increment index
    if index > 255:   # maximum value of the index
      index = 0       # overflow from 255 to 0
    self._dbusservice[path_UpdateIndex] = index
    return True

  def _handlechangedvalue(self, path, value):
    logging.debug("someone else updated %s to %s" % (path, value))
    return True # accept the change

def main():
  logging.basicConfig(level=logging.DEBUG) # use .INFO for less logging
  thread.daemon = True # allow the program to quit

  from dbus.mainloop.glib import DBusGMainLoop
  # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
  DBusGMainLoop(set_as_default=True)

#    servicename='com.victronenergy.grid',
#    deviceinstance=10,

  pvac_output = DbusDummyService(
    servicename='com.victronenergy.grid.ttyUSB0_di32_mb1',
    deviceinstance=40,
    paths={
      '/Ac/Power': {'initial': 0},
      '/Ac/L1/Voltage': {'initial': 0},
      '/Ac/L2/Voltage': {'initial': 0},
      '/Ac/L3/Voltage': {'initial': 0},
      '/Ac/L1/Current': {'initial': 0},
      '/Ac/L2/Current': {'initial': 0},
      '/Ac/L3/Current': {'initial': 0},
      '/Ac/L1/Power': {'initial': 0},
      '/Ac/L2/Power': {'initial': 0},
      '/Ac/L3/Power': {'initial': 0},
      '/Ac/Energy/Forward': {'initial': 0}, # energy bought from the grid
      '/Ac/Energy/Reverse': {'initial': 0}, # energy sold to the grid
      path_UpdateIndex: {'initial': 0},
    })

  logging.info('Connected to dbus, and switching over to gobject.MainLoop() (= event based)')
  mainloop = gobject.MainLoop()
  mainloop.run()

if __name__ == "__main__":
  main()
