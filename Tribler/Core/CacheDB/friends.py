# Written by Jie Yang
# see LICENSE.txt for license information
import sys
from time import time
import os
import base64
from traceback import print_exc

from Tribler.Core.Utilities.utilities import validIP, validPort, validPermid, validName, show_permid
from CacheDBHandler import FriendDBHandler
from Tribler.Core.simpledefs import NTFY_FRIENDS,NTFY_PEERS

default_friend_file = 'friends.txt'

DEBUG = False

def init(session):
    friend_db = session.open_dbhandler(NTFY_FRIENDS)
    peer_db = session.open_dbhandler(NTFY_PEERS)
    filename = make_filename(session.get_state_dir(), default_friend_file)
    ExternalFriendList(friend_db,peer_db,filename).updateFriendList()
    
def done(session):
    friend_db = session.open_dbhandler(NTFY_FRIENDS)
    peer_db = session.open_dbhandler(NTFY_PEERS)
    filename = make_filename(session.get_state_dir(), default_friend_file)
    ExternalFriendList(friend_db,peer_db,filename).writeFriendList()
    
def make_filename(config_dir,filename):
    if config_dir is None:
        return filename
    else:
        return os.path.join(config_dir,filename)    

class ExternalFriendList:
    def __init__(self,friend_db,peer_db,friend_file=default_friend_file):
        self.friend_file = friend_file
        self.friend_db = friend_db
        self.peer_db = peer_db
        
    def clean(self):    # delete friend file
        try:
            os.remove(self.friend_file)
        except Exception:
            pass

    def updateFriendList(self, friend_file=''):
        if not friend_file:
            friend_file = self.friend_file
        self.friend_list = self.readFriendList(friend_file)
        self.updateDB(self.friend_list)
        #self.clean()
        
    def updateDB(self, friend_list):
        if not friend_list:
            return
        for friend in friend_list:
            self.friend_db.addExternalFriend(friend)

    def getFriends(self):
        friends = []
        permids = self.friend_db.getFriends()
        for permid in permids:
            friend = self.peer_db.getPeer(permid)
            friends.append(friend)
        return friends
    
    def deleteFriend(self, permid):
        self.friend_db.deleteFriend(permid)
    
    def readFriendList(self, filename=''):
        """ read (name, permid, friend_ip, friend_port) lines from a text file """
        
        if not filename:
            filename = self.friend_file
        try:
            file = open(filename, "r")
            friends = file.readlines()
            file.close()
        except IOError:    # create a new file
            file = open(filename, "w")
            file.close()
            return []
        
        friends_info = []
        for friend in friends:
            if friend.strip().startswith("#"):    # skip commended lines
                continue
            friend_line = friend.split(',')
            friend_info = []
            for i in range(len(friend_line)):
                friend_info.append(friend_line[i].strip())
            try:
                friend_info[1] = base64.decodestring( friend_info[1]+'\n' )
            except:
                continue
            if self.validFriendList(friend_info):
                friend = {'name':friend_info[0], 'permid':friend_info[1], 
                          'ip':friend_info[2], 'port':int(friend_info[3])}
                friends_info.append(friend)
        return friends_info
    
    def validFriendList(self, friend_info):
        try:
            if len(friend_info) < 4:
                raise RuntimeError, "one line in friends.txt can only contain at least 4 elements"
            validName(friend_info[0])
            validPermid(friend_info[1])
            validIP(friend_info[2])
            validPort(int(friend_info[3]))
        except Exception, msg:
            if DEBUG:
                print "======== reading friend list error ========"
                print friend_info
                print msg
                print "==========================================="
            return False
        else:
            return True
    
    def writeFriendList(self, filename=''):
        if not filename:
            filename = self.friend_file
        try:
            file = open(filename, "w")
        except IOError:
            print_exc()
            return
        
        friends = self.getFriends()
        friends_to_write = self.formatForText(friends)
        file.writelines(friends_to_write)
        file.close()

    def formatForText(self, friends):
        lines = []
        for friend in friends:
            permid = show_permid(friend['permid'])
            line = ', '.join([friend['name'], permid, friend['ip'], str(friend['port'])])
            line += '\n'
            lines.append(line)
        return lines