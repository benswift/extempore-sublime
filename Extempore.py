import sublime, sublime_plugin
import socket

SETTINGS_FILE = 'Extempore.sublime-settings'
EXTEMPORE_SOCKETS = {}

def get_extempore_socket(current_view):
	return EXTEMPORE_SOCKETS[current_view.id()]

def is_currently_connected(current_view):
	try:
		get_extempore_socket(current_view)
		return True
	except KeyError:
		return False

def set_extempore_socket(current_view, sock):
	if current_view.id() in EXTEMPORE_SOCKETS:
		sublime.status_message("This view is already connected to Extempore")
	else:
		EXTEMPORE_SOCKETS[current_view.id()] = sock

def delete_extempore_socket(current_view):
	try:
		del EXTEMPORE_SOCKETS[current_view.id()]
	except KeyError:
		sublime.status_message("No connection found for current view.")

class ExtemporeConnectCommand(sublime_plugin.TextCommand):
	"""Connect to a running Extempore server"""
	default_host = 'localhost:7099'

	def run(self, edit):
		if not is_currently_connected(self.view):
			settings = sublime.load_settings(SETTINGS_FILE)
			if settings.has('hosts'):
				print settings.get('hosts')
				self.view.window().show_quick_panel(settings.get('hosts'), self.host_selection_handler)
			else:
				self.view.window().show_input_panel("Specify 'host:port' to connect to:", self.default_host, self.connect, None, None)
			self.connect('localhost')
		else:
			sublime.status_message("This view is already connected to Extempore, you can evaluate code with 'ctrl+x, ctrl+x'")

	def host_selection_handler(self, idx):
		if idx == -1:
			self.view.window().show_input_panel("Specify 'host:port' to connect to:", self.default_host, self.connect, None, None)
		else:
			self.connect(self.default_host)

	def connect(self, host_str):
		try:
			# parse the host:port string
			h, p = host_str.split(':')
			host = (h, int(p))
			# set up the socket
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.settimeout(1.0)
			s.connect(host)
			data = s.recv(1024)
			sublime.status_message(data)
			# add this socket to the global socket dict
			set_extempore_socket(self.view, s)
		except ValueError:
			sublime.status_message("Error in to host:port string")
		except socket.error as e:
			sublime.status_message("Unable to connect to Extempore server: " + repr(e))
			return None

class ExtemporeDisconnectCommand(sublime_plugin.TextCommand):
	"""Delete the current view's connection to the Extempore server"""

	def run(self, edit):
		try:
			s = get_extempore_socket(self.view)
			s.close()
			sublime.status_message("Closed connection to Extempore server")
			delete_extempore_socket(self.view)
		except socket.error as e:
			sublime.status_message("Unable to disconnect: " + e.message)

class ExtemporeEvaluateCommand(sublime_plugin.TextCommand):
	"""Send the current defn/region to the Extempore server for evaluation"""

	def __init__(self, view):
		sublime_plugin.TextCommand.__init__(self, view)

	def send_string_for_eval(self, string):
		try:
			s = get_extempore_socket(self.view)
			s.send(string + '\r\n')
			return s.recv(4096)
		except KeyError:
			sublime.status_message("Error: cannot find an Extempore connection for this view")
		except socket.error as e:
			sublime.status_message("Error in connection to Extempore server: " + repr(e))

	def toplevel_def_string(self):
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

	def run(self, edit):
		v = self.view
		# if no region highlighted, select the current 'top level' defun, otherwise just use the current selection
		if v.sel()[0].empty():
			eval_str = self.toplevel_def_string()
		else:
			eval_str = v.substr(v.sel()[0])
		# send the region to the Extempore server for evaluation
		try:
			response = self.send_string_for_eval(eval_str)
			sublime.status_message(response)
		except TypeError as e:
			sublime.status_message("")
		except socket.error as e:
			sublime.status_message("No response from socket: {1}".format(e))
