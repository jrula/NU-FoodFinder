import os, uuid, sys, hashlib, time
from datetime import datetime
from datetime import timedelta
from google.appengine.ext import webapp
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
        self.username = None
        
    def create_user(self, email, username, password, phone_no, email_alert, phone_alert):
        
        tmp = User(key_name=username.lower())
        tmp.username = username
        tmp.email = email
        # use SHA to generate 512bit (ultrasecure) hash. This creates a 128Byte
        # hex digest
        tmp.password = hashlib.sha512(password).hexdigest()
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
            
        tmp.put()
            
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
            # revoke their cookie by setting expire date in past
            # and setting cookie val to null
            expire = datetime.now() + timedelta(hours=-1)
            expire_str = expire.strftime("%a, %d-%b-%Y %H:%M:%S GMT")
            cook = 'username=; expires=%s;' % expire_str
            self.handler.response.headers.add_header('Set-Cookie', cook)
            cook = 'sid=; expires=%s;' % expire_str
            self.handler.response.headers.add_header('Set-Cookie', cook)
            user.session_id = None
            user.put()
            # memcache.delete(user.session_id)
            
    def user_exists(self, username):
        return User.get_by_key_name(username.lower())

    def _gen_session_id(self):
        return uuid.uuid4()
    
    def _sync_user(self, _user):
        uuid = str(self._gen_session_id())

        #  we will only store the uuid in cookie, the rest will be derived for security
        #  we'll compute the actual ssid with:
        #  512bit_hash( username + uuid + request ip_addr )

        # make the cookie expire in an hour
        expire = datetime.now() + timedelta(hours=1)
        expire_str = expire.strftime("%a, %d-%b-%Y %H:%M:%S GMT")
       
        # store the username so we can derive the actual ssid
        cook = 'username=%s; expires=%s;' %(_user.username.lower(), expire_str)
        self.handler.response.headers.add_header('Set-Cookie', cook)

        # store the plaintext sid
        cook = 'sid=%s; expires=%s;' %(uuid, expire_str)
        self.handler.response.headers.add_header('Set-Cookie', cook)

        # hash uuid, user, and requesting IP together to form the actual ssid
        tmpssid = '%s/%s/%s' %(_user.username.lower(), uuid, \
        str(self.handler.request.remote_addr))
        ssid = hashlib.sha512(tmpssid).hexdigest()
        _user.session_id = ssid
        _user.put()
        # memcache.add(sid,_user)
        
    def _update_user(self, _user):
        _user.put()
        # memcache.add(_user.session_id, _user)
        
    def _fetch_user_by_cookie(self):
        try:
            username = self.handler.request.cookies['username']
        except:
            return None

        try:
            uid = self.handler.request.cookies['sid']
        except:
            return None;

        if username is None or uid is None:
            return None

        # derive the request ssid
        ssid = '%s/%s/%s' %(username.lower(), uid, \
            str(self.handler.request.remote_addr))
        ssid = hashlib.sha512(ssid).hexdigest()

        stored_ssid = db.GqlQuery("SELECT * FROM User WHERE username = :1",\
        username.lower()).get().session_id

        # this is where session hijacking should be thwarted (maybe)
        if stored_ssid is None or ssid != stored_ssid:
            return None
        else:
            # finally let's refresh their cookie
            expire = datetime.now() + timedelta(hours=1)
            expire_str = expire.strftime("%a, %d-%b-%Y %H:%M:%S GMT")

            cook = 'username=%s; expires=%s;' %(username.lower(), expire_str)
            self.handler.response.headers.add_header('Set-Cookie', cook)

            cook = 'sid=%s; expires=%s;' %(uid, expire_str)
            self.handler.response.headers.add_header('Set-Cookie', cook)

            return User.all().filter('username = ', username.lower()).get()
            
            #data = memcache.get(sid)
            #if data is None:
                #if data is not None: memcache.add(sid, data)
            
    
    def _fetch_user_with_pass(self, u, p):
        tmp = User.get_by_key_name(u.lower())
        if not tmp: return None
        if tmp.password != hashlib.sha512(p).hexdigest(): return None
        if tmp.activated == False: return False
        return tmp
