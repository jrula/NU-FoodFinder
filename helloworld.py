import os, uuid, sys
from datetime import datetime
from datetime import timedelta
from google.appengine.ext import webapp
#from google.appengine.api import users
from google.appengine.api import mail
from google.appengine.api import memcache
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from django.utils import simplejson


class Entry(db.Model):
    building = db.StringProperty()
    room = db.StringProperty()
    foodSource = db.StringProperty()
    foodType = db.StringProperty()
    entryTime = db.DateTimeProperty()
    rating = db.IntegerProperty()
    description = db.StringProperty()
    author = db.UserProperty()
    timeDifference = db.StringProperty()
    timestampCreated = db.DateTimeProperty(auto_now_add=True)
    
    def humanizeTimeDiff(self):
        """
        Returns a humanized string representing time difference
        between now() and the input timestamp.
        
        The output rounds up to days, hours, minutes, or seconds.
        4 days 5 hours returns '4 days'
        0 days 4 hours 3 minutes returns '4 hours', etc...
        """
        import datetime
        
        timestamp = self.entryTime
        
        timeDiff = datetime.datetime.now() - timestamp
        days = timeDiff.days
        hours = timeDiff.seconds/3600
        minutes = timeDiff.seconds%3600/60
        seconds = timeDiff.seconds%3600%60
        
        str = ""
        tStr = ""
        if days > 0:
            if days == 1:   tStr = "day"
            else:           tStr = "days"
            str = str + "%s %s" %(days, tStr)
            return str
        elif hours > 0:
            if hours == 1:  tStr = "hour"
            else:           tStr = "hours"
            str = str + "%s %s" %(hours, tStr)
            return str
        elif minutes > 0:
            if minutes == 1:tStr = "min"
            else:           tStr = "mins"           
            str = str + "%s %s" %(minutes, tStr)
            return str
        elif seconds > 0:
            if seconds == 1:tStr = "sec"
            else:           tStr = "secs"
            str = str + "%s %s" %(seconds, tStr)
            return str
        else:
            return "0 secs"

class Entry2(db.Model):
    room = db.StringProperty()
    foodAmount = db.IntegerProperty()
    drinkAmount = db.IntegerProperty()
    supervision = db.BooleanProperty()
    time = db.DateTimeProperty()
    
    user = db.StringProperty()
    
    timestamp_created = db.DateTimeProperty(auto_now_add=True)
    
    def humanizeTimeDiff(self):
        """
        Returns a humanized string representing time difference
        between now() and the input timestamp.
        
        The output rounds up to days, hours, minutes, or seconds.
        4 days 5 hours returns '4 days'
        0 days 4 hours 3 minutes returns '4 hours', etc...
        """
        import datetime
        
        timestamp = self.time
        
        timeDiff = datetime.datetime.now() - timestamp
        days = timeDiff.days
        hours = timeDiff.seconds/3600
        minutes = timeDiff.seconds%3600/60
        seconds = timeDiff.seconds%3600%60
        
        str = ""
        tStr = ""
        if days > 0:
            if days == 1:   tStr = "day"
            else:           tStr = "days"
            str = str + "%s %s" %(days, tStr)
            return str
        elif hours > 0:
            if hours == 1:  tStr = "hour"
            else:           tStr = "hours"
            str = str + "%s %s" %(hours, tStr)
            return str
        elif minutes > 0:
            if minutes == 1:tStr = "min"
            else:           tStr = "mins"           
            str = str + "%s %s" %(minutes, tStr)
            return str
        elif seconds > 0:
            if seconds == 1:tStr = "sec"
            else:           tStr = "secs"
            str = str + "%s %s" %(seconds, tStr)
            return str
        else:
            return "0 secs"
    
class Room(db.Model):
    building = db.StringProperty()
    roomNumber = db.StringProperty()
    
class User(db.Model):
    username = db.StringProperty()
    email = db.EmailProperty()
    first_name = db.StringProperty()
    last_name = db.StringProperty()
    password = db.StringProperty()
    phone_no = db.StringProperty()
    session_id = db.StringProperty()
    activated = db.BooleanProperty(default=False)
    activation_code = db.StringProperty(default=str(uuid.uuid4()))
    send_email_alert = db.BooleanProperty(default=False)
    send_phone_alert = db.BooleanProperty(default=False)
    
    timestampCreated = db.DateTimeProperty(auto_now_add=True)
    
class Auth(db.Model):
    user_is = db.IntegerProperty()
    token = db.StringProperty()
    
    access_time = db.DateTimeProperty(auto_now_add=True)
    expiration_time = db.DateTimeProperty()
    
class session:
    
    def __init__(self,handler):
        
        self.handler = handler
        self.session_id = None
        
    def create_user(self, email, username, password, phone_no, email_alert, phone_alert):
        
        tmp = User(key_name=username.lower())
        tmp.username = username
        tmp.email = email
        tmp.password = password
        tmp.phone_no = phone_no
        tmp.send_email_alert = email_alert
        tmp.send_phone_alert = phone_alert
        
        
        mail.send_mail(
            sender="nu.foodfinder@gmail.com",
            to=email,
            subject="Account Activation",
            body="""
Dear """+username+""":
A new account has been created with this email address at http://nu-findfood.appspot.com

But in order to log in and get alert messages you must first activate your account
with your unique activation code included in this email. Simply click
the link included here to activate your account or copy and paste the
following URL into your browser

"""+"http://nu-findfood.appspot.com/validate?activate="+tmp.activation_code)
            
        self._sync_user(tmp)
            
    def get_current_user(self):
        return self._fetch_user_by_cookie()
    
    def grab_login(self, username, password):
        
        tmp = self._fetch_user_with_pass(username, password)
        if tmp:
            self._sync_user(tmp)
        return tmp
    
    def logout(self):
        
        user = self._fetch_user_by_cookie()
        if user:
            memcache.delete(user.session_id)
            user.session_id = None
            user.put()
            
    def _gen_session_id(self):
        return uuid.uuid4()
    
    def _sync_user(self, _user):
        sid = str(self._gen_session_id())
        ssid = '='.join(('ssid',sid))
        self.handler.response.headers.add_header('Set-Cookie',ssid)
        _user.session_id = sid
        self.session_id = sid
        _user.put()
        memcache.add(sid,_user)
        
    def _update_user(self, _user):
        _user.put()
        memcache.add(_user.session_id, _user)
        
    def _fetch_user_by_cookie(self):
        if not self.session_id:
            try:
                sid = self.handler.request.cookies['ssid']
            except:
                sid = ""
                ssid = '='.join(('ssid',sid))
                self.handler.response.headers.add_header('Set-Cookie',ssid)
        else:
            sid = self.session_id
            
        data = memcache.get(sid)
        if data is None:
            data = User.all().filter('session_id = ', sid).get()
            if data is not None: memcache.add(sid, data)
            
        return data
    
    def _fetch_user_with_pass(self, u,p):
        tmp = User.get_by_key_name(u.lower())
        if not tmp: return None
        if tmp.password != p: return None
        if tmp.activated == False: return False
        return tmp

class MainPage(webapp.RequestHandler):
    
    
    def get(self):
        user = session(self).get_current_user()
        
        entries = Entry.all().order('-timestampCreated')
        
        recentEntries = []
        for entry in entries:
            timeDiff = datetime.now() - entry.entryTime
            if timeDiff.seconds/3600 < 1:
                recentEntries.append(entry)
                
        entries2 = Entry2.all().order('-timestamp_created')
        
        template_values = {'allEntries' : entries, 'recentEntries': recentEntries, 'user':user, 'allEntries2' : entries2}

        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

class Mobile(webapp.RequestHandler):
    
    
    def get(self):
#        user = users.get_current_user()
        
        entries = Entry.all().order('-timestampCreated')
        
        recentEntries = []
        for entry in entries:
            timeDiff = datetime.now() - entry.entryTime
            if timeDiff.seconds/3600 < 1:
                recentEntries.append(entry)
        
        template_values = {'allEntries' : entries, 'recentEntries': recentEntries}

        path = os.path.join(os.path.dirname(__file__), 'index_m.html')
        self.response.out.write(template.render(path, template_values))


class ReportFood(webapp.RequestHandler):
    
    def post(self):
        entry = Entry()
        
        entry.building = self.request.get('building')
        entry.room = self.request.get('room')
        entry.foodSource = self.request.get('source')
        entry.foodType = self.request.get('type')
        entry.rating = int(self.request.get('rating'))
        
        entry.entryTime = datetime.now()
#        entry.author = users.get_current_user()
        
        entry.put()
        
        self.redirect('/')
        
class ReportFood2(webapp.RequestHandler):
    
    def post(self):
        
        FOOD_STRING = ["None", "Snack", "Partial Meal", "Full Meal"]
        DRINK_STRING = ["None", "Hot Drinks", "Cold Drinks", "Hot and Cold Drinks"]
        
        print >> sys.stderr, self.request
        
        #Save entry
        entry = Entry2()
        
        entry.room = self.request.get('room')
        
        if entry.room == 'other':
            other_room = self.request.get('room_other')
            entry.room = other_room
        
        entry.foodAmount = int(self.request.get('foodAmount'))
        entry.drinkAmount = int(self.request.get('drinkAmount'))
        entry.supervision = bool(self.request.get('supervision'))
        entry.time = datetime.now()
        u = session(self).get_current_user()
        if u:
            entry.user = u.username
        else:
            entry.user = "Anonymous"
        entry.put()
        
        #Report users via email
        msg_body = """
Food Has Been Found.

Where: %s
Found at: %s

Food:\t\t\t%s
Drink:\t\t\t%s
Supervision:\t\t%s

Sincerely,
Food Finder""" % (entry.room, entry.time.strftime("%Y-%m-%d %H:%M:%S"), FOOD_STRING[entry.foodAmount], DRINK_STRING[entry.drinkAmount], entry.supervision)

 
        #get all users
        users = User.all()
        #Probably want to set up a central account at gmail or something to send from
        for user in users:
            if user.send_email_alert:
                #send email to users about find
                mail.send_mail(
                sender="nu.foodfinder@gmail.com",
                to=user.email,
                subject="Food Found in %s" % entry.room,
                body=msg_body)
            
        self.redirect('/')

class Login(webapp.RequestHandler):
    
    def get(self):
        variables = {'callback_url':self.request.get('continue')}
        path = os.path.join(os.path.dirname(__file__), 'login.html')
        self.response.out.write(template.render(path,variables))
        
    def post(self):
        c = self.request.get('continue')
        if not c: c = '/'
        u = self.request.get('user')
        p = self.request.get('pass')
        tmp = session(self).grab_login(u,p)
        
        if not tmp:
            if tmp is None: msg = 'Bad username and/or password'
            if tmp is False: msg = 'That account has not been activated yet.'
            
            variables = {'callback_url':c,'message':msg}
            path = os.path.join(os.path.dirname(__file__),'login.html')
            self.response.out.write(template.render(path, variables))
        else:
            self.redirect(c)
            
class DoLogout(webapp.RequestHandler):
    
    def get(self):
        c = self.request.get('continue')
        if not c: c = '/'
        session(self).logout()
        self.redirect(c)
#        
#    def post(self):
#        self.redirect(users.create_logout_url('/'))

def login_required(handler_method):
    """
    A decorator to require that a user must be logged in to access a handdler method.
    
    >>> @login_requried
    ... def get(self):
    ...    self.response.out.write('Hello...)
    
    Will direct to a login page if the user is not logged in.
    """
    def check_login(self, *args):
        user = session(self).get_current_user()
        if not user:
            self.redirect('='.join(('login?continue',self.request.uri)))
        else:
            handler_method(self, *args)
            
    return check_login

class ActivateAccount(webapp.RequestHandler):
    def get(self):
        proposed_code = self.request.get('activate')
        a_user = User.all().filter('activation_code = ', proposed_code).get()
        if a_user:
            a_user.activated = True
            a_user.put()
            result = "Your account was activated successfully"
        else:
            result = "There was a problem activating the account."
        
        variables = {'result':result}
        path = os.path.join(os.path.dirname(__file__),'activate.html')
        self.response.out.write(template.render(path,variables))
        
class Register(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'register.html')
        self.response.out.write(template.render(path,None))
        
    def post(self):
        u = self.request.get('user')
        e = self.request.get('email')
        p = self.request.get('pass')
        ph= self.request.get('phone_no')
        
        if self.request.get('phone_alert'):
            ph_a = bool(self.request.get('phone_alert'))
        else:
            ph_a = False
            
        if self.request.get('email_alert'):
            e_a = bool(self.request.get('email_alert'))
        else:
            e_a = False
            
        session(self).create_user(e,u,p,ph,e_a,ph_a)
        self.redirect('/')
        
class Edit(webapp.RequestHandler):
    @login_required
    def get(self):
    
        user = session(self).get_current_user()
        template_values = {'user':user}
        
        path = os.path.join(os.path.dirname(__file__), 'edit.html')
        self.response.out.write(template.render(path,template_values))
        
        print >> sys.stderr, user, user.send_phone_alert, user.send_email_alert
        
    def post(self):
    
        print >> sys.stderr, self.request
        
        user = session(self).get_current_user()
        
        user.username = self.request.get('user')
        user.email = self.request.get('email')
        user.password = self.request.get('pass')
        user.phone_no= self.request.get('phone_no')
        
        if self.request.get('phone_alert'):
            user.send_phone_alert = True
        else:
            user.send_phone_alert = False
        
        if self.request.get('email_alert'):
            user.send_email_alert = True
        else:
            user.send_email_alert = False
        
        session(self)._sync_user(user)
        self.redirect('/')



        
#Define web services interface
#Simple REST GET/POST interfaces
#should i generate these in separate classes??
#maybe later, this will be template then
class Entries(webapp.RequestHandler):
    def get(self):
        #parse query string
        from time import strftime
        entries = Entry.all()
        out = []
        for entry in entries:
            e = {}
            e["building"] = entry.building
            e["room"] = entry.room
            e["foodSource"] = entry.foodSource
            e["foodType"] = entry.foodType
            e["rating"] = entry.rating
            #if entry.author: e["author"] = entry.author.email
            #else: e["author"] = entry.author
#            e["timeDifference"] = entry.timeDifference.isoformat()
            e["timestampCreated"] = entry.timestampCreated.strftime("%Y-%m-%d %H:%M:%S")
            out.append(e)
        if self.request.GET.has_key('count') and self.request.GET['count'] < len(out):
            out = out[:self.request.GET['count']]
        self.response.out.write(simplejson.dumps(out))

    def post(self):
        #create a new entry from the xml posted?
        #or should i use query strings? --> went with this --> actually with post dict not qs
        
        self.response.out.write("success")
        
class Entries2(webapp.RequestHandler):
    def get(self):
        from time import strftime
        entries = Entry2.all()
        out = []
        for entry in entries:
            e = {}
            e["room"] = entry.room
            e["foodAmount"] = entry.foodAmount
            e["drinkAmount"] = entry.drinkAmount
            e["supervision"] = entry.supervision
            e["time"] = entry.time.strftime("%Y-%m-%d %H:%M:%S")
            if entry.user: e["user"] = entry.user
            else: e["user"] = "Anonymous"
#            e["timeDifference"] = entry.timeDifference.isoformat()
            e["timestamp_created"] = entry.timestamp_created.strftime("%Y-%m-%d %H:%M:%S")
            out.append(e)
        if self.request.GET.has_key('count') and self.request.GET['count'] < len(out):
            out = out[:self.request.GET['count']]
        self.response.out.write(simplejson.dumps(out))
        
        
        
application = webapp.WSGIApplication([
                                      ('/', MainPage),
                                      ('/m', Mobile), 
                                      ('/report', ReportFood),
                                      ('/report2', ReportFood2),
                                      ('/register', Register), 
                                      ('/login', Login),
                                      ('/logout', DoLogout),
                                      ('/validate', ActivateAccount),
                                      ('/entries', Entries),
                                      ('/entries2', Entries2),
                                      ('/edit', Edit)],
                                      debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
