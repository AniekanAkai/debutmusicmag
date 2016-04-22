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
<form method='post' action='/test'>
	What is your birthday?
	<div style='color: red'>%(error)s</div>
	<br>
	<label>Day<input type='number' name='day' value='%(day)s'></label>
	<label>Month<input type='text' name='month' value='%(month)s'></label>
	<label>Year<input type='number' name='year' value='%(year)s'></label>
	<br><br>
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

def write_form(self, error="", month="", day="", year=""):
	self.response.out.write(form%{"error":error,
								  "month":escapeHTML(month),
								  "day":escapeHTML(day),
								  "year":escapeHTML(year)})

def validateMonth(s):
		short_month = s[:3].lower()
		capMonth = month_abbvs.get(short_month)		
		
		if capMonth in months:
			return True
			
		else:
			return False

def validateDay(s):
	if s.isdigit():
			intDay = int(float(s))
			if intDay <= 31:#numberOfDaysInMonth[months.index(capMonth)]:
				return True
			else:
				return False
	else:
			return False

def validateYear(s):
	if s.isdigit():
			intYear = int(float(s))
			if intYear<=2020 and intYear>0:
				return True
			else:
				return False
	else:
			return False


class MainHandler(webapp2.RequestHandler):
    def get(self):
		write_form(self)
	
		
class TestHandler(webapp2.RequestHandler):
	def post(self):
		#q = self.request.get("q")
		#self.response.out.write(q)
		#self.response.out.write("We made it!")
		#self.response.headers['Content-Type'] = 'text/plain'
		#self.response.out.write(self.request)
		day = self.request.get("day")
		month = self.request.get("month")
		year = self.request.get("year")
		
		if validateDay(day) and validateMonth(month) and validateYear(year):
				self.redirect("/thanks")
		else:
			error = "The date you entered is not standard"
			write_form(self, error, month, day, year)	

class ThanksHandler(webapp2.RequestHandler):
	def get(self):
		self.response.out.write("OK")		
			
			
app = webapp2.WSGIApplication([
    ('/', MainHandler), ('/test', TestHandler), ('/thanks', ThanksHandler)
], debug=True)

