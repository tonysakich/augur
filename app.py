#!/usr/bin/env python

from gevent import monkey
monkey.patch_all()

import json, datetime, sys, os, socket, time, re
from subprocess import call, Popen

from flask import Flask, session, request, escape, url_for, redirect, render_template, g, abort
from flask.ext.socketio import SocketIO, emit, send

from werkzeug import secure_filename

sys.path.insert(0, os.path.join('..'))

app = Flask(__name__)
socketio = SocketIO(app)
app.config['DEBUG'] = True

THRUTHCOIN_CORE_PATH = '../Truthcoin-POW'

###
# route and websocket handlers

@app.route('/', methods=['GET', 'POST'])
def dash():

    if request.method == 'POST':
        if request.form.get('password'):
            start_node(request.form['password'])

    address = send( {'command': ['my_address']} )

    if address:
        status = 'running'
    else:
        status = 'stopped'

    return render_template('dash.html', user={'address': address}, server={'status': status})


@socketio.on('info', namespace='/socket.io/')
def info(arg):

    data = send({ 'command': ['info', 'my_address'] })

    if data:

        emit('info', data)


@socketio.on('peers', namespace='/socket.io/')
def peers():

    data = send({ 'command': ['peers'] })

    if data:

        peers = []

        for peer in data:
            peers.append("%s:%s" % (peer[0][0], peer[0][1]))

        peers = list(set(peers))

        emit('peers', peers)


@socketio.on('start', namespace='/socket.io/')
def start(password):

    start_node(password)


@socketio.on('stop', namespace='/socket.io/')
def stop():

    stop_node()


@socketio.on('buy-shares', namespace='/socket.io/')
def buy_shares():

	tx = truth_cli.build_buy_shares()

	send({ 'command':['pushtx', json.dumps(tx).encode('base64')] })


@socketio.on('make-pm', namespace='/socket.io/')
def make_pm(data):

    tx = truth_cli.build_pm()

    send({ 'command': ['pushtx', json.dumps(tx).encode('base64')] })


@socketio.on('new-address', namespace='/socket.io/')
def new_address(data):

    prikey = tools.det_hash(data)
    pubkey = tools.privtopub(privkey)
    address = tools.make_address([pubkey], 1)

    print('brain: ' +str(c[1]))
    print('privkey: ' +str(privkey))
    print('pubkey: ' +str(pubkey))
    print('address: ' +str(address))


###
# node status and control

def check_status():

    repsonse = send( {'command': ['my_address']} )

    app.logger.info(response)


def start_node(password):

    if sys.platform == 'win32':

        pypath = list(os.path.split(sys.executable))
        pypath[-1] = 'pythonw.exe'
        os.system('start ' + os.path.join(*pypath) +  ' threads.py ' + password)
        sys.exit(0)

    else:
             
        cmd = THRUTHCOIN_CORE_PATH + '/threads.py'

        Popen(['python', cmd, password])

def stop_node():

    if sys.platform == 'win32':

        pypath = list(os.path.split(sys.executable))
        pypath[-1] = 'pythonw.exe'
        os.system('start ' + os.path.join(*pypath) +  ' truth_cli.py stop')
        sys.exit(0)

    else:
             
        cmd = THRUTHCOIN_CORE_PATH + '/truth_cli.py'
        status = call(['python', cmd, 'stop'])

        app.logger.info(status)

###
# API socket communication

def connect():

    port = 8899
    host = 'localhost'

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setblocking(5)

    try:
        s.connect((host, port))
    except:
        return {'error': 'cannot connect host:' + str(host) + ' port:' + str(port)}

    return s


def send(msg, retry=0):

    if retry > 3:
        return {'error': 'could not get a response'}

    s = connect()

    msg['version'] = '0.0009'

    json_msg = json.dumps(msg)
    padded_json = str(len(json_msg)).rjust(5, '0') + json_msg

    app.logger.info(padded_json)

    while padded_json:

        time.sleep(0.0001)

        try:
            sent = s.send(padded_json)

        except:
            return None 

        padded_json = padded_json[sent:]
    
    response = recieve(s)
    
    if response == 'broken connection':
    
        app.logger.error('broken connection: ' + str(msg))
    
        return send(msg, retry=retry+1)
    
    if response == 'no length':
    
        app.logger.error('no length: ' + str(msg))
    
        return send(msg, retry=retry+1)
    
    return response


def recieve(s, data=''):

    MAX_MESSAGE_SIZE = 60000

    try:
        data += s.recv(MAX_MESSAGE_SIZE)

    except:
        time.sleep(0.0001)
        app.logger.info('data not ready')

        receieve(s, data)   

    if not data:
        return 'broken connection'

    if len(data) < 5: 
        return recieve(s, data)

    try:
        length = int(data[0:5])
    except:
        return 'no length'

    data = data[5:]

    while len(data) < length:

        d = s.recv(MAX_MESSAGE_SIZE - len(data))

        if not j:
            return 'broken connection'

        data += d

    data = data.replace('"', '')   # remove outside double quotes

    try:                           # attempt to eval into python object
        data = eval(data)
    except:
        pass

    return data


###
# main

if __name__ == '__main__':

    socketio.run(app, host='127.0.0.1', port=5000)

