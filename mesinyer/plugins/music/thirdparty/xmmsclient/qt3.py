import qt

class XMMSConnector(qt.QObject):
	def __init__(self, parent, xmms):
		qt.QObject.__init__(self, parent)
		fd = xmms.get_fd()
		self.xmms = xmms
		self.xmms.set_need_out_fun(self.chkWr)

		self.rsock = qt.QSocketNotifier(fd, qt.QSocketNotifier.Read, self)
		self.connect(self.rsock, qt.SIGNAL("activated(int)"), self.do_read)
		self.rsock.setEnabled(False)
		
		self.wsock = qt.QSocketNotifier(fd, qt.QSocketNotifier.Write, self)
		self.connect(self.wsock, qt.SIGNAL("activated(int)"), self.do_write)
		self.wsock.setEnabled(False)

	def chkWr(self, i):
		if self.xmms.want_ioout():
			self.toggle_write(True)
		else:
			self.toggle_write(False)

	def toggle_read(self, bool):
		self.rsock.setEnabled(bool)
	
	def toggle_write(self, bool):
		self.wsock.setEnabled(bool)

	def do_read(self, i):
		self.xmms.ioin()

	def do_write(self, i):
		self.xmms.ioout()
	
