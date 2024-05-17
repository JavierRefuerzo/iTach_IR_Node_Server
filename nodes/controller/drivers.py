#!/usr/bin/env python3
"""
Polyglot v3 node server iTach IR
Copyright (C) 2021 Javier Refuerzo

"""
from enum import Enum


#enum for drivers
class Drivers(Enum):
    status = "ST"
    moduleAddress = "GV0"
    moduleType = "GV1"

#enum for status values
class ModuleTypes(Enum):
    UNKNOWN = 0
    WIFI = 1
    ETHERNET = 2
    RELAY_3 = 3
    IR_3 = 4
    SERIAL_1 = 5

    def getType(raw: str) -> int:
        if "WIFI" in raw:
            return ModuleTypes.WIFI.value
        if "ETHERNET" in raw:
            return ModuleTypes.ETHERNET.value
        if "3 RELAY" in raw:
            return ModuleTypes.RELAY_3.value
        if "3 IR" in raw:
            return ModuleTypes.IR_3.value
        #TODO: This should be it's own module Type This is for iTach Flex Cable see https://www.globalcache.com/files/releases/flex-16/API-Flex_TCP_1.6.pdf
        if "IR" in raw:
            return ModuleTypes.IR_3.value
        #TODO: This should be it's own module Type
        if "IR_BLASTER" in raw:
            return ModuleTypes.IR_3.value
        #TODO: This should be it's own module Type
        if "IRTRIPORT" in raw:
            return ModuleTypes.IR_3.value
        #TODO: This should be it's own module Type
        if "IRTRIPORT_BLASTER" in raw:
            return ModuleTypes.IR_3.value
        if "1 SERIAL" in raw:
            return ModuleTypes.SERIAL_1.value
        return ModuleTypes.UNKNOWN.value

#enum for status values
class StatusValues(Enum):
    false = 0
    true = 1


class ErrorValues(Enum):
    unknown = -2
    connection = -1
    none = 0
    ERR_01 = 1
    ERR_02 = 2
    ERR_03 = 3
    ERR_04 = 4
    ERR_05 = 5
    ERR_06 = 6
    ERR_07 = 7
    ERR_08 = 8
    ERR_09 = 9
    ERR_10 = 10
    ERR_11 = 11
    ERR_12 = 12
    ERR_13 = 13
    ERR_14 = 14
    ERR_15 = 15
    ERR_16 = 16
    ERR_17 = 17
    ERR_18 = 18
    ERR_19 = 19
    ERR_20 = 20
    ERR_21 = 21
    ERR_22 = 22
    ERR_23 = 23
    ERR_24 = 24
    ERR_25 = 25
    ERR_26 = 26
    ERR_27 = 27
    