import struct
from . import message
try:
    import numpy as np
except:
    from libdm.dmb import np_fallback as np


class DBR:
    def __init__(self, data):
        self.pos = 0
        self.data = data

    def at(self, idx):
        return self.data[idx]

    def range(self, start, end):
        return self.data[start:end]

    def avail(self):
        return len(self.data) - self.pos

    def uint8(self, be=False):
        bom = '>' if be else '<'
        data = self.data[self.pos:self.pos+1]
        self.pos += 1
        return struct.unpack('{0}B'.format(bom), data)[0]

    def uint16(self, be=False):
        bom = '>' if be else '<'
        data = self.data[self.pos:self.pos+2]
        self.pos += 2
        return struct.unpack('{0}H'.format(bom), data)[0]

    def uint32(self, be=False):
        bom = '>' if be else '<'
        data = self.data[self.pos:self.pos+4]
        self.pos += 4
        return struct.unpack('{0}I'.format(bom), data)[0]

    def bytes(self, count):
        data = self.data[self.pos:self.pos+count]
        self.pos += count
        return data

    def skip_to_check(self):
        return self.bytes(self.avail() - 1)

    def decrypt(self, key, check=True):
        return message.packet_decrypt(self.data, key, len(self.data) - 1 if check else -1)


class Dissector:
    def __init__(self):
        self.queued_dumps = []
        pass

    def fields(self, mlen, mid, isserver, tag="__main__"):
        if not isserver and mid == 1:
            return {
                8: "\033[35m",
                12: "\033[36m",
                16: "\033[37m",
                18: "\033[32m",
            }
        elif isserver and mid == 1 and tag == "decrypted":
            return {
                4: "\033[35m",
                8: "\033[36m",
                9: "\033[37m",
                10: "\033[32m",
                11: "\033[37m",
                15: "\033[30m",
                19: "\033[31m",
                mlen - 1: "\033[30m",
                mlen: "\033[31m",
            }
        elif mid == 26:
            return {
                mlen: "\033[0m",
            }
        return {
            mlen - 1: "\033[0m",
            mlen: "\033[31m",
        }

    def queue_hexdump(self, tag, message, mid, isserver):
        self.queued_dumps.append((tag, message, mid, isserver))

    def hexdump(self, message, mid, isserver, tag="__main__", no_queue=False):
        if tag != "__main__":
            print("@{0}:".format(tag))
        offset = 0

        color_codes = {
            0: "\033[0m"
        }
        if tag == "__main__":
            if mid == 1:
                color_codes = {
                    0: "\033[0m",
                    2: "\033[33m",
                    4: "\033[34m",
                }
            else:
                color_codes = {
                    0: "\033[0m",
                    2: "\033[35m",
                    4: "\033[33m",
                    6: "\033[34m",
                }
        color_codes.update(self.fields(len(message), mid, isserver, tag=tag))
        data = ""
        print("           \033[0;1m 0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F\033[0;m")
        for b in message:
            if data != "":
                data += " "
            else:
                data = "\033[0;1m{0:08X}\033[0m   ".format(offset)
            mn = len(message) + 1
            for i in color_codes:
                if i < mn and offset < i:
                    mn = i
            data += "{0}{1:02X}{2}".format(color_codes[mn], b, color_codes[0])
            offset += 1
            if offset % 16 == 0:
                print(data)
                data = ""
        if data != "":
            print(data)
        if not no_queue:
            for ntag, nmessage, nmid, nisserver in self.queued_dumps:
                self.hexdump(nmessage, nmid, nisserver, tag=ntag, no_queue=True)
            self.queued_dumps = []

    def dissect(self, messages):
        # analyzed = []
        client_key = 0
        server_key = 0
        handshook = False
        for isserver, msg in messages:

            # if isserver:
            #    analyzed.append("Server message, skipped.")
            #    print("Server message, skipped.")
            #    continue
            reader = DBR(msg)
            # if handshook:
            #    reader.decrypt(server_key)
            seq = 0
            msgid = reader.uint16(True)
            if not isserver and msgid != 1:
                seq = msgid
                msgid = reader.uint16(True)
            datalen = reader.uint16(True)
            thismsg = message.Message(msgid, reader.bytes(datalen))
            reader = DBR(thismsg.data)
            dissect_data = ""
            if not isserver:
                if msgid == 1:
                    client = reader.uint32()
                    protocol = reader.uint32()
                    client_key = int(np.uint32(reader.uint32()) + np.uint32(client) + np.uint32(protocol << 16))
                    next_seq = reader.uint16()
                    dissect_data = 'client version {0}, protocol version {1}, key {2}, next sequence: {3}'.format(client, protocol, hex(client_key), next_seq)
                elif msgid == 26:
                    print(repr(list(reader.data)))
                    print(datalen)
                    print(len(reader.data))
                    print(reader.at(-6))
                    #key_len = datalen - 8 - reader.at(-6)
                    for start in range(len(reader.data)):
                        for key_len in range(len(reader.data) - start):
                            conn_key = reader.range(start, start + key_len)
                            message.strange_decrypt(conn_key, b'<|3^\nq\r[')
                            #str_key = conn_key.decode('utf-8')
                            print("{0} ({2}:{1})".format(conn_key, key_len + start, start))
                    dissect_data = 'key length: {0}, connected key: {1}'.format(key_len, conn_key)
                else:
                    chk = reader.decrypt(server_key)
                    self.queue_hexdump("decrypted", reader.data, msgid, True)
                    #reader.skip_to_check()
                    #dissect_data = 'exp chk: {0}, sent chk: {1}'.format(chk, reader.uint8())
            else:
                if msgid == 1:
                    exp_check = reader.decrypt(client_key)
                    self.queue_hexdump("decrypted", reader.data, 1, True)
                    server = reader.uint32()
                    reader.uint32()
                    reader.bytes(3)
                    reader.bytes(4)  # obfuscation
                    server_key = reader.uint32()
                    garbage = reader.skip_to_check()
                    check = reader.uint8()
                    # garbage = reader.skip_to_check()
                    # check = reader.uint8()
                    dissect_data = 'server version {0}, garbage {1}, key {2} (check={3}, expected {4})'.format(server, garbage.hex(), hex(server_key), check, exp_check)
                    handshook = True
                else:
                    chk = reader.decrypt(server_key)
                    reader.skip_to_check()
                    dissect_data = 'exp chk: {0}, sent chk: {1}'.format(chk, reader.uint8())
                    pass

            print('{0} -- {1}: {2}'.format('Server' if isserver else 'Client', str(thismsg), dissect_data))
            self.hexdump(msg, thismsg.id, isserver)
            if (reader.avail() > 0):
                print("Warning: message has {0} unread bytes available".format(reader.avail()))
