import json
import os
import requests
import time
from hashlib import sha256
import shutil

from flask import Flask, request


class Block:
    def __init__(self, index, transaction, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transaction = transaction
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()


class Blockchain:

    difficulty = 2

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        data = []
        chain_blockchain = []
        if os.path.isfile('./chain'):
            with open('./chain', 'r') as file:
                data = file.read()
            chain = data.split('\n')
            if len(chain) > 0:
                for bck in chain:
                    chn = eval(bck)
                    if isinstance(chn['chain'], str):
                        for dic in eval(chn['chain']):
                            block = Block(dic['index'], dic['transaction'], dic['timestamp'], dic['previous_hash'])
                            block.hash = block.compute_hash()
                            chain_blockchain.append(block)
                    else:
                        for dic in chn['chain']:
                            block = Block(dic['index'], dic['transaction'], dic['timestamp'], dic['previous_hash'])
                            block.hash = block.compute_hash()
                            chain_blockchain.append(block)
                self.chain = chain_blockchain
            else:
                genesis_block = Block(0, [], time.time(), "0")
                genesis_block.hash = genesis_block.compute_hash()
                self.chain.append(genesis_block)
        else:
            genesis_block = Block(0, [], time.time(), "0")
            genesis_block.hash = genesis_block.compute_hash()
            self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, block, proof):

        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        if not Blockchain.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        try:
            with open('./chain', 'w') as file:
                file.write(get_my_chain())
        except:
            print("Cannot write in the chain's file")

        return True

    def proof_of_work(self, block):

        block.nonce = 0

        compute_hash = block.compute_hash()
        while not compute_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            compute_hash = block.compute_hash()

        return compute_hash

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    @classmethod
    def is_valid_proof(cls, block, block_hash):

        b = Blockchain()
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == b.proof_of_work(block))

    @classmethod
    def check_chain_validity(cls, chain):
        result = True
        previous_hash = "0"

        for block in chain:
            block_hash = block.hash

            delattr(block, "hash")

            if not cls.is_valid_proof(block, block.hash) or \
                    previous_hash != block.previous_hash:
                result = False
            if result:
                block.hash, previous_hash = block_hash, block_hash

            return result

    def mine(self):

        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        new_block = Block(index=last_block.index + 1,
                          transaction=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)
        proof = self.proof_of_work(new_block)
        added = self.add_block(new_block, proof)

        if added:
            self.unconfirmed_transactions = []
            announce_new_block(new_block)
            return new_block.index
        else:
            return False


app = Flask(__name__)

blockchain = Blockchain()
blockchain.create_genesis_block()


@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    data = request.get_json()
    required_fields = ["rule", "location", "host"]

    for field in required_fields:
        if not data.get(field):
            return "Invalid transaction data", 404

    data["timestamp"] = time.time()
    blockchain.add_new_transaction(data)

    return "Success", 200


@app.route('/mine', methods=['POST'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result:
        return "No transactions to mine", 500
    return "Block #{} is mined.".format(result), 200

@app.route('/peers', methods=['POST'])
def get_peers():
    with open('./peers', 'r') as file:
        data = file.read()
    peers = data.split('\n')
    return json.dumps({'peers': peers})

@app.route('/update_peers', methods=['POST'])
def add_peer():
    new_peer = request.get_json()['peer']
    with open('./peers', 'a') as file:
        file.write(new_peer+'\n')
    return "Peer: {} added".format(new_peer)


@app.route('/register_with', methods=['POST'])
def register_with_existing_node():

    node_address = request.get_json()["node_address"]
    myip = request.get_json()["myip"]
    secret = sha256(request.get_json()["secret"].encode()).hexdigest()

    if not node_address or not secret:
        return "Invalid data", 400

    data = {"host_origin": myip, "secret": secret}
    headers = {"Content-Type": "application/json"}

    response = requests.post("https://" + node_address + "register_node",
                             data=json.dumps(data), headers=headers, verify=False)

    if response.status_code == 200:
        print(response.text)
        global blockchain
        chain_dump = response.json()['chain']

        response2 = requests.post("https://" + node_address + "peers", verify=False)
        peers = response2.json()['peers']
        peers.append(node_address)
        file = open('./peers','w+')
        for p in peers:
            if p:
                file.write(p+'\r\n')
        file.close()
        blockchain = create_chain_from_dump(chain_dump, peers)
        return "New node successfully registered", 200
    else:
        return response.content, response.status_code


@app.route('/register_node', methods=['POST'])
def register_new_peers():
    headers = {"Content-Type": "application/json"}
    node_address = request.get_json()["host_origin"]
    secret = request.get_json()["secret"]
    if not node_address or not secret:
        return "Invalid data", 400

    with open('./secret', 'r') as file:
        code = file.read().replace('\n', '')
    with open('./peers', 'r') as file:
        data_peers = file.read()
    peers = data_peers.split('\n')
    for p in peers:
        if p:
            requests.post("https://" + p + "update_peers",
                          data=json.dumps({'peer': node_address}), headers=headers, verify=False)
    if secret == sha256(code.encode()).hexdigest():
        if node_address not in peers:
            with open('./peers', 'a') as file:
                file.write(node_address+'\n')
            chain = get_longest_chain()
            if chain:
                return json.dumps({"chain": str(chain)}), 200
            else:
                return "Error adding node", 500
        else:
            return "Node already in the peers's list", 200
    else:
        return "Error adding node", 500

def get_longest_chain():

    global blockchain
    my_chain = requests.post('https://127.0.0.1:8000/get_chain', verify=False).json()
    current_len = my_chain['length']
    longest_chain = my_chain['chain']

    with open('./peers', 'r') as file:
        data_peers = file.read()
    peers = data_peers.split('\n')

    for node in peers:
        if node:
            print('https://{}get_chain'.format(node))
            response = requests.post('https://{}get_chain'.format(node), verify=False)
            if response:
                print(response.status_code)
                length = response.json()["length"]
                chain = response.json()["chain"]
                if length > current_len and blockchain.check_chain_validity(chain):
                    current_len = length
                    longest_chain = chain

    if longest_chain:
        return longest_chain
    else:
        return False


def create_chain_from_dump(chain_dump, peers):

    chain_dump = chain_dump[1:]
    chain_dump = chain_dump[:-1]
    array = chain_dump.split('},')

    array_dic = []
    count = 0
    length = len(array)

    for a in array:
        if count != length - 1:
            array_dic.append(json.dumps(a + '}'))
            count += 1
        else:
            array_dic.append(json.dumps(a))

    chain_blockchain = []
    blockchain = Blockchain()
    for block_data in array_dic:
        block_d = eval(json.loads(block_data.strip()))
        block = Block(block_d["index"],
                      block_d["transaction"],
                      block_d["timestamp"],
                      block_d["previous_hash"],
                      block_d['hash'])
        chain_blockchain.append(block)
    blockchain.chain = chain_blockchain

    file_chain = []
    for c in chain_blockchain:
        file_chain.append(c.__dict__)
    dic = {"length": len(file_chain), "chain": json.dumps(file_chain), "peers": peers}
    file = open('./chain', 'w+')
    file.write(str(dic))
    file.close()

    return blockchain


@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"],
                       block_data["transaction"],
                       block_data["timestamp"],
                       block_data["previous_hash"])
    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201


@app.route('/pending_tx')
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)



@app.route('/get_chain', methods=['POST'])
def get_my_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    with open('./peers', 'r') as file:
        data_peers = file.read()
    peers = data_peers.split('\n')
    return json.dumps({"length": len(chain_data),
                       "chain": chain_data,
                       "peers": peers})



@app.route('/update_chain', methods=['POST'])
def update_chain():
    global blockchain
    chain = request.get_json()["chain"]
    if blockchain.check_chain_validity(chain):
        blockchain.chain = chain
        return 200
    else:
        return "No valid chain", 500


def announce_new_block(block):

    headers = {"Content-Type": "application/json"}
    with open('./peers', 'r') as file:
        data_peers = file.read()
    peers = data_peers.split('\n')
    for peer in peers:
        if peer:
            requests.post("https://"+peer+"add_block", headers=headers, data=json.dumps(block.__dict__, sort_keys=True), verify=False)


# --------------CONNECTOR IDS <-> BLOCKCHAIN--------------
@app.route('/update_snort_rules', methods=['POST'])
def update_snort_rules():
    if request.remote_addr == "127.0.0.1":
        global blockchain
        rules_data = []
        for block in blockchain.chain:
            rules_data.append(block.transaction)
        shutil.copy2('/etc/snort/rules/blockchain.rules', '/etc/snort/rules/blockchain.backup')
        os.remove('/etc/snort/rules/blockchain.rules')
        file = open('/etc/snort/rules/blockchain.rules', 'w+')

        for r in rules_data:
            if r:
                file.write(r[0]['rule']+"\r\n")
        file.close()

        return 'Update was succesfully done', 200
    else:
        return 'Only local request will attend.', 500

# --------------------------------------------------------

# -------------------RUN APPLICATION-------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, ssl_context=('./certificate/cert.pem', './certificate/key.pem'))
