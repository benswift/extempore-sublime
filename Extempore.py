import sublime, sublime_plugin
import socket

SETTINGS_FILE = 'Extempore.sublime-settings'
EXTEMPORE_SOCKETS = {}

# currently, the host and port are hardcoded
# h, p = host_str.split(':')
# self.window.show_input_panel("Specify host:port", "localhost:7099", self.on_done, None, None)

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

class ExtemporeConnectCommand(sublime_plugin.TextCommand):
	"""Connect to a running Extempore server"""
	def run(self, edit):
		if not is_currently_connected(self.view):		
			self.connect(('localhost', 7099))

	def connect(self, host):
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.settimeout(5)
			s.connect(host)
			data = s.recv(1024)
			sublime.status_message(data)
			# add this socket to the global socket dict
			set_extempore_socket(self.view, s)
		except socket.error as e:
			sublime.status_message("Unable to connect to Extempore server: " + repr(e))
			return None

	def disconnect(self):
			try:
				s = get_extempore_socket(self.view)
				s.close()
				sublime.status_message("Closed connection to Extempore server")
			except socket.error as e:
				sublime.status_message("Unable to disconnect: " + repr(e))

class ExtemporeEvaluateCommand(sublime_plugin.TextCommand):
	"""Send the current defn/region to the Extempore server for evaluation"""
	def __init__(self, view):
		sublime_plugin.TextCommand.__init__(self, view)

	def send_string_for_eval(self, string):
		try:
			s = get_extempore_socket(self.view)
			s.send(string + '\r\n')
			return s.recv(1024)
		except KeyError:
			sublime.status_message("Error: cannot find an Extempore connection for this view")
		except socket.error as e:
			sublime.status_message("Error in connection to Extempore server: " + repr(e))

# todo for tomorrow: I think this function should return a string, and then leave the point where it finds it (save it, then clear it, then add it with view.sel().add(sublime.Region(pos)))

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

		if v.sel()[0].empty():
			# if no region highlighted, select the current 'top level' defun, otherwise just use the current selection
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
