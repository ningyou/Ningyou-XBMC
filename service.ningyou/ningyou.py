import xbmc, xbmcaddon, xbmcvfs, os, sys, time
import telnetlib
import urllib, urllib2

try: import simplejson as json
except ImportError: import json

addon_id = "service.ningyou"
Addon = xbmcaddon.Addon(addon_id)
datadir = Addon.getAddonInfo('profile')
addondir = Addon.getAddonInfo('path')
url = "http://ningyou-project.org/api"

sys.path.append(xbmc.translatePath(os.path.join(addondir, 'resources', 'lib', 'ws4py')))

from ws4py.client.threadedclient import WebSocketClient

class Ningyou(WebSocketClient):
	abort = False

	def opened(self):
		xbmc.log("Ningyou: connected via websockets")

	def closed(self):
		xbmc.log("Ningyou: closed websocket")

	def API(self, method, params = []):
		data = {
			"version": 1,
			"method": method,
			"params": params,
			"token": Addon.getSetting("ningyou_token"),
		}
		data = urllib.urlencode(data, doseq=True)
		req = urllib2.Request(url, data)
		response = urllib2.urlopen(req)
		result = response.read()

		try:
			result = json.loads(result)
		except:
			result = None

		return result

	def findInList(self, id):
		if not id:
			return xbmc.log("Ningyou: ID was not passed to findInList")

		try:
			lists = self.API('getlists')
		except:
			xbmc.log("Unable to parse api response")
			return

		if lists:
			for list in lists:
				playlist = "special://profile/playlists/video/%s.xsp" % list['name']
				if xbmcvfs.exists(playlist):
					query = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"%s"},"id":1}' % playlist)
					query = unicode(query, 'utf-8', errors='ignore')
					response = json.loads(query)
					files = response['result']['files']
					if id in (obj['id'] for obj in files):
						return list['name']

	def received_message(self, message):
		data = json.loads(unicode(message))

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

					if int(show_info['episodes']) >= int(info['episode']) or show_info['status'] == "Completed":
						return xbmc.log('Ningyou: [%s] %s episode %d already marked as watched.' % (info['list'], info['tvshow'], info['episode']))

					data = self.API("updateshow", [info['list'],info['seriesid'],info['episode']])
					if data and 'error' in data:
						xbmc.log('Ningyou: Error ' + data['error'])
					elif data:
						xbmc.log('Ningyou: [%s] Updated %s to episode %d successfully' % (info['list'], info['tvshow'], info['episode']))

			elif data['method'] == 'System.OnQuit':
				self.abort = True
