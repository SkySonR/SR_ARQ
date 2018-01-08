#! /usr/bin/env python
"""""
@File:           arq-server.py
@Description:    This is a sender running Selective Repeat protocol
                 for reliable data transfer.
@Author:
@EMail:
@License         GNU General Public License
@python_version: 2.7
===============================================================================
"""
import argparse  # library for parsing arguments of the program
from classes import arq_server

parser = argparse.ArgumentParser()

parser.add_argument("-I", "--ip", type=str, help="specify destination ip address")
parser.add_argument("-t", "--timeout", type=str, help="specify timeout between windows")
parser.add_argument("-pc", "--client_port", type=int, help="specify the client port")
parser.add_argument("-ps", "--server_port", type=int, help="specify the server port")
parser.add_argument("-f", "--file", type=str, help="specify the transieved file")
args = parser.parse_args()
if not args.file or not args.ip  or not args.client_port or not args.server_port:
    parser.print_help()
    exit(0)
def main():
    server = arq_server.Receiver(file_path=args.file, senderIP=args.ip, senderPort=args.client_port, receiverPort=args.server_port)
    try:
        server.socket_open()
        server.file_open()
        server.run()
        server.socket_close()
    except:
        server.socket_close()

if __name__ == '__main__':
    main()
