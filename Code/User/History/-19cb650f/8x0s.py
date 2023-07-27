# -*- coding: utf-8 -*-

import six
import os
import time
import db
import urllib.parse as urlparse
import json
import io
from http.cookies import SimpleCookie
import cgi
from munch import Munch as Bunch
from myutil import jsonify
from myutil import str2bool
import myutil
import sqlalchemy
import plug
from datetime import datetime
import dateutil.parser
import inspect
import re
import sentry_sdk
from nodes import nodes

# Left side is the system name - right side is list of domains which are allowed to make requests WITH COOKIES to that domain
allowed_integrations = {
    'yoginis.gymsystem.se': ['yoginis.se', '64.227.79.114', 'yoginis.webblandskapet.se'],
    'fit4fightgym.gymsystem.se': ['fit4fightgym.se'],
    'metodikum.lokalsystem.se': ['zoeziweb.s3.eu-north-1.amazonaws.com'],
    'addon32.zoezi.se': ['dev.altromondoyoga.com', 'dev.altromondoyoga.com:3000']
}

always_allow_integrations_from = ['developer.zoezi.se', 'addon1.zoezi.se', 'portal.local', 'developer.zoezidev.se', 'developer.zoezitest.com']

current_version = plug.utils.get_current_version()

if not os.getenv('ECS'):
    os.makedirs('/node/logs/uwsgi/proc', exist_ok=True)

# FIXME: Restrict to GET/POST etc

def application(env, start_response):
    try:
        host = env['HTTP_HOST']
        db.setupDatabase(host)
        db.createSession()
        res = applicationInternal(env, start_response)
        if 'gunicorn' in env.get('SERVER_SOFTWARE', ''):
            res = iter([res])
        return res
    finally:
        db.closeSession()

def rpc(env, start_response):
    try:
        host = env['HTTP_HOST']
        db.setupDatabase(host)
        db.createSession()
        res = rpc_internal(env, start_response)
        if 'gunicorn' in env.get('SERVER_SOFTWARE', ''):
            res = iter([res])
        return res
    finally:
        db.closeSession()

def makeError(path, type, message, args=None, translate=True):
    if translate:
        translateMessages = path.startswith('/memberapi') or path.startswith('/public')
        if translateMessages:
            message = db.translate(message)
    res = {"type": type, "message": message}
    if args is not None:
        res['args'] = args
    return jsonify(res)

def checkAccess(apiData, op, args, apiFunction):
    spec = inspect.getfullargspec(apiFunction)

    if 'apiData' not in spec.args:
        del args['apiData']

    if 'modules' in op and op['modules']:
        for m in op['modules']:
            db.validateModule(m)

    if op.get('session') == True:
        if apiData['sessionId']:
            db.User._validateSessionApiData(apiData)
        else:
            raise db.PermissionException()

    if 'chain' in op and op['chain']:
        chain = plug.chain.get_chain()
        if chain not in op['chain']:
            raise db.PermissionException()

    if 'access' in op and op['access']:
        user = db.User._validateSessionApiData(apiData)
        for a in op['access']:
            user.validatePermission(a)
        if 'staff' in spec.args and 'staff' not in args:
            args['staff'] = user
        if 'user' in spec.args and 'user' not in args:
            args['user'] = user

def check_apis(apis):
    if not db.Settings._getSettings().test:
        return

    # permissions = plug.addon.api.get_all_permissions()
    # modules = lmap(lambda x: x.id, db.session.query(db.Module).all())
    # for path in apis:
    #     api = apis[path]

    #     for op in api['operations']:
    #         for a in op.get('access', []) or []:
    #             if a not in permissions:
    #                 raise Exception('{} is not a valid permission'.format(a))
    #         for m in op.get('modules', []) or []:
    #             if m not in modules:
    #                 raise Exception('{} is not a valid module'.format(m))

    return

    types = plug.get_api_param_types()
    for type in lfilter(lambda x: x and x[0].isupper(), types):
        for c in db.Base._decl_class_registry.values():
            if hasattr(c, '__name__') and c.__name__ == type:
                break
        else:
            raise Exception("Param type <{}> is not valid".format(type))

    for type in lfilter(lambda x: not x or x[0].islower(), types):
        if type in (None, 'json', 'date', 'datetime', 'string', 'integer', 'int', 'bool', 'boolean'):
            break
    else:
        raise Exception("Param type <{}> is not valid".format(type))

    print(types)

def applicationInternal(env, start_response):
    start_time = time.time()
    query = env['QUERY_STRING']
    query = dict(urlparse.parse_qsl(query, keep_blank_values=True))
    path = env['PATH_INFO']
    method = env['REQUEST_METHOD']
    post2 = env.get('HTTP_ENCODER', None) == 'post2'

    def is_bot():
        user_agent = env.get('HTTP_USER_AGENT')
        if not user_agent:
            return False
        for k in ['BingPreview', 'msnbot']:
            if k in user_agent:
                return True
        return False

    ip = env['REMOTE_ADDR']
    if ip == nodes['loadbalancer.privateip']:
        ip = env.get('HTTP_LB_CLIENT_IP')

    length = 0
    body = ""
    bodyFile = ""
    nameFile = ""
    bodyFiles = []
    formData = {}
    fs = None

    cookie = ""
    if 'HTTP_COOKIE' in env:
        cookie = env['HTTP_COOKIE']

    origin = "*"
    if 'HTTP_ORIGIN' in env:
        origin = env['HTTP_ORIGIN']

    apikey = None
    app = None
    if 'HTTP_AUTHORIZATION' in env:
        u = env['HTTP_AUTHORIZATION'].split(' ')[-1]
        if u:
            apikey = u
            app = plug.app.get_app(apikey)

    sessionId = ""
    cookie = re.sub(r'acceptcookie=?;?', '', cookie)  # https://github.com/python/cpython/issues/81458
    cookies = SimpleCookie(cookie)
    if 'staffsession' in cookies:
        sessionId = cookies['staffsession'].value
    if 'session' in cookies:
        sessionId = cookies['session'].value
    setSession = 'staffsession' in cookies and not 'session' in cookies
    querySession = query.get('session', None)
    if querySession is not None:
        sessionId = querySession

    plug.thread.get_session_cache('api.py')['apiData'] = apiData = {}
    apiData['method'] = method
    apiData['path'] = path
    apiData['query'] = query
    apiData['cookie'] = cookie
    apiData['cookies'] = cookies
    apiData['ip'] = ip
    apiData['sessionId'] = sessionId

    apiData['app'] = app
    apiData['user'] = None # Set in db.py, later used by log function
    apiData['env'] = env
    apiData['is_post2'] = post2
    apiData['apikey'] = apikey

    if 'HTTP_REFERER' in env:
        apiData['referer_page'] = env['HTTP_REFERER'].rsplit('/', 1)[-1].rstrip('?')

    res = None

    if not path.startswith("/api/"):
        start_response('404 Not found', [('Content-Type', 'text/html')])
        return b''

    path = path[4:]

    # Get API version
    apiVersion = None
    n = path[1:].find('/')
    if n != -1 and path[1] == 'v':
        apiVersion = path[2:n+1]
        if '.' in apiVersion:
            path = path[n+1:]
        else:
            apiVersion = None
    apiData['version'] = apiVersion

    if path == "/status":
        db.session.query(db.User).first()
        start_response('200 OK', [('Content-Type', 'text/html'),
                                  ('Access-Control-Allow-Origin', origin)])
        return b''

    apiData['path'] = path

    apis = plug.get_apis()
    if not hasattr(applicationInternal, 'apitest_performed'):
        check_apis(apis)
        applicationInternal.apitest_performed = True

    if path not in apis:
        apis = plug.addon.get_apis_from_started_addons()

    if path not in apis:
        start_response('404 Not found', [('Content-Type', 'text/html')])
        return b''

    if path in ('/staff/login', '/memberapi/login') and 'password' in query:
        apiVersion = '1.0'

    op = op2 = None
    current_version = plug.utils.version_tuple(plug.utils.get_current_version())
    apiVersion = plug.utils.version_tuple(apiVersion, current_version)
    operations = apis[path]['operations']

    for i in operations:
        version = plug.utils.version_tuple(i.get('version'), current_version)
        if version == apiVersion and i['method'] == method:
            op = i
            break
        if apiVersion < version:
            continue

        if i['method'] == method:
            if not op or version > plug.utils.version_tuple(op.get('version'), current_version):
                op = i
        else:
            if not op2 or version > plug.utils.version_tuple(op2.get('version'), current_version):
                op2 = i

    if not op:
        op = op2 or operations and operations[0]
    if op is None:
        start_response('404 Not found', [('Content-Type', 'text/html')])
        return b''

    apiData['log'] = (method == 'POST' and op.get('log', True)) or (app and app.log)
    apiData['apiVersion'] = op.get('version')
    apiFunction = op['function']

    if apiFunction is None:
        start_response('404 Not found', [('Content-Type', 'text/html')])
        return b''

    if hasattr(apiFunction, '_post2'):
        post2 = True
        apiData['is_post2'] = True

    if 'CONTENT_LENGTH' in env and len(env['CONTENT_LENGTH']) > 0 and 'CONTENT_TYPE' in env:
        length = int(env.get('CONTENT_LENGTH', '0'))

        ctype, pdict = cgi.parse_header(env['CONTENT_TYPE'])
        if ctype == 'multipart/form-data':
            fs = cgi.FieldStorage(fp=io.BytesIO(env['wsgi.input'].read()), environ=env)
            if 'file' in fs:
                bodyFile = fs['file'].file.read()
                bodyFiles = [bodyFile]
                nameFile = fs['file'].filename
            else:
                i = 0
                while True:
                    n = 'file-' + str(i)
                    if n in fs:
                        f = fs[n].file.read()
                        bodyFiles.append(f)
                        nameFile = fs[n].filename
                    else:
                        break
                    i += 1

                if i > 1:
                    nameFile = ''

            # form
            for k in fs.keys():
                if fs[k].type == 'text/plain':
                    formData[k] = fs[k].file.read()
        else:
            try:
                body = env['wsgi.input'].read(length).decode('utf8')
            except:
                start_response('400 Bad request', [('Content-Type', 'text/html')])
                return b''
            if post2:
                body_query = plug.json.load(body) or {}
            else:
                body_query = dict(urlparse.parse_qsl(body, keep_blank_values=True))
            if body_query:
                query.update(body_query)

    try:
        from sentry_sdk import configure_scope
        with configure_scope() as scope:
            scope.set_tag('path', path)
            scope.set_tag('app_id', app.id if app else None)
    except:
        pass

    apiData['body'] = body
    apiData['bodyFile'] = bodyFile
    apiData['nameFile'] = nameFile
    apiData['fieldStorage'] = fs
    apiData['bodyFiles'] = bodyFiles
    apiData['formData'] = formData

    type_mapper = {
        'int': int,
        'integer': int,
        'bool': bool,
        'boolean': bool,
        'datetime': datetime,
        'list': list,
        'array': list
    }

    args = dict()
    args["apiData"] = apiData
    parsingException = None
    if 'parameters' in op and method != 'OPTIONS':
        try:
            for param in op['parameters']:
                name = param['name']
                param_type = param['type'] if 'type' in param else param['dataType'] if 'dataType' in param else "string"
                value = None
                has_param = True

                if param.get('paramType', None) == "body":
                    if param_type == 'file':
                        value = apiData['bodyFile']
                    elif param_type == 'files':
                        value = apiData['bodyFiles']
                    else:
                        try:
                            value = json.loads(apiData['body'])
                        except:
                            if param['required']:
                                raise db.InvalidInputException("Cannot parse body. Parameter {} is missing for API {}".format(name, path))
                else:
                    if name in apiData['query']:
                        value = apiData['query'][name]
                        if param.get('parse'):
                            if param_type == 'date':
                                if value:
                                    value = dateutil.parser.parse(value)
                    else:
                        has_param = False
                        if param['required']:
                            if param.get('paramType') != 'query':
                                # Try to get from body
                                try:
                                    value = json.loads(apiData['body'])
                                except:
                                    raise db.InvalidInputException("Cannot parse body. Parameter {} is missing for API {}".format(name, path))
                            else:
                                raise db.InvalidInputException("Value <{}> is required for API [{}]".format(name, path))

                if post2:
                    if value is not None or param['required']:
                        rtype = type_mapper.get(param_type, None)
                        if rtype:
                            if not isinstance(value, rtype):
                                raise db.InvalidInputException('value <{}> should be {} for API {}'.format(name, rtype, path))
                    if has_param:
                        args[name] = value
                else:
                    if param_type in ('integer', 'int') and value not in [None, '']:
                        try:
                            if value == '' and not param['required']:
                                value = None
                            else:
                                value = int(value)
                        except:
                            raise db.InvalidInputException("Value <{}> should be integer for API {}".format(name, path))

                    if param_type in ['boolean', 'bool'] and value not in [None, '']:
                        value = str2bool(value)

                    if has_param:
                        args[name] = myutil.emptyStringsToNull(value)
        except db.InvalidInputException as e:
            parsingException = e

    printStuff = False
    mail_exception = False

    res = plug.ApiResponse()
    apiData['result'] = res
    result_success = False
    validate_result = False
    build_api_doc = False
    apilog = None
    if method != 'OPTIONS':
        try:
            if not os.getenv('ECS'):
                log_request(apiData)
            if apiData['log']:
                apilog = db.ApiLog.logRequest(apiData)
            if parsingException:
                raise parsingException
            checkAccess(apiData, op, args, apiFunction)
            if post2:
                result = apiFunction(**args)
                if isinstance(result, plug.net.Channel2):
                    result = {'$channel2': result.key}
                if result is None:
                    if not res.data:
                        res.data = 'null'
                elif isinstance(result, bytes):
                    res.data = result
                else:
                    if isinstance(result, plug.ApiResponse):
                        res = result
                    else:
                        res.data = plug.json.dump(result)
            else:
                result = apiFunction(**args)
                if result == None:
                    pass
                elif isinstance(result, plug.net.Channel2):
                    res.data = jsonify({'$channel2': result.key})
                elif isinstance(result, plug.ApiResponse):
                    res = result
                elif isinstance(result, bytes):
                    res.data = result
                else:
                    res.data = jsonify(result)

            if validate_result and op['responseClass'] is not None and not isinstance(op['responseClass'], (six.binary_type, six.text_type)):
                plug.validate_api_result(path, json.loads(res.data), op['responseClass'])

            if build_api_doc and not(op['responseClass'] is not None and not isinstance(op['responseClass'], (six.binary_type, six.text_type))):
                plug.build_api_doc(path, res, op, args)

            result_success = True
        except db.LoginException as e:
            res.code = "401 Unauthorized"
            message = e.message or "Invalid username or password"
            res.data = makeError(path, "login", message)
        except db.InvalidSessionException:
            res.code = "401 Unauthorized"
            res.data = makeError(path, "session", "Invalid session")
        except db.CustomException as e:
            res.code = "400 Bad request"
            db.log("Custom exception: " + e.message if e.message else 'None')
            printStuff = True
            mail_exception = not e.nomail and e
            res.data = makeError(path, "custom", e.message)
        except db.InvalidInputException as e:
            res.code = "400 Bad request"
            db.log("Invalid input data: " + e.message if e.message else 'None')
            if not is_bot():
                printStuff = True
                mail_exception = not e.nomail and e
            res.data = makeError(path, e.error_code or "input", e.message or "Invalid input data", args=e.data)
        except plug.e.DataNotAvailableException as e:
            mail_exception = False#not e.nomail
            res.code = '410 Gone'
            res.data = makeError(path, e.error_code, e.message or "Data not available")
        except db.TooShortPasswordException:
            res.code = "400 Bad request"
            res.data = makeError(path, "input", "The password must be at least {0} characters", [6])
        except db.DuplicateEntryException as e:
            res.code = "400 Bad request"
            db.log("Duplicate entry exception: " + str(e))
            printStuff = True
            mail_exception = not e.nomail and e
            res.data = makeError(path, "duplicate", "Data duplicated")
        except db.PermissionException:
            db.log("PermissionException")
            res.code = "401 Unauthorized"
            res.data = makeError(path, "access", "Insufficient access rights")
        except db.MissingTrainingCardException:
            res.code = "400 Bad request"
            db.log('MissingTrainingCardException')
            res.data = jsonify({'type': 'missingtrainingcard', 'message': ''})
        except db.NotPossibleToBookUsingCardException:
            res.code = "400 Bad request"
            db.log('NotPossibleToBookUsingCardException')
            res.data = jsonify({'type': 'notpossibletobookusingcard', 'message': ''})
        except db.CCUFailedException as e:
            res.code = "400 Bad request"
            db.log('CCUFailedException')
            res.data = jsonify({'type': 'ccu', 'message': '', 'bundle_id': e.bundle_id})
        except sqlalchemy.exc.IntegrityError as e:
            res.code = "400 Bad request"
            db.session.rollback()
            db.log("Duplicate entry...: " + str(e))
            printStuff = True
            mail_exception = e
            res.data = makeError(path, "duplicate", "Data duplicated", translate=False)
        except db.PaymentFailedException as e:
            mail_exception = not e.nomail and e
            res.code = "400 Bad request"
            args = {'reason': e.message} if e.message else None
            res.data = makeError(path, e.error_code, "PAYMENT_FAILED", args)
        except db.ResourceNotFreeException as e:
            res.code = "400 Bad request"
            res.data = jsonify({'type': 'collision', 'message': '', 'staffs': e.staffs})
        except plug.e.Response as e:
            res.code = "400 Bad request"
            res.data = plug.string.bytes(plug.json.dump({'type': e.error_code, 'message': e.message}))
        except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.ProgrammingError, plug.e.mysql.OperationalError, plug.e.mysql.ProgrammingError) as e:
            db.session.close()
            db.session = None
            db.engine.dispose()
            db.engine = None
            db.printException()
            printStuff = True
            mail_exception = e
            res.code = "400 Internal server error"
            res.data = makeError(path, "error", "Internal server error", translate=False)
        except plug.e.Exception as e:
            db.printException()
            printStuff = True
            mail_exception = not e.nomail and e
            res.code = "400 Bad request"
            res.data = makeError(path, e.error_code, e.message, args=e.data, translate=False)
        except Exception as e:
            db.printException()
            printStuff = True
            mail_exception = e
            res.code = "400 Internal server error"
            res.data = makeError(path, "error", "Internal server error", translate=False)
        finally:
            if db.session:
                db.session.rollback()
                db.ApiLog.extendLog(apiData, res, int((time.time() - start_time)*1000), apilog=apilog)

    plug.db.event.resolve_event(result_success)

    if printStuff:
        db.log("env = " + str(env))
        db.log("Args: " + str(args)[:1000])
        db.log("body = " + str(body[:200]))

    if mail_exception:
        sentry_sdk.capture_exception(error=mail_exception)

    if res.code.startswith('400') and db.session and db.currentUser and db.currentUser.superUser:
        faildata = {'data': res.data, 'code': res.code}
        faildata['exception'] = db.getException()
        db.sendToChangeQueue('apifail', faildata, 'add')

    if setSession and 'Set-Cookie' not in res.headers:
        res.headers['Set-Cookie'] = db.getSessionCookieString('session', sessionId)

    if res.data is None:
        res.data = b'[]'
    if isinstance(res.data, str):
        res.data = res.data.encode('utf8')

    res.headers.update({
        'Content-Length': str(len(res.data)),
        'Access-Control-Allow-Origin': origin,
        'Access-Control-Allow-Headers': 'content-type, encoder, authorization',
        'Cache-control': 'no-store, max-age=0'
    })

    allow_api_integration = False
    if origin:
        from_domain = origin.split('://')[-1].split('/')[0]
        allowed_for_hostname = allowed_integrations.get(plug.db.get_hostname())
        allow_api_integration = (allowed_for_hostname and from_domain in allowed_for_hostname) or from_domain in always_allow_integrations_from

    if allow_api_integration:
        res.headers['Access-Control-Allow-Credentials'] = 'true'

    headers = []
    if 'Set-Cookie' in res.headers:
        # Special handling of Set-Cookie - which we allow to be a list, to allow setting multiple cookies
        # That is the only response header which can appear several times
        cookies = res.headers['Set-Cookie']
        del res.headers['Set-Cookie']
        cookies = [cookies] if not isinstance(cookies, list) else cookies
        headers = lmap(lambda cookie: ('Set-Cookie', cookie), cookies)

    if 'Content-Type' in res.headers and res.headers['Content-Type'] == 'text/html':
        domains = db.Settings._getSettings().integration_domains or ''
        if domains:
            domains = ' ' + domains.replace(',', ' ')
        res.headers['Content-Security-Policy'] = "frame-ancestors 'self'{domains};".format(domains=domains)

        if not plug.db.should_show_up_on_google():
            res.headers['X-Robots-Tag'] = 'none'

    headers += list(res.headers.items())
    headers = lmap(lambda x: (x[0], str(x[1])), headers)

    if method != 'OPTIONS' and not os.getenv('ECS'):
        log_request(None)
    start_response(res.code, headers)
    return res.data

def log_request(apiData):
    filename = '/node/logs/uwsgi/proc/' + current_version + '_' + str(os.getpid())
    if apiData:
        data = '{}\n{}\n{}\n{}\n{}\n{}\n{}'.format(
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            apiData['ip'],
            plug.db.get_hostname(),
            apiData['method'],
            apiData['path'],
            apiData['query'],
            apiData['body']
        )
        with open(filename, 'w') as f:
            f.write(data)
            f.flush()
    else:
        os.remove(filename)

class NoMethodError(Exception):
    pass

def make_rpc_call(method, params):
    argv = []
    kw = {}
    if params:
        if isinstance(params, list):
            argv = params
        else:
            kw = params

    parts = method.split('.')
    fn = plug
    for k in parts[1:]:
        fn = getattr(fn, k, None)
        if fn is None:
            raise NoMethodError('No such method \'{}\''.format(method))

    with plug.db.commit_block():
        result = fn(*argv, **kw) # type: ignore
    return result

def make_rpc_response(result, error, request_id):
    if not request_id:
        return b''

    response = {
        'jsonrpc': '2.0',
        'id': request_id
    }
    if error:
        response['error'] = error
    else:
        response['result'] = result
    return plug.json.dump(response).encode('utf8')

def rpc_internal(env, start_response):
    length = int(env.get('CONTENT_LENGTH', '0'))
    body = env['wsgi.input'].read(length).decode('utf8')
    rpc_request = json.loads(body)
    method = rpc_request.get('method') or ''
    params = rpc_request.get('params') or []
    request_id = rpc_request.get('id')

    if not method.startswith('plug.'):
        start_response('404 Not found', [('Content-Type', 'application/json')])
        return make_rpc_response(None, {'code': -32601, 'message': 'Method not found'}, request_id)
    
    if method != 'plug.healthcheck':
        print('RPC call: {} {}'.format(method, params))

    try:
        result = make_rpc_call(method, params)
    except NoMethodError:
        start_response('404 Not found', [('Content-Type', 'application/json')])
        return make_rpc_response(None, {'code': -32601, 'message': 'Method not found'}, request_id)
    except Exception as e:
        print('Exception in RPC call: {}'.format(e))
        print(db.getException())
        start_response('500 Internal Server Error', [('Content-Type', 'application/json')])
        return make_rpc_response(None, {'code': -32603, 'message': 'Internal error'}, request_id)

    start_response('200 OK', [('Content-Type', 'application/json')])
    return make_rpc_response(result, None, request_id)
