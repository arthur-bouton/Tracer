#!/usr/bin/python
#-*- coding: utf-8 -*-
#
# tracer-qt4.py
#
#    Copyright (C) 2014 Arthur Bouton
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    The author of this code can be contacted at arthur.bouton@gadz.org
#    Any contact about this application is warmly welcomed.
#
from PyQt4 import QtGui
from PyQt4 import QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar2
from tracer import Tracer, import_TracerToolbar
TracerToolbar = import_TracerToolbar( NavigationToolbar2 )
import sys
reload( sys )
sys.setdefaultencoding( 'utf8' )
import os


class QTracerWindow( QtGui.QMainWindow ) :

	def __init__( self, tracer, parent=None ) :
		super( QTracerWindow, self ).__init__( parent )

		self.tracer = tracer

		# PARAMÈTRES DE LA FENÊTRE :

		self.setWindowTitle( self.tracer.window_title )
		self.setWindowIcon( QtGui.QIcon.fromTheme( 'utilities-system-monitor' ) )

		if self.tracer.x is not None or self.tracer.y is not None :
			self.move( self.tracer.x, self.tracer.y )
		self.resize( self.tracer.w, self.tracer.h )

		# DÉFINITION DE L'AGENCEMENT :

		self.canvas = FigureCanvas( self.tracer.fig )
		self.setCentralWidget( self.canvas )

		self.toolbar = TracerToolbar( self.canvas, self, self.tracer, self.save_window, self.get_band_n_rate )
		self.addToolBar( QtCore.Qt.BottomToolBarArea, self.toolbar )
		#QtCore.QObject.connect( self.toolbar, QtCore.SIGNAL( "message" ), self.statusBar().showMessage )

		# GESTION DES ÉVÉNEMENTS :

		self.canvas.setFocusPolicy( QtCore.Qt.StrongFocus )
		self.canvas.setFocus()
		self.canvas.mpl_connect( 'key_press_event', self.on_key )

		self.show()


	def on_key( self, event ) :
		
		if event.key == 'f' :
			if self.isFullScreen() :
				self.showNormal()
			else :
				self.showFullScreen()
		elif event.key == 'ctrl+w' :
			self.destroy()
		else :
			self.toolbar.tracer_key_handler( event )


	def save_window( self ) :

		filename = QtGui.QFileDialog.getSaveFileName( self, 'File for data saving', os.getcwd(), 'Text files (*.txt)' )
		if filename :
			try :
				return open( filename, 'wb' )
			except IOError as e :
				QtGui.QMessageBox.critical( self, 'Error', 'Unable to open the file %s :\n%s' % ( filename, e.strerror ) )
		return None

	
	def get_band_n_rate( self, newband, newrate ) :
		return self.BandAndRateWindow.get_band_n_rate( newband, newrate, self )


	class BandAndRateWindow( QtGui.QDialog ) :

		def __init__( self, oldband, oldrate, parent=None ) :
			super( QTracerWindow.BandAndRateWindow, self ).__init__( parent )

			self.setWindowTitle( 'Change band and rate' )
			self.setWindowIcon( QtGui.QIcon.fromTheme( 'utilities-system-monitor' ) )

			band_label = QtGui.QLabel( 'Band :' )
			rate_label = QtGui.QLabel( 'Rate :' )

			self.band_entry = QtGui.QLineEdit()
			if oldband is not None :
				self.band_entry.setText( str( oldband ) )
			#self.band_entry.setInputMask( '99999' )

			self.rate_entry = QtGui.QLineEdit()
			self.rate_entry.setText( str( oldrate ) )
			#self.rate_entry.setInputMask( '9.999999' )

			buttons = QtGui.QDialogButtonBox( QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self )
			buttons.accepted.connect( self.accept )
			buttons.rejected.connect( self.reject )

			grid = QtGui.QGridLayout()
			grid.addWidget( band_label, 0, 0 )
			grid.addWidget( rate_label, 1, 0 )

			grid.addWidget( self.band_entry, 0, 1 )
			grid.addWidget( self.rate_entry, 1, 1 )

			grid.addWidget( buttons, 4, 1 )

			self.setLayout( grid )

		@staticmethod
		def get_band_n_rate( oldband, oldrate, parent = None ) :
			popup = QTracerWindow.BandAndRateWindow( oldband, oldrate, parent )
			accepted = popup.exec_()
			newband, newrate = popup.band_entry.text(), popup.rate_entry.text()
			if accepted == QtGui.QDialog.Accepted :
				try :
					if len( newband ) != 0 :
						int( newband )
					float( newrate )
				except ValueError :
					QtGui.QMessageBox.critical( parent, 'Error', 'Bad entry !' )
			return accepted == QtGui.QDialog.Accepted, newband, newrate


if __name__ == '__main__' :

	main_tracer = Tracer()
	main_tracer.run( show=False )

	app = QtGui.QApplication( sys.argv )

	main_window = QTracerWindow( main_tracer )

	sys.exit( app.exec_() )
