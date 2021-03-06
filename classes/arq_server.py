#! /usr/bin/env python
import socket                   # Socket library. Wraper of C standard library
import traceback
import sys                      # library for interaction with OS
import os
import struct
import select
import hashlib
import logging
from collections import namedtuple
from operator import attrgetter

# Set logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s RECEIVER [%(levelname)s] %(message)s',)
log = logging.getLogger()
log.disabled = True
class Receiver(object):
    """
    Receiver running Selective Repeat protocol for reliable data transfer.
    """
    last_window_seq = []
    received_seq = []
    received_packets =[]
    checksum = False
    def __init__(self,
                 receiverIP="0.0.0.0",
                 receiverPort=55554,
                 senderIP="127.0.0.1",
                 senderPort=55555,
                 windowSize=1500,
                 timeout=1.1,
                 bufferSize=1500,
                 file_path=os.path.join(os.getcwd(), "data", "receiver") + "index.html"):
        self.receiverIP = receiverIP
        self.receiverPort = receiverPort
        self.receiverSocket = (self.receiverIP, self.receiverPort)
        self.windowSize = windowSize
        self.file_path = file_path
        self.senderIP = senderIP
        self.senderPort = senderPort
        self.senderSocket = (self.senderIP, self.senderPort)
        self.bufferSize = bufferSize
        self.timeout = timeout

    def socket_open(self):
        """
        Create UDP socket for communication with the client.
        """
        log.info("Creating UDP socket %s:%d for communication with the client",
                 self.receiverIP, self.receiverPort)

        try:
            self.receiverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.receiverSocket.bind((self.receiverIP, self.receiverPort))
        except Exception as e:
            log.error("Could not create UDP socket for communication with the client!")
            log.debug(e)
            traceback.print_exc()

    def file_open(self):
        """
        Open file or stdin.
        """
        log.info("Open file %s for writing" % self.file_path)
        global fd
        if self.file_path:
            try:
                fd = open(self.file_path, 'w')
                return fd # if name is given as a paramiter returns file descriptor
            except Exception:
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

    def file_write(self, packet):
        if packet.SequenceNumber not in self.received_seq:
            self.received_packets.append(packet)
            self.received_seq.append(packet.SequenceNumber)
        else:
            log.info("Received dublicate of previous packet")
        if len(self.received_packets) == self.windowSize:
            self.received_packets = sorted(self.received_packets, key=attrgetter('SequenceNumber'))
            for i in self.received_packets:
                fd.write(i.Data)
            self.received_packets = []
        if len(self.received_seq) + 1 == 10 * self.windowSize:
            self.received_seq = self.received_seq[self.windowSize:]
            print(self.received_seq)
        ready = select.select([self.receiverSocket], [], [], self.timeout)
        if ready[0]:
            pass
        else:
            self.received_packets = sorted(self.received_packets, key=attrgetter('SequenceNumber'))
            for i in self.received_packets:
                fd.write(i.Data)
            self.received_packets = []

    def run(self):
        """
        Start monitoring packet receipt.
        """
        log.info("Started to monitor packet receipt")
        # Monitor receiver
        # untill all packets are successfully received from sender
        i = 0
        while True:
            # Listen for incoming packets on receiver's socket
            # with the provided timeout
            try:
                receivedPacket, _ = self.receiverSocket.recvfrom(self.bufferSize)
            except Exception as e:
                log.error("Could not receive UDP packet!")
                log.debug(e)
            # Parse header fields and payload data from the received packet
            receivedPacket = self.parse(receivedPacket)
            # Check whether the received packet is not corrupt
            if self.checksum:
                if self.corrupt(receivedPacket):
                    log.warning("Received corrupt packet!!")
                    log.warning("Discarding packet with sequence number: %d",
                            receivedPacket.SequenceNumber)
                    continue
            # Otherwise, store received packet into receipt window and
            # send corresponding acknowledgement
            log.info("Received packet with sequence number: %d",
                         receivedPacket.SequenceNumber)
            log.info("Transmitting an acknowledgement with ack number: %d",
                         receivedPacket.SequenceNumber)
            self.generate_ack(receivedPacket.SequenceNumber)
            self.file_write(receivedPacket)

    def parse(self, receivedPacket):
        """
        Parse header fields and payload data from the received packet.
        """
        header = receivedPacket[0:6]
        data = receivedPacket[6:]

        sequenceNumber = struct.unpack('=I', header[0:4])[0]
        if self.checksum:
            checksum = struct.unpack('=H', header[4:6])[0]
            PACKET = namedtuple("Packet", ["SequenceNumber", "Checksum", "Data"])
            packet = PACKET(SequenceNumber=sequenceNumber,
                                      Checksum=checksum,
                                      Data=data)
        else:
            PACKET = namedtuple("Packet", ["SequenceNumber", "Data"])
            packet = PACKET(SequenceNumber=sequenceNumber,
                                      Data=data)
        return packet

    def udt_send(self, ack):
        """
        Transmit an acknowledgement using underlying UDP protocol.
        """
        try:
            self.receiverSocket.sendto(ack, (self.senderIP, self.senderPort))
        except Exception as e:
            log.error("Could not send UDP packet!")
            log.debug(e)

    def checksum(self, data):
        """
        Compute and return a checksum of the given payload data.
        """
        if (len(data)%2 != 0):
            data += "1"
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

    def generate_ack(self, ackNumber):
        """
        Reliable acknowledgement transfer.
        """
        if self.checksum:
            ACK = namedtuple("ACK", ["AckNumber", "Checksum"])
            ack = ACK(AckNumber=ackNumber,
                  Checksum=self.get_hashcode(ackNumber))
        else:
            ACK = namedtuple("ACK", ["AckNumber"])
            ack = ACK(AckNumber=ackNumber)
        # Create a raw acknowledgement
        rawAck = self.make_pkt(ack)
        # Transmit an acknowledgement using underlying UDP protocol
        self.udt_send(rawAck)

    def get_hashcode(self, data):
        """
        Compute the hash code.
        """
        hashcode = hashlib.md5()
        hashcode.update(str(data))
        return hashcode.digest()

    def make_pkt(self, ack):
        """
        Create a raw acknowledgement.
        """
        ackNumber = struct.pack('=I', ack.AckNumber)
        if self.checksum:
            checksum = struct.pack('=16s', ack.Checksum)
            rawAck = ackNumber + checksum
        else:
            rawAck = ackNumber
        return rawAck

    def corrupt(self, receivedPacket):
        """
        Check whether the received packet is corrupt or not.
        """
        # Compute checksum for the received packet
        computedChecksum = self.checksum(receivedPacket.Data)

        # Compare computed checksum with the checksum of received packet
        if computedChecksum != receivedPacket.Checksum:
            return True
        else:
            return False

    def socket_close(self):
        """
        Close UDP socket.
        """
        try:
            if self.receiverSocket:
                self.receiverSocket.close()
        except Exception as e:
            log.error("Could not close UDP socket!")
            log.debug(e)
        self.file_close()

def main():
    server = Receiver(file_path='/home/renat/Labs/Python/ARQ/ARQ/data/receiver/ViewOfMagdeburg.jpg')
    try:
        server.socket_open()
        server.socket_close()
    except:
        server.socket_close()

if __name__ == '__main__':
    main()
