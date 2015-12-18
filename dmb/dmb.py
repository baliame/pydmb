import json


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


class RawString:
    def __init__(self, byte, key):
        self.len = len(byte)
        self.data = byte
        self.key = key
        self.orig_data = byte
        self.orig_key = key
        self.decoded = False

    def decode(self):
        if not self.decoded:
            for i in range(self.len):
                self.data[i] = (self.data[i] ^ self.key) & 0xFF
                self.key += 9
            self.len = 0
            for code, replacement in control_codes.items():
                self.data = self.data.replace(code, replacement)
            ccindex = self.data.find(bytes([0xff]))
            if ccindex != -1:
                if len(self.data) > ccindex + 1:
                    raise ValueError("Found unhandled control code: {0}".format(self.data[ccindex + 1]))
                else:
                    return b'?'
            self.data = self.data.decode('iso-8859-1')
            self.decoded = True
        return self.data

    def encode(self):
        if self.decoded:
            self.data = self.data.encode('iso-8859-1')
            for i in range(self.len):
                self.data[i] = (self.data[i] ^ self.key) & 0xFF
                self.key += 9
            self.len = 0
            for code, replacement in control_codes.items():
                self.data = self.data.replace(replacement, code)
            self.decoded = False
        return self.data

    def __str__(self):
        return self.decode()

    def __repr__(self):
        return "RawString(b'{0}',{1})".format(self.orig_data, self.orig_key)


class Mob:
    pass


class Resource:
    def __init__(self, typeid, rhash):
        self.typeid = typeid
        self.hash = rhash


class Proc:
    def __init__(self):
        self.path = 0
        self.name = 0
        self.data = 0
        self.variable_list = 0
        self.argument_list = 0


class Var:
    def __init__(self):
        self.value = None,
        self.name = 0


class Instance:
    def __init__(self):
        self.value = None,
        self.initializer = 0


class WorldData:
    def __init__(self):
        self.world_version = 0
        self.min_server = 0
        self.min_client = 0
        self.map_x = 0
        self.map_y = 0
        self.map_z = 0

        self.default_mob = 0
        self.default_turf = 0
        self.default_area = 0
        self.world_procs = 0
        self.global_init = 0
        self.world_domain = 0
        self.world_name = 0
        self.tick_lag = 0
        self.unknown1 = 0
        self.client_type = 0
        self.image_type = 0
        self.lazy_eye = 0
        self.client_dir = 0
        self.control_freak = 0
        self.unknown2 = 0
        self.client_script = 0
        self.unknown3 = 0
        self.view_width = 0
        self.view_height = 0
        self.hub_password = 0
        self.world_status = 0
        self.unknown4 = 0
        self.unknown5 = 0
        self.version = 0
        self.cache_lifespan = 0
        self.default_command_text = 0
        self.default_command_prompt = 0
        self.hub_path = 0
        self.unknown6 = 0
        self.unknown7 = 0
        self.icon_width = 0
        self.icon_height = 0
        self.map_format = 0


class Tile:
    def __init__(self, area_id=0, turf_id=0, unknown_id=0):
        self.area_id = area_id
        self.turf_id = turf_id
        self.unknown_id = unknown_id
        self.instances = []


class Type:
    def __init__(self, path, parent):
        self.path = path
        self.parent = parent

        self.name = 0
        self.desc = 0
        self.icon = 0
        self.icon_state = 0
        self.dir = 0

        self.text = 0

        self.maptext = 0
        self.maptext_width = 0
        self.maptext_height = 0

        self.flags = 0
        self.variable_list = 0
        self.layer = 0.0
        self.builtin_variable_list = 0

        self.id = 0
        self.resolved = False

    def __json__(self):
        return {
            "path": self.path,
            "name": self.name,
            "desc": self.desc,
            "parent": self.parent.path,
        }
