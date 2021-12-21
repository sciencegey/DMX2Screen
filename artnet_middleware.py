# Stolen from here :)
# https://gist.github.com/alarrosa14/07bd1ee88a19204cbf22

# Library that takes Artnet (DMX) packets and converts them to data that Python can use.

import sys

from socket import (socket, AF_INET, SOCK_DGRAM)
from struct import pack, unpack

debug = False

class ArtnetPacket:

    ARTNET_HEADER = b'Art-Net\x00' # the header for artnet packets

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
    
    # Extracts DMX data from the Artnet packet and puts it into a nice array :)
    def artnet_packet_to_array(raw_data):
        if unpack('!8s', raw_data[:8])[0] != ArtnetPacket.ARTNET_HEADER:
            # The packet doesn't have a valid header, so it's probably not an Artnet packet (or it's broken... :V)
            if debug: print("Received a non Art-Net packet")
            return None

        # makes sure the packet is the correct length (if it fetches them too quickly it comes through all malformed)
        if len(raw_data) == 530:
            # stores the packet...
            packet = ArtnetPacket()
            (packet.op_code, packet.ver, packet.sequence, packet.physical,
                packet.universe, packet.length) = unpack('!HHBBHH', raw_data[8:18])
                # ...then unpacks it into it's constituent parts

            # this takes the DMX data and converts it to an array
            rawData = unpack(
                '{0}s'.format(int(packet.length)),
                raw_data[18:18+int(packet.length)])[0]
            
            packet.data = list(rawData)
            # then returns it
            return packet
        
        else:
            # otherwise, return nothing
            return None


def readPacket(IP, PORT):
    # opens a UDP socket and binds it to the supplied IP and port
    sock = socket(AF_INET, SOCK_DGRAM)  # UDP
    sock.bind((IP, PORT))

    # then receive 1024 bytes of data (the packet)
    data, addr = sock.recvfrom(1024)
    # and decode it using the function.
    packet = ArtnetPacket.artnet_packet_to_array(data)
    # finally close the socket and return the packet to the main program.
    sock.close()
    return(packet)