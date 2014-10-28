#!/usr/bin/env python

from gevent import monkey
monkey.patch_all()

import json, datetime, sys, os, socket, time, re, pprint

from flask import Flask, session, request, escape, url_for, redirect, render_template, g, abort
from flask.ext.socketio import SocketIO, emit, send

from werkzeug import secure_filename
from node import Node

sys.path.insert(0, os.path.join('..'))

app = Flask(__name__, template_folder='.')
socketio = SocketIO(app)
node = Node(app, socketio)

app.config['DEBUG'] = True
app.config['TRUTHCOIN_PATH'] = '../Truthcoin-POW'

###
# routes and websocket handlers

@app.route('/', methods=['GET', 'POST'])
def dash():

    if request.method == 'POST':
        if request.form.get('password'):
            node.start_node(request.form['password'])

    address = node.send( {'command': ['my_address']} )

    if address:
        status = 'running'
    else:
        status = 'stopped'

    return render_template('app.html')


@socketio.on('info', namespace='/socket.io/')
def info(arg):

    data = node.send({ 'command': ['info', 'my_address'] })

    if data:

        emit('info', data)


@socketio.on('my_address', namespace='/socket.io/')
def my_address():

    data = node.send({ 'command': ['my_address'] })

    if data:

        emit('my-address', data)


@socketio.on('check-status', namespace='/socket.io/')
def check_status():

    if node.running:
        emit('node-up')
    else:
        emit('node-down')


@socketio.on('blockcount', namespace='/socket.io/')
def blockcount():

    data = node.send({ 'command': ['blockcount'] })

    if data:

        emit('blockcount', data)


@socketio.on('get-block', namespace='/socket.io/')
def get_block(block_number):

    data = node.send({ 'command': ['info', block_number] })

    if data:

        block = pprint.pformat(data)
        app.logger.info(block)
        emit('show-block', block)


@socketio.on('peers', namespace='/socket.io/')
def peers():

    data = node.send({ 'command': ['peers'] })

    if data:

        peers = []

        for peer in data:
            peers.append("%s:%s" % (peer[0][0], peer[0][1]))

        peers = list(set(peers))

        emit('peers', peers)


@socketio.on('start', namespace='/socket.io/')
def start(password):

    node.start_node(password)


@socketio.on('stop', namespace='/socket.io/')
def stop():

    node.stop_node()


@socketio.on('miner', namespace='/socket.io/')
def miner(arg):

    if arg == 'start':
        data = node.send({ 'command': ['mine', 'on'] })
    elif arg == 'stop':
        data = node.send({ 'command': ['mine', 'off'] })
    else:
        data = node.send({ 'command': ['mine'] })

    app.logger.info(data)
    if data:
        if re.match('miner on', data) or re.match('miner is currently: on', data):
            emit('miner', 'on')
        elif re.match('miner is now turned off', data) or re.match('miner is currently: off', data):
            emit('miner', 'off')
        else:
            emit('miner', 'error')


@socketio.on('send-credits', namespace='/socket.io/')
def send_credits(address, amount):

    data = node.send({ 'command':['spend', amount, address] })


@socketio.on('create-jury', namespace='/socket.io/')
def create_jury(name):

    data = node.send({ 'command':['create_jury', name] })


@socketio.on('add-event', namespace='/socket.io/')
def buy_shares(args):

    data = node.send({ 'command':['ask_decision', args['juryId'], args['eventId'], '"'+args['eventText']+'"'] })

    app.logger.info(data)


@socketio.on('buy-shares', namespace='/socket.io/')
def buy_shares():

    pass    


@socketio.on('make-pm', namespace='/socket.io/')
def make_pm(data):

    pass


@socketio.on('new-address', namespace='/socket.io/')
def new_address(data):

    pass


###
# main

if __name__ == '__main__':

    socketio.run(app, host='127.0.0.1', port=9000)

