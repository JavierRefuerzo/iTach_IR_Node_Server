#!/usr/bin/env python3
"""
Polyglot v3 node server iTach IR
Copyright (C) 2021 Javier Refuerzo

"""

import udi_interface
import iTachLib
from objects.LiveObject import LiveObject
from iTachLib.controller.controller import Controller as Itach

LOGGER = udi_interface.LOGGER





class PolyglotObserver :
    
    #polyglot
    poly = None

    #controller (repository)
    iTach: Itach = None

    # Observed objects
    customParams: LiveObject
    stop: LiveObject
    polls: LiveObject
    iTachError: LiveObject
    moduleType: LiveObject
    
    #customParamObserverList: List[Callable]
    
    
    def __init__(self, poly):
        self.poly = poly

        #------------set initial Data

        # observed objects
        self.customParams = LiveObject()
        self.stop = LiveObject()
        self.polls = LiveObject()
        self.iTachError = LiveObject()
        self.moduleType = LiveObject()

        # subscribe to mqtt
        self.setMqttObsevers()


        
    #---------- Subscribe to MQTT

    def setMqttObsevers(self):
        self.poly.subscribe(self.poly.STOP, self.stop.update)
        self.poly.subscribe(self.poly.CUSTOMPARAMS, self.customParams.update)
        self.poly.subscribe(self.poly.POLL, self.polls.update)



    #---------- Getters

    def send_command(self, command) -> str:
        if self.iTach == None:
            return None
        return self.iTach.send_command(command= command)

    def send_stop_ir_command(self, connector: int) -> str:
        if self.iTach == None:
            return None
        return self.iTach.sendStop(connector)
        