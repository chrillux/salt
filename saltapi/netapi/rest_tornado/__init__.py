from multiprocessing import Process
import logging

import sys

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.gen

import salt.auth

from multiprocessing import Process

from . import saltnado

__virtualname__ = 'rest_tornado'

logger = logging.getLogger(__virtualname__)


def __virtual__():
    mod_opts = __opts__.get(__virtualname__, {})

    if 'port' in mod_opts:
        return __virtualname__

    logger.error("Not loading '%s'. 'port' not specified in config",
                 __virtualname__)
    return False


def start():
    '''
    Start the saltnado!
    '''
    mod_opts = __opts__.get(__virtualname__, {})

    if 'pub_uri' not in mod_opts:
        mod_opts['pub_uri'] = 'ipc://eventpublisher'

    # TODO: make this a subprocessing subclass
    p = Process(target=saltnado.EventPublisher, args=(mod_opts, __opts__))
    p.start()

    application = tornado.web.Application([
        (r"/", saltnado.SaltAPIHandler),
        (r"/login", saltnado.SaltAuthHandler),
        (r"/minions/(.*)", saltnado.MinionSaltAPIHandler),
        (r"/minions", saltnado.MinionSaltAPIHandler),
        (r"/jobs/(.*)", saltnado.JobsSaltAPIHandler),
        (r"/jobs", saltnado.JobsSaltAPIHandler),        
    ], debug=mod_opts.get('debug', False))
    
    application.opts = __opts__ 
    application.mod_opts = mod_opts
    application.auth = salt.auth.LoadAuth(__opts__)

    # the kwargs for the HTTPServer
    kwargs = {}
    if not mod_opts.get('disable_ssl', False):
        if 'certfile' not in mod_opts or 'keyfile' not in mod_opts:
            logger.error("Not starting '%s'. Options 'ssl_crt' and "
                    "'ssl_key' are required if SSL is not disabled.",
                    __name__)

            return None
        kwargs['ssl_options'] = {'certfile': mod_opts['ssl_crt'],
                                 'keyfile': mod_opts['ssl_key']}

    http_server = tornado.httpserver.HTTPServer(application, **kwargs)
    try:
        http_server.listen(mod_opts['port'])
    except:
        print 'Rest_tornado unable to bind to port {0}'.format(mod_opts['port'])
        p.terminate()
        raise SystemExit(1)
    tornado.ioloop.IOLoop.instance().start()

    try:
        ioloop.start()
    except KeyboardInterrupt:
        # cleanup eventpublisher
        p.terminate()
        raise SystemExit(0)
