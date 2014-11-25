console.log('[nodeMonitor] starting');

importScripts("http://localhost:9000/static/lodash.js");
importScripts("http://localhost:9000/static/socket.io.min.js");

var socket = io.connect('http://localhost:9000' + '/socket.io/')

var SECONDS_PER_BLOCK = 60;
var REPORT_CYCLE = 40;

var augur = {
    decisions: {},
    branches: {},
    markets: {},
    blockcount: 0,
    network_blockcount: 0,
    starting: false,
    current: false,
    market_queue: {},
    force: false
}

var cycle = {
    count: 0,
    decisions: {}
};

var account = {};

function blockTime(block) {   // estimates time of given block

    var d = new Date();
    var seconds_diff = (block - augur.network_blockcount) * SECONDS_PER_BLOCK;
    d.setSeconds(d.getSeconds() + seconds_diff);

    return d;
}

socket.on('account', function (data) { 

    account = _.extend(account, data)

    self.postMessage({'address': account.address});
    self.postMessage({'cash': account.cash});
});

socket.on('miner', function (data) { 
    self.postMessage({'miner': data});
});

socket.on('market', function (m) { 

    if (m.decisions) {

        var decision_id = m['decisions'][0];

        if (augur.markets[decision_id]) {
            augur.markets[decision_id] = _.extend(augur.markets[decision_id], m);

            if (account.shares && account.shares[augur.markets[decision_id]['PM_id']]) {
                augur.markets[decision_id]['my_shares'] = account.shares[augur.markets[decision_id]['PM_id']]
            }
        }
    }
});

socket.on('blockcount', function (count) {

    if (augur.blockcount != count || augur.force) {

        augur.force = false;

        var prev_blockcount = augur.blockcount;
        augur.blockcount = count;
        self.postMessage({'blockcount': count});

        var start_block = prev_blockcount + 1;

        socket.emit('update-account');

        // examine new blocks
        if (prev_blockcount != count) {
            console.log('[nodeMonitor] fetching blocks '+ start_block +' - '+augur.blockcount);
            for (i = start_block; i <= augur.blockcount; i++) {
                socket.emit('get-block', i);
            }
        }

        // update markets 
        _.each(augur.markets, function(m) {
            socket.emit('update-market', m['PM_id']);
        });

        // check for maturing decisions
        var changes = false;
        _.each(augur.decisions, function(d) {
            if (d['status'] == 'open' && d['maturation'] <= augur.network_blockcount) {
                changes = true;
                augur.decisions[d['decision_id']]['status'], d['status'] = 'closed';

                // update associated market
                augur.markets[d['decision_id']] = _.extend(augur.markets[d['decision_id']], d);
            }
        });

        // update DOM if there are changes
        if (changes) self.postMessage({'markets': augur.markets});

        // check cycle reporting phase
        cycle_count = parseInt(augur.network_blockcount / REPORT_CYCLE);
        cycle['block'] = augur.network_blockcount - (cycle_count * REPORT_CYCLE);
        cycle['end_block'] = (cycle_count + 1) * REPORT_CYCLE;
        cycle['end_date'] = blockTime((cycle_count + 1) * REPORT_CYCLE);
        cycle['last_end_block'] = cycle_count * REPORT_CYCLE;
        cycle['last_end_date'] = blockTime(cycle_count * REPORT_CYCLE);
        cycle['reveal_block'] = parseInt(cycle['last_end_block'] + REPORT_CYCLE * 0.875);
        cycle['reveal_date'] = blockTime(cycle['reveal_block']);
        cycle['svd_block'] = parseInt(cycle['last_end_block'] + REPORT_CYCLE * 0.975);
        cycle['svd_date'] = blockTime(cycle['svd_block']);
        cycle['percent'] = (cycle['block'] / REPORT_CYCLE) * 100;
        cycle['phase'] = 'catching up';

        if (augur.current) {   // only reveal reporting details if we have parsed the blockchain and are current

            if (cycle_count != cycle['count']) {   // we're in a new cycle 

                cycle['count'] = cycle_count;
                console.log("[nodeMonitor] reporting cycle " + cycle['count']);
            
                // collect reporting decisions
                cycle['decisions'] = {};
                _.each(augur.decisions, function(d) {
                    if (d['status'] == 'closed' && _.has(account['branches'], d['vote_id']) && _.has(augur.markets, d['decision_id'])) {
                        cycle['decisions'][d['decision_id']] = d;
                    };
                });
            }

            // reporting phase
            if (augur.blockcount < cycle['reveal_block'] && cycle['phase'] != 'reporting') {  

                cycle['phase'] = 'reporting';

                // update reporting
                self.postMessage({'report': cycle});

            // reveal phase
            } else if (augur.blockcount >= cycle['reveal_block'] && augur.blockcount < cycle['svd_block'] && cycle['phase'] != 'reveal') {   

                cycle['phase'] = 'reveal';

                // reveal reports
                 _.each(cycle['decisions'], function(d) {
                    if (d.state) {   // we have reported on this decision 
                        socket.emit('reveal-vote', d['vote_id'], d['decision_id']);
                        console.log('[nodeMonitor] revealing vote ('+d['decision_id']+') in '+d['vote_id']);
                    }
                });

                // update reporting
                self.postMessage({'report': cycle});

            // SVD phase
            } else if (augur.blockcount >= cycle['svd_block'] && cycle['phase'] != 'svd') {

                cycle['phase'] = 'svd';

                // collect all branches voted on
                branches = {}

                _.each(cycle['decisions'], function(d) {

                    branches[d['vote_id']] = true;

                    // dedupe list and do SVD concensus on all voted branches
                    _.each(Object.keys(branches), function(branch) {
                        socket.emit('svd-consensus', branch);
                        console.log('[nodeMonitor] svd consensus for ' + branch);
                    });
                });

                // update reporting
                self.postMessage({'report': cycle});
            }
        }

        self.postMessage({'cycle': cycle});   // update cycle data

    }
});

socket.on('block', function (block) {

    if (block && block['txs']) {

        var messages = []

        _.each(block['txs'], function(tx) {

            // build ledger of all account transactions
            if (tx['pubkey'] == account['pubkey']) acount['txs'].push(tx);

            if (tx['type'] == 'propose_decision') {

                tx['status'] = tx['maturation'] > augur.network_blockcount ? 'open' : 'closed';
                tx['maturation_date'] = blockTime(tx['maturation']);
                augur.decisions[tx['decision_id']] = tx;

                // check to see if we're waiting for this decision to show up
                if (augur.market_queue[tx['decision_id']]) {

                    socket.emit('add-market', augur.market_queue[tx['decision_id']]);
                    delete augur.market_queue[tx['decision_id']]
                }

                messages.push('New decision: ' + tx['txt'] + ' (' + tx['decision_id'] + ')');

            } else if (tx['type'] == 'prediction_market') {

                var decision_id = tx['decisions'][0];

                // augment market data with decision data
                augur.markets[decision_id] = _.extend(tx, augur.decisions[decision_id]);

                self.postMessage({'markets': augur.markets});

            } else if (tx['type'] == 'create_jury') {

                augur.branches[tx.vote_id] = tx;

                // check to see if we have any rep on this branch
                if (_.has(account.branches, tx.vote_id)) {
                    augur.branches[tx.vote_id]['my_rep'] = account.branches[tx.vote_id];
                }

                self.postMessage({'branches': augur.branches});
                messages.push('New branch: ' + tx['vote_id']);

            } else if (tx['type'] == 'spend') {

                sender = 'unknown';
                if (tx.vote_id) {
                    messages.push(sender + ' sent ' + tx['amount'] + ' ' + tx['vote_id'] + ' reputation to ' + tx['to']);
                } else {
                    messages.push(sender + ' sent ' + tx['amount'] + ' cash to ' + tx['to']);
                }

            }
        });

        // check to see if we have caught up and loaded all txs
        if (block['length'] == augur.network_blockcount && !augur.current) {
            augur.current = true;
            augur.force = true;
        }

        if (messages.length) self.postMessage({'alert': {'type': 'info', 'messages': messages}});
    }      
});

socket.on('peers', function (peers) {

    if (!augur.running) {
        socket.emit('get-account');
        augur.running = true;

        self.postMessage({'node-up': true});            
    }

    _.each(peers, function(data) {

        // update network blockcount to largest peers
        augur.network_blockcount = data.blockcount > augur.network_blockcount ? data.blockcount : augur.network_blockcount;
    });

    self.postMessage({'peers': peers});
});

socket.on('node-down', function() {

    // check to see if we were already running
    if  (augur.running || !_.has(augur, 'running')) {

        self.postMessage({'node-down': true});   
        augur.running = false;
    }
});

// message listeners from DOM script
self.addEventListener('message', function(message) {

    var m = message.data;

    // adding a pending decision to list until the blockchain confirms it
    if (m && m['add-decision']) {

        var tx = {
            'txt': m['add-decision']['decisionText'],
            'decision_id': m['add-decision']['decisionId'],
            'vote_id': m['add-decision']['branchId'],
            'maturation': m['add-decision']['decisionMaturation'],
            'status': 'pending'
        }

        augur.decisions[tx.decision_id] = tx;

        var tx = {
            'B': parseInt(m['add-decision']['marketInv']),
            'PM_id': m['add-decision']['decisionId'] + '.market',
            'decisions': [m['add-decision']['decisionId']],
            'decision_id': m['add-decision']['decisionId'],
            'fees': 0,
            'owner': account.address,
            'states': ['no', 'yes'],
            'type': 'prediction_market',
            'txt': m['add-decision']['decisionText'],
            'vote_id': m['add-decision']['branchId'],
            'maturation': m['add-decision']['decisionMaturation'],
            'maturation_date': blockTime(m['add-decision']['decisionMaturation']),
            'status': 'pending'
        }

        augur.markets[tx.decision_id] = tx;
        self.postMessage({'markets': augur.markets});

        augur.market_queue[m['add-decision'].decisionId] = m['add-decision'];


    } else if (m && m['report-decision']) {

        augur.decisions[m['report-decision']['decision_id']]['state'] = m['report-decision']['stage'];

        var data = _.extend(augur.decisions[m['report-decision']['decision_id']], m['report-decision']);
        socket.emit('report', data);


    } else if (m && m['trade']) {

        var id = m['trade'];

        self.postMessage({'trade': augur.markets[id]});
    }
});

// start pinging node for updates
setInterval(function() { socket.emit('ping') }, 2500);