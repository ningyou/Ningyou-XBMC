#!/usr/bin/env python
import xbmc, xbmcgui, xbmcaddon, os, sys
import urllib, urllib2
from hashlib import sha256
try: import simplejson as json
except ImportError: import json

url = "http://ningyou-project.org/api"
addon_id = "service.ningyou"
Addon = xbmcaddon.Addon(addon_id)

def authorize():
	data = {
		"version":1,
		"method":"requesttoken",
		"params":[Addon.getSetting("ningyou_username"),sha256(Addon.getSetting("ningyou_password")).hexdigest(),"Ningyou-XBMC"],
	}
	data = urllib.urlencode(data, doseq=True)
	req = urllib2.Request(url, data)
	response = urllib2.urlopen(req)
	data = response.read()
	data = json.loads(data)
	if 'error' in data:
		xbmc.log("ERROR: " + data['error'])
	else:
		Addon.setSetting("ningyou_token", data['token'])
		print data['token']
		return data['token']

if ( __name__ == "__main__" ):
	authorize()
