import xbmc, xbmcaddon, xbmcvfs, os, sys, time
import telnetlib
import urllib, urllib2
import threading

try: import simplejson as json
except ImportError: import json

class Ningyou(threading.Thread):
	addon_id = "service.ningyou"
	Addon = xbmcaddon.Addon(addon_id)
	datadir = Addon.getAddonInfo('profile')
	addondir = Addon.getAddonInfo('path')
	url = "http://ningyou-project.org/api"
	abort = False

	def API(self, method, params = []):
		data = {
			"version": 1,
			"method": method,
			"params": params,
			"token": self.Addon.getSetting("ningyou_token"),
		}
		data = urllib.urlencode(data, doseq=True)
		req = urllib2.Request(self.url, data)
		response = urllib2.urlopen(req)
		result = response.read()

		try:
			result = json.loads(result)
		except:
			result = None

		return result

	def findInList(self, id):
		lists = self.API('getlists')
		if lists:
			for list in lists:
				playlist = "special://videoplaylists/%s.xsp" % list['name']
				if xbmcvfs.exists(playlist):
					query = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"%s"},"id":1}' % playlist)
					query = unicode(query, 'utf-8', errors='ignore')
					response = json.loads(query)
					files = response['result']['files']

					if id in (obj['id'] for obj in files):
						return list['name']

	def handleMessage(self, message):
		data = json.loads(message)
		if 'method' in data and 'params' in data and 'sender' in data['params'] and data['params']['sender'] == 'xbmc':
			if data['method'] == 'VideoLibrary.OnUpdate' and data['params']['data']['item']['type'] == 'episode':
				episodeid = data['params']['data']['item']['id']
				query = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"VideoLibrary.GetEpisodeDetails","params":{"properties":["tvshowid", "playcount", "episode"],"episodeid":%d}, "id":1}' % episodeid)
				query = unicode(query, 'utf-8', errors='ignore')
				response = json.loads(query)
				info = response['result']['episodedetails']

				query = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"VideoLibrary.GetTVShowDetails","params":{"properties":["imdbnumber"],"tvshowid":%d}, "id":1}' % info['tvshowid'])
				query = unicode(query, 'utf-8', errors='ignore')
				response = json.loads(query)
				info['seriesid'] = response['result']['tvshowdetails']['imdbnumber']
				info['tvshow'] = response['result']['tvshowdetails']['label']
				info['list'] = self.findInList(info['tvshowid'])
				if info['list'] and info['playcount'] > 0:
					show_info = self.API('getshow', [info['list'],info['seriesid']])

					if not show_info:
						return xbmc.log('Ningyou: Bad or no response from server')

					if 'error' in show_info:
						return xbmc.log('Ningyou: Error ' + show_info['error'])

					if show_info['episodes'] >= info['episode'] or show_info['status'] == "Completed":
						return xbmc.log('Ningyou: [%s] %s episode %d already marked as watched.' % (info['list'], info['tvshow'], info['episode']))

					data = self.API("updateshow", [info['list'],info['seriesid'],info['episode']])
					if data and 'error' in data:
						xbmc.log('Ningyou: Error ' + data['error'])
					elif data:
						xbmc.log('Ningyou: [%s] Updated %s to episode %d successfully' % (info['list'], info['tvshow'], info['episode']))

			elif data['method'] == 'System.OnQuit':
				self.abort = True

	def run(self):
		while(not (xbmc.abortRequested or self.abort)):
			time.sleep(1)
			try:
				tn = telnetlib.Telnet('localhost', 9090, 10)
			except IOError as (errno, strerror):
				#connection failed, try again soon
				xbmc.log("Ningyou: Telnet too soon? ("+str(errno)+") "+strerror)
				time.sleep(1)
				continue

			bCount = 0
			xbmc.log("Ningyou: connected.")

			while(not (xbmc.abortRequested or self.abort)):
				try:
					if bCount == 0:
						notification = ""
						inString = False
					[index, match, raw] = tn.expect(["(\\\\)|(\\\")|[{\"}]"], 0.2) #note, pre-compiled regex might be faster here
					notification += raw
					if index == -1: # Timeout
						continue
					if index == 0: # Found escaped quote
						match = match.group(0)
						if match == "\"":
							inString = not inString
							continue
						if match == "{":
							bCount += 1
						if match == "}":
							bCount -= 1
					if bCount > 0:
						continue
					if bCount < 0:
						bCount = 0
				except EOFError:
					break #go out to the other loop to restart the connection

				self.handleMessage(notification)

		try:
			tn.close()
		except:
			xbmc.log("Ningyou: Encountered error attempting to close the telnet connection")
			raise
		xbmc.log('Ningyou: exiting')
		sys.exit(0)
