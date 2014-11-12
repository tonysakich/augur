#!/usr/bin/env python
from __future__ import division

from gevent import monkey
monkey.patch_all()

import json, datetime, sys, os, socket, time, re, pprint, ast

from flask import Flask, session, request, escape, url_for, redirect, render_template, g, abort
from flask.ext.socketio import SocketIO, emit, send

from werkzeug import secure_filename
from node import Node

app = Flask(__name__, template_folder='.')
socketio = SocketIO(app)
node = Node(app, socketio)

app.config['DEBUG'] = True

# change this to point to the core 
app.config['TRUTHCOIN_PATH'] = '../Truthcoin-POW'

###
# routes and websocket handlers

@app.route('/', methods=['GET', 'POST'])
def dash():

    return render_template('app.html')


@socketio.on('info', namespace='/socket.io/')
def info(arg):

    data = node.send({ 'command': ['info', 'my_address'] })

    if data:
        emit('info', data)


@socketio.on('end-date', namespace='/socket.io/')
def end_date():

    end_date = node.next_end_date()

    if end_date:

        formatted_end_date = end_date.strftime('%A, %B %d %H:%M')

        emit('period-end', formatted_end_date)


@socketio.on('my_address', namespace='/socket.io/')
def my_address():

    data = node.send({ 'command': ['my_address'] })

    if data:

        emit('my-address', data)


@socketio.on('check-status', namespace='/socket.io/')
def check_status():

    if node.running:
        emit('node-up')
    elif node.starting:
        emit('node-starting')
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
        emit('show-block', block)


@socketio.on('peers', namespace='/socket.io/')
def peers():

    data = node.send({'command': ['peers']})

    if data:

        peers = []

        for peer in data:
            peers.append("%s:%s" % (peer[0][0], peer[0][1]))
        if peers:
            peers = list(set(peers))
            emit('peers', peers)


@socketio.on('decisions', namespace='/socket.io/')
def decisions():

    emit('decisions', node.decisions[:20])


@socketio.on('markets', namespace='/socket.io/')
def markets():

    markets = node.markets[0:20]

    emit('markets', markets)


@socketio.on('branches', namespace='/socket.io/')
def branches():

    emit('branches', node.branches)


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

    if data:
        if re.match('miner on', data) or re.match('miner is currently: on', data):
            emit('miner', 'on')
        elif re.match('miner is now turned off', data) or re.match('miner is currently: off', data):
            emit('miner', 'off')
        else:
            emit('miner', 'error')


@socketio.on('send-cash', namespace='/socket.io/')
def send_cash(address, amount):

    data = node.send({ 'command':['spend', amount, address] })
    app.logger.debug(data)

@socketio.on('send-reps', namespace='/socket.io/')
def send_reps(address, amount, branch):

    data = node.send({ 'command':['votecoin_spend', amount, branch, address] })
    app.logger.debug(data)

@socketio.on('create-branch', namespace='/socket.io/')
def create_branch(name):

    data = node.send({ 'command':['create_jury', name] })
    app.logger.debug(data)

@socketio.on('add-decision', namespace='/socket.io/')
def add_decision(args):

    # calulate maturation block from days 
    block = node.blockcount + (720 * int(args['decisionTime']))

    data = node.send({ 'command':['ask_decision', args['branchId'], block, args['decisionId'], '"'+args['decisionText']+'"'] })
    app.logger.debug(data)


@socketio.on('trade', namespace='/socket.io/')
def trade(args):

    market = node.get_market(id=args['marketId'])

    if market:

        tx = {
            'type': 'buy_shares',
            'PM_id': args['marketId'],
            'buy': [],
            'pubkeys': [ unicode(node.pubkey) ],
            'count': node.my_tx_count
        }

        if args['tradeType'] == 'sell':
            amount = int(args['tradeAmount']) * -1
        else:
            amount = int(args['tradeAmount'])

        # find state index
        for i, s in enumerate(market['states']):
            app.logger.info("%s %s" % (s, args['marketState']))
            if s == args['marketState']:
                tx['buy'].append(amount)
            else:
                tx['buy'].append(0)

        cost = node.get_cost_per_share(tx)
        tx['price_limit'] = int(cost * 1.01)

        tx = node.trade_pow(tx)

    data = node.send({'command': ['pushtx', tx]})
    app.logger.debug(data)


@socketio.on('add-market', namespace='/socket.io/')
def add_market(args):

    tx = {
        "B": args['marketInv'],
        "PM_id": args['marketId'],
        "decisions": args["marketDecisions"].split(','),
        "fees": 0,
        "owner": node.my_address,
        "states": args["marketStates"].split(','),
        "states_combinatory": args["marketDep"],
        "type": "prediction_market",
    }

    data = node.send({'command': ['pushtx', tx]})
    app.logger.debug(data)


@socketio.on('new-address', namespace='/socket.io/')
def new_address(data):

    data = node.send({'command': ['new_address']})
    app.logger.debug(data)


###
# main

if __name__ == '__main__':

    from gevent.event import Event
    stopper = Event()

    socketio.run(app, host='127.0.0.1', port=9000)

    print "stopping..."

    # stop node monitor
    node.exit(wait_for_exit=True)

    try:
        stopper.wait()
    except KeyboardInterrupt:
        print