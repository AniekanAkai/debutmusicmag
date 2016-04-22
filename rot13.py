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

form = """
<h1>ROT13 Encryption test</h1>
<b>Enter text to be encrypted:</b><br>
<form method='post' action='/'>
	<div style="color: red">%(error)s</div>	
	<br>
	<textarea name='text' rows='5' cols='50'>%(str)s</textarea>
	<br>
	<input type='submit'>
</form>
"""
months = ['January',
		   'February',
		   'March',
		   'April',
		   'May',
		   'June',
		   'July',
		   'August',
		   'September',
		   'October',
		   'November',
		   'December'
		 ]
#month_abbvs contains a dictionary mapping the 1st three letters of the months to the full month name
month_abbvs = dict((m[:3].lower(),m) for m in months)
numberOfDaysInMonth = [31,29,31,30,31,30,31,31,30,31,30,31]

def escapeHTML(s):
	return cgi.escape(s, quote=True)

def write_form(self, error="", str=""):
	self.response.out.write(form%{"error":error,
								  "str":escapeHTML(str)})

				
class Handler(webapp2.RequestHandler):

	def get(self):
			write_form(self)
		
	def post(self):
			str = self.request.get("text")
			if '\n' in str:
				x = str.partition('\r\n')
				str1 = escapeHTML(x[0].encode("rot13"))
				str2 = escapeHTML('\r\n')
				str3 = escapeHTML(x[2].encode("rot13"))
				self.response.out.write(form%{"error":"",
								  "str":str1+str2+str3})
			else:
				self.response.out.write(form%{"error":"",
								  "str":escapeHTML(str.encode("rot13"))})

			
app = webapp2.WSGIApplication([('/', Handler)], debug=True)

