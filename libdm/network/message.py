try:
    import numpy as np
except:
    from libdm.dmb import np_fallback as np
import struct


def packet_encrypt(data, key, max=-1):
    old = np.seterr(all='ignore')
    index = np.uint8(0)
    count = max
    for idx, byte in enumerate(data):
        if count == 0:
            break
        b8 = np.uint8(byte)
        encoded = b8 + np.uint8((key >> (index & np.uint8(0x1F))) & 0xFF) + index
        index = index + b8
        data[idx] = int(encoded)
        count -= 1
    np.seterr(**old)
    return int(index)


def packet_decrypt(data, key, max=-1):
    old = np.seterr(all='ignore')
    index = np.uint8(0)
    count = max
    for idx, byte in enumerate(data):
        if count == 0:
            break
        b8 = np.uint8(byte)
        decoded = b8 - np.uint8((key >> (index & np.uint8(0x1F))) & 0xFF) - index
        data[idx] = int(decoded)
        index = index + decoded
        count -= 1
    np.seterr(**old)
    return int(index)


def strange_encrypt(data, key):
    old = np.seterr(all='ignore')
    s = np.uint8(0)
    for idx, spec in enumerate(list(reversed(list(enumerate(data))))):
        orig, byte = spec
        b8 = np.uint8(byte)
        encoded = b8 + s + np.uint8(key[idx % len(key)])
        s = s + b8
        data[orig] = int(encoded)
    np.seterr(**old)


def strange_decrypt(data, key):
    old = np.seterr(all='ignore')
    s = np.uint8(0)
    for idx, spec in enumerate(list(reversed(list(enumerate(data))))):  # jfc
        orig, byte = spec
        b8 = np.uint8(byte)
        decoded = b8 - s - np.uint8(key[idx % len(key)])
        s = s + decoded
        data[orig] = int(decoded)
    np.seterr(**old)


class bytebuf:
    def __init__(self, le=False):
        self.a = bytearray(b'')
        self.le = le

    def write(self, bcount, bdata, se=False):
        if (self.le and not se) or (se and not self.le):
            e = '<'
        else:
            e = '>'
        if bcount == 1:
            c = 'B'
        if bcount == 2:
            c = 'H'
        elif bcount == 4:
            c = 'I'
        else:
            raise ValueError('Byte count not recognized: {0}'.format(bcount))
        self.a += struct.pack('{0}{1}'.format(e, c), bdata)

    def write_raw(self, bdata):
        self.a += bdata

    def __bytes__(self):
        return self.a

    def __len__(self):
        return len(self.a)


class Message:
    def __init__(self, idnum, data):
        self.id = idnum
        self.data = data
        self._client = False

    def prepare(self, seq):
        buf = bytebuf()
        next_seq = (seq + 17364) % np.uint32(0xFFF1)
        if next_seq == 0:
            next_seq = 1
        if seq != 0:
            buf.write(2, seq)
        buf.write(2, self.id)
        buf.write(2, len(self.data))
        buf.write_raw(self.data)
        return (buf, next_seq)

    def str_type(self):
        if self.id == 1:
            return 'Handshake'
        if self.id == 26:
            return 'Key exchange'
        else:
            return 'UNKNOWN'

    def __str__(self):
        return "Message <id={0} ({2})>".format(self.id, self.data, self.str_type())
