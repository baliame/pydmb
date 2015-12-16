import json


class mob:
    pass


class resource:
    def __init__(self, typeid, rhash):
        self.typeid = typeid
        self.hash = rhash


class proc:
    def __init__(self):
        self.path = 0
        self.name = 0
        self.data = 0
        self.variable_list = 0
        self.argument_list = 0


class var:
    def __init__(self):
        self.value = None,
        self.name = 0


class instance:
    def __init__(self):
        self.value = None,
        self.initializer = 0


class world_data:
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


class tile:
    def __init__(self, area_id=0, turf_id=0, unknown_id=0):
        self.area_id = area_id
        self.turf_id = turf_id
        self.unknown_id = unknown_id
        self.instances = []


class type:
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

    def __json__(self):
        return {
            "path": self.path,
            "name": self.name,
            "desc": self.desc,
            "parent": self.parent.path,
        }
