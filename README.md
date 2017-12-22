# Introduction

This project was originally intended for academic purpose.
Read the motivation, progress and use-cases from: 
BlockchainPOCProject.pptx
ComprehensiveApplicationUseCases.docx

The code is originally sourced from:
"Learn Blockchains by Building One"
[![Build Status](https://travis-ci.org/dvf/blockchain.svg?branch=master)](https://travis-ci.org/dvf/blockchain)
Find the original source code on [Blockchain](https://github.com/dvf/blockchain) for the post on [Building a Blockchain](https://medium.com/p/117428612f46).

## Installation

Note: Please take care of installing the pre-requisites, if you do not have it installed in your system.
    The following pre-requisites might require installation based on the system you are using:
    1. urlib
    2. requests
    3. flask

1. Activate the nodes:
    * `$ python blockchain.py`
    * `$ python blockchain.py -p 5001`
    * `$ python blockchain.py --port 5002`

At this stage the 3 node P2P n/w is up. Here node on port 5000 will play a miner's role. All the nodes are running on localhost on different nodes.
 Note: To make it even more truly decentralized, the blockchain.py file 
 can be run on different systems altogether. In that case, mention correct IP addresses in node registration and other operations.

2. Run the client to interact with the nodes:
This can be easily done using [Postman](https://www.getpostman.com/) Chrome Plug-in or by using CURL commands from a terminal. 
If you decide to go with Postman:
Install Postman. After installing postman, use http requests to interact with the nodes.
For further details on how to build http requests on postman for this project, refer to PostmanRequests folder.
Import the postman collection files(json files) to your installed Postman client and follow the numbered sequence from 1_View Chain till 5_Consensus.

If you find it difficult to follow the steps, please raise an issue to improve the documentation.

## Change list
This section describes the changes made in this project to the original code:

Major
1. Discovering transactions pending to be added to a blockchain.
2. Modification of transaction attributes.
(closely following Venmo-like transaction information)
3. Purging verified and included transactions from all nodes.
4. Improved hashing logic to include last block's data for true immutability.
5. 4. Recovering excluded transactions and making them available for re-mining.

Minor
1. Converting timestamps to human readable format.
2. Adding end points to check nodes in n/w.
3. Adding end point to check transactions in a node.


## Contribution
Contributions are welcome! Please feel free to submit a Pull Request.
