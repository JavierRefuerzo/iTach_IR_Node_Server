#!/usr/bin/env python3
"""
Polyglot v3 node server iTach IR
Copyright (C) 2021 Javier Refuerzo

"""
from os import name
import udi_interface
from typing import Callable, List, final
from iTachLib.controller.Device import Device
from iTachLib.controller.codeSetParser import CodeSetParser
from nodes.controller.drivers import Drivers, ModuleTypes
from nodes.controller.drivers import StatusValues
from nodes.controller.drivers import ErrorValues
from nodes.device.DeviceNode import DeviceNode
from objects.DocumentModifier import DocumentModifier
from objects.errors import Errors
from iTachLib.controller.controller import Controller as ITach
from objects.polyglotObserver import PolyglotObserver
from constants.params import Params

LOGGER = udi_interface.LOGGER
Custom = udi_interface.Custom



'''
Controller 
'''
class Controller(udi_interface.Node):
    # Node Definitions
    id = 'ctl'
    address='itachir' 
    name='iTach IR'

    # Status Drivers
    drivers = [
            {'driver': Drivers.status.value, 'value': StatusValues.true.value, 'uom': 2},
            {'driver': Drivers.moduleAddress.value, 'value': 1, 'uom': 56},
            {'driver': Drivers.moduleType.value, 'value': ModuleTypes.UNKNOWN.value, 'uom': 25},
            ]
    

    # Data
    iTach: ITach = None
    deviceNodeList: List[DeviceNode]
    errorCode: int = ErrorValues.none.value

    # Nodes/Node Holders


    #shared observer
    polyObserver: PolyglotObserver

    
    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot, self.address, self.address, self.name)   
        
        self.poly = polyglot
        self.polyObserver = PolyglotObserver(self.poly)
        self.polyObserver.moduleType.attach(self.setModuleType)
        self.deviceNodeList = []

        #set custom params
        self.Parameters = Custom(polyglot, 'customparams')

        #Set initaial status 
        #self.deviceList = []
        self.setStatus(statusEnum=StatusValues.true)

        # start processing events and create or add our controller node
        self.poly.ready()
        
        # Add this node to ISY
        self.poly.addNode(self)


        # subscribe to the events we want
        self.setMqttObsevers()
        self.observeShared()

        #this should be moved out of this class and into an observer model
        #test_connect = connect.Connect(self.poly, controller=self)




    #---------- Status Setters

    def setStatus(self, statusEnum: StatusValues):
        self.setDriver(Drivers.status.value, statusEnum.value, True, True)

    def setModuleType(self, type: int):
        self.setDriver(Drivers.moduleType.value, type, True, True)



    #---------- Shared Observer
    def observeShared(self):
        self.polyObserver.stop.attach(self.stop)
        self.polyObserver.customParams.attach(self.parameterHandler)
        self.polyObserver.polls.attach(self.poll)



    #---------- MQTT Observers

    def setMqttObsevers(self):
        self.poly.subscribe(self.poly.START, self.start, self.address)
        #other mqtt subsribe functions in shared observer
    
    def stop(self):
        LOGGER.info(' stop')
        self.setStatus(statusEnum=StatusValues.false)
        self.poly.stop()

    def start(self):
        LOGGER.info(' start called')
        self.poly.setCustomParamsDoc()
        self.poly.updateProfile()

    def parameterHandler(self, params):
        self.Parameters.load(params)
        LOGGER.info('GET Custom params TEST ' + str(self.Parameters))
        self.processParameters(params=params)

    def poll(self, polltype):
        if 'shortPoll' in polltype:
            print("shortPoll")
        # if 'longPoll' in polltype:
        #     self.updateStatus()


    #---------- Command  Observers

    

    #Set Command Observers
    commands = {}


   
#---------- Business Logic

    def processParameters(self, params):
        LOGGER.info('Process Params: ' + str(len(params)))
        # make sure defined params are set
        self.processDefinedParams(params)
        
        #clear the device list
        deviceList: List[Device] = []

        # process ir codes for each param
        for param in params:
            LOGGER.info('Process Param: ' + param)
            # det not try to parse defined param
            enum = Params.get(value=param)
            if enum != None:
                LOGGER.info('Defined Param: ' + param)
                continue

            # This is a button code
            LOGGER.info('Device Param: ' + param)
            device = self.getDevice(params, param)
            if device == None:
                LOGGER.info('Could not get Device: ' + param)
                continue
            LOGGER.info('Added Device to Node List: ' + device.name)
            deviceList.append(device)

        #check that the controller is not null
        if self.iTach == None:
            LOGGER.info('iTach Controller NOT set ')
            return

        # update the iTach Controller with new device list
        LOGGER.info('Updating iTach Controller Device List. Number of Devices: ' + str(len(deviceList)))
        self.iTach.updateDevices(devices=deviceList)
        LOGGER.info('iTach Controller now has ' + str(len(self.iTach.deviceList)) + ' Devices ')
        # update device nodes
        self.updateDeviceNodeList()

            
    def processDefinedParams(self, params):
        #get url
        url = params[Params.url.value]
        if self.iTach == None:
            LOGGER.info('Creating iTach Controller')
            self.iTach = ITach(address=url, observers=self.polyObserver)
            self.polyObserver.iTach = self.iTach
        else:
            LOGGER.info('Updating iTach URL')
            self.iTach.updateAddress(url)


    def getDevice(self, params, param) -> Device :
        try:
            parser = CodeSetParser(params[param])
            codeSet = parser.codeSet
            if len(codeSet) == 0:
                LOGGER.info("Parse Error: code list is empty")
                return None
            LOGGER.info('Number of ir codes for "'+ param  + '": ' + str(len(parser.codeSet)))
            return Device(name=param, buttons=codeSet)
        except Exception as e:
            LOGGER.info("Parse Error: " + str(e))
            return None

        

    def updateDeviceNodeList(self):
        LOGGER.info('Updating Device Node List')
        if self.iTach == None:
            LOGGER.info('iTach Controller NOT set')
            return
        # get the device list from iTach
        devices = self.iTach.deviceList
        LOGGER.info('Devices in iTach Controller: ' + str(len(devices)))
        for device in devices:
            LOGGER.info('Checking Device against existing Nodes: ' + device.name)
            exists = False
            for node in self.deviceNodeList:
                if node.device.name == device.name:
                    LOGGER.info('updating Device Node: ' + node.device.name)
                    #node exists update the device i.e. ir codes
                    node.device = device
                    exists = True
                    break

            if not exists:
                #create new node
                LOGGER.info('Createing New Device Node: ' + device.name)
                deviceNode = DeviceNode(self.poly, self.address, device, self.polyObserver)
                self.deviceNodeList.append(deviceNode)

        # All DeviceNodes should be added/updated
        # Remove any nodes which no longer exist
        self._cleanDeviceList(newDeviceList=devices)

        mod = DocumentModifier()
        mod.writeFiles(devices=devices)
        self.poly.updateProfile()


    #removes any device not in new device list
    def _cleanDeviceList(self, newDeviceList: List[Device]):
        # check if the device already exists
        removalList: List[DeviceNode] = []
        for oldDevice in self.deviceNodeList:
            exists = False
            for newDevice in newDeviceList:
                if oldDevice.device.name == newDevice.name:
                    exists = True
                    break
            if not exists:
                removalList.append(oldDevice)
                
        #remove devices
        for device in removalList:
            # TODO: remove device from ISY
            LOGGER.info("TODO remove device: " + device.device.name)
            self.deviceNodeList.remove(device)


