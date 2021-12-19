# Stolen from here :)
# https://gist.github.com/alarrosa14/07bd1ee88a19204cbf22

import sys

from socket import (socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR,
                    SO_BROADCAST)
from struct import pack, unpack

BROADCAST_PORT = 7788


class ArtnetPacket:

    ARTNET_HEADER = b'Art-Net\x00'

    def __init__(self):
        self.op_code = None
        self.ver = None
        self.sequence = None
        self.physical = None
        self.universe = None
        self.length = None
        self.data = None

    def __str__(self):
        return ("ArtNet package:\n - op_code: {0}\n - version: {1}\n - "
                "sequence: {2}\n - physical: {3}\n - universe: {4}\n - "
                "length: {5}\n - data : {6}").format(
            self.op_code, self.ver, self.sequence, self.physical,
            self.universe, self.length, self.data)

    def unpack_raw_artnet_packet(raw_data):

        if unpack('!8s', raw_data[:8])[0] != ArtnetPacket.ARTNET_HEADER:
            print("Received a non Art-Net packet")
            return None

        packet = ArtnetPacket()
        (packet.op_code, packet.ver, packet.sequence, packet.physical,
            packet.universe, packet.length) = unpack('!HHBBHH', raw_data[8:18])

        packet.data = unpack(
            '{0}s'.format(int(packet.length)),
            raw_data[18:18+int(packet.length)])[0]

        return packet
    
    def artnet_packet_to_array(raw_data):
        if unpack('!8s', raw_data[:8])[0] != ArtnetPacket.ARTNET_HEADER:
            print("Received a non Art-Net packet")
            return None

        if len(raw_data) == 530:
            packet = ArtnetPacket()
            (packet.op_code, packet.ver, packet.sequence, packet.physical,
                packet.universe, packet.length) = unpack('!HHBBHH', raw_data[8:18])

            rawData = unpack(
                '{0}s'.format(int(packet.length)),
                raw_data[18:18+int(packet.length)])[0]
            
            packet.data = list(rawData)
            return packet
        
        else:
            return None
        
        

def readPacket(IP, PORT):
    sock = socket(AF_INET, SOCK_DGRAM)  # UDP
    sock.bind((IP, PORT))

    data, addr = sock.recvfrom(1024)
    packet = ArtnetPacket.artnet_packet_to_array(data)
    sock.close()
    return(packet)