# Copyright (c) 2018 IoTeX
# This is an alpha (internal) release and is not suitable for production. This source code is provided ‘as is’ and no
# warranties are given as to title or non-infringement, merchantability or fitness for purpose and, to the extent
# permitted by law, all liability for your use of the code is disclaimed. This source code is governed by Apache
# License 2.0 that can be found in the LICENSE file.

"""This module defines the Player class, which represents a player in the network and contains functionality to make transactions, propose blocks, and validate blocks.
"""

import random

import grpc
import numpy as np

from proto import simulator_pb2_grpc
from proto import simulator_pb2
import block
import solver
import transaction
import states
import message
import consensus_client

class Player:
    id = 0 # player id
    
    MEAN_TX_FEE = 0.2                       # mean transaction fee
    STD_TX_FEE  = 0.05                      # std of transaction fee
    msgMap      = {(1999, ""): "dummy msg"} # maps message to message name for printing

    def __init__(self, stake):
        """Creates a new Player object"""

        self.id = Player.id # the player's id
        Player.id += 1                 

        self.stake = stake  # the number of tokens the player has staked in the system

        self.blockchain  = []   # blockchain (technically a blocklist)
        self.connections = []   # list of connected players
        self.inbound     = []   # inbound messages from other players in the network at heartbeat r
        self.outbound    = []   # outbound messages to other players in the network at heartbeat r

        self.consensus          = consensus_client.Consensus()
        self.consensus.playerID = self.id
        self.consensus.player   = self

    def action(self, heartbeat):
        """Executes the player's actions for heartbeat r"""

        print("player %d action started at heartbeat %d" % (self.id, heartbeat))

        # print messages
        for msg, timestamp in self.inbound:
            print("received %s with timestamp %f" % (Player.msgMap[msg], timestamp))

        if len(list(filter(lambda x: x[1] <= heartbeat, self.inbound))) == 0: # if there are no messages to process, add a "dummy" message so consensus engine is pinged anyways
            self.inbound += [[(1999, ""), heartbeat]]

        # process each message
        for msg, timestamp in self.inbound:
            # note: msg is a tuple: (msgType, msgBody)
            if timestamp > heartbeat: continue

            print("sent %s to consensus engine" % Player.msgMap[msg])
            received = self.consensus.processMessage(msg)
            
            for mt, v in received:
                if v not in Player.msgMap:
                    Player.msgMap[v] = "msg "+str(len(Player.msgMap))
                print("received %s from consensus engine" % Player.msgMap[v])
                
                if mt == 0: # view state change message
                    self.outbound.append([v, timestamp])
                else: # block to be committed
                    self.blockchain.append(v)
                    print("committed %s to blockchain" % Player.msgMap[v])
            
        self.inbound = list(filter(lambda x: x[1] > heartbeat, self.inbound)) # get rid of processed messages
        
        self.sendOutbound() # send messages to connected players

        print()

    def sendOutbound(self):
        """Send all outbound connections to connected nodes"""
        
        for i in self.connections:
            for message, timestamp in self.outbound:
                dt = np.random.exponential(self.MEAN_PROP_TIME) # add propagation time to timestamp
                print("sent %s to %s" % (Player.msgMap[message], i))
                i.inbound.append([message, timestamp+dt])

        self.outbound.clear()

    def __str__(self):
        return "player %s" % (self.id)

    def __repr__(self):
        return "player %s" % (self.id)
        

            
