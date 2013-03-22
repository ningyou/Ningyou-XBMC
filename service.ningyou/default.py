#!/usr/bin/env python
import xbmc, xbmcgui, xbmcaddon, os, sys
from ningyou import Ningyou

xbmc.log("Ningyou updater is starting...")
ws = Ningyou('ws://localhost:9090/jsonrpc')

while(not (xbmc.abortRequested or ws.abort)):
	try:
		ws.connect()
		ws._th.join()
	except:
		xbmc.log("Ningyou: failed to connect")
		continue

try:
	print "Closing"
	ws.close()
except:
	xbmc.log("Ningyou: failed to close websocket")
	raise
