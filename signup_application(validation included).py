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

form = """
<head>
<title>User sign up</title>
</head>
<h1>Account sign up</h1>
<br>
<form method='post' action='/'>
	<label>
	Username:<input type='text' name='username' value='%(username)s'>
	<div style="color: red">%(usernameError)s</div>
	</label>	
	<label>
	Password:<input type='password' name='password'>
	<div style="color: red">%(pwError)s</div>
	</label>	
	<label>
	Confirm Password:<input type='password' name='verify'>
	<div style="color: red">%(verifyError)s</div>
	</label>	
	<label>
	Email(Optional):<input type='text' name='email' value='%(email)s'>
	<div style="color: red">%(emailError)s</div>
	</label>	
	<br>
	<input type='submit'>
</form>
"""

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

def write_form(self, username="",  email="", usernameError="", pwError="", verifyError="", emailError=""):
	self.response.out.write(form%{"usernameError":usernameError,
								  "pwError":pwError, 
								  "verifyError":verifyError,
								  "emailError":emailError,
								  "email":escapeHTML(email),
								  "username":escapeHTML(username)})
								  

								  
class Handler(webapp2.RequestHandler):

	def get(self):
			write_form(self)
		
	def post(self):
			username = self.request.get("username")
			password = self.request.get("password")
			confirmation = self.request.get("verify")
			email = self.request.get("email")
			
			if password != confirmation:
					write_form(self,username,email,"","","The password does not match","")
			
			else:
					if not validateUser(username) and not validatePass(password):
						write_form(self,username,email,"Bad Username","Bad Password","","")
					
					elif not validateUser(username):
						write_form(self,username,email,"Bad Username","","","")
					
					elif not validatePass(password):
						write_form(self,username,email,"","Bad Password","","")
						
					elif  email and not validateEmail(email):
						write_form(self,username,email,"","","","Bad Email")
						
					else:
						self.redirect("/welcome?username=%(name)s"%{"name":username})
						

class WelcomeHandler(webapp2.RequestHandler):

	def get(self):
		user = self.request.get("username")
		self.response.out.write("Welcome, "+user)

			
app = webapp2.WSGIApplication([('/', Handler), ('/welcome', WelcomeHandler)], debug=True)

