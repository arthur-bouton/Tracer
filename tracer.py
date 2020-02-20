#!/usr/bin/python
#-*- coding: utf-8 -*-
#
# tracer.py
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
import argparse
import os
import sys
import stat
import signal
import time
import copy


class Tracer :
	"""
	A class to plot curves in real time or from a text file.

	For a direct use, just do :
	    Tracer().run()
	
	The number in square brackets is the amount of data plotted.
	"""

	def _s_positive_int( self, arg ) :
		try :
			s_positive_int = int( arg )
			assert s_positive_int > 0
		except :
			raise argparse.ArgumentTypeError( "invalid strictly positive int value: '%s'" % arg )
		return s_positive_int


	def _columns( self, arg ) :
		try :
			columns = arg.split( '/' )
			for i, subplot in enumerate( columns ) :
				columns[i] = subplot.split( ',' )
				for j, column in enumerate( columns[i] ) :
					columns[i][j] = int( column )
					assert columns[i][j] > 0
		except :
			raise argparse.ArgumentTypeError( "invalid columns list: '%s': must be integers separeted by commas or slashes" % arg )
		return columns


	def _indexes( self, arg ) :
		try :
			indexes = arg.split( ',' )
			for i, index in enumerate( indexes ) :
				indexes[i] = int( index )
				assert indexes[i] > 0
		except :
			raise argparse.ArgumentTypeError( "invalid list: '%s': must be integers separeted by commas" % arg )
		return indexes


	def _float_list( self, arg ) :
		try :
			floats = arg.split( ',' )
			for i, value in enumerate( floats ) :
				if value == '' :
					floats[i] = self.lines_width
				else :
					floats[i] = float( value )
		except :
			raise argparse.ArgumentTypeError( "invalid list: '%s': must be floats separeted by commas" % arg )
		return floats


	def _percentage( self, arg ) :
		try :
			percentage = float( arg )
			assert percentage >= 0 and percentage <= 100
		except :
			raise argparse.ArgumentTypeError( "invalid percentage value: '%s'" % arg )
		return percentage


	def _size( self, arg ) :
		try :
			size = arg.split( 'x' )
			size[0] = float( size[0] )
			size[1] = float( size[1] )
			assert len( size ) == 2 and size[0] > 0 and size[1] > 0 and size[0] <= 100 and size[1] <= 100
		except :
			raise argparse.ArgumentTypeError( "invalid size: '%s': must be of the form 'WIDTH(%)xHEIGHT(%)'" % arg )
		return size


	def _str_list( self, arg ) :
		return arg.split( ',' )

	
	def __init__( self, args=None, input=None,
	              
				  # PÉRIODE DE RAFRAÎCHISSEMENT PAR DÉFAUT :
				  rate = 0.05,

                  # TAILLE DE LA FENÊTRE PAR DÉFAUT :
                  w = 650,
                  h = 524,

                  # COULEURS DE LA FIGURE :
                  face_color = '0.25',
                  background_color = '0.5',
                  grid_color = 'w',
                  axis_color = '0.9',
                  ticks_color = '0.9',
                  labels_color = '0.9',
                  title_color = '0.7',
                  legends_color = '0.9',
                  edge_color = 'k',

                  # ÉPAISSEUR DES COURBES PAR DÉFAUT :
                  lines_width = 1.0,

                  # COULEURS DES COURBES PAR DÉFAUT :
				  lines_color = [ 'b', 'g', 'r', 'm', 'y', 'c' ] ) :

		"""
		At the declaration, parse the argument from the command line
		or from the string 'args' if specified.

		You can directly specify a file object to use as input.

		'rate' is the default minimum time in seconds between two updates,
		'w' and 'h' are the default size of the window in pixels,
		'lines_width' is the default width of the lines,
		'lines_color' is a list of their default colors
		and the other arguments are the figure's colors.
		"""

		self.progname = os.path.basename( sys.argv[0] )

		self.w = w
		self.h = h

		self.x = None
		self.y = None

		self.lines_width = lines_width
		self.lines_color = lines_color

		self.parser = argparse.ArgumentParser()
		self.parser.add_argument( '--sep', type=str, help="set the delimiter string" )
		self.parser.add_argument( '-C', '--columns', type=self._columns, help="specify the columns to be processed, separated by commas and the subplots by slashes" )
		self.parser.add_argument( '-n', '--ncolumns', type=self._s_positive_int, help="process only the lines with NCOLUMNS columns" )
		self.parser.add_argument( '-a', '--abscissa', action='store_true', help="take the first series as abscissa" )
		self.parser.add_argument( '-f', '--file', type=argparse.FileType('r'), help="read from the file FILE" )
		self.parser.add_argument( '-o', '--offset', type=self._s_positive_int, help="add a starting offset" )
		self.parser.add_argument( '-b', '--band', type=self._s_positive_int, help="limit the number of data to display" )
		self.parser.add_argument( '-r', '--rate', type=float, default=rate, help="set a minimum time in seconds between two updates of the window" )
		self.parser.add_argument( '-q', '--quiet', action='store_true', help="silence unprocessed lines" )
		self.parser.add_argument( '-p', '--pass', dest='reprint', action='store_true', help="rewrite the data on standard output" )
		self.parser.add_argument( '-x', '--x_pos', type=self._percentage, help="position the window in a percentage relative to the width of the screen" )
		self.parser.add_argument( '-y', '--y_pos', type=self._percentage, help="position the window in a percentage relative to the height of the screen" )
		self.parser.add_argument( '-s', '--size', type=self._size, help="resize the window in percentages relative to the screen according to the format 'WIDTHxHEIGHT'" )
		self.parser.add_argument( '-c', '--colors', type=self._str_list, default=self.lines_color, help="set the color cycle for the lines, separated by commas" )
		self.parser.add_argument( '-l', '--loop', action='store_true', help="loop the colors at each subplots" )
		self.parser.add_argument( '-d', '--dashed', type=self._indexes, help="declare dashed lines, separated by commas" )
		self.parser.add_argument( '-t', '--dotted', type=self._indexes, help="declare dotted lines, separated by commas" )
		self.parser.add_argument( '-m', '--mixed', type=self._indexes, help="declare mixed lines, separated by commas" )
		self.parser.add_argument( '-w', '--linewidth', type=self._float_list, help="set the linewidths, separated by commas" )
		self.parser.add_argument( '-z', '--zero', type=self._indexes, nargs='?', const=[0], help="declare subplots where to keep zero in sight, separated by commas or every one when not specified" )
		self.parser.add_argument( '-g', '--nogrid', type=self._indexes, nargs='?', const=[0], help="declare subplots where not to display the grid, separated by commas or every one when not specified" )
		self.parser.add_argument( '-L', '--labels', type=self._str_list, default=[], help="set the labels for each series, separated by commas" )
		self.parser.add_argument( '-A', '--xlabel', type=str, help="set the label for the abscissa" )
		self.parser.add_argument( '-T', '--titles', type=self._str_list, help="set the titles for each subplots, separated by commas" )
		self.parser.add_argument( '-X', '--latex', action='store_true', help="use LaTeX for the texts" )
		self.parser.add_argument( '-P', '--plain', action='store_true', help="set plain colors for the figure" )
		self.parser.add_argument( '-S', '--transparent', action='store_true', help="set the margins transparent" )
		self.parser.add_argument( '-Q', '--Qt4', action='store_true', help="use Qt4 as backend" )
		self.parser.add_argument( '--ylog', type=self._indexes, nargs='?', const=[0], help="declare y axes where to use a log scale, separated by commas or every one when not specified" )
		self.parser.add_argument( '--xlog', action='store_true', help="use a log scale for the x axis, which implies to take the first series as abscissa" )


		# LECTURE DES ARGUMENTS :

		if args is not None :
			self.args = self.parser.parse_args( args.split() )
		else :
			self.args = self.parser.parse_args()

		if self.args.xlog :
			self.args.abscissa = True


		# INITIALISATIONS :

		self._fromfile = False

		if input is not None :
			self.input = input
			self.window_title = '%s (%i)' % ( self.progname, self.input.fileno() )
		elif self.args.file is not None :
			self.input = self.args.file
			self.window_title = '%s (%s)' % ( self.progname, self.args.file.name )
			mode = os.fstat( self.args.file.fileno() ).st_mode
			if not stat.S_ISFIFO( mode ) and not stat.S_ISSOCK( mode ) :
				self._fromfile = True
		else :
			self.window_title = self.progname + ' (stdin)'

		if not self._fromfile :
			import select
			import fcntl

			self.input = sys.stdin
			self._poll = select.poll()
			self._poll.register( self.input, select.POLLIN )
			fl = fcntl.fcntl( self.input, fcntl.F_GETFL )
			fcntl.fcntl( self.input, fcntl.F_SETFL, fl | os.O_NONBLOCK )

		sys.stdout = os.fdopen( sys.stdout.fileno(), 'w' )

		if self.args.columns is not None :
			self._series = self.args.columns
			self._nsubplots = len( self._series )
			self._nseries = 0
			for subplot in self._series :
				self._nseries += len( subplot )

			self._data = [ [] for i in range( self._nseries ) ]

		else :
			self._series = None
			self._nsubplots = 1

		self._lines = []

		self._data_count = 0
		self._perf = 1.

		if self.args.plain :
			self.face_color = 'w'
			self.background_color = 'w'
			self.grid_color = 'k'
			self.axis_color = 'k'
			self.ticks_color = 'k'
			self.labels_color = 'k'
			self.title_color = 'k'
			self.legends_color = 'k'
			self.edge_color = 'k'
		else :
			self.face_color = face_color
			self.background_color = background_color
			self.grid_color = grid_color
			self.axis_color = axis_color
			self.ticks_color = ticks_color
			self.labels_color = labels_color
			self.title_color = title_color
			self.legends_color = legends_color
			self.edge_color = edge_color

		self._paused = False

		self._ended = False


		# VÉRIFICATION DE LA COHÉRENCE DES ARGUMENTS :

		if self.args.abscissa :
			n = 2
			if self.args.columns is not None :
				n = len( self.args.columns[0] )
			elif self.args.ncolumns is not None :
				n = self.args.ncolumns
			if n < 2 :
				self.parser.error( "there must be at least two series to process if one is put in the abscissa" )

		if self.args.columns is not None :
			self._seriesmax = 0
			for subplot in self.args.columns :
				self._seriesmax = max( self._seriesmax, max( subplot ) )
			if self.args.ncolumns is not None and self.args.ncolumns < self._seriesmax :
				self.parser.error( "the number of columns must be at least equal to the highest selected column" )


	def run( self, show=True, fork=True ) :
		"""
		Create the figure and run the reading thread.

		If show=True, the standard window is created and the method blocks.

		If fork=True, the program will fork and the parent process is used for terminal handling.
		"""


		# CRÉATION D'UN SOUS-PROCESSUS :

		if fork :

			child_pid = os.fork()

			if child_pid != 0 :

				def ctrl_c_handler( signum, frame ) :
					sys.stderr.write( '\r' )
					try :
						os.kill( child_pid, signal.SIGTERM )
						signal.pause()
					except OSError as e :
						if e.errno == 3 :
							pass
						else :
							raise

				def exited_child_handler( signum, frame ) :
					os.waitpid( child_pid, os.WNOHANG )

				signal.signal( signal.SIGCHLD, exited_child_handler )
				signal.signal( signal.SIGINT, ctrl_c_handler )

				signal.pause()

				sys.exit( 0 )


			signal.signal( signal.SIGINT, signal.SIG_IGN )
			signal.signal( signal.SIGTSTP, signal.SIG_IGN )


		# CRÉATION DE LA FENÊTRE :

		import matplotlib
		if self.args.Qt4 :
			matplotlib.use( 'Qt4Agg' )
		import matplotlib.pyplot as pyplot
		import threading


		self.backend = matplotlib.get_backend()

		if self.args.latex :
			pyplot.rcParams['text.usetex']=True

		if self._series is not None :
			self.fig, self.axes = pyplot.subplots( self._nsubplots, sharex=True )
			if self._nsubplots == 1 :
				self.axes = [ self.axes ]
		else :
			self.fig, self.axes = pyplot.subplots()
			self.axes = [ self.axes ]

		self.fig.set_facecolor( self.face_color )
		self.fig.set_edgecolor( self.edge_color )

		if self.args.transparent :
			self.fig.patch.set_alpha( 0 )

		if self.args.titles is None :
			self.axes[0].set_title( '[ 0 ]' )

		for i in range( self._nsubplots ) :

			if self.args.titles is not None and len( self.args.titles ) > i :
				self.axes[i].set_title( self.args.titles[i] )
			self.axes[i].title.set_color( self.title_color )

			self.axes[i].set_facecolor( self.background_color )

			for spine in self.axes[i].spines.values() :
				spine.set_color( self.axis_color )

			self.axes[i].tick_params( axis='x', colors=self.ticks_color, which='both' )
			self.axes[i].xaxis.get_offset_text().set_color( self.ticks_color )
			self.axes[i].tick_params( axis='y', colors=self.ticks_color, which='both' )
			self.axes[i].yaxis.get_offset_text().set_color( self.ticks_color )

			if self.args.xlog :
				self.axes[i].set_xscale( "symlog" )
			if self.args.ylog is not None and ( self.args.ylog[0] == 0 or i + 1 in self.args.ylog ) :
				self.axes[i].set_yscale( "symlog" )

			isgrid = False if self.args.nogrid is not None and ( self.args.nogrid[0] == 0 or i + 1 in self.args.nogrid ) else True
			self.axes[i].grid( color=self.grid_color, ls='dotted', alpha=0.3 )
			self.axes[i].grid( isgrid )
			self.axes[i].abscissa = self.axes[i].axhline( color=self.grid_color, ls='dashed', alpha=0.2, visible=isgrid )

			self.axes[i].set_prop_cycle( color=self.args.colors )

		if not self._fromfile and self._series is not None :
			self._plot_data()


		# AFFICHAGE DES DONNÉES :

		self._data_mutex = threading.Lock()

		if self._fromfile :
			self._read_data()
		else :
			reading_thread = threading.Thread( target=self._read_data )
			reading_thread.setDaemon( True )
			reading_thread.start()

		if show :
			self.set_window( pyplot.get_current_fig_manager() )
			pyplot.show()
		else :
			self.set_window()

		return 0


	def set_window( self, fig_manager=None ) :
		"""
		Calculate w, h, x and y according to the screen size.

		If a figure manager is given, it will try to set these parameters.
		"""

		if fig_manager is not None :
			try :
				fig_manager.set_window_title( self.window_title )
			except :
				sys.stderr.write( self.progname + ": error: unable to rename the window\n" )

		if self.args.x_pos is not None or self.args.y_pos is not None or self.args.size is not None :

			if self.args.x_pos is None :
				self.args.x_pos = 50

			if self.args.y_pos is None :
				self.args.y_pos = 50

			try :
				screen_size = os.popen( "xrandr | grep \* | cut -d ' ' -f4" ).readline().split( 'x' )
				w_screen = int( screen_size[0] )
				h_screen = int( screen_size[1] )
			except :
				sys.stderr.write( self.progname + ": error: unable to get the screen size - window setting aborted\n" )
				return

			if self.args.size is not None :
				self.w = self.args.size[0]*w_screen/100
				self.h = self.args.size[1]*h_screen/100

			self.x = int( max( 0, w_screen*self.args.x_pos/100 - self.w/2 ) )
			self.y = int( max( 0, h_screen*self.args.y_pos/100 - self.h/2 ) )

			if fig_manager is not None :
				try :
					if self.backend == 'TkAgg' :
						fig_manager.window.geometry( '%+i%+i' % ( self.x, self.y ) )
					else :
						fig_manager.window.move( self.x, self.y )
				except :
					sys.stderr.write( self.progname + ": error: unable to move the window\n" )

		if fig_manager is not None :
			try :
				if self.backend == 'TkAgg' :
					fig_manager.window.geometry( '%ix%i' % ( self.w, self.h ) )
				else :
					fig_manager.window.resize( self.w, self.h )
			except :
				sys.stderr.write( self.progname + ": error: unable to resize the window\n" )


	def _linestyle( self, i ) :
		if self.args.dashed is not None and i in self.args.dashed :
			return '--'
		elif self.args.dotted is not None and i in self.args.dotted :
			return ':'
		elif self.args.mixed is not None and i in self.args.mixed :
			return '-.'
		else :
			return '-'


	def _legend( self, i, series, n_end ) :

		n_start = n_end - len( series )
		n_labels = max( 0, len( self.args.labels ) - n_start )
		labels = self.args.labels[n_start:n_start+n_labels] + series[n_labels:]

		leg = self.axes[i].legend( self._lines[n_start-( 1 if self.args.abscissa else 0 ):n_end], labels, frameon=self.args.plain )
		for text in leg.get_texts() :
			text.set_color( self.legends_color )
		self.axes[i].xaxis.label.set_color( self.labels_color )


	def _zero_sight( self ) :

		n = -1 if self.args.abscissa else 0
		for i, ax in enumerate( self.axes ) :
			if self.args.zero is not None and ( self.args.zero[0] == 0 or i + 1 in self.args.zero ) :
				ax.relim()
				n += len( self._series[i] )
			else :
				first = True
				for serie in self._series[i] :
					if n >= 0 :
						ax.dataLim.update_from_path( self._lines[n].get_path(), first )
						first = False
					n += 1
			ax.autoscale( True )


	def _plot_data( self ) :

		if self.args.titles is None :
			self.axes[0].set_title( '[ %i ]' % self._data_count )

		n = 0
		if self.args.abscissa :
			for i, subplot in enumerate( self._series ) :
				if i and not self.args.loop :
					self.axes[i]._get_lines.prop_cycler = self.axes[i-1]._get_lines.prop_cycler
				for serie in subplot :
					if n :
						self._lines += self.axes[i].plot( self._data[0], self._data[n], ls=self._linestyle( n ) )
						if self.args.linewidth is not None and len( self.args.linewidth ) >= n :
							self._lines[n-1].set_linewidth( self.args.linewidth[n-1] )
						else :
							self._lines[n-1].set_linewidth( self.lines_width )
					n += 1
				shift = 0 if i else 1
				if len( subplot ) > shift + 1 :
					self._legend( i, subplot[shift:], n )
				elif len( self.args.labels ) > n - 1 :
					self.axes[i].set_ylabel( self.args.labels[n-1], color=self.labels_color )
				else :
					self.axes[i].set_ylabel( subplot[shift], color=self.labels_color )
			if len( self.args.labels ) > 0 :
				self.axes[i].set_xlabel( self.args.labels[0], color=self.labels_color )
			else :
				self.axes[i].set_xlabel( self._series[0][0], color=self.labels_color )
				
		else :
			for i, subplot in enumerate( self._series ) :
				if i and not self.args.loop :
					self.axes[i]._get_lines.prop_cycler = self.axes[i-1]._get_lines.prop_cycler
				for serie in subplot :
					self._lines += self.axes[i].plot( self._data[n], ls=self._linestyle( n + 1 ) )
					if self.args.linewidth is not None and len( self.args.linewidth ) > n :
						self._lines[n].set_linewidth( self.args.linewidth[n] )
					else :
						self._lines[n].set_linewidth( self.lines_width )
					n += 1
				if len( subplot ) > 1 :
					self._legend( i, subplot, n )
				elif len( self.args.labels ) > n - 1 :
					self.axes[i].set_ylabel( self.args.labels[n-1], color=self.labels_color )
				else :
					self.axes[i].set_ylabel( subplot[0], color=self.labels_color )
			if self.args.xlabel is not None :
				self.axes[i].set_xlabel( self.args.xlabel, color=self.labels_color )
			else :
				self.axes[i].xaxis.label.set_color( self.labels_color )

			self._zero_sight()


	def _relim_data( self ) :

		if self.args.band is not None and self._data_count > self.args.band :
			for i in range( self._nseries ) :
				del self._data[i][0:self._data_count-self.args.band]

			self._data_count = self.args.band


	def redraw_data( self, msg='' ) :
		"""
		Update the figure from the read data.

		The string as argument is written on top of the number of data if no title has been specified.
		"""

		if self.args.titles is None :
			self.axes[0].set_title( '%s\n[ %i ]' % ( msg, self._data_count ) )

		if self._new_data :
			if self.args.abscissa :
				for i in range( 1, self._nseries ) :
					self._lines[i-1].set_xdata( self._data[0] )
					self._lines[i-1].set_ydata( self._data[i] )

			else :
				for i in range( self._nseries ) :
					self._lines[i].set_xdata( range( self._data_count ) )
					self._lines[i].set_ydata( self._data[i] )

			self._zero_sight()

			self._new_data = False

			self.fig.canvas.toolbar.update()
			self.fig.canvas.toolbar.push_current()

		try :
			self.fig.canvas.draw_idle()
		except RuntimeError :
			pass


	def _readline( self ) :
		line = ''
		c = os.read( self.input.fileno(), 1 ).decode( 'utf-8' )
		if c :
			while c != '\n' :
				if not self._poll.poll( self.args.rate*1e3 ) == [] :
					line += c
					c = os.read( self.input.fileno(), 1 ).decode( 'utf-8' )
				elif self._new_data and not self._paused :
					self._warning = ''
					self._top_time = time.time()
					self._data_mutex.acquire()
					self._relim_data()
					self.redraw_data( self._warning )
					self._data_mutex.release()
			line += '\n'
		return line


	def _end( self ) :
		if self._data_count == 0 :
			self.redraw_data( 'ENDED WITH NO DATA' )
		else :
			self._relim_data()
			self.redraw_data( 'ENDED' )


	def _read_data( self ) :

		self._new_data = False
		self._warning = ''
		self._top_time = time.time()

		self._data_mutex.acquire()

		while True :
			self._data_mutex.release()


			# SYNCHRONISATION AVEC LES DONNÉES :

			if self._fromfile :
				strline = self.input.readline()

			else :
				try :
					strline = self._readline()
				except OSError :
					uptodate = True
					timeout = self._poll.poll( self.args.rate*1e3 ) == []
				else :
					uptodate = False
					timeout = False

				if timeout and self._new_data and not self._paused :
					self._warning = ''
					self._top_time = time.time()
					self._data_mutex.acquire()
					self._relim_data()
					self.redraw_data( self._warning )
					continue
				elif timeout :
					self._data_mutex.acquire()
					continue
				elif uptodate :
					strline = self._readline()


			# LECTURE D'UNE NOUVELLE LIGNE :

			if not strline :
				break

			self._data_mutex.acquire()

			line = strline.split( self.args.sep )
			
			if self.args.offset is not None and self.args.offset > 0 :
				self.args.offset -= 1
				if not self.args.quiet :
					sys.stdout.write( strline )
				continue

			if self.args.ncolumns is not None and len( line ) != self.args.ncolumns :
				if not self.args.quiet :
					sys.stdout.write( strline )
				continue
			
			if self._series is None :

				self._series = [[]]
				for i, word in enumerate( line ) :
					try :
						line[i] = float( word )
					except ValueError :
						continue
					self._series[0].append( i + 1 )

				self._nseries = len( self._series[0] )
				if ( not self.args.abscissa and self._nseries < 1 ) or ( self.args.abscissa and self._nseries < 2 ) :
					self._series = None
					if not self.args.quiet :
						sys.stdout.write( strline )
					continue

				self._seriesmax = max( self._series[0] )
				self._data = [ [] for i in self._series[0] ]

				if not self._fromfile :
					self._plot_data()

			else :

				if len( line ) < self._seriesmax :
					if not self.args.quiet :
						sys.stdout.write( strline )
					continue

				try :
					for subplot in self._series :
						for serie in subplot :
							line[serie-1] = float( line[serie-1] )
				except ValueError :
					if not self.args.quiet :
						sys.stdout.write( strline )
					continue
			
			if self.args.reprint :
				sys.stdout.write( strline )

			sys.stdout.flush()


			# AJOUT DES NOUVELLES DONNÉES :

			n = 0
			for i, subplot in enumerate( self._series ) :
				for j, serie in enumerate( subplot ) :
					self._data[n].append( line[serie-1] )
					n += 1
			
			self._data_count += 1
			self._new_data = True

			if self._fromfile :
				if self.args.band is not None and self._data_count >= self.args.band :
					break
				continue

			elif time.time() - self._top_time >= self.args.rate :
				if uptodate :
					self._top_time = time.time()
					self._relim_data()
					if not self._paused :
						self.redraw_data( self._warning )
					self._warning = ''
				else :
					self._warning = 'OVERRUN'


		# FIN DES DONNÉES :

		self._ended = True

		if self._fromfile :
			if self._series is not None :
				self._plot_data()
			else :
				sys.stderr.write( "No data were found in %s !\n" % self.args.file.name )
				os.kill( os.getpid(), signal.SIGTERM )
		elif not self._paused :
			self._end()


	def pause( self ) :
		"Pause the drawing."

		if self._ended :
			if self._paused :
				self._paused = False
				self._end()
			return

		self._paused = not self._paused
		
		if self._data_count == 0 :
			self.redraw_data( 'PAUSED' if self._paused else '' )
			return

		if self._paused :
			self._data_mutex.acquire()
			self._relim_data()
			self._data_count_backup = self._data_count
			self._data_backup = copy.deepcopy( self._data )
			self.redraw_data( 'PAUSED' )
			self._data_mutex.release()
		else :
			self._data_mutex.acquire()
			self._relim_data()
			self.redraw_data( '' )
			self._data_mutex.release()


	def is_paused( self ) :
		"Return True if the drawing is paused."

		return self._paused


	def is_ended( self ) :
		"Return True if the EOF has been reached."

		return self._ended


	def is_fromfile( self ) :
		"Return True if reading from a regular file."

		return self._fromfile

	
	def get_series( self ) :
		"Return the list of series grouped by subplots."

		return copy.deepcopy( self._series )


	def data_count( self ) :
		"Return the current data length."

		return self._data_count

	
	def get_data( self ) :
		"""
		Return the data length and the data list.
		If the reading is paused, these are from the moment of the pause.

		The data list is composed by a list of floats for each series.
		"""

		if self._data_count == 0 :
			return 0, None

		if not self._paused :

			if self._ended :
				return self._data_count, self._data

			self._data_mutex.acquire()
			self._data_count_backup = self._data_count
			self._data_backup = copy.deepcopy( self._data )
			self._data_mutex.release()

		return self._data_count_backup, self._data_backup


def import_TracerToolbar( NavigationToolbar2 ) :
	"""
	Return a class describing a custom toolbar to be matched with a Tracer.

	You have to specify the proper parent class.
	For example if you want to use the toolbar with Tkinter,
	this will be the class NavigationToolbar2TkAgg from the module matplotlib.backends.backend_tkagg.
	For Qt4, this will be the class NavigationToolbar2QTAgg from the module matplotlib.backends.backend_qt4agg.

	The TracerToolbar instantiation takes :
		A canvas (instance of FigureCanvasQTAgg from matplotlib.backends.backend_qt4agg
		                   or FigureCanvasTkAgg from matplotlib.backends.backend_tkagg for examples).
		A window from whatever window manager.
		A TracerToolbar instance.
		A function (or None) which has to return a file object for saving data whenever it is called.
		A function (or None) which takes the current band and rate as arguments and has to return new ones.
		False if the messages should not be printed in the toolbar (Qt only).

	New shortcuts are :
		'p' or 'space' to pause the drawing.
		'b' to switch to the band/rate tool.
		'd' to save the data.
		'a' to toggle the displaying of the abscissa.
	"""

	try :
		from matplotlib.backend_bases import key_press_handler
	except ImportError :
		sys.stderr.write( __file__ + ": error: your version of matplotlib is too old to use the custom toolbar properly\n" )


	class TracerToolbar( NavigationToolbar2 ) :

		def __init__( self, canvas, window, tracer, get_save_file=None, get_band_n_rate=None, *args ) :
			self.canvas = canvas
			self.tracer = tracer
			self.get_save_file = get_save_file
			self.get_band_n_rate = get_band_n_rate

			if not tracer.is_fromfile() :
				if self.get_save_file is not None :
					self.toolitems = (
						( 'Home', 'Reset original view', 'home', 'home' ),
						( 'Back', 'Back to  previous view', 'back', 'back' ),
						( 'Forward', 'Forward to next view', 'forward', 'forward' ),
						( None, None, None, None ),
						( 'Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan' ),
						( 'Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom' ),
						( None, None, None, None ),
						( 'Band', 'Change the data band with left mouse, rate with right', 'move', 'band' ),
						( 'Pause', 'Pause', 'forward', 'pause' ),
						( 'Data', 'Save the data', 'filesave', 'save_data' ),
						( None, None, None, None ),
						( 'Subplots', 'Configure subplots', 'subplots', 'configure_subplots' ),
						( 'Save', 'Save the figure', 'filesave', 'save_figure' ),
						)
				else :
					self.toolitems = (
						( 'Home', 'Reset original view', 'home', 'home' ),
						( 'Back', 'Back to  previous view', 'back', 'back' ),
						( 'Forward', 'Forward to next view', 'forward', 'forward' ),
						( None, None, None, None ),
						( 'Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan' ),
						( 'Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom' ),
						( None, None, None, None ),
						( 'Band', 'Change data band with left mouse, rate with right', 'move', 'band' ),
						( 'Pause', 'Pause', 'forward', 'pause' ),
						( None, None, None, None ),
						( 'Subplots', 'Configure subplots', 'subplots', 'configure_subplots' ),
						( 'Save', 'Save the figure', 'filesave', 'save_figure' ),
						)

			NavigationToolbar2.__init__( self, canvas, window, *args )

			self.band_bak = tracer.args.band
			self.rate_bak = tracer.args.rate

			self.update_message()

			self.band_sensi = lambda x: ( x*5e-2 )**3
			self.rate_sensi = lambda x: x**3*1e-9


		def tracer_key_handler( self, event ) :

			if event.key == 'p' or event.key == ' ' :
				self.pause()
			elif event.key == 'b' :
				self.band()
			elif event.key == 'd' :
				self.save_data()
			elif event.key == 'a' :
				event.inaxes.abscissa.set_visible( not event.inaxes.abscissa.get_visible() )
				self.canvas.draw()
			else :
				try :
					key_press_handler( event, self.canvas, self )
				except NameError :
					pass


		def pause( self ) :

			if self.tracer.is_ended() and not self.tracer.is_paused() :
				self.set_message( 'ended' )
				return

			self.tracer.pause()

			if self.tracer.is_paused() :
				self.mode = 'paused'
			else :
				self.mode = ''
			self.set_message( self.mode )


		def update_message( self ) :

			if not self.tracer.is_fromfile() and self.tracer.is_ended() :
				self.mode = 'ended'
			elif self._active == 'BAND' :
				if self.band_bak is not None :
					self.mode = 'band : %i / rate : %f' % ( self.band_bak, self.rate_bak )
				else :
					self.mode = 'no band / rate : %f' % self.rate_bak
				return
			elif self.tracer.is_paused() :
				self.mode = 'paused'
			elif self._active == 'PAN' :
				self.mode = 'pan/zoom'
			elif self._active == 'ZOOM' :
				self.mode = 'zoom rect'
			else :
				self.mode = ''

			self.set_message( self.mode )


		def mouse_move( self, event ) :
			self.update_message()
			if event.inaxes and self._active == 'BAND' and self._lastCursor != 3 :
				self.set_cursor( 3 )
				self._lastCursor = 3
			super( NavigationToolbar2, self ).mouse_move( event )


		def band( self, *args ) :

			change = False
			if self._active == 'BAND' :
				self._active = None
				if self.get_band_n_rate is not None and self.mode == 'change band/rate' :
					change = True
					accepted, newband, newrate = self.get_band_n_rate( self.tracer.args.band, self.tracer.args.rate )
					if accepted :
						try :
							if newband is None :
								self.band_bak, self.rate_bak = None, float( newrate )
							else :
								self.band_bak, self.rate_bak = int( newband ), float( newrate )
						except ValueError :
							self.set_message( 'bad entry' )
						else :
							self.tracer.args.band, self.tracer.args.rate = self.band_bak, self.rate_bak

							if self.band_bak is None :
								self.set_message( 'no band / rate : %f' % self.rate_bak )
							else :
								self.set_message( 'band : %i / rate : %f' % ( self.band_bak, self.rate_bak ) )
					else :
						self.set_message( 'canceled' )
			else :
				self._active = 'BAND'

			if self._idPress is not None :
				self._idPress = self.canvas.mpl_disconnect( self._idPress )
				self.mode = ''

			if self._idRelease is not None :
				self._idRelease = self.canvas.mpl_disconnect( self._idRelease )
				self.mode = ''

			if self._active :
				self._idPress = self.canvas.mpl_connect( 'button_press_event', self.press_band )
				self._idRelease = self.canvas.mpl_connect( 'button_release_event', self.release_band )
				self.mode = 'change band/rate'
				self.canvas.widgetlock( self )
			else :
				self.canvas.widgetlock.release( self )

			if not change :
				self.set_message( self.mode )


		def press_band( self, event ) :

			if event.button == 1 :
				self._button_pressed = 1

				self.band_y = event.y

				if self.tracer.args.band is not None :
					self.band_bak = self.tracer.args.band
				else :
					self.band_bak = self.tracer.data_count()

			elif event.button == 3 :
				self._button_pressed = 3

				self.rate_y = event.y

			else :
				self._button_pressed = None
				return

			self.update_message()

			self.canvas.mpl_disconnect( self._idDrag )
			self._idDrag = self.canvas.mpl_connect( 'motion_notify_event', self.drag_band )

			self.press( event )


		def release_band( self, event ) :

			if self._button_pressed == 1 :
				self.band_bak = self.tracer.args.band
			elif self._button_pressed == 3 :
				self.rate_bak = self.tracer.args.rate
			elif self._button_pressed is None :
				return

			self.canvas.mpl_disconnect( self._idDrag )
			self._idDrag = self.canvas.mpl_connect( 'motion_notify_event', self.mouse_move )

			self._button_pressed = None
			self.release( event )


		def drag_band( self, event ) :

			if self._button_pressed == 1 :
				newband = max( 1, self.band_bak + self.band_sensi( event.y - self.band_y ) )
				self.set_message( 'new band : %i' % newband )
				self.tracer.args.band = int( newband )

			if self._button_pressed == 3 :
				newrate = max( 0, self.rate_bak + self.rate_sensi( event.y - self.rate_y ) )
				self.set_message( 'new rate : %f' % newrate )
				self.tracer.args.rate = float( newrate )


		def save_data( self ) :

			if self.get_save_file is not None :
				n, data = self.tracer.get_data()
				if n > 0 :
					f = self.get_save_file()
					if hasattr( f, 'write' ) :
						s = len( data )
						for i in range( n ) :
							line = ''
							for j in range( s - 1 ) :
								line += str( data[j][i] ) + ' '
							line += str( data[s-1][i] ) + '\n'
							f.write( line )
						if hasattr( f, 'close' ) :
							f.close()
				else :
					self.set_message( 'no data to save' )


	return TracerToolbar


if __name__ == '__main__' :

	sys.exit( Tracer().run() )
