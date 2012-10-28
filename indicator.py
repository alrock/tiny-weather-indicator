#!/usr/bin/env python

import sys
import urllib2
import syslog
import argparse

from xml.dom import minidom
from gi.repository import Gtk, GObject
from gi.repository import AppIndicator3 as appindicator

code2store = {
  0: 'weather-storm-symbolic',              # tornado
  1: 'weather-storm-symbolic',              # tropical storm
  2: 'weather-storm-symbolic',              # hurricane
  3: 'weather-storm-symbolic',              # severe thunderstorms
  4: 'weather-storm-symbolic',              # thunderstorms
  5: 'weather-snow-symbolic',               # mixed rain and snow
  6: 'weather-snow-symbolic',               # mixed rain and sleet
  7: 'weather-snow-symbolic',               # mixed snow and sleet
  8: 'weather-showers-scattered-symbolic',  # freezing drizzle
  9: 'weather-showers-scattered-symbolic',  # drizzle
  10: 'weather-showers-symbolic',           # freezing rain
  11: 'weather-showers-symbolic',           # showers
  12: 'weather-showers-symbolic',           # showers
  13: 'weather-snow-symbolic',              # snow flurries
  14: 'weather-snow-symbolic',              # light snow showers
  15: 'weather-snow-symbolic',              # blowing snow
  16: 'weather-snow-symbolic',              # snow
  17: 'weather-showers-symbolic',           # hail
  18: 'weather-snow-symbolic',              # sleet
  19: 'weather-fog-symbolic',               # sic! #  dust
  20: 'weather-fog-symbolic',               # foggy
  21: 'weather-fog-symbolic',               # haze
  22: 'weather-fog-symbolic',               # smoky
  23: 'weather-few-clouds-symbolic',        # blustery
  24: 'weather-few-clouds-symbolic',        # windy
  25: 'weather-clear-symbolic',             # cold
  26: 'weather-overcast-symbolic',          # cloudy
  27: 'weather-clouds-night-symbolic',      # mostly cloudy (night)
  28: 'weather-clouds-symbolic',            # mostly cloudy (day)
  29: 'weather-few-clouds-night-symbolic',  # partly cloudy (night)
  30: 'weather-few-clouds-symbolic',        # partly cloudy (day)
  31: 'weather-clear-night-symbolic',       # clear (night)
  32: 'weather-clear-symbolic',             # sunny
  33: 'weather-clear-night-symbolic',       # fair (night)
  34: 'weather-clear-symbolic',             # fair (day)
  35: 'weather-showers-symbolic',           # mixed rain and hail
  36: 'weather-clear-symbolic',             # hot
  37: 'weather-storm-symbolic',             # isolated thunderstorms
  38: 'weather-storm-symbolic',             # scattered thunderstorms
  39: 'weather-storm-symbolic',             # scattered thunderstorms
  40: 'weather-showers-scattered-symbolic', # scattered showers
  41: 'weather-snow-symbolic',              # heavy snow
  42: 'weather-snow-symbolic',              # scattered snow showers
  43: 'weather-snow-symbolic',              # heavy snow
  44: 'weather-clouds-symbolic',            # partly cloudy
  45: 'weather-storm-symbolic',             # thundershowers
  46: 'weather-snow-symbolic',              # snow showers
  47: 'weather-storm-symbolic',             # isolated thundershowers
  3200: 'weather-severe-alert-symbolic'     # not available
}

WEATHER_URL = 'http://xml.weather.yahoo.com/forecastrss?w={0!s}&u={1}'
WEATHER_NS = 'http://xml.weather.yahoo.com/ns/rss/1.0'

FAIL_LIMIT = 3

def weather_for_woeid(woeid, format = 'c'):
  url = WEATHER_URL.format(woeid, format)
  dom = minidom.parse(urllib2.urlopen(url))
  forecasts = []
  for node in dom.getElementsByTagNameNS(WEATHER_NS, 'forecast'):
      forecasts.append({
          'date': node.getAttribute('date'),
          'low': node.getAttribute('low'),
          'high': node.getAttribute('high'),
          'condition': node.getAttribute('text'),
          'code': node.getAttribute('code')
      })
  ylocation = dom.getElementsByTagNameNS(WEATHER_NS, 'location')[0]
  yunits = dom.getElementsByTagNameNS(WEATHER_NS, 'units')[0]
  ywind = dom.getElementsByTagNameNS(WEATHER_NS, 'wind')[0]
  yatmosphere = dom.getElementsByTagNameNS(WEATHER_NS, 'atmosphere')[0]
  yatmosphere = dom.getElementsByTagNameNS(WEATHER_NS, 'atmosphere')[0]
  yastronomy = dom.getElementsByTagNameNS(WEATHER_NS, 'astronomy')[0]
  ycondition = dom.getElementsByTagNameNS(WEATHER_NS, 'condition')[0]
  return {
      'city': ylocation.getAttribute('city'),
      'current_condition': ycondition.getAttribute('text'),
      'code': ycondition.getAttribute('code'),
      'current_temp': ycondition.getAttribute('temp'),
      'forecasts': forecasts,
      'title': dom.getElementsByTagName('title')[0].firstChild.data
  }

class WeatherIndicator:
  def __init__(self, woeid, format, period):
    self.ind = appindicator.Indicator.new ("ubuntu-weather-indicator",
                                    code2store[3200],
                                    appindicator.IndicatorCategory.APPLICATION_STATUS)
    self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
    self.ind.set_label('n/a', 'Current conditions is not available')
    self.ind.set_attention_icon(code2store[3200])

    self.fails = 0               # number of fails since last update
    self.woeid = woeid
    self.format = format
    self.period = period * 1000

    self.menu_setup()
    self.ind.set_menu(self.menu)
    

  def empty_menu(self):
    self.empty_menu = Gtk.Menu()

    self.quit_item = Gtk.MenuItem("Quit")
    self.quit_item.connect("activate", self.quit)
    self.quit_item.show()
    self.menu.append(self.quit_item)

    self.ind.set_menu(self.menu)

  def menu_setup(self):
    self.menu = Gtk.Menu()

    self.title_item = Gtk.MenuItem('Weather for')
    self.title_item.show()
    self.menu.append(self.title_item)

    self.separator_item = Gtk.MenuItem()
    self.separator_item.show()
    self.menu.append(self.separator_item)

    self.quit_item = Gtk.MenuItem("Quit")
    self.quit_item.connect("activate", self.quit)
    self.quit_item.show()
    self.menu.append(self.quit_item)

  def main(self):
    self.check_weather()
    Gtk.main()

  def quit(self, widget):
    sys.exit(0)

  def check_weather(self):
    try:
      w = weather_for_woeid(self.woeid, self.format)

      self.ind.set_icon(code2store[int(w['code'])])
      self.ind.set_label(u' {0}\xB0'.format(w['current_temp']), 'Current conditions')
      #self.title_item.set_text('Weather for {}', w['city'])
      self.fails = 0
    except urllib2.URLError as e:
      self.fails = self.fails + 1
      if self.fails > FAIL_LIMIT:
        self.ind.set_status(appindicator.IndicatorStatus.ATTENTION)
      syslog.syslog(syslog.LOG_ERR, "Can't retrieve data: {}".format(e.reason))

    GObject.timeout_add(self.period, self.check_weather)


def valid_periodicity(string):
  try:
    value = int(string)
    if value < 60 or value > 18000:
      raise argparse.ArgumentTypeError('invalid choice: {0!r} (choose from 60 to 18000)'.format(string))
  except ValueError:
    msg = 'invalid int value: {0!r}'.format(string)
    raise argparse.ArgumentTypeError(msg)
  return value

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='simple ubuntu weather indicator')
  parser.add_argument('woeid', type=int, help='where on earth identifier')
  parser.add_argument('-f', '--format', choices=['f', 'c'], default='c',
                      help='units for temperature (f: Fahrenheit; c: Celsius)')
  parser.add_argument('-p', '--period', type=valid_periodicity, 
                      default=60*5, help='update periodicity in seconds')
  args = parser.parse_args()

  indicator = WeatherIndicator(args.woeid, args.format, args.period)
  indicator.main()
