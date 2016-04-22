import os
import webapp2
import jinja2
import hashlib
import hmac
import cgi #would be used in escaping html
import re #to allow regular expression capability
import random
import string
import json
from collections import OrderedDict
from google.appengine.ext import db
from google.appengine.api import memcache
import logging
import time

template_dir = os.path.join(os.path.dirname(__file__), 'mytemplates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)

USER_RE= re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PW_RE= re.compile(r"^.{3,20}$")
EMAIL_RE= re.compile(r"^[\S]+@[\S]+\.[\S]+$")
COOKIE_RE = re.compile(r".+=;\s*Path=/")
querytime = -1
def valid_cookie(cookie):
    return cookie and COOKIE_RE.match(cookie)

def validateUser(name):
	return USER_RE.match(name)

def validatePass(word):
	return PW_RE.match(word)

def validateEmail(address):
	return EMAIL_RE.match(address)

def escapeHTML(s):
	return cgi.escape(s, quote=True)
	
def make_secure_val(s):
	return "%s|%s"%(s,hashlib.sha256(s).hexdigest())

def check_secure_val(h):
	val = h.split("|")[0]
	if h == make_secure_val(val):
		return val

#Creating a 5 letter random String to be used as 'salt' 
def make_salt():
	salt = ''
	for x in xrange(5):
		salt += random.choice(string.letters)
	return salt

#Hash the pw and username using a salt either... 
#passed in when validating or a new one when a...
#new user is created
def make_pw_hash(name,pw,s=None):
	if s:
		h = hashlib.sha256(name+pw+s).hexdigest()
	else:
		s = make_salt()
		h = hashlib.sha256(name+pw+s).hexdigest()
	return "%s|%s"%(h,s)
		
def validate_pw(name, pw, h):
	salt = h.split("|")[1]
	if h == make_pw_hash(name,pw,salt):
		return True
	return False

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

#Giving the blog a parent to help organisation
def blog_key(name='default'):
	return db.Key.from_path('blogs', name)

def login(self, user):	
		#user just signed up
		hid=make_secure_val(str(user.key().id()))
		self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path="/blog"'%hid)


class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t=jinja_env.get_template(template)
		hid = self.request.cookies.get('user_id')
		if hid and hid.split('|')[0].isdigit():
			id = int(hid.split('|')[0])
			key = db.Key.from_path('Users', id)
			user = db.get(key)
			if not user:
				self.redirect('/blog/signup')
			else:
				params['user'] = user
		qt = time.time() - querytime
		params['queriedTime'] = '%.0f'%qt
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))
		
	def read_secure_cookie(self, name):
		cookie_val = self.request.cookies.get(name)
		return cookie_val and check_secure_val(cookie_val)
	

class Blogpost(db.Model): #to create an entity in google appengine datastore
	
	title = db.StringProperty(required=True)
	article = db.TextProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)
	author = db.StringProperty(required=False)
	artist_tags = db.StringProperty(required = False)
	genre_tags = db.StringProperty(required = False)
	tags = db.StringProperty(required=False)
	#auto_now_add option allows for the date to be added automatically 
	
	def render(self):
		self._render_text = self.article.replace('\n', '<br>')
		return render_str("post.html", a=self)

	def to_dict(self):
		dict = {'subject':self.title,
				'content':self.article, 
				'created':self.created.strftime("%d %b %Y"),
				'author':self.author,
				'artist_tags':self.artist_tags,
				'genre_tags':self.genre_tags,
				'tags':self.tags}
		return dict
		
class Users(db.Model):#Database of users
	username = db.StringProperty(required=True)
	password = db.StringProperty(required=True)
	email = db.StringProperty(required=False)#if set to 'EmailProperty', email must not be empty
	created = db.DateTimeProperty(auto_now_add=True)
	
	@classmethod
	def by_id(cls, uid):
		return cls.get_by_id(uid)#, parent=users_key())
	
	@classmethod
	def by_name(cls, name):
		u = cls.all().filter('name =', name).get()
		return u
		
	@classmethod
	def register(cls, name, pw, email=None):
		pw_hash = make_pw_hash(name,pw)
		return cls(username=name, password=pw_hash, email=email())
		
	@classmethod
	def login(cls, name, pw):
		u = cls.by_name(name)
		if u and valid_pw(name, pw, u.pw_hash):
			return u

def cached_entries(update=False, id=''):
	key = 'topposts'+id
	#client = memcache.Client()
	#topposts = client.gets(key)
	global querytime
	topposts = memcache.get(key)
	if topposts is None or update:
		logging.debug("DB Queried")
		querytime = time.time()
		if id == '':
			#'limit 10' in the query specifies that only the first 10 rows to be returned
			#posts = Blogpost.all().order('-created') #same as line below
			posts = db.GqlQuery("select * from Blogpost order by created desc limit 10")
			topposts = list(posts)
		else:
			k = db.Key.from_path('Blogpost', int(id))
			topposts = db.get(k)
		memcache.set(key, topposts)
	return topposts
		#while true:
		#	if client.cas(key, posts):
		#		return posts
		#	else:
		#		client.gets(key)

	
class HomeHandler(Handler):
	def render_mainpage(self, key="Enter key...", error=""):
		#'limit 10' in the query specifies that only the first 10 rows to be returned
		posts = cached_entries()		
		hid = self.request.cookies.get('user_id')
		self.render('debut_home.html', posts = posts)

	def get(self):
		self.render_mainpage()
	
	def post(self):
		self.render_mainpage()
		

class NewPostHandler(Handler):
	def get(self):
		self.render('newpost.html')
		
	def post(self):
		article = self.request.get('content')
		title = self.request.get('subject')
		artistTags = self.request.get('artists')
		genreTags = self.request.get('genres')
		if title and article:
			a = Blogpost(title=title, article=article, artist_tags=artistTags, genre_tags=genreTags)
			a.put()		
			cached_entries(True)
			self.redirect('/blog/%s'%a.key().id())
		else:
			self.render('newpost.html',titletext=title, article=article, artists=artistTags, genres=genreTags,
						error="Fill all mandatory fields(i.e. fields with(*))")

class ArticleHandler(Handler):
	def get(self, id):
		#not scalabale because it scans through the blog
		#posts = db.GqlQuery("select * from Blogpost")
		#for a in posts:
		#	aID=a.key().id()
		#	if int(id) == int(aID):
		#		self.render('specificpost.html', title=a.title, article=a.article, date=a.created,author="", 
		#					artists=a.artist_tags, genres=a.genre_tags, tags=a.tags)		
		#scalable solution
		#key = db.Key.from_path('Blogpost', int(id))
		a = cached_entries(False, id)#db.get(key)		
		if not a:
			self.error(404)
			return
		
		self.render('specificpost.html',a = a) 
		
class MainPage(Handler):
	def get(self):
		self.response.headers['Content-Type']='text/plain'
		visits = 0
		visits_cookie_str = self.request.cookies.get('visits')#accessing dictionary of cookies
		
		if visits_cookie_str:
			cookie_val = check_secure_val(visits_cookie_str)
			if cookie_val:
				visits= int(cookie_val)
		
		visits+=1
		
		new_cookie_val = make_secure_val(str(visits))
	
		#add_header used in place of appending like a dict, since headers are allowed to have the same title
		self.response.headers.add_header('Set-Cookie', 'visits=%s; Path="/blog"'%new_cookie_val)
		self.write("You've been here %s times"%visits)

	
class SignupHandler(Handler):
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
					users = db.GqlQuery("select * from Users where username='%s'"%username)
					users = list(users)
					count=0
					for u in users:
						count+=1
					if count==0:
						pwh = make_pw_hash(username,password)
						if email:
							x = Users(username=username,password=pwh, email=email)
						else:
							x = Users(username=username,password=pwh, email="")
						x.put()#store new user in the DB
						login(self, x)
						self.redirect("/blog")
					else:
						params['usernameError'] = "This username exists"
			self.render('lesson2SignUp.html', **params)

class WelcomeHandler(Handler):
	def get(self):
		hid = self.request.cookies.get('user_id')
		if hid and hid.split('|')[0].isdigit():
			id = int(hid.split('|')[0])
			key = db.Key.from_path('Users', id)
			user = db.get(key)
			if not user:
				self.redirect('/blog/signup')
			self.write("Welcome, %s"%user.username)
		else:
			self.redirect('/blog/signup')

			
class LoginHandler(Handler):
	def get(self):
		self.render('loginPage.html')
	
	def post(self):
		username = self.request.get("username")
		password = self.request.get("password")
		
		params = dict(username=username)
		
		if not validateUser(username) and not validatePass(password):
			params['usernameError'] = "Inappropriate Username"
			params['pwError'] = "Inappropriate password"						
		
		elif not validateUser(username):
			params['usernameError'] = "Inappropriate Username"						
					
		elif not validatePass(password):
			params['pwError'] = "Bad Password"		
		else:
			users = db.GqlQuery("select * from Users where username='%s'"%username)
			count=0			
			for u in users:				
				count+=1
				if validate_pw(username, password,u.password):
					login(self, u)
					self.redirect("/blog")
					return
			if count==0:
				params['usernameError']="User does not exist"
			else:
				params['pwError']="Password is incorrect"				
		self.render('loginPage.html', **params)
		

class LogoutHandler(Handler):
	def get(self):
		hid = self.request.cookies.get('user_id')
		if hid:
			id = int(hid.split('|')[0])
			key = db.Key.from_path('Users', id)
			user = db.get(key)
		self.write("Thank you come again, %s"%user.username)
		cookie = '+=;Path=/'
		if valid_cookie(cookie):
			self.response.delete_cookie('user_id', '/blog')
			self.redirect('/blog/signup')
		else:
			self.write("Bad Cookie")
			
			
class JSONHandler(Handler):
	def get(self, page):
		self.response.headers['Content-Type']='application/json'
		self.response.headers.add_header("Access-Control-Allow-Origin","*")
		
		if page=='blog':
			#show JSON implementation of the entire blog
			blog = []
			posts = db.GqlQuery("select * from Blogpost order by created desc limit 10")
			for a in posts:
				blog.append(a.to_dict())				
			api = json.dumps(blog, sort_keys=False, indent=4, separators=(',', ':'))
			self.write(api)
		elif page.split('/')[1].isdigit():
			#show JSON implementations of the specific blog entry			
			blog = []
			id = page.split('/')[1]
			key = db.Key.from_path('Blogpost', int(id))
			a = db.get(key)
			blog.append(a.to_dict())
			api = json.dumps(blog, sort_keys=False, indent=4, separators=(',', ':'))
			self.write(api)
			
	def post(self):
		self.response.headers['Content-Type']='application/json'
		self.response.out.write('Show JSON')
		
class CacheFlushHandler(Handler):
	def get(self):
		if memcache.flush_all():
			self.redirect('/blog')
		else:
			logging.error("Error with cache flush")
		
	
app = webapp2.WSGIApplication([('/visits',MainPage),
								('/',HomeHandler), ('/blog',HomeHandler),
								('/blog/newpost', NewPostHandler), 
								('/blog/(\d+)', ArticleHandler), 
								('/blog/signup', SignupHandler),
								('/blog/welcome', WelcomeHandler),
								('/blog/login', LoginHandler),
								('/blog/logout', LogoutHandler),
								('/(.*).json',JSONHandler),
								('/blog/flush', CacheFlushHandler)], debug=True)
#/.*\.json$