import itertools
from dmb import dmb
import re
import struct


class DmbFileError(ValueError):
    pass


class dmbreader:
    def __init__(self, dmbname):
        self.reader = open(dmbname, 'rb')
        self.bit32 = False
        self.world = dmb.world_data()
        self.parse_version_data()

    def __del__(self):
        if self.reader is not None:
            self.reader.close()

    def uint32(self):
        b = self.reader.read(4)
        return struct.unpack('<I', b)[0]

    def uint16(self):
        b = self.reader.read(2)
        return struct.unpack('<h', b)[0]

    def parse_version_data(self):
        ver_str = self.read_bytes_until(b'\x0A').decode('ascii')
        match = re.search(r'world bin v([0-9]*)', ver_str)
        if match is not None:
            self.world.world_version = int(match.group(1))
        else:
            raise DmbFileError('Cannot parse world version from dmb file.')
        ver_str = self.read_bytes_until(b'\x0A').decode('ascii')
        match = re.search(r'min compatibility v([0-9]*) ([0-9]*)', ver_str)
        if match is not None:
            self.world.min_server = int(match.group(1))
            self.world.min_client = int(match.group(2))
        else:
            raise DmbFileError('Cannot parse compatibility version from dmb file.')

        flags = self.uint32()
        self.world.map_x, self.world.map_y, self.world.map_z = (self.uint16(), self.uint16(), self.uint16())
        self.bit32 = flags & 0x40000000 > 0

    def bytegen(self):
        eof = False
        while not eof:
            byte = self.reader.read(1)
            if byte == b'':
                eof = True
                break
            yield byte

    def read_bytes_until(self, delimiter):
        return b''.join([b for b in itertools.takewhile(lambda x: x != delimiter, self.bytegen())])
