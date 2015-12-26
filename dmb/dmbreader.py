from .dmb import Tile, Mob, Proc, WorldData, Var, Instance, Resource, Type, RawString
from .dmbwriter import DmbWriter
from .tree import ObjectTree
from . import value, constants
from .crypt import byond32
from blist import *
import numpy as np
import re
import io
import struct
import time


class DmbFileError(ValueError):
    pass


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
                self.curr = (self.reader._uarch(), self.reader._uarch(), self.reader._uarch())
                self.rle_count = self.reader._uint8()
            self.rle_count -= 1
            self.len -= 1
            count -= 1
            self.calls += 1
            yield Tile(self.curr[0], self.curr[1], self.curr[2])


class Dmb:
    def __init__(self, dmbname, throttle=False, verbose=False, string_mode=constants.string_mode_default, check_string_crc=False):
        self.string_mode = string_mode if string_mode != constants.string_mode_default else contants.string_mode_byte_strings
        self.check_string_crc = check_string_crc
        self.reader = open(dmbname, 'rb')
        self.bit32 = False
        self.throttle = throttle
        self.ops = 0
        self.world = WorldData()
        self._parse_version_data()
        if verbose:
            print("Compiled with byond {0} (requires {1} server, {2} client)".format(self.world.world_version, self.world.min_server, self.world.min_client))

        self.flags = self._uint32()
        self.world.map_x, self.world.map_y, self.world.map_z = (self._uint16(), self._uint16(), self._uint16())
        self.bit32 = (self.flags & 0x40000000) > 0

        if verbose:
            print("{0}-bit dmb".format(32 if self.bit32 else 16))

        tilegen = TileGenerator(self, self.world.map_x * self.world.map_y * self.world.map_z)
        self.tiles = [[[tile for tile in tilegen.gen(self.world.map_x)] for j in range(self.world.map_y)] for i in range(self.world.map_z)]
        self._uint32()  # drop this

        self.no_parent_type = Type("/", None)

        type_count = self._uarch()
        if verbose:
            print("{0} types".format(type_count))
        self.types = blist([t for t in self._typegen(type_count)])

        mob_count = self._uarch()
        if verbose:
            print("{0} mobs".format(mob_count))
        self.mobs = blist([m for m in self._mobgen(mob_count)])

        self.strcrc = np.uint32(0)
        string_count = self._uarch()
        if verbose:
            print("{0} strings".format(string_count))
        self.strings = blist([s for s in self._stringgen(string_count)])
        crc = self._uint32()  # CRC
        if self.check_string_crc:
            if crc != self.strcrc:
                raise DmbFileError("String table CRC mismatch (expected: {0}, got: {1})".format(crc, self.strcrc))
            elif verbose:
                print("String table CRC check passed.")

        data_count = self._uarch()
        if verbose:
            print("{0} data".format(data_count))
        self.data = blist([d for d in self._datagen(data_count)])

        proc_count = self._uarch()
        if verbose:
            print("{0} procs".format(proc_count))
        self.procs = blist([p for p in self._procgen(proc_count)])

        var_count = self._uarch()
        if verbose:
            print("{0} vars".format(var_count))
        self.variables = blist([v for v in self._vargen(var_count)])

        argproc_count = self._uarch()
        if verbose:
            print("{0} argprocs".format(argproc_count))
        self.argprocs = blist([v for v in self._argprocgen(argproc_count)])

        instance_count = self._uarch()
        if verbose:
            print("{0} instances".format(instance_count))
        self.instances = blist([i for i in self._instancegen(instance_count)])

        mappop_count = self._uint32()
        if verbose:
            print("{0} mappops".format(mappop_count))
        self._populate_map(mappop_count)

        self._parse_extended_data()

        res_count = self._uarch()
        if verbose:
            print("{0} resources".format(res_count))
        self.resources = blist([r for r in self._resourcegen(res_count)])

        self.reader.close()
        self.reader = None

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
                x, y, z = self._shift_coords(move_count, x, y, z)
                tile = self.tile(x, y, z)
            tile.instances.append(self._resolve_instance(instanceid))

    def _unpack_arch(self, bs):
        return struct.unpack("<" + (("I" if self.bit32 else "H") * int(len(bs) / (4 if self.bit32 else 2))), bs)

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

    def _nbytesarch(self, n32, n16):
        read = n16
        if self.bit32:
            read = n32
        return self._nbytes(read)

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

    def write(self, dmbname):
        writer = DmbWriter(dmbname, self)
        writer.write()

    def _throttle(self):
        if self.throttle:
            self.ops += 1
            if self.ops >= 1000:
                time.sleep(0.5)
                self.ops = 0

    def _typegen(self, count):
        typeid = 0
        while count > 0:
            path = self._uarch()
            parent = self._uarch()
            curr = Type(path, parent)

            curr.id = typeid
            typeid += 1

            curr.name = self._uarch()
            curr.desc = self._uarch()
            curr.icon = self._uarch()
            curr.icon_state = self._uarch()
            curr.dir = self._uint8()

            curr._unknown1 = self._uint8()
            if curr._unknown1 == 15:
                curr._fdata1 = self._nbytes(4)
            curr.text = self._uarch()
            curr.suffix = self._uarch()  # suffix
            curr.maptext_width = self._uint16()
            curr.maptext_height = self._uint16()
            if self.world.min_client > 507:
                curr.maptext_x = self._uint16()
                curr.maptext_y = self._uint16()
            curr.maptext = self._uarch()
            curr.flags = self._uint32()
            curr.verb_list = self._uarch()
            curr.proc_list = self._uarch()
            curr._unknown3 = self._uarch()
            curr._unknown4 = self._uarch()
            curr.variable_list = self._uarch()
            curr.layer = self._float32()
            if self.world.min_client >= 500:
                curr._unknown2 = self._uint8()
                if curr._unknown2 > 0:
                    curr._fdata4 = self._nbytes(24)
            curr.builtin_variable_list = self._uarch()
            count -= 1
            yield curr
            self._throttle()

    def _mobgen(self, count):
        while count > 0:
            mob = Mob()
            mob._fdata1 = self._nbytesarch(8, 4)
            mob._unknown = self._uint8()
            if (mob._unknown & 0x80) > 0:
                mob._fdata2 = self._nbytes(6)
            count -= 1
            yield mob
            self._throttle()

    def _crc(self, b):
        self.strcrc = byond32(self.strcrc, b, null_terminate=True)

    def _stringgen(self, count):
        while count > 0:
            c = self.reader.seek(0, io.SEEK_CUR)
            lb = self._uint16()
            strlen = (lb ^ c) & 65535
            lastread = strlen
            while strlen == 65535:
                c += 2
                lastread = self._uint16()
                nextd = (lastread ^ c) & 65535
                strlen += nextd
            key = c + 2
            count -= 1
            estr = self._nbytes(strlen)
            string = RawString(bytearray(estr), key, lazy=True)
            if self.check_string_crc:
                self._crc(string.decrypt())
            if self.string_mode == constants.string_mode_byte_strings:
                yield string.decrypt()
            elif self.string_mode == constants.string_mode_strings:
                yield string.decode()
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
            ret = Proc()
            ret.path = self._uarch()
            ret.name = self._uarch()
            ret.desc = self._uarch()
            ret.category = self._uarch()
            ret.range = self._uint8()
            ret.access = self._uint8()
            ret.flags = self._uint8()
            if ret.flags & 0x80 > 0:
                ret.ext_flags = self._uint32()
                ret.invisibility = self._uint8()
            ret.data = self._uarch()
            ret.variable_list = self._uarch()
            ret.argument_list = self._uarch()
            count -= 1
            yield ret
            self._throttle()

    def _vargen(self, count):
        while count > 0:
            ret = Var()
            typeid = self._uint8()
            typeval = self._uint32()
            ret.name = self._uarch()
            ret.value = value.decode(typeid, typeval)
            count -= 1
            yield ret
            self._throttle()

    def _instancegen(self, count):
        while count > 0:
            ret = Instance()
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
            yield Resource(typeid, rhash)
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

    def _resolve_data(self, dataid):
        if dataid == 65535:
            return None
        try:
            return self.data[dataid]
        except:
            print(dataid)
            raise

    def _resolve_resource(self, resourceid):
        if resourceid == 65535:
            return None
        try:
            return self.resources[resourceid]
        except:
            print(resourceid)
            raise

    def _resolve_proc(self, procid):
        try:
            return self.procs[procid]
        except:
            print(procid)
            raise

    def _resolve_var(self, varid):
        try:
            return self.variables[varid]
        except:
            print(varid)
            raise

    def _resolve_instance(self, instanceid):
        try:
            return self.instances[instanceid]
        except:
            print(instanceid)
            raise

    def _resolve_string(self, stringid, mode=constants.string_mode_default):
        if stringid == 0xFFFF:
            return None
        ret = self.strings[stringid]
        if isinstance(ret, RawString):
            val = ret.decrypt()
            self.strings[stringid] = val
            ret = val
        dcmode = self.string_mode if mode == constants.string_mode_default else mode
        if dcmode != self.string_mode:
            if dcmode == constants.string_mode_strings:
                return RawString(ret, 0, mode=constants.raw_string_mode_decrypted).decode()
            elif dcmode == constants.string_mode_byte_strings:
                return RawString(ret, 0, mode=constants.raw_string_mode_string).encode()
        return ret
