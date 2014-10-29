import json, sys, os, socket, time, re

from subprocess import call, Popen
from threading import Thread, Event

###
# node monitoring and communication object/thread

class Node(Thread):

    def __init__(self, app, socketio):

        self.exit_event = Event()
        self.sleep_interval = 1
        self.blockcount = 0
        self.app = app
        self.socketio = socketio
        self.running = False

        self.markets = []
        self.events = []
        self.juries = []

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

                    self.parse_block_chain()
                    self.socketio.emit('events', self.events[:10], namespace='/socket.io/')
                    self.socketio.emit('markets', self.markets[:10], namespace='/socket.io/')
                    self.socketio.emit('juries', self.juries[:10], namespace='/socket.io/')

                    self.socketio.emit('node-up', namespace='/socket.io/')
                    self.running = True

                # watch for block count change and update 
                if int(blockcount) != self.blockcount:

                    self.app.logger.info("> blockcount changed %s" % blockcount)

                    self.blockcount = int(blockcount)
                    self.socketio.emit('blockcount', self.blockcount, namespace='/socket.io/')

                    # fetch and examine block txs
                    block = self.send({ 'command': ['info', 'blockcount'] })
                    self.examine_block(block)

                    data = self.send({ 'command': ['info', 'my_address'] })
                    if data:

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

        msg['version'] = '0.0009'

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

        MAX_MESSAGE_SIZE = 60000

        try:
            data += s.recv(MAX_MESSAGE_SIZE)

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

    def examine_block(self, block):

        if block.get('txs'):

            for tx in block['txs']:

                if tx['type'] == 'propose_decision':

                    self.events.append(tx)

                if tx['type'] == 'prediction_market':

                    self.markets.append(tx)

                if tx['type'] == 'create_jury':

                    self.juries.append(tx)        


    def parse_block_chain(self):

        self.markets = []
        self.events = []
        self.juries = []

        for n in xrange(int(self.send({'command':['blockcount']}))): 

            j = self.send({'command':['info', n]})

            try:
                block = eval(str(j))
            except:
                self.app.logger.error('error parsing block')

            self.examine_block(block)
