import sublime, sublime_plugin
import socket

class ExtemporeServerConnection:
	"""A class representing a TCP connection to the Extempore server"""
	# a dict for keeping track of all the connections
	EXTEMPORE_CONNECTIONS = {}
	def __init__(self, host='localhost', port=7099):
		self.host = host
		self.port = port
		self.sock = None
	def create_socket():
		try:
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.sock.settimeout(5)
			self.sock.connect((self.host, self.port))
			data = ExtemporeServerConnection.sock.recv(1024)
			sublime.status_message(data)
		except socket.error, e:
			sublime.status_message("Unable to connect to Extempore server: " + repr(e))
			return None
	def close_socket():
		try:
			self.sock.close()
			sublime.status_message("Closed connection to Extempore server")
		except socket.error, e:
			print repr(e)

class ExtemporeConnectCommand(sublime_plugin.TextCommand):
	"""Connect to a running Extempore server at localhost:7099"""
	def run(self,edit):
		if extemore_connection_dict[view.id()]
		# how do I check if there's an element there, and add one if not?
		try:
			ExtemporeServerConnection.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			ExtemporeServerConnection.s.settimeout(5)
			ExtemporeServerConnection.s.connect((ExtemporeServerConnection.hostname, ExtemporeServerConnection.port))
			data = ExtemporeServerConnection.s.recv(1024)
			sublime.status_message(data)
		except socket.error, e:
			sublime.status_message("Unable to connect to Extempore server")
			return None

class ExtemporeDisconnectCommand(sublime_plugin.TextCommand):
	"""Disconnect from the Extempore server"""
	def run(self, edit):
		view.extempore_connect()

class ExtemporeEvaluateCommand(sublime_plugin.TextCommand):
	"""Send the current defn/region to the Extempore server for evaluation"""
	def __init__(self, view):
		sublime_plugin.TextCommand.__init__(self, view)

	def send(self, sock, string):
		count = sock.send(string + '\r\n')
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

