import struct
from . import constants
from .dmb import RawString, Type
from .crypt import byond32
import numpy as np
import io


class DmbWriter:
    def __init__(self, dmbname, dmb):
        self.dmb = dmb
        self.writer = open(dmbname, 'wb')

    def __del__(self):
        if self.writer is not None:
            self.writer.close()
            self.writer = None

    def _uint8(self, v):
        data = struct.pack('<B', v & 0xFF)    # interprets the provided integer as 1 byte
        self.writer.write(data)
        return 1

    def _uint16(self, v):
        data = struct.pack('<H', v & 0xFFFF)    # interprets the provided integer as 2 LE bytes
        self.writer.write(data)
        return 2

    def _uint32(self, v):
        data = struct.pack('<I', v & 0xFFFFFFFF)    # interprets the provided integer as 4 LE bytes
        self.writer.write(data)
        return 4

    def _float32(self, v):
        data = struct.pack('<f', v)
        self.writer.write(data)
        return 4

    def _uarch(self, v):
        if self.dmb.bit32:
            return self._uint32(v)
        else:
            return self._uint16(v)

    def _nbytes(self, count, bs):
        if isinstance(bs, str):
            bs = bs.encode('iso-8859-1')
        elif isinstance(bs, list):
            bs = bytes(bs)
        avail = len(bs)
        if count > avail:
            raise IndexError("Cannot write {0} bytes, provided object only contains {1} bytes.".format(count, avail))
        elif count == avail:
            self.writer.write(bs)
        else:
            self.writer.write(bs[0:count])
        return count

    def _bytes(self, bs):
        self.writer.write(bs)
        return len(bs)

    def _str(self, data):
        e = data.encode('iso-8859-1')
        self.writer.write(e)
        return len(e)

    def _byte(self, bs):
        if isinstance(bs, int):
            self._nbytes(1, [bs])
        else:
            self._nbytes(1, bs)

    def _write_version_data(self):
        s1 = "world bin v{0}".format(self.dmb.world.world_version)
        self._str(s1)
        self._byte(b'\x0A')
        s2 = "min compatibility v{0} {1}".format(self.dmb.world.min_server, self.dmb.world.min_client)
        self._str(s2)
        self._byte(b'\x0A')
        return len(s1) + len(s2) + 2

    def _write_tiles(self):
        length = self.dmb.world.map_x * self.dmb.world.map_y * self.dmb.world.map_z
        x = 0
        y = 0
        z = 0
        rle = 0
        last_match = (None, None, None)
        lxr = len(self.dmb.tiles[z][y])
        lyr = len(self.dmb.tiles[z])
        lzr = len(self.dmb.tiles)
        while length > 0:
            tile = self.dmb.tiles[z][y][x]
            if isinstance(tile.area, Type):
                area = tile.area.id
            else:
                area = tile.area
            if isinstance(tile.turf, Type):
                turf = tile.turf.id
            else:
                turf = tile.turf
            unk = tile.unknown

            if rle > 0:
                if (area, turf, unk) == last_match:
                    rle += 1
                    if rle > 255:
                        raise RuntimeError("RLE overflow.")
                    elif rle == 255:
                        self._uarch(area)
                        self._uarch(turf)
                        self._uarch(unk)
                        self._uint8(255)
                        rle = 0
                else:
                    self._uarch(last_match[0])
                    self._uarch(last_match[1])
                    self._uarch(last_match[2])
                    self._uint8(rle)
                    rle = 1
                    last_match = (area, turf, unk)
            else:
                rle = 1
                last_match = (area, turf, unk)
            length -= 1
            x += 1
            if x >= lxr:
                x = 0
                y += 1
                if y >= lyr:
                    y = 0
                    z += 1
                    if z >= lzr and length > 0:
                        raise ValueError("Length of tile write longer than total length of map.")
        if rle > 0:
            self._uarch(last_match[0])
            self._uarch(last_match[1])
            self._uarch(last_match[2])
            self._uint8(rle)

    def _write_types(self):
        type_count = len(self.dmb.types)
        self._uarch(type_count)
        for t in self.dmb.types:
            self._uarch(t.path)
            self._uarch(t.parent)
            self._uarch(t.name)
            self._uarch(t.desc)
            self._uarch(t.icon)
            self._uarch(t.icon_state)
            self._uint8(t.dir)
            self._uint8(t._unknown1)
            if t._unknown1 == 15:
                self._bytes(t._fdata1)
            self._uarch(t.text)
            self._uarch(t.suffix)
            self._uint16(t.maptext_width)
            self._uint16(t.maptext_height)
            if self.dmb.world.min_client > 507:
                self._uint16(t.maptext_x)
                self._uint16(t.maptext_y)
            self._uarch(t.maptext)
            self._uint32(t.flags)
            self._uarch(t.verb_list)
            self._uarch(t.proc_list)
            self._uarch(t._unknown3)
            self._uarch(t._unknown4)
            self._uarch(t.variable_list)
            self._float32(t.layer)
            if self.dmb.world.min_client >= 500:
                self._uint8(t._unknown2)
                if t._unknown2 > 0:
                    self._bytes(t._fdata4)
            self._uarch(t.builtin_variable_list)

    def _ffwd(self, count):
        return self.writer.seek(count, io.SEEK_CUR)

    def _write_string_length(self, strlen):
        while strlen >= 65535:
            s = (strlen ^ self._ffwd(0)) & 65535
            self._uint16(s)
            strlen -= 65535
        s = (strlen ^ self._ffwd(0)) & 65535
        self._uint16(s)

    def _crc(self, b, curr):
        return byond32(curr, b, null_terminate=True)

    def _write_strings(self):
        strcrc = np.uint32(0xFFFFFFFF)
        string_count = len(self.dmb.strings)
        self._uarch(string_count)
        for s in self.strings:
            strcrc = self._crc(s, strcrc)
            self._write_string_length(len(s))
            s = RawString(s, self._ffwd(0), mode=constants.raw_string_mode_decrypted, lazy=True)
            data = s.encrypt(True)
            self._bytes(data)
        self._uint32(strcrc)

    def _write_mobs(self):
        mob_count = len(self.dmb.mobs)
        self._uarch(mob_count)
        for mob in self.dmb.mobs:
            self._bytes(mob._fdata1)
            self._uint8(mob._unknown)
            if (mob._unknown & 0x80) > 0:
                self._bytes(mob._fdata2)

    def _write_data(self):
        data_count = len(self.dmb.data)
        self._uarch(data_count)
        for data in self.dmb.data:
            dlen = len(data)
            if self.dmb.bit32:
                dlen /= 4
            else:
                dlen /= 2
            self._uint16(int(dlen))
            self._bytes(data)

    def _write_procs(self):
        proc_count = len(self.written_procs)
        self._uarch(proc_count)
        for proc in self.dmb.procs:
            self._uarch(proc.path)
            self._uarch(proc.name)
            self._uarch(proc.desc)
            self._uarch(proc.category)
            self._uint8(proc.range)
            self._uint8(proc.access)
            self._uint8(proc.flags)
            if (proc.flags & 0x80) > 0:
                self._uint32(proc.ext_flags)
                self._uint8(proc.invisibility)
            self._uarch(proc.data)
            self._uarch(proc.variable_list)
            self._uarch(proc.argument_list)

    def _write_vars(self):
        var_count = len(self.written_vars)
        self._uarch(var_count)
        for var in self.dmb.vars:
            self._uint8(var.value._typeid)
            self._uint32(var.value._value)
            self._uarch(var.name)

    def _write_instances(self):
        inst_count = len(self.dmb.instances)
        self._uarch(inst_count)
        for inst in self.dmb.instances:
            self._uint8(inst.value._typeid)
            self._uint32(inst.value._value)
            self._uarch(inst.initializer)  # TODO: unresolve

    def _write_argprocs(self):
        ap_count = len(self.dmb.argprocs)
        self._uarch(ap_count)
        for a in self.dmb.argprocs:
            self._uarch(a)

    def _write_mappops(self):
        total = 0
        tid = 0
        last_tid = 0
        for zlevel in self.dmb.tiles:
            for row in zlevel:
                for tile in row:
                    total += len(tile.instances)
        self._uint32(total)
        for zlevel in self.dmb.tiles:
            for row in zlevel:
                for tile in row:
                    for inst in tile.instances:
                        self._uint16(tid - last_tid)
                        last_tid = tid
                        iid = self.dmb.instances.index(inst)
                        self._uarch(iid)
                    tid += 1

    def _write_resources(self):
        res_count = len(self.dmb.resources)
        self._uarch(res_count)
        for r in self.dmb.resources:
            self._uint32(r.hash)
            self._uint8(r.typeid)

    def _write_extended_data(self):
        self._uarch(self.dmb.world.default_mob)
        self._uarch(self.dmb.world.default_turf)
        self._uarch(self.dmb.world.default_area)
        self._uarch(self.dmb.world.world_procs)
        self._uarch(self.dmb.world.global_init)
        self._uarch(self.dmb.world.world_domain)
        self._uarch(self.dmb.world.world_name)
        self._uint16(self.dmb.world.tick_lag)
        self._uint16(self.dmb.world.unknown1)
        self._uarch(self.dmb.world.client_type)
        self._uarch(self.dmb.world.image_type)
        self._uint8(self.dmb.world.lazy_eye)
        self._uint8(self.dmb.world.client_dir)
        self._uint8(self.dmb.world.control_freak)
        self._uint16(self.dmb.world.unknown2)
        self._uarch(self.dmb.world.client_script)
        self._uint16(self.dmb.world.unknown3)
        self._uint8(self.dmb.world.view_width)
        self._uint8(self.dmb.world.view_height)
        self._uarch(self.dmb.world.hub_password)
        self._uarch(self.dmb.world.world_status)
        self._uint16(self.dmb.world.unknown4)
        self._uint16(self.dmb.world.unknown5)
        self._uint32(self.dmb.world.version)
        self._uint16(self.dmb.world.cache_lifespan)
        self._uarch(self.dmb.world.default_command_text)
        self._uarch(self.dmb.world.default_command_prompt)
        self._uarch(self.dmb.world.hub_path)
        self._uarch(self.dmb.world.unknown6)
        self._uarch(self.dmb.world.unknown7)
        self._uint16(self.dmb.world.icon_width)
        self._uint16(self.dmb.world.icon_height)
        self._uint16(self.dmb.world.map_format)

    def write(self):
        if self.dmb.string_mode == constants.string_mode_strings:
            self.strings = [RawString(s, 0, mode=constants.raw_string_mode_string, lazy=True).encode() for s in self.dmb.strings]
        else:
            self.strings = self.dmb.strings
        self.string_mem_len = 0
        for s in self.strings:
            self.string_mem_len += len(s) + 1

        self._write_version_data()
        self._uint32(self.dmb.flags)
        self._uint16(self.dmb.world.map_x)
        self._uint16(self.dmb.world.map_y)
        self._uint16(self.dmb.world.map_z)
        self._write_tiles()
        self._uint32(self.string_mem_len)

        self._write_types()
        self._write_mobs()

        self._write_strings()
        self._write_data()
        self._write_procs()
        self._write_vars()
        self._write_argprocs()
        self._write_instances()
        self._write_mappops()
        self._write_extended_data()
        self._write_resources()
