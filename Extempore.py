import sublime, sublime_plugin
import socket

SETTINGS_FILE = 'Extempore.sublime-settings'
DEFAULT_HOST = 'localhost:7099'

#Print to both the console and the status bar
def notify(string):
	sublime.status_message(string)
	print(string)

#Defines a single extempore connection
class ExtemporeConnection(object):

	socket = None

	def evaluate(self, string):
		try:
			if(self.socket is None):
				notify("Evaluation failed: not connected")
				return
			self.socket.send(string + '\r\n')
			notify("Response:" + repr(self.socket.recv(4096)))
			return
		except socket.error as e:
			notify("Evaluation failed: %s" % e)
			return
		notify("Evaluation success")

	def connect(self, host_str):
		#cleaning up old socket
		if(self.socket is not None):
			try:
				self.socket.close()
			except socket.error:
				pass
			self.socket = None

		try:
			# parse the host:port string
			h, p = host_str.split(':')
			host = (h, int(p))
			# set up the socket
			self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.socket.settimeout(2.0)
			self.socket.connect(host)
			data = self.socket.recv(1024)
		except ValueError:
			notify("Connection failed: host:port string invalid")
			return
		except socket.error as e:
			self.socket = None
			notify("Connection failed: %s" % e)
			return
		notify("Connection success")

	def disconnect(self):
		try:
			if(self.socket is None):
				notify("Disconnection failed: not connected")
				return
			self.socket.close()
			self.socket = None
			notify("Disconnection success")
			return
		except socket.error as e:
			notify("Disconnection failed: %s" % e)

#Dictionary for a number of extempore connections
class ExtemporeConnectionSet(dict):

	def add(self, view, host_str):
		if view in self:
			if host_str in self[view]:
				self[view][host_str].connect(host_str)
				self.print_connections()
				return
		connection = ExtemporeConnection()
		connection.connect(host_str)
		
		if view in self:
			self[view][host_str] = connection
		else:
			self[view] = {}
			self[view][host_str] = connection
		self.print_connections()

	def remove(self, view):
		if view in self:
			for i in self[view].keys():
				self[view][i].disconnect()

			del self[view]
		self.print_connections()

	def remove_all(self):
		for k in self.keys():
			self.remove(k)

	def print_connections(self):
		strings = []
		for v in self.keys():
			string = str(v.id()) + ": {" + ", ".join(self[v].keys()) + "}"
			strings.append(string)
		result = "Connections: {" + ", ".join(strings) + "}"
		print result


connections = ExtemporeConnectionSet()

#Connects to the specified host.
class ExtemporeConnectCommand(sublime_plugin.TextCommand):

	hosts = []

	def run(self, edit):
		settings = sublime.load_settings(SETTINGS_FILE)
		if settings.has('hosts'):
			self.hosts = settings.get('hosts')
			self.hosts.append("Other");
			self.view.window().show_quick_panel(self.hosts, self.host_selection_handler)
		else:
			self.display_input_panel()

	def host_selection_handler(self, idx):
		if idx == -1:
			return
		if self.hosts[idx] == "Other":
			self.display_input_panel()
		else:
			print self.hosts[idx]
			self.connect_view_to_host(self.hosts[idx][0])

	def display_input_panel(self):
		self.view.window().show_input_panel("Specify 'host:port' to connect to:", DEFAULT_HOST, self.connect_view_to_host, None, None)

	def connect_view_to_host(self, host_str):
		connections.add(self.view, host_str)

#Disconnects all connections
class ExtemporeDisconnectCommand(sublime_plugin.TextCommand):

	def run(self, edit):
		connections.remove_all(self.view)

#Evaluates the selection or the top-level definition
class ExtemporeEvaluateCommand(sublime_plugin.TextCommand):

	def __init__(self, view):
		sublime_plugin.TextCommand.__init__(self, view)

	def run(self, edit):

		v = self.view
		# if no region highlighted, select the current 'top level' defun, otherwise just use the current selection
		if v.sel()[0].empty():
			eval_str = self.get_top_level_definition()
		else:
			eval_str = v.substr(v.sel()[0])
		# send the region to the Extempore server for evaluation
		try:
			if self.view in connections:
				for k in connections[self.view].keys():
					print k
					response = connections[self.view][k].evaluate(eval_str)
			else:
				notify("Evaluation failed: not connected")
		except TypeError as e:
			notify("Evaluation failed: type error")
		except socket.error as e:
			notify("Evaluation failed: %s" % e)

	def get_top_level_definition(self): 
		v = self.view
		v.run_command("single_selection")
		initial_reg = v.sel()[0]
		reg = initial_reg
		old_reg = None
		# loop until the region stabilises or starts at the beginning of a line
		while reg != old_reg and v.rowcol(reg.a)[1] != 0:
			v.run_command("expand_selection", {"to": "brackets"})
			old_reg = reg
			reg = v.sel()[0]
		def_str = v.substr(v.sel()[0])
		# return the point to where it was
		v.sel().clear()
		v.sel().add(initial_reg)
		return def_str


