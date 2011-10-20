# -*- coding: utf-8 -*-

"""
Copyright (c) 2009 John Hobbs, Little Filament

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import web
import Image
import base64
import time
from subprocess import call
import glob
import os

web.config.debug = False

urls = (
	'/', 'main',
	'/set/open', 'open_set',
	'/set/close', 'close_set',
	'/photo', 'save_photo',
	'/favicon.ico', 'favicon_serve'
)

# Need a render engine for the core template files
core_render = web.template.render( 'static/core/' )
# Now make that available to the template engine as a global
web.template.Template.globals['core'] = core_render

# A configuration object to pass information to themes
opb = {
	'core_path': '/static/core/',
	'vendor_path': '/static/vendor/',
	'theme_path': '/static/themes/default/',
  'thumb_path': '/static/thumbs/'
}

theme_render = None
set_id = False
enableGphoto2 = True
enablePrinter = False

# Sets everything required for properly rendering a theme
def SetTheme ( theme_name ):
	global theme_render
	global opb
	opb['theme_path'] = '/static/themes/%s/' % ( theme_name )
	theme_render = web.template.render( 'static/themes/%s/' % ( theme_name ) )

# Create the application
app = web.application( urls, globals() )

class main:
	def GET( self ):
		return theme_render.index( opb )

class save_photo:
	def POST( self ):
		global set_id
		web.header( 'Content-type', 'application/json; charset=utf-8' )

		""" Save the photo data, thumbnail it and move on. """
		if False != set_id:
			filename = "%s_%s.jpg" % ( set_id, int( time.time() ) )
		else:
			filename = "NOSET_%s.jpg" % ( int( time.time() ) )

		if (enableGphoto2):
			call(['gphoto2', '--capture-image-and-download', '--filename=./static/photos/%s' % filename])
		else:
			i = web.input( image=None )

			fullsize = open( './static/photos/' + filename, 'wb' )
			fullsize.write( base64.standard_b64decode( i.image ) )
			fullsize.close()

		size = 160, 120
		im = Image.open( './static/photos/' + filename )
		im.thumbnail( size )
		im.save( './static/thumbs/' + filename, "JPEG" )
		return '{ "saved": true, "thumbnail": "%s" }' % ( filename )

class open_set:
	def GET ( self ):
		global set_id
		set_id = "%s" % int( time.time() )
		return '{ "set": "%s" }' % set_id

class close_set:
	def GET ( self ):
		global set_id
		if enablePrinter:
			printImage(set_id)

		set_id = False
		return '{ "set": false }'

	def printImage(set_id):
		images = list()
                im = Image.new("RGB", (2000, 1500))
                for filename in glob.glob('./static/photos/%s_*.jpg' % set_id):
                	images.append(Image.open(filename).resize((1000, 750)))

                if len(images) == 4:
                        im.paste(images[0], (0, 0))
			im.paste(images[1], (1000, 0))
			im.paste(images[2], (0, 750))
			im.paste(images[3], (1000, 750))
			im.save('./static/photos/%s_print.jpg' % set_id)
		
		return

class favicon_serve:
	def GET ( self ):
		raise web.redirect( '/static/favicon.ico' )

if __name__ == "__main__" :
	SetTheme( 'touchscreen' )
	app.run()
