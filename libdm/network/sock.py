from message import Message
import socket
import struct


class ByondSocket:
    def __init__(self):
        self.sock = socket.socket()

    def receive(self, seq):
        msg = self.sock.recv(4096)
        ptr = 0
        if seq != 0:
            ptr += 2
        idnum = struct.unpack('>H', msg[ptr:ptr+2])[0]
        ptr += 2
        dlen = struct.unpack('>H', msg[ptr:ptr+2])[0]
        while len(msg) - ptr < dlen:
            msg += self.sock.recv(4096)
        data = msg[ptr:ptr+dlen]
        return Message(idnum, data)
