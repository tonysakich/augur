#!/usr/bin/env python
from __future__ import division

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

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(HERE, os.pardir, "Truthcoin-POW"))

import tools

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
def add_event(args):

    data = node.send({ 'command':['ask_decision', args['juryId'], args['eventId'], '"'+args['eventText']+'"'] })

    app.logger.info(data)


@socketio.on('buy-shares', namespace='/socket.io/')
def buy_shares():

    pass    


@socketio.on('make-pm', namespace='/socket.io/')
def make_pm(args):
    """
    Example:
        What is the address or pubkey of the owner of the PM?
        >11gt9t8wqqmBPt8rSmAnhcyvwA2QrpM
        What is the unique name for this new prediction market?
        >weatherPM1
        how big should B be? Initial investment is B*ln(n) where n is the number of states
        >10000
        how many decisions is this prediction market to be based upon?
        >1
        What is the unique name of the 0 decision?
        >what
        how many states can this PM result in?
        >2
        what is the text title of the 0 state?
        >rain
        how does the 0 state depend upon the outcome of the decisions? For example: if there are 2 decisions, and this market only comes true when the first is "yes" and the second is "no", then you would put: "1 0" here.
        >1
        what is the text title of the 1 state?
        >sun
        {
           "B": 10000, 
           "PM_id": "weatherPM1", 
           "count": 714, 
           "decisions": [
              "what"
           ], 
           "fees": 0, 
           "owner": "11gt9t8wqqmBPt8rSmAnhcyvwA2QrpM", 
           "pubkeys": [
              "04fe2654f07ffe0c66529707762aabebbec19870aaa36dbc503526a556e55c4926f093a23596337bce001a5a219d800917359f4bc5d5ed58a727243580ce1d2e20"
           ], 
           "signatures": [
              "G8fGpV5fF8QDOVgC/1QOtORMv4tMG/wQL7z6xEgNu+ArkHIRyHZvBECXDipUduXJLB0RiyKtZHhkzV78Yi/VJQg="
           ], 
           "states": [
              "rain", 
              "sun"
           ], 
           "states_combinatory": [
              [
                 1
              ]
           ], 
           "type": "prediction_market"
        }
    """
    privkey = tools.db_get("privkey")
    pubkey = tools.privtopub(privkey)
    tx = {
        "B": args["B"],
        "PM_id": args["PM_id"],
        "decisions": args["decisions"],
        "fees": 0,
        "owner": args["owner"], # tools.make_address([pubkey], 1)
        "pubkeys": [pubkey],
        "states": args["states"],
        "states_combinatory": args["states_combinatory"],
        "type": "prediction_market",
    }
    signature = tools.sign(tx, privkey)
    tx["signatures"] = [signature]
    msg = {
        "command": [
            "pushtx",
            base64.b64encode(tx),
            privkey,
        ]
    }
    app.logger.info(msg)
    data = node.send(msg)
    app.logger.info(data)


@socketio.on('new-address', namespace='/socket.io/')
def new_address(data):

    pass


###
# main

if __name__ == '__main__':

    socketio.run(app, host='127.0.0.1', port=9000)

