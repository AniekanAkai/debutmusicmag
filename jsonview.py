import os
import cgi #would be used in escaping html
import webapp2
import jinja2
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'mytemplates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)

class HomeHandler(webapp2.RequestHandler):
	def get(self):
		self.response.out.write("dsdfdssd")

app = webapp2.WSGIApplication([('/(\d+).json',HomeHandler)], debug=True)	