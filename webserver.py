from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import jinja2
import os
import cgi

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

				self.render('restaurants.htm')
				print output
				return

			if self.path.endswith("/hola"):
				self.send_response(200)
				self.send_header('Content-Type', 'text/html')
				self.end_headers()

				output = ""
				output += "<html><body>&iexcl;Hola!<br><a href='/hello'>Home</a><br><br>"
				output += "<form method='POST' enctype='multipart/form-data'"
				output += " action='/hello'><h2>What would you like to say to me?"
				output += "</h2><input name='message' type='text'><input type="
				output += "'submit'></form><br></body></html>"

				self.wfile.write(output)
				print output
				return

		except IOError:
			self.send_error(404, "File not found %s" % self.path)


	def do_POST(self):
		try:
			self.send_response(301)
			self.end_headers()

			ctype, pdict = cgi.parse_header(self.headers.getheader('Content-Type'))
			if ctype == 'multipart/form-data':
				fields=cgi.parse_multipart(self.rfile, pdict)
				messagecontent = fields.get('message')

			output = ""
			output += "<html><body>"
			output += " <h2> Okay, how about this: </h2>"
			output += "<h1> %s </h1>" % messagecontent[0]
			output += "<html><body><a href='/hello'>Home</a><br><br>"
			output += "<form method='POST' enctype='multipart/form-data'"
			output += " action='/hello'><h2>What would you like to say to me?"
			output += "</h2><input name='message' type='text'><input type="
			output += "'submit'></form><br>"
			output += "</body></html>"

			self.wfile.write(output)
			print output
			return

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
