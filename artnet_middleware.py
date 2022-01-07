# Stolen from here :)
# https://gist.github.com/alarrosa14/07bd1ee88a19204cbf22

# Library that takes Artnet (DMX) packets and converts them to data that Python can use.
import threading

from time import sleep

from socket import (socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR)
from struct import pack, unpack

debug = False

# This class is the actual packet itself (called from within the main class)
class ArtnetPacket:
    def __init__(self):
        self.op_code = None
        self.ver = None
        self.sequence = None
        self.physical = None
        self.universe = None
        self.length = None
        self.data = None

class Artnet:
    ARTNET_HEADER = b'Art-Net\x00' # the header for artnet packets

    def __init__(self, IP, PORT):
        self.IP = IP        # IP from main program
        self.PORT = PORT    # Port from main program

        self.packet = None

        # Starts the listner in it's own thread
        self.listen = True
        self.t = threading.Thread(target=self.__init_socket, daemon=True)
        self.t.start()

    def __init_socket(self):
        # Creates a UDP socket with the specified IP and Port
        self.sock = socket(AF_INET, SOCK_DGRAM)  # UDP
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.sock.bind((self.IP, self.PORT))
        
        # Will keep listening until it's told to stop ;)
        while self.listen:
            try:
                data, addr = self.sock.recvfrom(1024)
            except Exception as e:
                # Unless something goes wrong :V
                sleep(0.1)
                print(e)
                self.packet = None
            else:
                # Otherwise get the raw packet and decode it using the function.
                self.packet = Artnet.artnet_packet_to_array(data)

    def close(self):
        # Tells the socket to stop running and joins the thread back
        self.listen = False
        self.t.join() 

    def __str__(self):
        return ("ArtNet package:\n - op_code: {0}\n - version: {1}\n - "
                "sequence: {2}\n - physical: {3}\n - universe: {4}\n - "
                "length: {5}\n - data : {6}").format(
            self.op_code, self.ver, self.sequence, self.physical,
            self.universe, self.length, self.data)

    # Extracts DMX data from the Artnet packet and puts it into a nice array :)
    def artnet_packet_to_array(raw_data):
        if unpack('!8s', raw_data[:8])[0] != Artnet.ARTNET_HEADER:
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

            # and checks to see if the packet is an DMX Artnet packet (0x80)
            if packet.op_code == 80:
                # this takes the DMX data and converts it to an array
                rawData = unpack(
                    '{0}s'.format(int(packet.length)),
                    raw_data[18:18+int(packet.length)])[0]
                
                packet.data = list(rawData)
                # then returns it
                return packet
            else:
                return None
        
        else:
            # otherwise, return nothing
            return None

    def readPacket(self):
        # Literally just returns the packet ¯\_(ツ)_/¯
        return(self.packet)