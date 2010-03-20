"""

 A GLib connector for PyGTK - 
	to use with your cool PyGTK xmms2 client.
 Tobias Rundstrom <tru@xmms.org)

 Just create the GLibConnector() class with a xmmsclient as argument

"""

import gobject

class GLibConnector:
	def __init__(self, xmms):
		self.xmms = xmms
		xmms.set_need_out_fun(self.need_out)
		gobject.io_add_watch(self.xmms.get_fd(), gobject.IO_IN, self.handle_in)
		self.has_out_watch = False

	def need_out(self, i):
		if self.xmms.want_ioout() and not self.has_out_watch:
			gobject.io_add_watch(self.xmms.get_fd(), gobject.IO_OUT, self.handle_out)
			self.has_out_watch = True

	def handle_in(self, source, cond):
		if cond == gobject.IO_IN:
			return self.xmms.ioin()

		return True

	def handle_out(self, source, cond):
		if cond == gobject.IO_OUT:
			self.xmms.ioout()
		self.has_out_watch = self.xmms.want_ioout()
		return self.has_out_watch

