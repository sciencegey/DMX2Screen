'''Simple library that takes Art-Net (DMX) packets and converts them to data that Python can use.

Made in Python 3.8
Artnet spec: https://www.artisticlicence.com/WebSiteMaster/User%20Guides/art-net.pdf
'''
import threading

from time import sleep
import random

from socket import (socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR)
from struct import pack, unpack

# This class is the actual packet itself (called from within the main class)
class ArtnetPacket:
    '''This class is the data structure for the packet.'''
    def __init__(self):
        self.opCode = None      # Should always be 80 (0x5000) (int16) (little endian)
        self.ver = None         # Latest is V1.4 (14) (int16, split in two)
        self.sequence = None    # Sequence number, used to check if the packets have arrived in the correct order (int8)
        self.physical = None    # The physical DMX512 port this data came from. (int8)
        self.universe = None    # Which universe this packet is meant for (int16 (actually 15 bytes)) (little endian)
        self.length = None      # How much DMX data we have (full packet is 18+length) (int16)
        self.data = None        # The actual DMX data itself

class ArtPollPacket:
    '''This class holds the incoming ArtPoll packet'''
    def __init__(self):
        self.opCode = None          # Should always be 32 (0x2000) (int16) (little endian)
        self.ver = None             # Latest is V1.4 (14) (int16, split in two)
        self.flags = None           # see art-net documentation (int8)
        self.diagPriority = None    # see artnet documentation (table 5) (int8)
                                    # And then we just ignore the rest ;)

class ArtPollReplyPacket:
    '''This class holds the ArtPollReply packet'''
    def __init__(self):
        self.id = b'Art-Net\x00'                # b'Art-Net\x00' (int8)
        self.opCode = pack('<H', 0x2100)        # 0x2100 (int16) (little endian)
        self.ipAddress = [127,0,0,1]            # array of the IP address (4xint8)
        self.port = pack('<H', 0x1936)          # 6454 (0x1936) (int16) (little endian)
        self.versInfo = b"14"                   # We're operating on V1.4 (14) (int16, split in two)
        self.netSwitch = 0b00000000             # 
        self.subSwitch = 0b00000000             # 
        self.oemCode = 0xabcd                   # Artnet OEM code (int16)
        self.ubeaVersion = 0                    # Not used, set to 0 (int8)
        self.status1 = 0b00110000               # see art-net documentation (int8)
        self.estaMan = pack('<H', 0x7FF0)       # ESTA manufacturer code (int16, little endian)
        self.portName = b'\x00'*18              # Set by the controller (17 characters and null, int8)
        self.longName = b'\x00'*64              # Set by the controller (63 characters and null, int8)
        self.nodeReport = b'\x00'*64            # Used for debugging, is formatted as xxxx [yyyy] zzzzz... (64 characters padding with null, int8)
        self.numPorts = 1                       # Num of input/output ports. Maximum is 4, but a node can ignore this and just set 0 (int16)
        self.portTypes = [0x80,0x00,0x00,0x00]  #
        self.goodInput = [0b00000000]*4         # Status of node, see documentation for bits to set (int8)
        self.goodInputA = [0b00000000]*4        # Same as above (int8)
        self.swIn = [0x00]*4                    # (4xint8)
        self.swOut = [0x00]*4                   # (4xint8)
        self.acnPriority = 1                    # Priority of sACN packet between 1 and 200, 200 being most important
        self.swMacro = 0                        # Only used if supporting macro inputs, otherwise set all 0s (int8)
        self.swRemote = 0                       # Only used if supporting remote trigger inputs, otherwise set all 0s (int8)
        self.null1 = b'\x00'*3                  # 3 bytes of null go here
        self.style = 0x00                       # see art-net documentation (int8)
        self.mac = [b"\x00"]*6                  # MAC address of the interface (6xint8)
        self.bindIp = [0,0,0,0]                 # IP address of the rppt device (only if part of a larger product) (4xint8)
        self.bindIndex = 0                      # 
        self.status2 = 0b00001101               # see art-net documentation (int8)
        self.goodOutputB = 0b11000000           # see art-net documentation (int8)
        self.status3 = 0b00000000               # see art-net documentation (int8)
        self.defaultRespUid = b'\x00'*6         #
        self.userData = 0x0000                  # User configurable, set to 0 (int16)
        self.refreshRate = 44                   # Max refresh rate for device, max DMX512 is 44hz (int16)
        self.null2 = b'\x00'*11                 # 11 bytes of null go here
    
    def __iter__(self):
        for each in self.__dict__.values():
            if isinstance(each,list):
               for j in each:
                   yield j
            else:
                yield each

class Artnet:
    ARTNET_HEADER = b'Art-Net\x00' # the header for Art-Net packets

    def __init__(self, BINDIP = "", PORT = 6454, SYSIP = "10.10.10.1", MAC = ["AA","BB","CC","DD","EE","FF"], SWVER = "14", SHORTNAME = "python_artnet", LONGNAME = "python_artnet", OEMCODE = 0xabcd, ESTACODE = 0x7FF0, PORTTYPE = [0x80,0x00,0x00,0x00], REFRESH = 44, DEBUG = False):
        self.BINDIP = BINDIP            # IP to listen on (either 0.0.0.0 (all interfaces) or a broadcast address)
        self.SYSIP = SYSIP              # IP of the system itself
        self.PORT = PORT                # Port to listen on (default is 6454)
        self.MAC = MAC                  # MAC address of the ArtNet port
        self.SWVER = SWVER              # Software version
        self.SHORTNAME = SHORTNAME[:17] # Short name
        self.LONGNAME = LONGNAME[:63]   # Long name
        self.OEMCODE = OEMCODE          # Art-Net OEM code
        self.ESTACODE = ESTACODE        # ESTA Manufacturer code
        self.PORTTYPE = PORTTYPE        # 
        self.REFRESH = REFRESH          # Refresh rate of the node

        self.debug = DEBUG

        self.packet = None
        self.packetBuffer = [ArtnetPacket()]*16

        # Starts the listner in it's own thread
        self.listen = True
        self.t = threading.Thread(target=self.__init_socket, daemon=True)
        self.t.start()

    def __init_socket(self):
        '''Creates a UDP socket with the specified IP and Port'''
        self.sock = socket(AF_INET, SOCK_DGRAM)  # UDP
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.sock.bind((self.BINDIP, self.PORT))
        
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
                # print("Recieved from:" + str(addr))
                self.packet = Artnet.artnet_packet_to_array(self, data, addr)

    def close(self):
        '''Tells the socket to stop running and joins the thread back'''
        self.listen = False
        self.t.join()

    def art_pol_reply(self, senderAddr):
        '''Sends a reply to an ArtPoll packet; this allows other devices on the network to know who we are.'''
        reply = ArtPollReplyPacket()
        
        reply.ipAddress = [int(i) for i in self.SYSIP.split(".")]
        reply.port = pack('<H', self.PORT)
        reply.versInfo = str.encode(self.SWVER)
        reply.oemCode = self.OEMCODE
        reply.estaMan = pack('<H', self.ESTACODE)
        reply.portTypes = self.PORTTYPE
        reply.refreshRate = self.REFRESH
        for i in range(len(self.MAC)):
            reply.mac[i] = bytes.fromhex(self.MAC[i])
        reply.portName = str.encode(self.SHORTNAME).ljust(18, b'\x00')
        reply.longName = str.encode(self.LONGNAME).ljust(64, b'\x00')
        
        if self.debug: print(*reply)
        packedReply = pack('!8s2s4B2s2sBBHBB2s18s64s64sH4B4B4B4B4BBBB3sB1s1s1s1s1s1s4BBBBB6sHH11s', *reply)
        
        # Sleep a random period between 0 and 1 seconds before sending the reply
        sleep(random.random())
        self.sock.sendto(packedReply, senderAddr)
        if self.debug: print("sent!")
        
        return None
        
    def artnet_packet_to_array(self, raw_data, senderAddr):
        '''Extracts DMX data from the Art-Net packet and returns it as a nice array.'''
        if unpack('!8s', raw_data[:8])[0] != Artnet.ARTNET_HEADER:
            # The packet doesn't have a valid header, so it's probably not an Art-Net packet (or it's broken... :V)
            if self.debug: print("Received a non Art-Net packet")
            return None

        # Extracts the opcode from the packed (little endian int16)
        opCode = unpack('<H', raw_data[8:10])
        # and checks to see if the packet is an DMX Art-Net packet (0x5000)
        if opCode[0] == 0x5000:
            length = unpack('!H', raw_data[16:18])
            # makes sure the packet is the correct length (if it fetches them too quickly it comes through all malformed)
            if len(raw_data) == 18+length[0]:
                # stores the packet...
                packet = ArtnetPacket()
                # ...then unpacks it into it's constituent parts
                (packet.ver, packet.sequence, packet.physical, packet.universe, packet.length) = unpack('!HBBHH', raw_data[10:18])
                
                # These guys are little endian, so we need to swap the order
                packet.opCode = opCode[0]
                packet.universe = unpack('<H', pack('!H', packet.universe))[0]

                # this takes the DMX data and converts it to an array
                rawData = unpack(
                    '{0}s'.format(int(packet.length)),
                    raw_data[18:18+int(packet.length)])[0]
                
                packet.data = list(rawData)
                # then returns it
                self.packetBuffer[packet.universe] = packet
                return packet
            else:
                return None

        # or checks to see if the packet is an ArtPoll packet (0x2000)
        elif opCode[0] == 0x2000:
            if self.debug: print("poll!")
            # if the packet is at least 14 bytes, then it might be an ArtPoll packet
            if len(raw_data) >= 14:
                # stores the packet...
                pollPacket = ArtPollPacket()
                # ...then unpacks it into it's constituent parts
                (pollPacket.ver, pollPacket.flags, pollPacket.diagPriority) = unpack('!HBB', raw_data[10:14])

                pollPacket.opCode = opCode[0]
                
                # Then we need to be nice and send an ArtPollReply to let the controller know that we exist
                self.reply = threading.Thread(target=Artnet.art_pol_reply, args=(self, senderAddr))
                self.reply.start()
                
                # When we've sent the packet, we can return
                return None
            else:
                # No idea what we received in that case :V
                return None
            
        else:
            # otherwise, nothing happened so return it
            return None

    def readPacket(self):
        '''Returns the last Art-Net packet that we received.'''
        return(self.packet)
    
    def readBuffer(self):
        '''Returns the Art-Net packet buffer'''
        return(self.packetBuffer)
    
    def version(self):
        '''Returns the library version'''
        return "1.1.0"
    
if __name__ == "__main__":
    ### Art-Net Config ###
    artnetBindIp = ""
    systemIp = "192.168.1.165"
    artnetPort = 6454
    artnetUniverse = 0
    
    artNet = Artnet(artnetBindIp,artnetPort,systemIp,DEBUG=True)
    while True:
        try:
            artNetPacket = artNet.readPacket()
            if artNetPacket is not None:
                # Checks to see if the current packet is for the specified DMX Universe
                if artNetPacket.universe == artnetUniverse:
                    # Stores the packet data array
                    dmx = artNetPacket.data
                    print(*dmx[:12])
                    sleep(1)
        except KeyboardInterrupt:
            break
