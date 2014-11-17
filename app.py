#!/usr/bin/env python
from __future__ import division

from gevent import monkey
monkey.patch_all()

import json, datetime, sys, os, socket, time, re, pprint, ast

from flask import Flask, session, request, escape, url_for, redirect, render_template, g, abort
from flask.ext.socketio import SocketIO, emit, send

from multiprocessing import Process
from werkzeug import secure_filename
from node import Node

app = Flask(__name__, template_folder='.')
socketio = SocketIO(app)
node = Node(app, socketio)

app.config['DEBUG'] = True

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
 
    emit('blockcount', node.blockcount, node.current)


@socketio.on('reporting', namespace='/socket.io/')
def reporting():

    emit('report', node.cycle, namespace='/socket.io/')


@socketio.on('report', namespace='/socket.io/')
def report(report):

    for d in report:

        data = node.send({ 'command': ['vote_on_decision', d['branch'], d['name'], d['value']] })
        app.logger.debug(data)

        node.cycle['reporting'][d['name']]['my_choice'] = d['value']

    # flag account as reported
    node.cycle['reported'] = True

    emit('report', node.cycle, namespace='/socket.io/')


@socketio.on('my_address', namespace='/socket.io/')
def my_address():

    emit('my-address', node.my_account['address'], namespace='/socket.io/')


@socketio.on('get-block', namespace='/socket.io/')
def get_block(block_number):

    data = node.send({ 'command': ['info', block_number] })

    if data:

        block = pprint.pformat(data)
        emit('show-block', block)


@socketio.on('peers', namespace='/socket.io/')
def peers():

    emit('peers', node.peers)


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
    block = node.network_blockcount + 40

    data = node.send({ 'command':['ask_decision', args['branchId'], block, args['decisionId'], args['decisionText']] })
    app.logger.debug(data)

    tx = {
        "B": args['marketInv'],
        "PM_id": "%s-market" % args['decisionId'],
        "decisions": args['decisionId'],
        "fees": 0,
        "owner": node.my_account['address'],
        "states": ['yes', 'no'],
        "states_combinatory": 1,
        "type": "prediction_market",
    }

    data = node.send({'command': ['pushtx', tx]})
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
            'count': node.my_account['tx_count']
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
        "owner": node.my_account['address'],
        "states": args["marketStates"].split(','),
        "states_combinatory": args["marketDep"],
        "type": "prediction_market",
    }

    data = node.send({'command': ['pushtx', tx]})
    app.logger.debug(data)


@socketio.on('ping', namespace='/socket.io/')
def ping():

    data = node.send({ 'command': ['peers'] })

    if data:
        app.logger.debug(data)

        peers = {}
        for peer in data:
            address = "%s:%s" % (peer[0][0], peer[0][1])
            if peers.get(address):
                if int(peer[3]) > peers[address]['blockcount']:
                    peers[address]['blockcount'] = int(peer[3])
            else:
                peers[address] = {'blockcount': int(peer[3]), 'id': peer[2]}
            
        emit('peers', peers)

    data = node.send({ 'command': ['blockcount'] })

    if data:
        app.logger.debug(data)
        
        emit('blockcount', int(data))



# general putpose socket
@socketio.on('command', namespace='/socket.io/')
def command(args):

    data = node.send({ 'command': args })

    if data:

        app.logger.debug(data)

        if args[0] == 'peers':

            peers = {}
            for peer in data:
                address = "%s:%s" % (peer[0][0], peer[0][1])
                if peers.get(address):
                    if int(peer[3]) > peers[address]['blockcount']:
                        peers[address]['blockcount'] = int(peer[3])
                else:
                    peers[address] = {'blockcount': int(peer[3]), 'id': peer[2]}
                
            emit('peers', peers)

        elif args[0] == 'blockcount':

           emit('blockcount', int(data))

        elif args[0] == 'mine':

            if re.match('miner on', data) or re.match('miner is currently: on', data):
                emit('miner', 'on')
            elif re.match('miner is now turned off', data) or re.match('miner is currently: off', data):
                emit('miner', 'off')
            else:
                emit('miner', 'error')



###
# main

if __name__ == '__main__':

    from gevent.event import Event
    stopper = Event()

    server = Process(target=socketio.run(app, host='127.0.0.1', port=9000))
    server.start()

    print "stopping..."

    # stop node monitor
    node.exit(wait_for_exit=True)

    try:
        stopper.wait()
    except KeyboardInterrupt:
        print