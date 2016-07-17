from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import jinja2
import os
import cgi
from database_setup import Base, Restaurant, MenuItems
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

template_dir = os.path.join(os.path.dirname(__file__), 'static/templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
								autoescape = True)


class templateHandler():
	def write(self, *a, **kw):
		self.wfile.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))


class webserverHandler(BaseHTTPRequestHandler, templateHandler):

	def do_GET(self):
		try:
			if self.path.endswith("/restaurants"):
				self.send_response(200)
				self.send_header('Content-Type', 'text/html')
				self.end_headers()

				# get restaurants from database
				restaurants = session.query(Restaurant).all()
				# debug output
				print restaurants
				self.render('restaurants.htm', restaurants = restaurants)
				return

			if self.path.endswith("/addRestaurant"):
				self.send_response(200)
				self.send_header('Content-Type', 'text/html')
				self.end_headers()
				# Render template
				self.render('addRestaurant.htm')
				return

			if self.path.endswith("/editRestaurant"):
				# strip the Restaurant id from the url
				restaurantID = self.path.split("/")[1]
				self.send_response(200)
				self.send_header('Content-Type', 'text/html')
				self.end_headers()
				# get the Restaurant from the database and pass in name to tmplate
				db_restaurant = session.query(Restaurant).filter_by(id=restaurantID).one()
				# Render template
				self.render('editRestaurant.htm', restaurant = db_restaurant)
				return

			if self.path.endswith("/deleteRestaurant"):
				# strip the Restaurant id from the url
				restaurantID = self.path.split("/")[1]
				self.send_response(200)
				self.send_header('Content-Type', 'text/html')
				self.end_headers()
				# get the Restaurant from the database and pass in name to tmplate
				db_restaurant = session.query(Restaurant).filter_by(id=restaurantID).one()
				# Render template
				self.render('deleteRestaurant.htm', restaurant = db_restaurant)
				return

		except IOError:
			self.send_error(404, "File not found %s" % self.path)


	def do_POST(self):
		try:
			if self.path.endswith('/addRestaurant'):
				self.send_response(301)
				self.end_headers()

				ctype, pdict = cgi.parse_header(self.headers.getheader('Content-Type'))
				if ctype == 'multipart/form-data':
					fields=cgi.parse_multipart(self.rfile, pdict)
					fieldName = fields.get('name')

					if fieldName[0] != '':
						newRestaurant = Restaurant(name=fieldName[0])
						session.add(newRestaurant)
						session.commit()
						self.send_response(301)
						self.send_header('Content-type', 'text/html')
						self.send_header('Location', '/restaurants')
						self.end_headers()

					return
					

			if self.path.endswith('/editRestaurant'):
				self.send_response(301)
				self.end_headers()

				ctype, pdict = cgi.parse_header(self.headers.getheader('Content-Type'))
				if ctype == 'multipart/form-data':
					fields=cgi.parse_multipart(self.rfile, pdict)
					fieldName = fields.get('name')
					print fieldName
					restaurantID = self.path.split('/')[1]
					print "restaurant id: %s" % restaurantID
					restaurantQuery = session.query(Restaurant).filter_by(id=
															restaurantID).one()

					if restaurantQuery != []:
						restaurantQuery.name = fieldName[0]
						session.add(restaurantQuery)
						session.commit()
						self.send_response(301)
						self.send_header('Content-type', 'text/html')
						self.send_header('Location', '/restaurants')
						self.end_headers()
						return

			if self.path.endswith('/delete'):
				self.send_response(301)
				self.end_headers()

				# ctype, pdict = cgi.parse_header(self.headers.getheader('Content-Type'))
				# if ctype == 'multipart/form-data':
				#	fields=cgi.parse_multipart(self.rfile, pdict)

				restaurantID = self.path.split('/')[1]
				print "restaurant id: %s" % restaurantID
				restaurantQuery = session.query(Restaurant).filter_by(id=
														restaurantID).one()

				if restaurantQuery != []:
					session.delete(restaurantQuery)
					session.commit()
					self.send_response(301)
					self.send_header('Content-type', 'text/html')
					self.send_header('Location', '/restaurants')
					self.end_headers()

		except:
			pass

def main():
	try:
		port = 8080
		server = HTTPServer(('',port), webserverHandler)
		print 'Web server is running on port %s' % port
		server.serve_forever()

	except KeyboardInterrupt:
		print ' entered, stoping web server...'
		server.socket.close()


if __name__ == '__main__':
	main()
