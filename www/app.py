#! /usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Kubert'

'''
async web application.
'''


import logging; logging.basicConfig(level=logging.INFO)

import asyncio, os, json, time
from datetime import datetime

from aiohttp import web
'''
add by kuber begined at 2017.03.14
'''
from jinja2 import Environment, FileSystemLoader

import orm
from coroweb import add_route, add_static

def init_jinja2(app, **kw):
    logging.info('init jinja2...')
    option = dict(
        autoescape = kw,get('autoescape',True),
        block_start_string = kw.get('block_start_string','%}'),
        block_end_string = kw.get('block_end_string', '%}'),
        variable_start_string = kw.get('variable_start_string', '{{'),
        variable_end_string = kw.get('variable_end_string', '}}'),
        auto_reload = kw.get('auto_reload', True)
        )
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set jinja2 template path: %s' % path)
    env = Environment(loader = FileSystemLoader(path), **options)
    filters = kw.get('filters', None)
    if filters is not None:
        for name, f in filters.item():
            env.filters[names] = f
    app['__templating'] = env

# 一个记录URL日志的logger可以简单定义如下：
async def logger_factory(app, handler):
    async def logger(request):
        # 记录日志
        logging.info('Request: %s %s' % (request.method, request.path))
        # await asyncio.sleep(0,3)
        # 继续处理请求
        return (await handler(request))
    return logger

async def data_factory(app, handler):
    async def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startswith('application/json'):
                request.__data__ = await request.json()
                logging.info('request json: %s' % str(request.__data__))
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()
                logging.info('request form: %s' % str(request.__data__))    
        return (await handler(request))
    return parse_data

# 而response这个middleware把返回值转换为web.Response对象再返回，以保证满足aiohttp的要求
async def response_factory(app, handler):
    async def respose(request):
        # 结果：
        logging.info('Response handler...')
        r = await handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
        if isinstance(r, int) and r >= 100 and r < 600:
            return web.Response(r)
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(r, int) and t >= 100 and t < 600:
                return web.Response(t, str(m))
        # default
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    return response

def datatime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%分钟前' % (delta // 60)
    if delta < 86400:
        return u'%小时前' % (delta // 3600)
    if delta < 604800:
        return u'%年%月%日' % (dt.year, dt.mouth, dt.day)
            
'''
add by Kuber finished at 3.22
'''
#def index(request):
    #return web.Response(body=b'<h1>Wo Ai NanNan</h1>', content_type='text/html',charset='UTF-8')

#@asyncio.coroutine
def init(loop):
    await orm.create_pool(loop=loop, host='127.0.0.1', port=3306, user='www', password='www', db='awesome')
    #app = web.Application(loop=loop)
    # 加入middleware、jinja2模板和自注册的支持
    # middleware是一种拦截器，一个URL在被某个函数处理前，可以经过一系列的middleware的处理
    # middleware的用处就在于把通用的功能从每个URL处理函数中拿出来，集中放到一个地方
    # 例如，logger的定义在上面可以看到
    app = web.Application(loop=loop,middleware=[
        logger_factory, response_factory
    ])
    init_jinja2(app, filters=dict(datetime=datatime_filter))
    add_route(app, 'handlers')
    add_static(app)
    # 加入middleware、jinja2模板和自注册的支持
    #app.router.add_route('GET','/',index)
    srv = yield from loop.create_server(app.make_handler(),'127.0.0.1', 9000)
    #ssrv = yield from loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
