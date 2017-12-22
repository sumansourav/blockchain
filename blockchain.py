#! /usr/local/bin/python3

import hashlib
import json
from datetime import datetime
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import Flask, jsonify, request


class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()

        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address):
        """
        Add a new node to the list of nodes

        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid

        :param chain: A blockchain
        :return: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print('{0}'.format(last_block))
            print('{0}'.format(block))
            print("\n-----------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof'], block['previous_hash']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get('http://{0}/chain'.format(node))

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        return_value = False
        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            # Make the transactions not part of the authoratitive chain available for re-mining
            self.current_transactions = self.recover_transactions(self.current_transactions, new_chain)

            # Replace chain
            self.chain = new_chain
            return_value = True

        # Double Check. Should be optimized
        # If we have transactions in current_transactions,
        # which are already a part of the authoritative blockchain, we purge those
        self_transactions = self.current_transactions
        for transaction in self_transactions:
            for block in self.chain[1:]:
                if transaction in block["transactions"]:
                    self.current_transactions.remove(transaction)
                    break

        return return_value

    def recover_transactions(self, curr_transaction, auth_chain):
        """
        This function covers a special case: When there is a transaction waiting to be a part of a block chain,
        but it has not been included by any mining node. The function recovers such transactions and makes
        them available for re-mining at a later stage. Without this, the transactions not part of a block-chain yet
        would be lost.

        :return: list of transactions recovered
        """
        recovered_transactions = []

        for trans_item in curr_transaction:
            if (trans_item not in auth_chain[-1]['transactions']) and ('Miner' not in trans_item["message"]):
                recovered_transactions.append(trans_item)
        return recovered_transactions

    def new_block(self, proof, previous_hash):
        """
        Create a new Block in the Blockchain

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.now()),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount, timestamp, message="Probably pizza!"):
        """
        Creates a new transaction to go into the next mined Block

        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'timestamp': str(datetime.now()),
            'message': message
        })

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block

        :param block: Block
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_block):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp'h) contains leading 4 zeroes, where p is the previous p'
         - p is the previous proof, and p' is the new proof, and h is the hash of the prev block
        """

        proof = 0
        while self.valid_proof(last_block['proof'], proof, self.hash(last_block)) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof, previous_hash):
        """
        Validates the Proof

        :param last_proof: Previous Proof
        :param proof: Current Proof
        :param previous_hash: <str> The hash of the previous block
        :return: True if correct, False if not.
        """

        guess = '{0}{1}{2}'.format(last_proof, proof, previous_hash).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

# Using flask as a Python based micro app-server
# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
    sender="0",
    recipient=node_identifier,
    amount=0.1,
    timestamp=str(datetime.now()),
    message="Miner's transaction"
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    try:
        message = values['message']
    except KeyError:
        message = "Probably Pizza!"

    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'], str(datetime.now()), message)

    response = {'message': 'Transaction will be added to Block {0}'.format(index)}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/transactions', methods=['GET'])
def transactions():
    response = {
        'transactions': blockchain.current_transactions,
        'length': len(blockchain.current_transactions),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/transactions/discover', methods=['GET'])
def discover_transactions():
    nodes = blockchain.nodes
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        response = requests.get('http://{0}/transactions'.format(node))

        if response.status_code == 200:
            blockchain.current_transactions = blockchain.current_transactions + response.json()['transactions']
            blockchain.current_transactions = \
                list({trans['timestamp']: trans for trans in blockchain.current_transactions}.values())

    # Discover all transactions waiting to be added to the chain.
    response = {
        'message': 'Gathered all transactions to be mined from different nodes',
        'transactions': blockchain.current_transactions,
    }
    return jsonify(response), 200


@app.route('/nodes', methods=['GET'])
def get_nodes():
    response = {
        'total_nodes': len(list(blockchain.nodes)),
        'nodes': list(blockchain.nodes)
    }
    return jsonify(response), 200


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)
