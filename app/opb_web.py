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
import os.path
import mimetypes
import ConfigParser
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
import urllib

mimetypes.init()

web.config.debug = False

urls = [
	'/', 'main',
	'/set/open', 'open_set',
	'/set/close', 'close_set',
	'/photo', 'save_photo',
  '/favicon.ico', 'favicon_serve',
	'/plugin/(.*)/static/(.*)', 'plugin_static',
	'/plugin/(.*)/(.*)', 'plugin_serve',
]

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

config = ConfigParser.SafeConfigParser({'EnableExternalCamera': False, 'EnablePrinter': False, 'Rows': 4, 'Columns': 1, 'SetsPerPage': 4, 'ImageSizeX': 1000, 'ImageSizeY': 750, 'FooterImage': ''})
config.read('config.ini')

theme_render = None
set_id = False
printQueue = []
enableGphoto2 = config.getboolean("Features", "EnableExternalCamera")
enableMjpgStreamer = config.getboolean("Features", "EnableMjpgStreamer")
enablePrinter = config.getboolean("Features", "EnablePrinter")
printerRows = config.getint("Printing", "Rows")
printerColumns = config.getint("Printing", "Columns")
printerSetsPerPage = config.getint("Printing", "SetsPerPage")
printerImageSizeX = config.getint("Printing", "ImageSizeX")
printerImageSizeY = config.getint("Printing", "ImageSizeY")
printerFooterImage = config.get("Printing", "FooterImage")

##### Load Plugins
requested_plugins = [ 'hello_world', ]
plugins = {}

for name in requested_plugins:
	m = __import__( '.'.join( ( 'plugins', name ) ), [], [], ['hook'], -1 )
	plugins[name] = m.hook.Plugin()
##### End Plugins

# Sets everything required for properly rendering a theme
def SetTheme ( theme_name ):
	global theme_render
	global opb
	opb['theme_path'] = '/static/themes/%s/' % ( theme_name )
	theme_render = web.template.render( 'static/themes/%s/' % ( theme_name ) )

def printImage(set_id):
  images = list()
  footer = False
  printerFooterSizeX = 0
  printerFooterSizeY = 0
  actualImageSizeX = 0
  actualImageSizeY = 0

  imageSize = printerImageSizeX, printerImageSizeY

  if printerFooterImage:
    footerFileName = './static/photos/%s' % printerFooterImage
    if os.path.isfile(footerFileName):
      footer = Image.open(footerFileName)
      footer.thumbnail(imageSize, Image.ANTIALIAS)
      printerFooterSizeX, printerFooterSizeY = footer.size

  for filename in glob.glob('./static/photos/%s_*.jpg' % set_id):
    image = Image.open(filename)
    image.thumbnail(imageSize, Image.ANTIALIAS)
    actualImageSizeX, actualImageSizeY = image.size
    images.append(image)

  if actualImageSizeX > 0:
    im = Image.new("RGB", (actualImageSizeX * printerColumns, actualImageSizeY * printerRows + printerFooterSizeY))

    if len(images) == 4:
      im.paste(images[0], (0, 0))
      im.paste(images[1], (0, actualImageSizeY))
      im.paste(images[2], (0, actualImageSizeY * 2))
      im.paste(images[3], (0, actualImageSizeY * 3))
      if footer:
        im.paste(footer, (0, actualImageSizeY * 4))

      im = im.rotate(90)
      fileName = './static/photos/%s_print.jpg' % set_id
      im.save(fileName)

      addToPrintQueue(fileName)
      addToPrintQueue(fileName)
      addToPrintQueue(fileName)
      addToPrintQueue(fileName)
  return

def addToPrintQueue(fileName):
  global printQueue
  printQueue.append(fileName)
  if len(printQueue) >= 4:
    printFileName = './static/photos/%s_to_print.pdf' % int( time.time() )
    printCanvas = canvas.Canvas(printFileName, pagesize=letter)
    width, height = letter
    #stripsize = int(height * inch/ printerSetsPerPage), int(width * inch)
    for idx, file in enumerate(printQueue):
      image = ImageReader(file)
      printCanvas.drawImage(image, 0.25 * inch, (idx * 2.60 * inch) - (4.25 * inch), width=8 * inch, preserveAspectRatio=True)

    printCanvas.save()

    call(['lpr', printFileName])

    printQueue = []

  return

# Create the application
app = web.application( tuple( urls ), globals() )

class main:
	def GET( self ):
		return theme_render.index( opb )

# Serves static files at /plugin/[plugin name]/[file path]
class plugin_static:
	def GET ( self, plugin, path ):
		filename = os.path.join( 'plugins', plugin, 'static', path ) 
		if os.path.isfile( filename ):
			t = mimetypes.guess_type( filename )
			if t[0]:
				web.header( 'Content-Type', t[0] )
				web.header('Transfer-Encoding','chunked') 
				with open( filename, 'rb' ) as f: 
					while 1:
						buf = f.read(1024 * 8) 
						if not buf: 
							break 
						yield buf
				return
		
		app.notfound()

class plugin_serve:
	def GET ( self, plugin, path ):
		if plugin in plugins.keys():
			return plugins[plugin].GET( path, web, app )
		else:
			app.notfound()
	def POST ( self, plugin, path ):
		if plugin in plugins.keys():
			return plugins[plugin].POST( path, web, app )
		else:
			app.notfound()

class save_photo:
  def POST( self ):
    global set_id
    web.header( 'Content-type', 'application/json; charset=utf-8' )

    """ Save the photo data, thumbnail it and move on. """
    if False != set_id:
      filename = "%s_%s.jpg" % ( set_id, int( time.time() ) )
    else:
      filename = "NOSET_%s.jpg" % ( int( time.time() ) )

    if enableGphoto2:
      call(['gphoto2', '--capture-image-and-download', '--filename=./static/photos/%s' % filename])
    elif enableMjpgStreamer:
      urllib.urlretrieve("http://localhost:8081/?action=snapshot", './static/photos/%s' % filename)
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

class favicon_serve:
	def GET ( self ):
		raise web.redirect( '/static/favicon.ico' )

if __name__ == "__main__" :
	SetTheme( 'touchscreen' )
	app.run()
