import json, sys, os, socket, time, re, ast, math, random, datetime

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

    SLEEP_INTERVAL = 1
    MAX_MESSAGE_SIZE = 60000

    BUY_SHARES_TARGET = '0' * 3 + '1' + '9' * 60
    MINUTES_PER_BLOCK = 2
    REPORT_CYCLE = 5040    # in blocks (one week)

    # node settings
    PORT = 8899
    HOST = 'localhost'
    TRUTHCOIN_PATH = '../Truthcoin-POW'

    def __init__(self, app, socketio):

        self.exit_event = Event()
        self.app = app
        self.socketio = socketio

        self.running = False
        self.starting = False
        self.current = False

        self.network_blockcount = 0
        self.blockcount = 0
        self.peers = None

        self.cycle = {
            'count': -1,
            'end_block': None,
            'last_end_block': None,
            'end_date': None,
            'last_end_date': None,
            'phase': None,
            'my_decisions': {}
        }

        self.markets = []
        self.decisions = []
        self.branches = []

        self.my_account = {
            'address': None,
            'cash': 0,
            'tx_count': 0,
            'shares': {},
            'branches': {},
            'privkey': None,
            'pubkey': None
        }

        Thread.__init__(self)

        self.start()


    def exit(self, wait_for_exit=False):

        self.exit_event.set()

        if wait_for_exit:
            self.join()

    # main monitoring and update loop
    # TODO: move this whole thread client-sde with a web worker.  the concern here should only be a light API wrapper.
    def run(self):

        while not self.exit_event.isSet():

            now = datetime.datetime.now()

            # check to see if the node is running, what the peers are and what the network blockcount is
            peers = self.check_peers()

            if peers:

                blockcount = self.send({ 'command': ['blockcount'] })

                # watch for block count change and update 
                if int(blockcount) != self.blockcount:

                    old_blockcount = self.blockcount
                    self.blockcount = int(blockcount)

                    # check blockchain status (current versus catching up)
                    self.current = True if self.network_blockcount > self.blockcount else False

                    self.socketio.emit('blockcount', self.blockcount, self.current, namespace='/socket.io/')

                    # fetch and examine new blocks
                    for n in range(old_blockcount+1, blockcount):

                        block = self.send({ 'command': ['info', n ]})
                        if block:
                            summary = self.examine_block(block)

                            if summary:
                                self.socketio.emit('alert', {'type': 'info', 'message': summary}, namespace='/socket.io/')

                    # update account info
                    # TODO: be smarter and examine block (above) for account info changes
                    data = self.send({ 'command': ['info', 'my_address'] })
                    if data:

                        self.my_account['tx_count'] = data.get('count', 1)
                        self.my_account['cash'] = data.get('amount', 0)
                        self.my_account['shares'] = data.get('shares', {})
                        self.my_account['branches'] = data.get('votecoin', {})

                        for branch in self.branches:
                            if branch['vote_id'] in self.my_account['branches']:
                                branch['my_rep'] = self.my_account['branches'][branch['vote_id']]

                        self.socketio.emit('branches', self.branches, namespace='/socket.io/')
                        self.socketio.emit('info', data, namespace='/socket.io/')

                    # check for any mature decisions that are open and change state
                    for decision in [ d for d in self.decisions if d['state'] == 'open' ]:
                        if decision['maturation'] < self.network_blockcount:
                            decision['state'] = 'mature'

                    # update reporting if needed
                    cycle_count = int(self.network_blockcount / self.REPORT_CYCLE)
                    cycle_block_count = self.network_blockcount - (cycle_count * self.REPORT_CYCLE)

                    if cycle_count != self.cycle['count']:

                        old_cycle_count = self.cycle['count']
                        self.cycle['count'] = cycle_count

                        self.cycle['reported'] = False
                        self.cycle['phase'] = 'reporting'

                        self.app.logger.debug("cycle %s" % self.cycle['count'])

                        self.cycle['end_block'] = cycle_count * self.REPORT_CYCLE
                        self.cycle['end_date'] = now + datetime.timedelta(minutes=((self.network_blockcount + self.cycle['end_block']) * self.MINUTES_PER_BLOCK))
                        self.app.logger.debug(self.cycle['end_date'])

                        if cycle_count > 0:

                            self.cycle['last_end_block'] = (cycle_count - 1) * self.REPORT_CYCLE
                            self.cycle['last_end_date'] = now - datetime.timedelta(minutes=((self.network_blockcount - self.cycle['last_end_block']) * self.MINUTES_PER_BLOCK))
                            self.app.logger.debug(self.cycle['last_end_date'])

                            # collect reporting decisions
                            for d in self.decisions:
                                if d['state'] == 'mature' and d['vote_id'] in self.my_account['branches'].keys():
                                    self.cycle['my_decisions'][d['decision_id']] = d
                            
                        self.socketio.emit('report', self.cycle, namespace='/socket.io/')

                    elif cycle_block_count > 4410 and cycle_block_count < 4536:   # 7/8 to last 10th

                        self.cycle['phase'] = None

                        self.socketio.emit('report', self.cycle, namespace='/socket.io/')

                    elif cycle_block_count >= 4536:   # last 10th

                        self.cycle['phase'] = 'reveal'

                        if cycle_block_count >= 4914:   # last 40th

                            self.phase['phase'] = 'svd'

                        self.socketio.emit('report', self.cycle, namespace='/socket.io/')


                # check if node just came up
                if not self.running:

                    self.starting = True
                    self.socketio.emit('node-starting', namespace='/socket.io/')

                    address = self.send({ 'command': ['my_address'] })
                    if address:
                        self.my_account['address'] = address

                    privkey = self.send({ 'command': ['info', 'privkey'] })

                    if privkey:

                        self.my_account['privkey'] = str(privkey)
                        self.my_account['pubkey'] = ecdsa.privkey_to_pubkey(privkey)

                    self.socketio.emit('node-up', namespace='/socket.io/')

                    self.running = True
                    self.starting = False

            else:

                # check if node just went down
                if self.running:
                    self.socketio.emit('node-down', namespace='/socket.io/')
                    self.running = False

            time.sleep(self.SLEEP_INTERVAL)


    def check_peers(self):

        data = self.send({'command': ['peers']})

        if data:
            peers = {}
            for peer in data:
                address = "%s:%s" % (peer[0][0], peer[0][1])
                if peers.get(address):
                    if int(peer[3]) > peers[address]['blockcount']:
                        peers[address]['blockcount'] = int(peer[3])
                else:
                    peers[address] = {'blockcount': int(peer[3]), 'id': peer[2]}
                self.network_blockcount = int(peer[3]) if peer[3] > self.network_blockcount else self.network_blockcount
                
            # TODO: only update peers if they're different    
            self.peers = peers
            self.socketio.emit('peers', peers)

            return peers


    @property
    def python_cmd(self):

        if sys.platform == 'win32':
            result = os.path.split(sys.executable)[:-1] + ('pythonw.exe',)
        else:
            result = ('python',)

        return os.path.join(*result)

    def start_node(self, password):

        cmd = os.path.join(self.TRUTHCOIN_PATH, 'threads.py')
        Popen([self.python_cmd, cmd, password])

    def stop_node(self):

        cmd = os.path.join(self.TRUTHCOIN_PATH, 'truth_cli.py')
        status = call([self.python_cmd, cmd, 'stop'])

        self.running = False

    def connect(self):

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setblocking(5)

        try:
            s.connect((self.HOST, self.PORT))
        except:
            return {'error': 'cannot connect host:' + str(self.HOST) + ' port:' + str(self.PORT)}

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
                msg['command'][1]['pubkeys'] = [ unicode(self.my_account['pubkey']) ]
                msg['command'][1]['count'] = self.my_account['tx_count']

                # hash message, sign and add sig
                h = self.det_hash(msg['command'][1])
                msg['command'][1]['signatures'] = [ ecdsa.ecdsa_sign(h, self.my_account['privkey'])]

                msg['command'][1] = json.dumps(msg['command'][1]).encode('base64')

                # add privkey to pushtx
                #msg['command'].append(self.my_account['privkey'])

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

        if block and block.get('txs'):

            summary = []

            for tx in block['txs']:

                s = None

                if tx['type'] == 'propose_decision':
                    
                    block_delta = tx['maturation'] - self.network_blockcount
                    minutes = int(block_delta / 2)   # assumes 2 minutes per block
                    date = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
                    tx['maturation_date'] = date

                    if tx['maturation'] > self.network_blockcount:
                        tx['state'] = 'open'
                    else:
                        tx['state'] = 'mature'

                    self.decisions.append(tx)
                    self.socketio.emit('decisions', self.decisions, namespace='/socket.io/')
                    s = 'New decision added: %s (%s)' % (tx['txt'], tx['decision_id'])

                elif tx['type'] == 'prediction_market':

                    data = self.get_market(tx['PM_id'])
                    tx['total_shares'] = data.get('shares_purchased', [])   # add extra db data to tx data

                    # check to see if we own any shares
                    tx['my_shares'] = self.my_account['shares'].get(tx['PM_id'], [])

                    self.markets.append(tx)
                    self.socketio.emit('markets', self.markets[:20], namespace='/socket.io/')
                    s = 'New market added: %s' % (tx['PM_id'])

                elif tx['type'] == 'create_jury':

                    self.branches.append(tx)
                    self.socketio.emit('branches', self.branches, namespace='/socket.io/')
                    s = 'New branch added: %s' % (tx['vote_id'])

                elif tx['type'] == 'spend':

                    sender = 'unknown'
                    if tx.get('vote_id'):
                        s = '%s sent %s %s reputation to %s' % (sender, tx['amount'], tx['vote_id'], tx['to'])
                    else:
                        s = '%s sent %s cash to %s' % (sender, tx['amount'], tx['to'])

                if s:
                    summary.append(s)

            return summary


    def get_market(self, id=None):

        if id:

            market = self.send({'command':['info', id]})

            return market


    def det_hash(self, tx):

        return hashlib.sha384(json.dumps(tx, sort_keys=True)).hexdigest()[0:64]


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

        B = market['B'] * 1.0

        def C(s, B): return B * math.log(sum(map(lambda x: math.e ** (x/B), s)))

        C_old = C(market['shares_purchased'], B)

        def add(a, b): return a + b
        
        C_new = C(map(add, market['shares_purchased'], tx['buy']), B)
        
        return int(C_new - C_old)

