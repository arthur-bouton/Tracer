#!/usr/bin/env python
from setuptools import setup

setup(
	name='tracer',
	version='1.1',
	description='Real-time versatile plotter based on Matplotlib',
	license='GPL-2.0',
	author='Arthur Bouton',
	author_email='arthur.bouton@gadz.org',
	url='https://github.com/Bouty92/Tracer',
	py_modules=[ 'tracer', 'tracer_qt4', 'tracer_tk' ],
	entry_points={ 'console_scripts':
		[ 'tracer=tracer:main', 'tracer-qt4=tracer_qt4:main', 'tracer-tk=tracer_tk:main' ] },
	install_requires=[ 'matplotlib>=1.5.1' ]
)
