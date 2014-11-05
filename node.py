import json, sys, os, socket, time, re, ast, math, random

# for signing 
import hashlib, base64

from subprocess import call, Popen
from threading import Thread, Event

# get elliptical signing function so we can create our own tx
# TODO: have the API handle the make_PM command like everything else!
import ecdsa

###
# node monitoring and communication object/thread

class Node(Thread):

    BUY_SHARES_TARGET = '0' * 3 + '1' + '9' * 60
    MAX_MESSAGE_SIZE = 60000

    def __init__(self, app, socketio):

        self.exit_event = Event()
        self.sleep_interval = 1
        self.blockcount = 0
        self.app = app
        self.socketio = socketio
        self.running = False

        self.my_address = None
        self.my_tx_count = 0
        self.privkey = None
        self.pubkey = None

        self.markets = []
        self.decisions = []
        self.branches = []

        Thread.__init__(self)

        self.start()


    def exit(self, wait_for_exit=False):

        self.exit_event.set()

        if wait_for_exit:
            self.join()

    def run(self):

        while not self.exit_event.isSet():

            blockcount = self.send({ 'command': ['blockcount'] })

            if blockcount:

                # check if node just came up
                if not self.running:

                    self.socketio.emit('node-starting', namespace='/socket.io/')

                    self.parse_block_chain()
                    self.socketio.emit('decisions', self.decisions[:20], namespace='/socket.io/')
                    self.socketio.emit('markets', self.markets[:20], namespace='/socket.io/')
                    self.socketio.emit('branches', self.branches[:20], namespace='/socket.io/')

                    address = self.send({ 'command': ['my_address'] })
                    if address:
                        self.my_address = address

                    privkey = self.send({ 'command': ['info', 'privkey'] })

                    if privkey:

                        self.privkey = str(privkey)
                        self.pubkey = ecdsa.privkey_to_pubkey(privkey)

                    self.socketio.emit('node-up', namespace='/socket.io/')
                    self.running = True

                # watch for block count change and update 
                if int(blockcount) != self.blockcount:

                    self.blockcount = int(blockcount)
                    self.socketio.emit('blockcount', self.blockcount, namespace='/socket.io/')

                    # fetch and examine block txs
                    block = self.send({ 'command': ['info', 'blockcount'] })
                    if block['count']:
                        self.examine_block(block)

                    # TODO: be smarter and examine block for account info changes
                    data = self.send({ 'command': ['info', 'my_address'] })
                    if data:
                        self.my_tx_count = data.get('count', 1)
                        self.socketio.emit('info', data, namespace='/socket.io/')

            else:

                # check if node just went down
                if self.running:
                    self.socketio.emit('node-down', namespace='/socket.io/')
                    self.running = False

            time.sleep(self.sleep_interval)

    @property
    def python_cmd(self):

        if sys.platform == 'win32':
            result = os.path.split(sys.executable)[:-1] + ('pythonw.exe',)
        else:
            result = ('python',)

        return os.path.join(*result)

    def start_node(self, password):

        cmd = os.path.join(self.app.config['TRUTHCOIN_PATH'], 'threads.py')
        Popen([self.python_cmd, cmd, password])

    def stop_node(self):

        cmd = os.path.join(self.app.config['TRUTHCOIN_PATH'], 'truth_cli.py')
        status = call([self.python_cmd, cmd, 'stop'])

        node.running = False

    def connect(self):

        port = 8899
        host = 'localhost'

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setblocking(5)

        try:
            s.connect((host, port))
        except:
            return {'error': 'cannot connect host:' + str(host) + ' port:' + str(port)}

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
                msg['command'][1]['count'] = self.my_tx_count

                # hash message, sign and add sig
                h = hashlib.sha384(json.dumps(msg['command'][1], sort_keys=True)).hexdigest()[0:64]
                msg['command'][1]['signatures'] = [ ecdsa.ecdsa_sign(h, self.privkey)]

                msg['command'][1] = json.dumps(msg['command'][1]).encode('base64')

                # add privkey to pushtx
                #msg['command'].append(self.privkey)

        json_msg = json.dumps(msg)

        #self.app.logger.debug('sending: '+json_msg)

        padded_json = str(len(json_msg)).rjust(5, '0') + json_msg

        #self.app.logger.debug(padded_json)

        while padded_json:

            time.sleep(0.0001)

            try:
                sent = s.send(padded_json)

            except:
                return None 

            padded_json = padded_json[sent:]
        
        response = self.receive(s)
        
        if response == 'broken connection':
        
            self.app.logger.error('broken connection: ' + str(msg))
        
            return self.send(msg, retry=retry+1)
        
        if response == 'no length':
        
            self.app.logger.error('no length: ' + str(msg))
        
            return self.send(msg, retry=retry+1)
        
        return response


    def receive(self, s, data=''):

        try:
            data += s.recv(self.MAX_MESSAGE_SIZE)

        except:
            time.sleep(0.0001)
            self.app.logger.info('data not ready')

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
            self.app.logger.error(e)

        if type(data) == str and re.match(r'[\{\[]', data):

            try:
                data = ast.literal_eval(data)
            except Exception as e:
                self.app.logger.error(e)

        return data

    def examine_block(self, block):

        if block.get('txs'):

            for tx in block['txs']:

                if tx['type'] == 'propose_decision':
                    self.decisions.append(tx)
                if tx['type'] == 'prediction_market':
                    self.markets.append(tx)
                if tx['type'] == 'create_jury':
                    self.branches.append(tx)

    def parse_block_chain(self):

        self.markets = []
        self.decisions = []
        self.branches = []

        for n in xrange(int(self.send({'command':['blockcount']}))):

            block = self.send({'command':['info', n]})
            self.examine_block(block)

    def get_market(self, id=None):

        if id:

            market = self.send({'command':['info', id]})

            return market

    def det_hash(self, tx):

        return hashlib.sha384(json.dumps(tx, sort_keys=True)).hexdigest()[0:64]


    def trade_pow(self, tx):

        tx = json.loads(json.dumps(tx))

        h = hashlib.sha384(json.dumps(tx, sort_keys=True)).hexdigest()[0:64]

        tx[u'nonce'] = random.randint(0, 10000000000000000000000000000000000000000)

        a = 'F' * 64

        while hashlib.sha384(json.dumps(a, sort_keys=True)).hexdigest()[0:64] > self.BUY_SHARES_TARGET:

            tx[u'nonce'] += 1
            a = {u'nonce': tx['nonce'], u'halfHash': h}

        return tx

    def get_cost_per_share(self, tx):

        market = self.get_market(id=tx['PM_id'])

        B = market['B'] * 1.0

        def C(s, B): return B * math.log(sum(map(lambda x: math.e ** (x/B), s)))

        C_old = C(market['shares_purchased'], B)

        def add(a, b): return a + b
        
        C_new = C(map(add, market['shares_purchased'], tx['buy']), B)
        
        return int(C_new - C_old)

