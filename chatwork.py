# -*- coding: utf-8 -*-
import os,sys,time
import logging
import json
import requests,threading

from errbot.errBot import ErrBot
from errbot.backends.base import Message, Person, Room, RoomOccupant
from errbot.rendering import md

log = logging.getLogger('errbot.backends.chatwork')

class ChatworkException( Exception ):
    """ ChatworkException """

# Person
# idd = account_id 
# username = username
# avaterurl = no support
#
class ChatworkPerson(Person):
    def __init__(self, idd=None, username=None, avatarurl=None ):
        self._idd = idd
        self._username = username
        self._avaterurl = None

    @property
    def idd(self):
        return str( self._idd )

    @property
    def username(self):
        return self._username

    @property
    def avatarurl(self):
        return self._avatarurl

    @property
    def client(self):
        return ''

    @property
    def fullname(self):
        return self._username

    @property
    def person(self):
        return self._username

    @property
    def nick(self):
        return self._username

    @property
    def aclattr(self):
        return self._idd

    @staticmethod
    def build_json( from_user ):
        return ChatworkPerson(  idd=from_user['account_id'],
                                username=from_user['name'],
                                avatarurl=None )

    def __eq__(self,other):
        return str(self) == str(other)

    def __unicode__(self):
        return str( self._idd )

    __set__ = __unicode__
    aclattr = idd

# RoomOccupant
#  ChatworkPerson + RoomOccupant
#
class ChatworkRoomOccupant(ChatworkPerson, RoomOccupant):
    def __init__( self, room, idd=None, username=None, avatarurl=None ):
        self._room = room
        super().__init__( idd=idd, username=username, avatarurl=avatarurl )

    @staticmethod
    def build_json( room, from_user ):
        return ChatworkRoomOccupant( room, idd=from_user['account_id'], username=from_user['name'], avatarurl=None )

    @property
    def room(self):
        return self._room

    def __unicode__(self):
        return str( self._idd )

    def __eq__(self,other):
        if hasattr(other,'person') :
            return self.person == other.person
        return str(self) == str(other)
    
    __str__ = __unicode__




class ChatworkRoom(Room):
    def __init__(self, backend=None, idd=None, name=None):
        self._backend = backend
        self._idd = idd
        self._name = name

    def join(self, username=None, password=None):
        log.info("Joining room %s (%s)" % (self._name, self._idd) )
        try:
          response = self._backend.writeAPIRequest('rooms', {})
        except Exception:
          log.exception("Failer join room")
        self._backend.follow_room(self)

    @property
    def idd(self):
      return self._idd  

    @property
    def name(self):
        return self._name

    def create(self):
      pass

    def destroy(self):
      pass
    
    def leave(self):
      pass

    @property
    def topic(self):
      return ""

    @property
    def occupants( self ):
      occupants = []
      js_users = self.readAPIRequest('rooms/%s' % self._name )
      for jsu in js_users:
        occupants.append( ChatworkRoomOccupant.build_json(self,jsu['id']) )
      return occupants

    def __eq__(self, other):
      return str(self) == str(other)

    def __unicode__(self):
      return self._name

    __set__ = __unicode__




class ChatworkBackend(ErrBot):
    def __init__(self, config):
        super().__init__(config)

        if not config.CHATWORK_IDENTITY:
          log.fatal("""
          You need to config.py CHATWORK_IDENTITY
          chatwork apiotken 
          Example. config.py
            import os
            CHATWORK_IDENTITY={
              "token": "xxxxxxxxx"
            }
          
          or
          Example. environment variables 
            CHATWORK_IDENTITY={
              "token": os.environ.get('CHATWORK_API_TOKEN')
            }

          """)
          sys.exit(1)

        self.md = md()

        self._settings = config.CHATWORK_SETTINGS
        self._apiuri = self._settings['apiuri']
        self._msg_refresh = self._settings['messages']['refresh']
        self._msg_intervals = self._settings['messages']['intervals']
        self._watchchannels = self._settings['watchchannels']
        self._headers = { 'X-ChatWorkToken': config.CHATWORK_IDENTITY['token'] }
        self.bot_identifier = self.get_identifier()

    def get_identifier( self ):
        res = self.readAPIRequest('me')
        ident = ChatworkPerson.build_json( res )
        log.info( 'errbot chatwork identifier %s ' %  ident._idd )
        return ident


    def readAPIRequest(self, endpoint, params=None):
        log.info( "readAPIRequest %s" % ( self._apiuri + endpoint ) )
        r = requests.get( self._apiuri + endpoint, headers=self._headers, params=params )
        if r.status_code == requests.codes.ok :
            return r.json()
        return None 

    def writeAPIRequest(self, endpoint, content):
        log.info("POST url=%s" % ( self._apiuri + endpoint ))
        try:
            r = requests.post( self._apiuri + endpoint, headers=self._headers, data=content )
        except:
            log.fatal('writeAPIRequest %s %s' % (endpoint, content) )
        return r.json()


    # using chatwork api latest maessage
    def follow_room( self, room ):

        def background(_room,_interval,_refresh):
            room = _room
            interval = _interval
            refresh = _refresh
            while True:
                resmsgs = self.readAPIRequest('rooms/%s/messages' % room._idd)
                if resmsgs != None and len(resmsgs)>0 :
                    for jmsg in resmsgs:
                        from_user = jmsg['account']
                        msg = Message( jmsg['body'] )
                        msg.to = self.bot_identifier
                        msg.frm = ChatworkRoomOccupant.build_json(room,from_user)
                        self.recv_message(msg)
                        time.sleep( interval )
                                
                time.sleep( refresh )
        
        t = threading.Thread( target=background, args=(room,self._msg_intervals,self._msg_refresh) )
        t.daemon = False
        time.sleep( self._msg_intervals )
        t.start()

    def rooms(self):
        js_rooms = self.readAPIRequest('rooms')
        rooms = []
        for jroom in js_rooms:
          cr = ChatworkRoom( self, idd=jroom['room_id'], 
                                    name=jroom['name'] )
          rooms.append( cr )
        return rooms

    def contacts(self):
        js_rooms = self.readAPIRequest('contacts')
        contacts = []
        for jroom in js_rooms:
            cr = ChatworkRoom( backend=self, idd=jroom['room_id'], 
                                    name=jroom['name'])
            contacts.append( cr )

        return contacts


    def build_identifier( self, strrep ):
        return self.bot_identifier

        log.info("build_identifier %s " % (strrep) )
        if strrep == str(self.bot_identifier) :
            return self.bot_identifier
        try:
            all_rooms = self.readAPIRequest('rooms')
            room = self.query_room(strrep)
            if room is not all_rooms:
                return room
        except:
            raise Exception( "Could build as identifier from %s" % strrep )


    def query_room(self,room):
        for it in self.rooms():
            if it == room: 
                return it
        return None

    def send_message(self, mess):
        log.info("send message")
        super().send_message(mess)
        body = self.md.convert( mess.body )
        content = {'body': body }
        if hasattr( mess.to, 'room' ):
            self.writeAPIRequest('rooms/%s/messages' % (mess.to.room.idd), content )
        else:
            log.fatal("Error: send message")


    def build_reply(self,mess,text=None,private=False):
        log.info("build reply")
        response = self.build_message(text)
        response.frm = mess.to
        response.to = mess.frm
        if private:
            response.to = self.build_identifier(mess.frm)
        return response


    def serve_once(self):
        self.connect_callback()
        try:
            while True:
              time.sleep( 15 )
        except KeyboardInterrup:
            log.info("Interrupt recieve shutdown. ")
            return True
        finally:
            log.info("Interrupt received, shutting down...")
            self.disconnect_callback()

   
    def recv_message(self, object):
        if object == None :
            return
        self.callback_message(object)


    def change_presence(self, status, message):
        pass

    def connect_callback(self):
        super().connect_callback()
        for room in self.rooms():
            if str( room.idd ) in self._watchchannels :
                self.follow_room( room )
                time.sleep( 15 )

    @property
    def mode(self):
        return 'Chatwork'


