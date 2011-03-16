from xml.dom.minidom import Document
import sqlite3.dbapi2 as sqlite

class synch(object):

        def __init__(self):
            pass

        def start_synch(self, session, synch_function=None):
	    self.__session = session

        def set_source_path(self,path):
	    self.__srcpath=path
	    print path

        def set_destination_path(self,path):
            self.__destpath=path
            print path

        @property
        def dest_path(self):
            return self.__destpath

        @property
        def src_path(self):
            return self.__srcpath
