#!/usr/bin/env python3
"""
Polyglot v3 node server iTach IR
Copyright (C) 2021 Javier Refuerzo

"""

import udi_interface
from typing import  List
from nodes.controller.drivers import ErrorValues, ModuleTypes
from iTachLib.controller.Device import Device
import socket


LOGGER = udi_interface.LOGGER


class Controller :
    observers = None
    address: str
    deviceList: List[Device]
    # this may be a variable in the futue is used to get module type
    moduleAddress: int = 1

    def __init__(self, address: str, observers):
        self.observers = observers
        self.updateAddress(address)
        self.deviceList = []
        # TODO Add connection Test

    def updateAddress(self, address: str):
        self.address = address
        self.address = self.address.replace("http://", "")
        LOGGER.info("address is: " + self.address)
        self.getDevices()

    # ------ Setters with update listeners

    def setErrors(self, error: int):
        #return if there is no observer
        if self.observers != None:  
            self.observers.iTachError.update(error)
            LOGGER.info("Sent error to observable")
            return
        LOGGER.info("Observer Not Set")
    
    def _setModuleTypeObserver(self, value: int):
        if self.observers != None:
            self.observers.moduleType.update(value)
            return
        LOGGER.info("Observer Not Set")

    # ------ Setters

    # should be called after all data is parsed into a List of Devices
    def updateDevices(self, devices: List[Device]):
        LOGGER.info("update Devices")
        # update the device list to ensure the device is listed
        # there may be multiple items for the same device in device list
        # so do NOT just replace the values
        for newDevice in devices:
            device = self._getDevice(newDevice)
            if device != None:
                LOGGER.info("update existing Device: " + device.name)
                #the device exists so update values
                device.updateButtons(newIrCodeList=newDevice.buttons)
            else:
                LOGGER.info("Adding New Device: " + newDevice.name)
                # the device does not exist so add to list
                self.deviceList.append(newDevice)
       
        # all values should now be updated, so remove any that are not in the list
        self._cleanDeviceList(newDeviceList=devices)


    #removes any device not in new device list
    def _cleanDeviceList(self, newDeviceList: List[Device]):
        LOGGER.info("clean Device List")
        # check if the device already exists
        removalList: List[Device] = []
        for oldDevice in self.deviceList:
            exists = False
            for newDevice in newDeviceList:
                if oldDevice.name == newDevice.name:
                    exists = True
                    break
            if not exists:
                removalList.append(oldDevice)

        #remove devices
        for device in removalList:
            LOGGER.info("removing Device: " + device.name)
            # notify observes of removal
            device.willRemoveDevice()
            self.deviceList.remove(device)


    def _getDevice(self, newDevice: Device) -> Device:
        LOGGER.info("Get Device")
        # check if the device already exists
        for oldDevice in self.deviceList:
            if newDevice.name == oldDevice.name:
                LOGGER.info("Device Found: " + oldDevice.name)
                return oldDevice
        #the device does not exist
        LOGGER.info("device not found")
        return None
    
    # ---- Command functions

    def send_command(self, command) -> str:
        byte_size=4096
        timeout=3
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        command = command + "\r"
        response: str = None
        try:
            sock.connect((self.address, 4998))
            command = command.encode()
            sock.sendall(command)
            response = self.format_message(sock.recv(byte_size))
            LOGGER.info("RECEIVED: " + response)
        except socket.error as error:
            LOGGER.info("ERROR : " + str(error))
            response = "ERR_0:0,-1, " + str(error)
        finally:
            sock.close()
            LOGGER.info("Close Socket")
            error = self.getError(str(response))
            LOGGER.info("error is: " + str(error))
            self.setErrors(error)
            return str(response)

    def getError(self, response) -> int:
        if response == None:
            return ErrorValues.connection.value
        # valid response
        if "completeir" in response:
            return ErrorValues.none.value
        if "stopir" in response:
            return ErrorValues.none.value
        if "device" in response:
            return ErrorValues.none.value
        # error response   
        if "ERR_" not in response:
            return ErrorValues.unknown.value
        # Looking for this ERR_0:0,001 
        split = response.split(",")    
        if len(split) > 2:
            return ErrorValues.unknown.value
        error = split[1]
        try:
            intError = int(error)
            return intError
        except Exception as e:
            LOGGER.info("Could not get error code: " + error + ". " + str(e))
        return ErrorValues.unknown
    
    def format_message(self, msg):
        """format message"""
        if isinstance(msg, bytes):
            return msg.decode()
        return msg

    def sendStop(self, connector: int) -> str:
        command = 'stopir,1:' + str(connector)
        response: str = self.send_command(command)
        return response

    def getDevices(self) -> str:
        command = 'getdevices'
        response: str = self.send_command(command)
        if "device" not in response:
            self._setModuleTypeObserver(ModuleTypes.UNKNOWN.value)
            LOGGER.info("devices not in response")
            # error should already be set
            return response
        split = response.split("\r")
        # This is for iTach
        # ['device,0,0 ETHERNET', 'device,1,3 IR', 'endlistdevices', '']
        # This if for iTachFlex
       # ['device,0,0 ETHERNET', 'device,1,1 IRTRIPORT', 'endlistdevices', ''] 
        if len(split) < (self.moduleAddress + 1):
            self._setModuleTypeObserver(ModuleTypes.UNKNOWN.value)
            return
        moduleData = split[self.moduleAddress]
        moduleSplit = moduleData.split(",")
        if len(moduleSplit) < 3:
            # device,1,3 IR
            self._setModuleTypeObserver(ModuleTypes.UNKNOWN.value)
            return
        moduleType: ModuleTypes = ModuleTypes.getType(moduleSplit[2])
        self._setModuleTypeObserver(moduleType)
        return response

    