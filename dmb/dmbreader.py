from .dmb import tile, proc, world_data, var, instance, resource, type as btype
from .tree import ObjectTree
from .util import ModularInt, mod8
from . import value
import re
import io
import struct
import time


control_codes = {
    bytes([0xff, 1]):  b'\\1',
    bytes([0xff, 2]):  b'\\2',
    bytes([0xff, 3]):  b'\\3',
    bytes([0xff, 6]):  b'\\a',
    bytes([0xff, 7]):  b'\\A',
    bytes([0xff, 8]):  b'\\the',
    bytes([0xff, 9]):  b'\\The',
    bytes([0xff, 10]): b'\\he',
    bytes([0xff, 11]): b'\\He',
    bytes([0xff, 12]): b'\\his',
    bytes([0xff, 13]): b'\\His',
    bytes([0xff, 16]): b'\\him',
    bytes([0xff, 17]): b'\\himself',
    bytes([0xff, 18]): b'\\...',
    bytes([0xff, 20]): b'\\s',
    bytes([0xff, 21]): b'\\proper',
    bytes([0xff, 22]): b'\\improper',
    bytes([0xff, 23]): b'\\bold',
    bytes([0xff, 24]): b'\\italic',
    bytes([0xff, 25]): b'\\underline',
    bytes([0xff, 27]): b'\\font',
    bytes([0xff, 28]): b'\\color',
    bytes([0xff, 31]): b'\\red',
    bytes([0xff, 32]): b'\\green',
    bytes([0xff, 33]): b'\\blue',
    bytes([0xff, 34]): b'\\black',
    bytes([0xff, 35]): b'\\white',
    bytes([0xff, 36]): b'\\yellow',
    bytes([0xff, 37]): b'\\cyan',
    bytes([0xff, 38]): b'\\magenta',
    bytes([0xff, 39]): b'\\beep',
    bytes([0xff, 40]): b'\\link',
    bytes([0xff, 42]): b'\\ref',
    bytes([0xff, 43]): b'\\icon',
}


def resolve_control_codes(b):
    global control_codes
    for code, replacement in control_codes.items():
        b = b.replace(code, replacement)
    ccindex = b.find(bytes([0xff]))
    if ccindex != -1:
        if len(b) > ccindex + 1:
            raise ValueError("Found unhandled control code: {0}".format(b[ccindex + 1]))
        else:
            return b'?'
    return b


class DmbFileError(ValueError):
    pass


class StringDecoder:
    def __init__(self, reader, key, count):
        self.reader = reader
        self.key = key
        self.len = count

    def __iter__(self):
        return self

    def __next__(self):
        if self.len <= 0:
            raise StopIteration
        else:
            self.len -= 1
            val = (self.reader._uint8() ^ self.key) & 0xFF
            self.key += 9
            return val

    def dump(self):
        d = bytearray(self.reader._nbytes(self.len))
        for i in range(self.len):
            d[i] = (d[i] ^ self.key) & 0xFF
            self.key += 9
        self.len = 0
        return bytes(d)


class TileGenerator:
    def __init__(self, reader, count):
        self.reader = reader
        self.len = count
        self.curr = None
        self.rle_count = 0
        self.calls = 0

    def gen(self, count):
        while self.len > 0 and count > 0:
            if self.curr is None or self.rle_count == 0:
                self.curr = tile(self.reader._uarch(), self.reader._uarch(), self.reader._uarch())
                self.rle_count = self.reader._uint8()
            self.rle_count -= 1
            self.len -= 1
            count -= 1
            self.calls += 1
            yield self.curr


class Dmb:
    def __init__(self, dmbname, throttle=0, verbose=0):
        self.reader = open(dmbname, 'rb')
        self.bit32 = False
        self.throttle = throttle
        self.ops = 0
        self.world = world_data()
        self._parse_version_data()
        if verbose:
            print("Compiled with byond {0} (requires {1} server, {2} client)".format(self.world.world_version, self.world.min_server, self.world.min_client))

        flags = self._uint32()
        self.world.map_x, self.world.map_y, self.world.map_z = (self._uint16(), self._uint16(), self._uint16())
        self.bit32 = (flags & 0x40000000) > 0

        if verbose:
            print("{0}-bit dmb".format(32 if self.bit32 else 16))

        tilegen = TileGenerator(self, self.world.map_x * self.world.map_y * self.world.map_z)
        self.tiles = [[[tile for tile in tilegen.gen(self.world.map_x)] for j in range(self.world.map_y)] for i in range(self.world.map_z)]
        self._uint32()  # drop this

        self.no_parent_type = btype("/", None)

        type_count = self._uarch()
        if verbose:
            print("{0} types".format(type_count))
        self.types = [t for t in self._typegen(type_count)]

        mob_count = self._uarch()
        if verbose:
            print("{0} mobs".format(mob_count))
        [m for m in self._mobgen(mob_count)]  # skip mobs

        string_count = self._uarch()
        if verbose:
            print("{0} strings".format(string_count))
        self.strings = [s for s in self._stringgen(string_count)]
        self._uint32()  # CRC

        data_count = self._uarch()
        if verbose:
            print("{0} data".format(data_count))
        self.data = [d for d in self._datagen(data_count)]

        proc_count = self._uarch()
        if verbose:
            print("{0} procs".format(proc_count))
        self.procs = [p for p in self._procgen(proc_count)]

        var_count = self._uarch()
        if verbose:
            print("{0} vars".format(var_count))
        self.vars = [v for v in self._vargen(var_count)]

        argproc_count = self._uarch()
        if verbose:
            print("{0} argprocs".format(argproc_count))
        self.argprocs = [v for v in self._argprocgen(argproc_count)]

        instance_count = self._uarch()
        if verbose:
            print("{0} instances".format(instance_count))
        self.instances = [i for i in self._instancegen(instance_count)]

        mappop_count = self._uint32()
        if verbose:
            print("{0} mappops".format(mappop_count))
        self._populate_map(mappop_count)

        self._parse_extended_data()

        res_count = self._uarch()
        # print("{0} resources".format(res_count), file=sys.stderr)
        self.resources = [r for r in self._resourcegen(res_count)]

        self.reader.close()
        self.reader = None
        self.tree = ObjectTree()

        self._populate_types()

    def __del__(self):
        if self.reader is not None:
            self.reader.close()

    def _shift_coords(self, move_count, x, y, z):
        x += move_count

        while x >= self.world.map_x:
            x -= self.world.map_x
            y += 1
        while x < 0:
            x += self.world.map_x
            y -= 1

        while y >= self.world.map_y:
            y -= self.world.map_y
            z += 1
        while y < 0:
            y += self.world.map_y
            z -= 1

        return (x, y, z)

    def _populate_map(self, count):
        x = 0
        y = 0
        z = 0
        tile = self.tile(x, y, z)
        for move_count, instanceid in self._mappopgen(count):
            if move_count > 0:
                tile = self.tile(self._shift_coords(move_count, x, y, z))
            tile.instances.append(self._resolve_instance(instanceid))

    def _populate_types(self):
        for t in self.types:
            t.path = self.strings[t.path]
            try:
                t.parent = self.types[t.parent]
            except:
                t.parent = self.no_parent_type
            t.name = self._resolve_string(t.name)
            t.desc = self._resolve_string(t.desc)

            self.tree.push(t)

    def tile(self, x, y=None, z=None):
        if isinstance(x, tuple):
            z = x[2]
            y = x[1]
            x = x[0]
        if z > len(self.tiles):
            raise IndexError("Z out of map range.")
        if y > len(self.tiles[z]):
            raise IndexError("Y out of map range.")
        if x > len(self.tiles[z][y]):
            raise IndexError("X out of map range.")
        return self.tiles[z][y][x]

    def _uarch(self):
        if self.bit32:
            return self._uint32()
        else:
            return self._uint16()

    def _ffwd(self, seek):
        return self.reader.seek(seek, io.SEEK_CUR)

    def _ffwdarch(self, seek32, seek16):
        seek = seek16
        if self.bit32:
            seek = seek32
        return self._ffwd(seek)

    def _nbytes(self, n):
        return self.reader.read(n)

    def _float32(self):
        b = self.reader.read(4)
        if len(b) < 4:
            raise EOFError("Read beyond end of file.")
        return struct.unpack('<f', b)[0]    # interprets 4 bytes as little-endian float

    def _uint32(self):
        b = self.reader.read(4)
        if len(b) < 4:
            raise EOFError("Read beyond end of file.")
        return struct.unpack('<I', b)[0]    # interprets 4 bytes as little-endian unsigned long

    def _uint16(self):
        b = self.reader.read(2)
        if len(b) < 2:
            raise EOFError("Read beyond end of file.")
        return struct.unpack('<H', b)[0]    # interprets 2 bytes as little-endian unsigned short

    def _uint8(self):
        b = self.reader.read(1)
        if len(b) < 1:
            raise EOFError("Read beyond end of file.")
        return struct.unpack('<B', b)[0]    # interprets 1 byte as an unsigned byte

    def _byte(self):
        return self.reader.read(1)

    def _parse_version_data(self):
        ver_str = self._read_bytes_until(b'\x0A').decode('ascii')
        match = re.search(r'world bin v([0-9]*)', ver_str)
        if match is not None:
            self.world.world_version = int(match.group(1))
        else:
            raise DmbFileError('Cannot parse world version from dmb file.')
        ver_str = self._read_bytes_until(b'\x0A').decode('ascii')
        match = re.search(r'min compatibility v([0-9]*) ([0-9]*)', ver_str)
        if match is not None:
            self.world.min_server = int(match.group(1))
            self.world.min_client = int(match.group(2))
        else:
            raise DmbFileError('Cannot parse compatibility version from dmb file.')

    def _parse_extended_data(self):
        self.world.default_mob = self._uarch()
        self.world.default_turf = self._uarch()
        self.world.default_area = self._uarch()
        self.world.world_procs = self._uarch()
        self.world.global_init = self._uarch()
        self.world.world_domain = self._uarch()
        self.world.world_name = self._uarch()
        self.world.tick_lag = self._uint16()
        self.world.unknown1 = self._uint16()
        self.world.client_type = self._uarch()
        self.world.image_type = self._uarch()
        self.world.lazy_eye = self._uint8()
        self.world.client_dir = self._uint8()
        self.world.control_freak = self._uint8()
        self.world.unknown2 = self._uint16()
        self.world.client_script = self._uarch()
        self.world.unknown3 = self._uint16()
        self.world.view_width = self._uint8()
        self.world.view_height = self._uint8()
        self.world.hub_password = self._uarch()
        self.world.world_status = self._uarch()
        self.world.unknown4 = self._uint16()
        self.world.unknown5 = self._uint16()
        self.world.version = self._uint32()
        self.world.cache_lifespan = self._uint16()
        self.world.default_command_text = self._uarch()
        self.world.default_command_prompt = self._uarch()
        self.world.hub_path = self._uarch()
        self.world.unknown6 = self._uarch()
        self.world.unknown7 = self._uarch()
        self.world.icon_width = self._uint16()
        self.world.icon_height = self._uint16()
        self.world.map_format = self._uint16()

    def _throttle(self):
        if self.throttle:
            self.ops += 1
            if self.ops >= 1000:
                time.sleep(0.5)
                self.ops = 0

    def _typegen(self, count):
        while count > 0:
            path = self._uarch()
            parent = self._uarch()
            curr = btype(path, parent)
            curr.name = self._uarch()
            curr.desc = self._uarch()
            curr.icon = self._uarch()
            curr.icon_state = self._uarch()
            curr.dir = self._uint8()

            unknown = self._uint8()
            if unknown == 15:
                self._ffwd(4)
            curr.text = self._uarch()
            self._uarch()  # suffix
            self._ffwdarch(8, 6)
            curr.flags = self._uint32()
            self._ffwdarch(16, 8)
            curr.variable_list = self._uarch()
            curr.layer = self._float32()
            if self.world.min_client >= 500:
                unknown = self._uint8()
                if unknown > 0:
                    self._ffwd(24)
            curr.builtin_variable_list = self._uarch()
            count -= 1
            yield curr
            self._throttle()

    def _mobgen(self, count):
        while count > 0:
            self._ffwdarch(8, 4)
            unknown = self._uint8()
            if (unknown & 0x80) > 0:
                self._ffwd(6)
            count -= 1
            yield True
            self._throttle()

    def _stringgen(self, count):
        while count > 0:
            c = self.reader.seek(0, io.SEEK_CUR)
            strlen = (self._uint16() ^ c) & 65535
            lastread = strlen
            while strlen == 65535:
                c += 2
                lastread = self._uint16()
                nextd = (lastread ^ c) & 65535
                strlen += nextd
            key = ModularInt(c + 2, mod8)
            decoder = StringDecoder(self, key, strlen)
            count -= 1
            b = decoder.dump()
            try:
                temp = resolve_control_codes(b)
                b = temp
                string = b.decode('iso-8859-1')
            except:
                print("Position {0}".format(hex(c)))
                print(b)
                # print([chr(a) for a in list(b)])
                raise
            yield string
            self._throttle()

    def _datagen(self, count):
        while count > 0:
            mult = 2
            if self.bit32:
                mult = 4
            datalen = self._uint16() * mult
            data = self._nbytes(datalen)
            count -= 1
            yield data
            self._throttle()

    def _procgen(self, count):
        while count > 0:
            ret = proc()
            ret.path = self._uarch()
            ret.name = self._uarch()
            self._ffwdarch(10, 6)
            unknown = self._uint8()
            if unknown & 0x80 > 0:
                self._ffwd(5)
            ret.data = self._uarch()
            ret.variable_list = self._uarch()
            ret.argument_list = self._uarch()
            count -= 1
            yield ret
            self._throttle()

    def _vargen(self, count):
        while count > 0:
            ret = var()
            typeid = self._uint8()
            typeval = self._uint32()
            ret.name = self._uarch()
            ret.value = value.decode(typeid, typeval)
            count -= 1
            yield ret
            self._throttle()

    def _instancegen(self, count):
        while count > 0:
            ret = instance()
            typeid = self._uint8()
            typeval = self._uint32()
            ret.initializer = self._uarch()
            ret.value = value.decode(typeid, typeval)
            count -= 1
            yield ret
            self._throttle()

    def _argprocgen(self, count):
        while count > 0:
            count -= 1
            yield self._uarch()
            self._throttle()

    def _mappopgen(self, count):
        while count > 0:
            move = self._uint16()
            instance = self._uarch()
            count -= 1
            yield (move, instance)
            self._throttle()

    def _resourcegen(self, count):
        while count > 0:
            rhash = self._uint32()
            typeid = self._uint8()
            count -= 1
            yield resource(typeid, rhash)
            self._throttle()

    def _bytegen(self, delimiter):
        eof = False
        while not eof:
            byte = self.reader.read(1)
            if byte == b'':
                eof = True
                break
            if byte == delimiter:
                break
            yield byte
            self._throttle()

    def _read_bytes_until(self, delimiter):
        return b''.join([b for b in self._bytegen(delimiter)])

    def _resolve_proc(self, procid):
        try:
            return self.procs[procid]
        except:
            print(procid)
            raise

    def _resolve_instance(self, instanceid):
        try:
            return self.instances[instanceid]
        except:
            print(instanceid)
            raise

    def _resolve_string(self, stringid):
        if stringid == 0xFFFF:
            return None
        return self.strings[stringid]
