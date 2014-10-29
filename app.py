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


@socketio.on('events', namespace='/socket.io/')
def events():

    emit('events', node.events[:10])


@socketio.on('markets', namespace='/socket.io/')
def markets():

    emit('markets', node.markets[:10])


@socketio.on('juries', namespace='/socket.io/')
def juries():

    emit('juries', node.juries[:10])


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
    """Example:
    
    $ ./truth_cli.py ask_decision j_1 world_end_this_week is the world going to end sometime this week

    Output:
    {
       "count": 793, 
       "decision_id": "world_end_this_week", 
       "pubkeys": [
          "04fe2654f07ffe0c66529707762aabebbec19870aaa36dbc503526a556e55c4926f093a23596337bce001a5a219d800917359f4bc5d5ed58a727243580ce1d2e20"
       ], 
       "signatures": [
          "G8oZq7bqXskySI/HCV4n9xmqe0q+n0j3TFQfCTZvwgLRkOGHKwiBCQF7kATHna5a6aEqZ6fWbBqUoAoHHs9LLV0="
       ], 
       "txt": "world_end_this_week is the world going to end sometime this week", 
       "type": "propose_decision", 
       "vote_id": "j_1"
    }

    """
    data = node.send({ 'command':['ask_decision', args['juryId'], args['eventId'], '"'+args['eventText']+'"'] })

    app.logger.info(data)


@socketio.on('buy-shares', namespace='/socket.io/')
def buy_shares(args):
    """Example:

    ./truth_cli.py info world_ending_PM
    {
       "B": 1000, 
       "author": "11gt9t8wqqmBPt8rSmAnhcyvwA2QrpM", 
       "decisions": [
          "world_end_this_week"
       ], 
       "fees": 0, 
       "shares_purchased": [
          0, 
          0
       ], 
       "states": [
          "yes", 
          "no"
       ], 
       "states_combinatory": [
          [
             1
          ]
       ]
    }

    $ ./truth_cli.py buy_shares
    What is the unique name for this prediction market?
    >world_ending_PM
    how many states does this pm have?
    >2
    how many shares do you want to buy of state 0? To sell states, use negative numbers.
    >10
    how many shares do you want to buy of state 1? To sell states, use negative numbers.
    >0
    What is your brainwallet
    >my_password
    now for a little proof of work. This may take several minutes. The purpose of this pow is to make it more difficult for a front runner to steal your trade.
    tx for copy/pasting into pushtx: eyJjb3VudCI6IDc5OCwgIm5vbmNlIjogNDQ4MDk3OTgwNjI3MTk5NzUzNDg3MjkxNTE5NzUyNDU0
    MTUwNzA2OSwgImJ1eSI6IFsxMCwgMF0sICJ0eXBlIjogImJ1eV9zaGFyZXMiLCAiUE1faWQiOiAi
    d29ybGRfZW5kaW5nX1BNIiwgInNpZ25hdHVyZXMiOiBbIkhBUngrUzlLcjZ3cEtIbDJHdm9YYTFR
    a3I2bS8vYWY1dUVaZ05OQ1BncHhZR1EzZlVpc0pab2RSSUFOaURvMFRWT0RTRkdYNkx2WSs3bWhn
    eWlod3dMZz0iXSwgInB1YmtleXMiOiBbIjA0ZmUyNjU0ZjA3ZmZlMGM2NjUyOTcwNzc2MmFhYmVi
    YmVjMTk4NzBhYWEzNmRiYzUwMzUyNmE1NTZlNTVjNDkyNmYwOTNhMjM1OTYzMzdiY2UwMDFhNWEy
    MTlkODAwOTE3MzU5ZjRiYzVkNWVkNThhNzI3MjQzNTgwY2UxZDJlMjAiXSwgInByaWNlX2xpbWl0
    IjogNX0=

    added tx: 
    {
       "PM_id": "world_ending_PM", 
       "buy": [
          10, 
          0
       ], 
       "count": 798, 
       "nonce": 4480979806271997534872915197524541507069, 
       "price_limit": 5, 
       "pubkeys": [
          "04fe2654f07ffe0c66529707762aabebbec19870aaa36dbc503526a556e55c4926f093a23596337bce001a5a219d800917359f4bc5d5ed58a727243580ce1d2e20"
       ], 
       "signatures": [
          "HARx+S9Kr6wpKHl2GvoXa1Qkr6m//af5uEZgNNCPgpxYGQ3fUisJZodRIANiDo0TVODSFGX6LvY+7mhgyihwwLg="
       ], 
       "type": "buy_shares"
    }

    """
    privkey = tools.db_get("privkey")
    pubkey = tools.privtopub(privkey)
    tx = {
        "fees": 0,
        "pubkeys": [pubkey],
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


@socketio.on('add-market', namespace='/socket.io/')
def add_market(args):
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
        "B": args['marketInv'],
        "PM_id": args['marketId'],
        "decisions": args["marketEvents"].split(','),
        "fees": 0,
        "owner": node.my_address,
        "pubkeys": [pubkey],
        "states": args["marketStates"].split(','),
        "states_combinatory": args["marketDep"],
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
    data = node.send({'command': ['new_address']})
    app.logger.info(data)


###
# main

if __name__ == '__main__':

    socketio.run(app, host='127.0.0.1', port=9000)

