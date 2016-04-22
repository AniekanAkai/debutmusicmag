#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import cgi #would be used in escaping html
import re #to allow regular expression capability
import os
import jinja2 #for use of templates in the place of string substitution
from string import letters
from google.appengine.ext import db


template_dir = os.path.join(os.path.dirname(__file__), 'mytemplates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

USER_RE= re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PW_RE= re.compile(r"^.{3,20}$")
EMAIL_RE= re.compile(r"^[\S]+@[\S]+\.[\S]+$")

def validateUser(name):
	return USER_RE.match(name)

def validatePass(word):
	return PW_RE.match(word)

def validateEmail(address):
	return EMAIL_RE.match(address)

def escapeHTML(s):
	return cgi.escape(s, quote=True)

def render_str(template, **params):
	t = jinja_env.get_template(template)
	return t.render(params)

class BaseHandler(webapp2.RequestHandler):
	def render(self, template, **kw):
		self.response.out.write(render_str(template, **kw))
	
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

class HomeHandler(BaseHandler):
	def get(self):
		self.render('home.html')

class EncryptHandler(BaseHandler):
	def get(self):
		self.render('rot13.html')
	
	def post(self):		
		t = self.request.get('text')
		rot13 = t.encode("rot13")
		self.render('rot13.html', text=rot13)
	
class SignupHandler(BaseHandler):
	def get(self):
			self.render('lesson2SignUp.html')
		
	def post(self):
			username = self.request.get("username")
			password = self.request.get("password")
			confirmation = self.request.get("verify")
			email = self.request.get("email")
			
			params = dict(username = username, email = email)
			
			if password != confirmation:
					params['verifyError']="Passwords don't match"
								
			else:
					if not validateUser(username) and not validatePass(password):
						params['usernameError'] = "Inappropriate Username"
						params['pwError'] = "Inappropriate password"						
					
					
					elif not validateUser(username):
						params['usernameError'] = "Inappropriate username"						
						
					elif not validatePass(password):
						params['pwError'] = "Bad Password"
						
					elif  email and not validateEmail(email):
						params['emailError'] = "Bad Email"
						
					else:
						self.redirect("/welcome?username="+username)
					
			self.render('lesson2SignUp.html', **params)

class WelcomeHandler(BaseHandler):
	def get(self):
		user = self.request.get("username")
		self.write("Welcome, "+user)

			
app = webapp2.WSGIApplication([('/',HomeHandler), ('/rot13',EncryptHandler), ('/signup', SignupHandler), ('/welcome', WelcomeHandler)], debug=True)

