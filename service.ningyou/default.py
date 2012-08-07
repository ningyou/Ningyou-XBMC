#!/usr/bin/env python
import xbmc, xbmcgui, xbmcaddon, os, sys
from ningyou import Ningyou

xbmc.log("Ningyou updater is starting...")
Ningyou().run()
