import collections
from . import constants


control_codes = collections.OrderedDict()
control_codes[bytes([0xff, 17])] = b'\\himself'
control_codes[bytes([0xff, 1])] = b'\\1'
control_codes[bytes([0xff, 2])] = b'\\2'
control_codes[bytes([0xff, 3])] = b'\\3'
control_codes[bytes([0xff, 5])] = b'\\th'
control_codes[bytes([0xff, 6])] = b'\\a'
control_codes[bytes([0xff, 7])] = b'\\A'
control_codes[bytes([0xff, 8])] = b'\\the'
control_codes[bytes([0xff, 9])] = b'\\The'
control_codes[bytes([0xff, 10])] = b'\\he'
control_codes[bytes([0xff, 11])] = b'\\He'
control_codes[bytes([0xff, 12])] = b'\\his'
control_codes[bytes([0xff, 13])] = b'\\His'
control_codes[bytes([0xff, 14])] = b'\\hers'
control_codes[bytes([0xff, 15])] = b'\\Hers'
control_codes[bytes([0xff, 16])] = b'\\him'
control_codes[bytes([0xff, 18])] = b'\\...'
control_codes[bytes([0xff, 20])] = b'\\s'
control_codes[bytes([0xff, 21])] = b'\\proper'
control_codes[bytes([0xff, 22])] = b'\\improper'
control_codes[bytes([0xff, 23])] = b'\\bold'
control_codes[bytes([0xff, 24])] = b'\\italic'
control_codes[bytes([0xff, 25])] = b'\\underline'
control_codes[bytes([0xff, 27])] = b'\\font'
control_codes[bytes([0xff, 28])] = b'\\color'
control_codes[bytes([0xff, 30])] = b'\\resetcolor'  # TODO
control_codes[bytes([0xff, 31])] = b'\\red'
control_codes[bytes([0xff, 32])] = b'\\green'
control_codes[bytes([0xff, 33])] = b'\\blue'
control_codes[bytes([0xff, 34])] = b'\\black'
control_codes[bytes([0xff, 35])] = b'\\white'
control_codes[bytes([0xff, 36])] = b'\\yellow'
control_codes[bytes([0xff, 37])] = b'\\cyan'
control_codes[bytes([0xff, 38])] = b'\\magenta'
control_codes[bytes([0xff, 39])] = b'\\beep'
control_codes[bytes([0xff, 40])] = b'\\link'
control_codes[bytes([0xff, 42])] = b'\\ref'
control_codes[bytes([0xff, 43])] = b'\\icon'
control_codes[bytes([0xff, 44])] = b'\\Roman'
control_codes[bytes([0xff, 45])] = b'\\Roman'  # reset code


class RawString:
    def __init__(self, byte, key, mode=constants.raw_string_mode_encrypted, lazy=False):
        self.key = key
        self.orig_key = key
        if mode == constants.raw_string_mode_encrypted:
            self.orig_data = byte
            self.data = None
            self.string = None
            if not lazy:
                self.decrypt(True)
                self.decode(True)
        elif mode == constants.raw_string_mode_decrypted:
            self.data = byte
            self.string = None
            self.orig_data = None
            if not lazy:
                self.encrypt(True)
                self.decode(True)
        elif mode == constants.raw_string_mode_string:
            self.string = byte
            self.data = None
            self.orig_data = None
            if not lazy:
                self.encrypt(True)
                self.encode(True)

    # orig_data (encrypted bytes) -> data (decrypted bytes)
    def decrypt(self, force=False):
        if not force and self.data is not None:
            return self.data
        self.data = bytearray(self.orig_data)
        for i in range(len(self.orig_data)):
            self.data[i] = (self.orig_data[i] ^ self.key) & 0xFF
            self.key += 9
        return self.data

    # data (decrypted bytes) -> orig_data (encrypted bytes)
    def encrypt(self, force=False):
        if self.data is None:
            self.encode()
        if not force and self.orig_data is not None:
            return self.orig_data
        self.orig_data = bytearray(self.data)
        for i in range(len(self.data)):
            self.orig_data[i] = (self.data[i] ^ self.key) & 0xFF
            self.key += 9
        return self.orig_data

    # data (decrypted bytes) -> string (human-readable string)
    def decode(self, force=False):
        if self.data is None:
            self.decrypt()
        if self.string is None or force:
            temp = bytearray(self.data)
            for code, replacement in control_codes.items():
                temp = temp.replace(code, replacement)
            ccindex = temp.find(bytes([0xff]))
            if ccindex != -1:
                if len(temp) > ccindex + 1:
                    raise ValueError("Found unhandled control code: {0}".format(self.data[ccindex + 1]))
                else:
                    return "?"
            self.string = temp.decode('iso-8859-1')
            self.key = self.orig_key
        return self.string

    # string (human-readable string) -> data (decrypted bytes)
    def encode(self, force=False):
        if self.data is None or force:
            self.data = self.string.encode('iso-8859-1')
            for code, replacement in control_codes.items():
                self.data = self.data.replace(replacement, code)
            self.key = self.orig_key
        return self.data

    def __bytes__(self):
        return self.decrypt()

    def __str__(self):
        return self.decode()

    def __repr__(self):
        return "RawString(b'{0}',{1})".format(self.orig_data, self.orig_key)


class Mob:
    def __init__(self):
        self._unknown = 0
        self._fdata1 = 0
        self._fdata2 = 0


class Resource:
    def __init__(self, typeid, rhash):
        self.typeid = typeid
        self.hash = rhash


astype_map = {
    1: "mob",
    2: "obj",
    4: "text",
    8: "num",
    16: "file",
    32: "turf",
    128: "null",
    256: "area",
    1024: "sound",
    2048: "message",
    4096: "anything",
}


def resolve_astype(flags):
    types = []
    for pos in astype_map:
        if flags & pos > 0:
            types.append(astype_map[pos])
    return types


intype_map = {
    1: "view",
    2: "oview",
    3: "usr.loc",
    8: "usr",
    16: "world",
    64: "custom",
}


intype_has_parameter = ["view", "oview"]


class Arg:
    def __init__(self, name, astype=0, intype=1, inrange=125):
        self.name = name
        if isinstance(astype, list):
            self.astype = astype
        else:
            self.astype = resolve_astype(astype)
        if isinstance(intype, int):
            self.intype = intype_map[intype]
        else:
            self.intype = intype
        if not isinstance(inrange, Proc) and inrange == 125:
            self.inrange = None
        else:
            self.inrange = inrange

    def __str__(self):
        data = self.name
        if len(self.astype):
            data += " as {0}".format("|".join(self.astype))
        if self.intype is not None:
            if self.intype != "custom":
                if self.intype in intype_has_parameter:
                    if self.inrange is not None:
                        data += " in {0}({1})".format(self.intype, self.inrange)
                    elif self.intype != "view":
                        data += " in {0}()".format(self.intype)
                else:
                    data += " in {0}".format(self.intype)
            else:
                data += " in <proc:{0}>".format(self.inrange.argproc_id)
        return data

    def __repr__(self):
        return "Arg({0}, astype={1}, intype={2}, inrange={3})".format(repr(self.name), repr(self.astype), repr(self.intype), repr(self.inrange))

    def __json__(self):
        return {
            "name": self.name,
            "astype": self.astype,
            "intype": self.intype,
            "inrange": self.inrange,
        }

    @classmethod
    def from_json(j):
        ret = Arg()
        ret.name = j["name"]
        ret.astype = j["astype"]
        ret.intype = j["intype"]
        if isinstance(j["inrange"], dict):
            ret.inrange = Proc.from_json(j["inrange"])
        else:
            ret.inrange = j["inrange"]
        return ret


class Proc:
    def __init__(self):
        self.path = 0
        self.name = 0
        self.desc = 0
        self.category = 0
        self.data = 0
        self.variable_list = 0
        self.argument_list = 0

        self.range = 0
        self.access = 0
        self.flags = 0
        # 0x80: use extended flags
        # 0x20: popup_menu
        #
        # 0x01: hidden
        self._ufield3 = 0
        self.ext_flags = 0
        self.invisibility = 0

        self.id = 0

        self.parameters = []
        self.argproc_id = None
        self.locals = []
        self.defined_on = None

    def __json__(self):
        return {
            "path": self.path,
            "name": self.name,
            "desc": self.desc,
            "category": self.category,
            "parameters": self.parameters,
            "range": self.range,
            "access": self.access,
            "ext_flags": self.ext_flags,
            "invisibility": self.invisibility,
            "argproc_id": self.argproc_id,
            "id": self.id,
        }

    @classmethod
    def from_json(j):
        ret = Proc()
        ret.path = j["path"]
        ret.name = j["name"]
        ret.desc = j["desc"]
        ret.category = j["category"]
        ret.range = j["range"]
        ret.access = j["access"]
        ret.ext_flags = j["ext_flags"]
        ret.invisibility = j["invisibility"]
        ret.argproc_id = j["argproc_id"]
        ret.id = j["id"]
        ret.parameters = []
        for entry in j["parameters"]:
            ret.parameters.append(Arg.from_json(entry))
        return ret


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
        self.area = area_id
        self.turf = turf_id
        self.unknown = unknown_id
        self.instances = []


def extract_pids(pdict):
    return [pdict[key].id for key in pdict]


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
        self.suffix = 0

        self.maptext = 0
        self.maptext_width = 0
        self.maptext_height = 0
        self.maptext_x = 0
        self.maptext_y = 0

        self.flags = 0
        self.proc_list = 0
        self.verb_list = 0
        self.variable_list = 0
        self.layer = 0.0
        self.builtin_variable_list = 0

        self.id = 0
        self.resolved_vars = False
        self.variables = None
        self.procedures = None
        self.verbs = None
        self.procedures_own = {}
        self.verbs_own = {}

        self._unknown1 = 0
        self._unknown2 = 0
        self._unknown3 = 0
        self._unknown4 = 0
        self._fdata1 = 0
        self._fdata4 = 0

    def __json__(self):
        return {
            "path": self.path,
            "name": self.name,
            "desc": self.desc,
            "parent": self.parent.path,
            "variables": self.variables,
            "procedures": [pid for pid in extract_pids(self.procedures)],
            "verbs": [pid for pid in extract_pids(self.verbs)],
            "procedures_own": [pid for pid in extract_pids(self.procedures_own)],
            "verbs_own": [pid for pid in extract_pids(self.verbs_own)],
        }

    def __str__(self):
        return '"Type: {0}"'.format(self.path)

    def __repr__(self):
        return '"{0}"'.format(self.path)
        try:
            return 'type({0}, {1})'.format(self.path, self.parent.path)
        except:
            return 'type({0}, {1})'.format(self.path, self.parent)
