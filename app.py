#!/usr/bin/env python
from __future__ import division

from gevent import monkey
monkey.patch_all()

import json, datetime, sys, os, socket, time, re, pprint, ast, hashlib, random
from decimal import Decimal

from flask import Flask, session, request, escape, url_for, redirect, render_template, g, abort
from flask.ext.socketio import SocketIO, emit, send

from multiprocessing import Process
from werkzeug import secure_filename

# for signing 
import hashlib, base64

from subprocess import call, Popen

# get elliptical signing function so we can create our own tx
import ecdsa

app = Flask(__name__, template_folder='.')
socketio = SocketIO(app)

app.config['DEBUG'] = True

# node API communication
class Api(object):

    MAX_MESSAGE_SIZE = 60000
    BUY_SHARES_TARGET = '0' * 3 + '1' + '9' * 60

    def __init__(self):

        self.tx_count = 0
        self.host = 'localhost'
        self.port = 8899
        self.core_path = '../Truthcoin-POW'

    @property
    def python_cmd(self):

        if sys.platform == 'win32':
            result = os.path.split(sys.executable)[:-1] + ('pythonw.exe',)
        else:
            result = ('python',)

        return os.path.join(*result)

    def start_node(self, password):

        cmd = os.path.join(self.core_path, 'threads.py')
        Popen([self.python_cmd, cmd, password])

    def stop_node(self):

        cmd = os.path.join(self.core_path, 'truth_cli.py')
        status = call([self.python_cmd, cmd, 'stop'])

    def connect(self):

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setblocking(5)

        try:
            s.connect((self.host, self.port))
        except:
            return {'error': 'cannot connect host:' + str(self.host) + ' port:' + str(self.port)}

        return s


    def send(self, msg, retry=0):

        if retry > 3:
            return {'error': 'could not get a response'}

        s = self.connect()

        if retry == 0:

            # add version
            msg['version'] = '0.0009'

            # sniff out pushtx commands and sign and repackage
            if msg['command'][0] == 'pushtx':

                # add required args
                msg['command'][1]['pubkeys'] = [ unicode(self.pubkey) ]
                msg['command'][1]['count'] = self.tx_count

                # hash message, sign and add sig
                h = self.det_hash(msg['command'][1])
                msg['command'][1]['signatures'] = [ ecdsa.ecdsa_sign(h, self.privkey)]

                msg['command'][1] = json.dumps(msg['command'][1]).encode('base64')

                # add privkey to pushtx
                #msg['command'].append(self.privkey)

        json_msg = json.dumps(msg)

        #app.logger.debug('sending: '+json_msg)

        padded_json = str(len(json_msg)).rjust(5, '0') + json_msg

        #app.logger.debug(padded_json)

        while padded_json:

            time.sleep(0.0001)

            try:
                sent = s.send(padded_json)

            except:
                return None 

            padded_json = padded_json[sent:]
        
        response = self.receive(s)
        
        if response == 'broken connection':
        
            app.logger.error('broken connection: ' + str(msg))
        
            return self.send(msg, retry=retry+1)
        
        elif response == 'no length':
    
            app.logger.error('no length: ' + str(msg))
        
            return self.send(msg, retry=retry+1)

        return response


    def receive(self, s, data=''):

        try:
            data += s.recv(self.MAX_MESSAGE_SIZE)

        except:
            time.sleep(0.0001)
            app.logger.info('data not ready')

            self.receive(s, data)   

        if not data:
            return 'broken connection'

        if len(data) < 5: 
            return self.receive(s, data)

        try:
            length = int(data[0:5])
        except:
            return 'no length'

        data = data[5:]

        while len(data) < length:

            d = s.recv(self.MAX_MESSAGE_SIZE - len(data))

            if not j:
                return 'broken connection'

            data += d

        # do anything and everything here to detect the different 
        # malformed response data and massage it back into python

        try:
            data = ast.literal_eval(data)
        except Exception as e:
            app.logger.error(e)

        if type(data) == str and re.match(r'[\{\[]', data):

            try:
                data = ast.literal_eval(data)
            except Exception as e:
                app.logger.error(e)

        return data


    def det_hash(self, tx):

        return hashlib.sha384(json.dumps(tx, sort_keys=True)).hexdigest()[0:64]


    def get_market(self, id=None):

        if id:
            market = self.send({'command':['info', id]})

            return market


    def trade_pow(self, tx):

        tx = json.loads(json.dumps(tx))
        h = self.det_hash(tx)
        tx[u'nonce'] = random.randint(0, 10000000000000000000000000000000000000000)
        a = 'F' * 64

        while self.det_hash(a) > self.BUY_SHARES_TARGET:

            tx[u'nonce'] += 1
            a = {u'nonce': tx['nonce'], u'halfHash': h}

        return tx


    def get_cost_per_share(self, tx):

        market = self.get_market(id=tx['PM_id'])
        B = market['B'] * Decimal(1.0)
        E = Decimal('2.718281828459045')

        def C(s, B): return B * (sum(map(lambda x: E ** (x / B), s))).ln()
        C_old = C(market['shares_purchased'], B)

        def add(a, b): return a + b
        C_new = C(map(add, market['shares_purchased'], tx['buy']), B)

        return int(C_new - C_old)


api = Api()


###
# routes and websocket handlers

@app.route('/', methods=['GET', 'POST'])
def dash():

    return render_template('app.html')


@socketio.on('ping', namespace='/socket.io/')
def ping():

    data = api.send({ 'command': ['peers'] })

    if data:

        peers = {}
        for peer in data:
            address = "%s:%s" % (peer[0][0], peer[0][1])
            if peers.get(address):
                if int(peer[3]) > peers[address]['blockcount']:
                    peers[address]['blockcount'] = int(peer[3])
            else:
                peers[address] = {'blockcount': int(peer[3]), 'id': peer[2]}
            
        emit('peers', peers)

    data = api.send({ 'command': ['blockcount'] })

    if data:
        emit('blockcount', int(data))
    else:
        emit('node-down')

    data = api.send({ 'command': ['mine'] })

    if data:
        if re.match('miner on', data) or re.match('miner is currently: on', data):
            emit('miner', 'on')
        elif re.match('miner is now turned off', data) or re.match('miner is currently: off', data):
            emit('miner', 'off')
        else:
            emit('miner', 'error')


@socketio.on('get-account', namespace='/socket.io/')
def get_account():

    data = api.send({ 'command': ['info', 'my_address'] })

    if data:

        api.address = api.send({ 'command': ['my_address'] })
        api.privkey = str(api.send({ 'command': ['info', 'privkey'] }))
        api.pubkey = ecdsa.privkey_to_pubkey(api.privkey)

        # update tx count for push_tx commands (%$^#%$^)
        api.tx_count = data['count']

        account = {
            'address': api.address,
            'privkey': api.privkey,
            'pubkey': api.pubkey,
            'cash': data['amount'],
            'shares': data['shares'],
            'branches': data['votecoin']
        }

        emit('account', account)


@socketio.on('update-account', namespace='/socket.io/')
def update_account():

    data = api.send({ 'command': ['info', 'my_address'] })

    account = {
        'cash': data['amount'],
        'shares': data['shares'],
        'branches': data['votecoin']
    }

    emit('account', account)


@socketio.on('get-block', namespace='/socket.io/')
def get_block(block_number):

    block = api.send({ 'command': ['info', block_number] })

    if block:
        emit('block', block)


@socketio.on('peers', namespace='/socket.io/')
def peers():

    data = api.send({ 'command': ['peers'] })

    if data:
        emit('peers', data)
       

@socketio.on('blockcount', namespace='/socket.io/')
def blockcount():
 
    data = api.send({ 'command': ['blockcount'] })

    if data:
        emit('blockcount', data)


@socketio.on('report', namespace='/socket.io/')
def report(report):

    data = api.send({ 'command': ['vote_on_decision', report['vote_id'], report['decision_id'], report['state']] })
    app.logger.debug(data)


@socketio.on('explore-block', namespace='/socket.io/')
def explore_block(block_number):

    data = api.send({ 'command': ['info', block_number] })

    if data:
        block = pprint.pformat(data)
        emit('show-block', block)


@socketio.on('start', namespace='/socket.io/')
def start(password):

    api.start_node(password)


@socketio.on('stop', namespace='/socket.io/')
def stop():

    api.stop_node()


@socketio.on('miner', namespace='/socket.io/')
def miner(arg):

    if arg == 'start':
        data = api.send({ 'command': ['mine', 'on'] })
    elif arg == 'stop':
        data = api.send({ 'command': ['mine', 'off'] })

    if data:
        if re.match('miner on', data) or re.match('miner is currently: on', data):
            emit('miner', 'on')
        elif re.match('miner is now turned off', data) or re.match('miner is currently: off', data):
            emit('miner', 'off')
        else:
            emit('miner', 'error')
        app.logger.debug(data)


@socketio.on('send-cash', namespace='/socket.io/')
def send_cash(address, amount):

    data = api.send({ 'command':['spend', amount, address] })
    app.logger.debug(data)


@socketio.on('send-reps', namespace='/socket.io/')
def send_reps(address, amount, branch):

    data = api.send({ 'command':['votecoin_spend', amount, branch, address] })
    app.logger.debug(data)


@socketio.on('create-branch', namespace='/socket.io/')
def create_branch(name):

    data = api.send({ 'command':['create_jury', name] })
    app.logger.debug(data)


@socketio.on('add-decision', namespace='/socket.io/')
def add_decision(args):

    block = args['decisionMaturation']

    args['decisionId'] = hashlib.sha1(args['decisionText']).hexdigest()[:16]

    # return decision id and args back to client so it can automatically add a market for this decision
    emit('add-decision', args)

    data = api.send({ 'command':['ask_decision', args['branchId'], block, args['decisionId'], args['decisionText']] })
    app.logger.debug(data)


@socketio.on('add-market', namespace='/socket.io/')
def add_market(args):

    app.logger.debug(args)

    tx = {
        "B": int(args['marketInv']),
        "PM_id": args['decisionId'] + '.market',
        "decisions": [args['decisionId']],
        "fees": 0,
        "owner": api.address,
        "states": ['no', 'yes'],
        "states_combinatory": [[0]],
        "type": "prediction_market",
    }

    data = api.send({ 'command': ['info', 'my_address'] })
    if data:
        api.tx_count = data['count']

    data = api.send({'command': ['pushtx', tx]})
    app.logger.debug(data)


@socketio.on('update-market', namespace='/socket.io/')
def update_market(id):

    data = api.get_market(id)
    if data:
        emit('market', data)


@socketio.on('trade', namespace='/socket.io/')
def trade(args):

    market = api.get_market(id=args['marketId'])

    if market:

        tx = {
            'type': 'buy_shares',
            'PM_id': args['marketId'],
            'buy': [],
            'pubkeys': [ unicode(api.pubkey) ],
            'count': api.tx_count
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

        cost = api.get_cost_per_share(tx)
        tx['price_limit'] = int(cost * 1.01) + 1

        tx = api.trade_pow(tx)

    data = api.send({'command': ['pushtx', tx]})
    app.logger.debug(data)


###
# main

if __name__ == '__main__':

    socketio.run(app, host='127.0.0.1', port=9000)

    print "stopping..."