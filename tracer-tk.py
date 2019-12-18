#!/usr/bin/python3
#
# tracer-tk.py
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
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from tracer import Tracer, import_TracerToolbar
TracerToolbar = import_TracerToolbar( NavigationToolbar2Tk )
import os


class TkTracerWindow() :

	def __init__( self, window, tracer ) :

		self.window = window

		self.tracer = tracer

		# PARAMÈTRES DE LA FENÊTRE :

		window.title( self.tracer.window_title )

		if self.tracer.x is not None or self.tracer.y is not None :
			window.geometry( '%+i%+i' % ( self.tracer.x, self.tracer.y ) )
		window.geometry( '%ix%i' % ( self.tracer.w, self.tracer.h ) )

		# DÉFINITION DE L'AGENCEMENT :

		self.canvas = FigureCanvas( self.tracer.fig, self.window )
		self.toolbar = TracerToolbar( self.canvas, self.window, self.tracer, self.save_window, self.get_band_n_rate )
		self.canvas._tkcanvas.pack( side=tk.TOP, fill=tk.BOTH, expand=1 )

		# GESTION DES ÉVÉNEMENTS :

		self.canvas.mpl_connect( 'key_press_event', self.on_key )

		def destroy( *args ) :
			self.window.quit()
		self.canvas._tkcanvas.bind( "<Destroy>", destroy )

		self.canvas.draw()


	def on_key( self, event ) :
		
		if event.key == 'f' :
			is_fullscreen = bool( self.window.attributes( '-fullscreen' ) )
			self.window.attributes( '-fullscreen', not is_fullscreen )
		elif event.key == 'ctrl+w' :
			self.window.quit()
		else :
			self.toolbar.tracer_key_handler( event )
	

	def save_window( self ) :

		filename = filedialog.asksaveasfilename( title='File for data saving', initialdir=os.getcwd() )
		if filename :
			try :
				return open( filename, 'w' )
			except IOError as e :
				messagebox.showerror( 'Error', 'Unable to open the file %s :\n%s' % ( filename, e.strerror ) )
		return None

	
	def get_band_n_rate( self, newband, newrate ) :
		return self.BandAndRateWindow.get_band_n_rate( newband, newrate, self.window )


	class BandAndRateWindow() :

		def __init__( self, oldband, oldrate, parent=None ) :

			self.accepted = False

			self.band_value = str( oldband )
			self.rate_value = str( oldrate )

			self.window = tk.Toplevel( parent )
			self.window.title( 'Change band and rate' )

			self.window.protocol( 'WM_DELETE_WINDOW', self.close )

			tk.Label( self.window, text="Band :" ).grid( row=0 )
			tk.Label( self.window, text="Rate :" ).grid( row=1 )

			self.band_entry = tk.Entry( self.window )
			if oldband is not None :
				self.band_entry.insert( 0, self.band_value )
			self.rate_entry = tk.Entry( self.window )
			self.rate_entry.insert( 0, self.rate_value )

			self.band_entry.grid( row=0, column=1, columnspan=2 )
			self.rate_entry.grid( row=1, column=1, columnspan=2 )

			tk.Button( self.window, text='Accept', command=self.accept ).grid( row=3, column=1, pady=4 )
			tk.Button( self.window, text='Cancel', command=self.close ).grid( row=3, column=2, pady=4 )

			self.window.bind( "<Return>", self.accept )

		def close( self ) :
			self.band_value, self.rate_value = self.band_entry.get(), self.rate_entry.get()
			self.window.destroy()

		def accept( self, event=None ) :
			self.accepted = True
			self.close()

		@staticmethod
		def get_band_n_rate( oldband, oldrate, parent = None ) :
			popup = TkTracerWindow.BandAndRateWindow( oldband, oldrate, parent )
			popup.window.grab_set()
			popup.window.wait_window( popup.window )
			if popup.accepted :
				try :
					if len( popup.band_value ) != 0 :
						int( popup.band_value )
					float( popup.rate_value )
				except ValueError :
					messagebox.showerror( 'Error', 'Bad entry !' )
			return popup.accepted, popup.band_value, popup.rate_value


if __name__ == '__main__' :

	main_tracer = Tracer()
	main_tracer.run( show=False )

	app = tk.Tk()

	main_window = TkTracerWindow( app, main_tracer )

	app.mainloop()
