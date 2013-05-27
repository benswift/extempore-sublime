import sublime, sublime_plugin
import socket

# a dict (of sockets) for keeping track of all the connections
EXTEMPORE_CONNECTIONS = {}

class ExtemporeConnectCommand(sublime_plugin.WindowCommand):
	"""Connect to a running Extempore server"""
	host = None

	def run(self):
		if self.window.active_view().id() not in EXTEMPORE_CONNECTIONS:
			# self.window.show_input_panel("Specify host:port", "localhost:7099", self.get_host, None, None)
			self.connect(('localhost', 7099))

	def get_host(self, hoststring):
		h, p = hoststring.split(':')
		self.host = (h, int(p))

	def connect(self, host):
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.settimeout(5)
			sock.connect(host)
			data = sock.recv(1024)
			sublime.status_message(data)
			# add the socket to the global connections dict
			EXTEMPORE_CONNECTIONS[self.window.active_view().id()] = sock
		except socket.error, e:
			sublime.status_message("Unable to connect to Extempore server: " + repr(e))
			return None

class ExtemporeDisconnectCommand(sublime_plugin.WindowCommand):
	"""Disconnect from the Extempore server"""
	def run(self, edit):
		view_id = self.window.active_view().id()
		if view_id in EXTEMPORE_CONNECTIONS:
			try:
				EXTEMPORE_CONNECTIONS[view_id].close()
				sublime.status_message("Closed connection to Extempore server")
			except socket.error, e:
				print repr(e)

class ExtemporeEvaluateCommand(sublime_plugin.TextCommand):
	"""Send the current defn/region to the Extempore server for evaluation"""
	# def __init__(self, view):
	# 	sublime_plugin.TextCommand.__init__(self, view)

	def defun_bounds(self):
		# todo implement this!
		pass

	def send(self, sock, string):
		sock.send(string + '\r\n')
		return sock.recv(1024)
		
	def run(self, edit):
		sels = self.view.sel()
		sock = ExtemporeServerConnection.s

		if not sock:
			sublime.status_message("Not currently connected, trying to connect...")
			self.view.run_command('extempore_connect')
			sock = ExtemporeServerConnection.s

		if sock:
			for sel in sels:
				string = self.view.substr(sel)
				if len(string) > 0:
					try:
						response = self.send(sock,string)
						sublime.status_message(response)
						self.view.sel().clear()
					except Exception, e:
						sublime.status_message("No response from socket")
		else:
			sublime.error_message("Error: no available for Extempore connection")

