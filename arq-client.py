#!/usr/bin/env python
"""""
@File:           arq-client.py
@Description:    This is a sender running Selective Repeat protocol
                 for reliable data transfer.
@Author:
@EMail:
@License         GNU General Public License
@python_version: 2.7
===============================================================================
"""
import argparse  # library for parsing arguments of the program
import socket 	 # socket library. Wraper of C standard library
import sys		 # library for interaction with OS
import os
import struct
import select
import logging
from collections import namedtuple

import traceback

sys.setrecursionlimit(100000)

# Set logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s SENDER [%(levelname)s] %(message)s',)
log = logging.getLogger()

class Sender(object):
    """
    Sender running Selective Repeat protocol for reliable data transfer.
    """
    def __init__(self,
                 senderIP="127.0.0.1",
                 senderPort=55555,
                 receiverIP="127.0.0.1",
<<<<<<< HEAD
                 receiverPort=55554,
                 sequenceNumberBits=2,
                 windowSize=5,
=======
                 receiverPort=8000,
                 windowSize=128,
>>>>>>> e0e8bc6e076988095c4fc158c0e0551f69c65e70
                 timeout=1,
                 maxSegmentSize=1480,
                 file_path=os.path.join(os.getcwd(), "data", "sender") + "index.html"):
        self.senderIP = senderIP
        self.senderPort = senderPort
        self.receiverIP = receiverIP
        self.receiverPort = receiverPort
        self.sequenceNumberBits = sequenceNumberBits
        self.maxSegmentSize = maxSegmentSize
        self.windowSize = windowSize
        self.file_path = file_path
        self.timeout = timeout
        self.receiverSocket = (self.receiverIP, self.receiverPort)

    def file_open(self):
        """
                Read data from file or from stdin.
                        """
        log.info("Open file %s for reading" % self.file_path)
        global fd
        if self.file_path:
            try:
                fd = open(self.file_path, 'rb')
                return fd # if name is given as a paramiter returns file descriptor
            except Exception:
                if not os.path.exists(file_path):
                    log.info("File does not exist!\nFilename: %s" % file_path)
                    sys.exit(0)
            else:
                try:
                    return sys.stdin       # else returns stdin
                except Exception as e:
                    log.info("Function sys.stdin return not zero code!")
                    log.debug(e)
                    sys.exit(0)

    def file_close(self):
        try:
            if self.fd:
                self.fd.close() # try to close descriptor
        except Exception:
            pass

    def socket_open(self):
        """
        Create UDP socket for communication with the server.
        """
        log.info("Creating UDP socket %s:%d for communication with the server",
                 self.receiverIP, self.receiverPort)
        try:
            self.senderSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.senderSocket.bind((self.senderIP, self.senderPort))
        except Exception as e:
            log.error("Could not create UDP socket for communication with the server!")
            log.debug(e)
            traceback.print_exc()

    def socket_close(self):
        """
        Close UDP socket.
        """
        try:
            if self.senderSocket:
                self.senderSocket.close()
        except Exception as e:
            log.error("Could not close UDP socket!")
            log.debug(e)
        self.file_close()

    def generate_packets(self, fd):
        """
        Generate packets for transmitting to receiver.
        """
        packets = []
        i = 1
        sequenceNumber = 1
        log.info("Generating packets for transmitting to receiver")
        while True:
            # Read data such that
            # size of data chunk should not exceed maximum payload size
            # If not data, finish reading
            if sequenceNumber % self.windowSize == 0:
                break
            data = fd.read(self.maxSegmentSize)
            # If not data, finish reading
            if not data:
                break
            # Set sequence number for a packet to be transmitted
            sequenceNumber = i
            # Create a packet with required header fields and payload
            PACKET = namedtuple("Packet", ["SequenceNumber", "Checksum", "Data"])
            pkt = PACKET(SequenceNumber=sequenceNumber,
                         Checksum=self.checksum(data),
                         Data=data)
            packets.append(pkt)
            i += 1
        return packets

    def checksum(self, data):
        """
        Compute and return a checksum of the given payload data.
        """
<<<<<<< HEAD
        if (len(data)%2 != 0):
            data += "0"
=======
        if (len(data) % 2) != 0:
            data += "0"

>>>>>>> e0e8bc6e076988095c4fc158c0e0551f69c65e70
        sum = 0
        for i in range(0, len(data), 2):
            data16 = ord(data[i]) + (ord(data[i+1]) << 8)
            sum = self.carry_around_add(sum, data16)
        return ~sum & 0xffff

    def carry_around_add(self, sum, data16):
        """
        Helper function for carry around add.
        """
        sum = sum + data16
        return (sum & 0xffff) + (sum >> 16)

    def send_packets(self, fd):
        """
        Start packet transmission.
        """
        # Get data from Application Layer and
        # create packets for reliable transmission
        log.info("Generating packets")
        global packets
        packets = self.generate_packets(fd) # Global variable
        lever = True
        if packets:
            log.info("Starting transmission of %s packets" % self.windowSize)
            for packet in packets:
                raw_packet = self.make_pkt(packet)
                self.senderSocket.sendto(raw_packet, self.receiverSocket)
            log.info("Stopping transmission of %s packets" % self.windowSize)
        else:
            self.socket_close()

    def make_pkt(self, packet):
        """
        Create a raw packet.
        """
        sequenceNumber = struct.pack('=I', packet.SequenceNumber)
        checksum = struct.pack('=H', packet.Checksum)
        rawPacket = sequenceNumber + checksum + packet.Data
        return rawPacket

    def parse(self, receivedPacket):
        """
        Parse header fields and payload data from the received packet.
        """
        header = receivedPacket[0:6]
        sequenceNumber = struct.unpack('=I', header[0:4])[0]
        checksum = struct.unpack('=H', header[4:])[0]
        ACK = namedtuple("ACK", ["AckNumber", "Checksum"])
        packet = ACK(AckNumber=sequenceNumber,
                     Checksum=checksum)
        return packet

    def ack_timeout(self, fd):
        """
        Wait for acknowledgement.
        """
        while True:
            ready = select.select([self.senderSocket], [], [], self.timeout)
            if ready[0]:
                while packets:
                    received_data = self.senderSocket.recv(6)
                    ack = self.parse(received_data)
                    print ack
                    for packet in packets:
                        if packet.SequenceNumber == ack.AckNumber:
                            packets.remove(packet)
                    if len(packets) != 0:
                        self.resend_packets(packets, fd)
                    else:
                        break
                break
            else:
                self.resend_packets(packets, fd)

    def resend_packets(self, packet, fd):
        """
        Retransmit lost data.
        """
        log.info("Starting retransmition of %s packets" % len(packets))
        for packet in packets:
            raw_packet = self.make_pkt(packet)
            self.senderSocket.sendto(raw_packet, self.receiverSocket)
        log.info("Stopping retransmission of %s packets" % len(packets))

    def windows_num(self):
        file_struct = os.stat(self.file_path)
        windows_num = file_struct.st_size/(self.windowSize*self.maxSegmentSize)
        print windows_num
        return windows_num


def main():
    #client = Sender(file_path='/home/renat/Labs/Python/ARQ/ARQ/data/sender/ViewOfMagdeburg.jpg')
    client = Sender(file_path='/home/max/ARQ/SR_ARQ/data/send/viber.deb')
    client.socket_open()
    fd = client.file_open()
    windows_num = client.windows_num()
    for window in range(windows_num + 1):
        client.send_packets(fd)
        client.ack_timeout(fd)
    client.socket_close()


if __name__ == '__main__':
    main()
