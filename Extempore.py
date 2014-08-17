import sublime, sublime_plugin
import os, socket, threading, errno, time

SETTINGS_FILE = 'Extempore.sublime-settings'
DEFAULT_HOST = 'localhost:7099'

#Print to both the console and the status bar
def notify(message):
	sublime.set_timeout(lambda: sublime.status_message(message), 1)
	print(message)

class Listener(threading.Thread):

	running = 1

	def run(self):
		print("Started listening thread")
		while self.running:
			try:
				data = self.socket.recv(4096)
				if data:
					notify(data.partition(b'\0')[0].decode("UTF-8"))
			except socket.error as e:
				if e.errno == errno.EBADF or e.errno == errno.ECONNRESET: #socket has been closed
					self.running = 0
				elif os.name == 'nt' and (e.errno == errno.WSAECONNRESET or e.errno == errno.ERROR_PORT_UNREACHABLE): #windows connection forcibly closed
					self.running = 0
				else:
					notify("Polling failed: %s" % e)
			time.sleep(0.1)
		print("Terminated listening thread")

	def set_socket(self, socket):
		self.socket = socket

	def notify_stop(self):
		self.running = 0

class ListenerWrapper(object):

	def __init__(self, socket):
		self.listener = Listener()
		self.listener.setDaemon(True)
		self.listener.set_socket(socket)
		self.listener.start()

	def __del__(self):
		self.listener.notify_stop()

#Defines a single extempore connection
class ExtemporeConnection(object):

	socket = None

	def evaluate(self, code):
		try:
			if(self.socket is None):
				notify("Evaluation failed: not connected")
				return
			self.socket.send((code + '\r\n').encode())
			return
		except socket.error as e:
			notify("Evaluation failed: %s" % e)
			return

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
			self.socket.connect(host)
			self.listener = ListenerWrapper(self.socket)
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
			if(self.socket is None or self.listener is None):
				notify("Disconnection failed: not connected")
				return
			self.listener = None
			self.socket.close()
			self.socket = None
			
			notify("Disconnection success")
			return
		except socket.error as e:
			notify("Disconnection failed: %s" % e)

#Dictionary for a number of extempore connections
class ExtemporeConnectionSet(dict):

	def add(self, view_id, host_str):
		if view_id in self:
			if host_str in self[view_id]:
				self[view_id][host_str].connect(host_str)
				self.print_connections()
				return
		connection = ExtemporeConnection()
		connection.connect(host_str)
		
		if view_id in self:
			self[view_id][host_str] = connection
		else:
			self[view_id] = {}
			self[view_id][host_str] = connection
		self.print_connections()

	def remove(self, view_id):
		if view_id in self:
			for key, value in self[view_id].items():
				value.disconnect()

			del self[view_id]
		self.print_connections()

	def remove_all(self):
		if not self:
			notify("Disconnection failed: not connected")
			return
		for view_key, view_value in self.items():
			for key, value in view_value.items():
				value.disconnect()
		self.clear()
		self.print_connections()

	def print_connections(self):
		connection_strs = []
		for v in self.keys():
			connection_str = str(v) + ": {" + ", ".join(self[v].keys()) + "}"
			connection_strs.append(connection_str)
		result = "Connections: {" + ", ".join(connection_strs) + "}"
		print(result)


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
			print (self.hosts[idx])
			self.connect_view_to_host(self.hosts[idx][0])

	def display_input_panel(self):
		self.view.window().show_input_panel("Specify 'host:port' to connect to:", DEFAULT_HOST, self.connect_view_to_host, None, None)

	def connect_view_to_host(self, host_str):
		connections.add(self.view.id(), host_str)

#Disconnects all connections
class ExtemporeDisconnectCommand(sublime_plugin.TextCommand):

	def run(self, edit):
		connections.remove_all()

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
			self.highlight(v.sel())

		# send the region to the Extempore server for evaluation
		try:
			if self.view.id() in connections:
				for k in connections[self.view.id()].keys():
					response = connections[self.view.id()][k].evaluate(eval_str)
			else:
				notify("Evaluation failed: not connected")
		except TypeError as e:
			notify("Evaluation failed: Type error. %s" % e)
		except socket.error as e:
			notify("Evaluation failed: Socket error. %s" % e)

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

		self.highlight(v.sel())

		# return the point to where it was
		v.sel().clear()
		v.sel().add(initial_reg)
		return def_str

	def highlight(self, regions):
		v = self.view
		v.add_regions("ExtemporeEvaluate", [regions[0]], "string", "", False * sublime.DRAW_OUTLINED)
		sublime.set_timeout(lambda: v.erase_regions("ExtemporeEvaluate"), 200)# Note that this will clear all existing regions with the given key. Will fail to clear correctly when called twice quickly

