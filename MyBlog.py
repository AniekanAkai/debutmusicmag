import os
import webapp2
import jinja2
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'mytemplates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t=jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

#Giving the blog a parent to help organisation
def blog_key(name='default'):
	return db.Key.from_path('blogs', name)

class Blogpost(db.Model): #to create an entity in google appengine datastore
	title = db.StringProperty(required=True)
	article = db.TextProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)
	author = db.StringProperty(required=False)
	artist_tags = db.StringProperty(required = False)
	genre_tags = db.StringProperty(required = False)
	tags = db.StringProperty(required=False)
	#auto_now_add option allows for the date to be added automattically 
	
	def render(self):
		self._render_text = self.article.replace('\n', '<br>')
		return render_str("post.html", a=self)

class HomeHandler(Handler):
	def render_mainpage(self, key="Enter key...", error=""):
		posts = db.GqlQuery("select * from Blogpost order by created desc limit 10")#'limit 10' in the query specifies that only the first 10 rows to be returned
		#posts = Blogpost.all().order('-created') #same as line above
		self.render('debut_home.html', searchkey=key, error=error, posts = posts)

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
		key = db.Key.from_path('Blogpost', int(id))
		a = db.get(key)		
		if not a:
			self.error(404)
			return
		
		self.render('specificpost.html', title=a.title, article=a.article, date=a.created.strftime("%b %d, %Y"),author="", 
							artists=a.artist_tags, genres=a.genre_tags, tags=a.tags)
		
		
		
		
app = webapp2.WSGIApplication([('/',HomeHandler), ('/newpost', NewPostHandler), ('/blog/(\d+)', ArticleHandler)], debug=True)
