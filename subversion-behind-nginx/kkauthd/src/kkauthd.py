# -*- coding: utf8 -*-

from __future__ import division, generators, nested_scopes, print_function, with_statement

from ConfigParser import RawConfigParser
from hashlib import sha1
import logging
from sys import argv
from urlparse import parse_qs, urlparse

from beaker.cache import cache_region, cache_regions
from bottle import get, hook, request, response, route, run, static_file, default_app  # @UnusedImport
from peewee import *  # @UnusedWildImport
from playhouse.pool import PooledMySQLDatabase

conf = RawConfigParser()
conf.read('kkauthd.conf')

db = None
if conf.get('db', 'type') == 'mysql':
    db = PooledMySQLDatabase(database=conf.get('db', 'database'),
                             host=conf.get('db', 'host'),
                             port=conf.getint('db', 'port'),
                             user=conf.get('db', 'user'),
                             passwd=conf.get('db', 'passwd'),
                             max_connections=10,
                             threadlocals=True)
elif conf.get('db', 'type') == 'sqlite':
    db = SqliteDatabase(conf.get('db', 'file'), threadlocals=True)
    
cache_regions.update({'short': {'expire': conf.getint('cache', 'expire'),
                                'type': 'memory'}})

@get('/')
def index():
    return static_file('index.html', root='static')

@get('/static/<path:path>')
def serve_static(path):
    return static_file(path, root='static')

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    id = PrimaryKeyField()
    login = CharField()
    realm = CharField(null=True)
    name = CharField()
    hash_type = CharField(null=True)
    hash = CharField(null=True)
    active = BooleanField(default=True)
    class Meta:
        indexes = (
            (('login', 'realm'), True),
        )

class Target(BaseModel):
    id = PrimaryKeyField()
    path = CharField()
    description = CharField(null=True)
    class Meta:
        indexes = (
            (('path',), True),
        )

class Action(BaseModel):
    id = PrimaryKeyField()
    name = CharField()
    description = CharField(null=True)
    class Meta:
        indexes = (
            (('name',), True),
        )
    
class Access(BaseModel):
    user = ForeignKeyField(User)
    target = ForeignKeyField(Target)
    action = ForeignKeyField(Action)
    class Meta:
        indexes = (
            (('user', 'target', 'action'), True),
        )

def ssha1(salt, plain):
    h = sha1(plain)
    h.update(salt)
    return h.digest()

def validate_login(realm, header):
    schema, token = header.split(' ')
    if schema.lower() == 'basic':
        login, passwd = token.decode('base64').split(':')
    else:
        return
    
    user = User.get(User.login==login, User.realm==realm)
    if user is None or user.active is False:
        return
    if user.id == 0:
        return user
    
    if user.hash_type == 'SHA1' and \
        sha1(passwd).digest() == user.hash.decode('base64'):
        return user
    elif user.hash_type == 'SSHA1' and \
        ssha1(user.salt.decode('base64'), passwd) == user.hash.decode('base64'):
        return user

@cache_region('short', 'check_access')
def check_access(realm, header, target_path, action_name):
    db.connect()
    
    try:
        user = validate_login(realm, request.headers.get('Authorization'))
        target = Target.get(Target.path==target_path)
        action = Action.get(Action.name==action_name)
        c = Access.select().where(Access.user==user,
                                  Access.target==target,
                                  Access.action==action
                                  ).count()
        if c > 0:
            return user
    except:
        pass
    

@hook('after_request')
def _close_db():
    if not db.is_closed():
        db.close()

@route('/handler')
def handle():
    target_path, realm, action_name = None, None, None
    #parsed = urlparse(request.headers.get('X-Original-URI'))
    method = urlparse(request.environ.get('KKAUTHD_ORIG_METHOD'))  # @UndefinedVariable
    parsed = urlparse(request.environ.get('KKAUTHD_ORIG_URI'))  # @UndefinedVariable
    
    if parsed.path.startswith('/svn'):
        target_path = 'svn:%s:%s' % tuple(parsed.path.split('/')[2:4])
        realm = 'SVN'
        if method in ['GET', 'HEAD', 'OPTIONS', 'PROFIND', 'REPORT']:
            action_name = 'svn:read'
        else:
            action_name = 'svn:write'
    elif parsed.path.startswith('/websvn'):
        reponame = parse_qs(parsed.query)['reponame'][0]
        target_path = 'svn:%s:%s' % tuple(reponame.split('.'))
        realm = 'SVN'
        action_name = 'svn:read'
    
    user = check_access(realm, request.get_header("Authorization"), target_path, action_name)
    if user:
        response.set_header('X-KKAuth-Login', user.login)
        response.set_header('X-KKAuth-Name', user.name.encode('utf8'))
        response.status = 200
    else:
        response.set_header('WWW-Authenticate', 'Basic realm="%s"' % realm)
        response.status = 401

class PasswordToken(BaseModel):
    user = ForeignKeyField(User, primary_key=True)
    mail = CharField()
    token = CharField(null=True)
    class Meta:
        indexes = (
            (('token',), True),
        )

app = default_app()

if __name__ == '__main__':
    logger = logging.getLogger('peewee')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    if argv[1] == 'run':
        run(port=8000, debug=True)
    elif argv[1] == 'initdb':
        db.connect()
        db.create_tables([User, Target, Action, Access, PasswordToken])
    else:
        print('Usage: python kkauthd.py start|stop|initdb|run')
