class compiled_value():
    pass


class value_null(compiled_value):
    def __init__(self, typeid, value):
        pass


class value_mob(compiled_value):
    def __init__(self, typeid, value):
        self.value = value


class value_resource(compiled_value):
    def __init__(self, typeid, value):
        self.value = value


class value_type(compiled_value):
    def __init__(self, typeid, value):
        self.value = value


class value_savefile_type(compiled_value):
    def __init__(self, typeid, value):
        pass


class value_file_type(compiled_value):
    def __init__(self, typeid, value):
        pass


class value_list_type(compiled_value):
    def __init__(self, typeid, value):
        pass


class value_client_type(compiled_value):
    def __init__(self, typeid, value):
        pass


class value_string(compiled_value):
    def __init__(self, typeid, value):
        self.value = value


class value_number(compiled_value):
    def __init__(self, typeid, value):
        self.value = value


class value_list(compiled_value):
    def __init__(self, typeid, value):
        self.value = value


class value_proc(compiled_value):
    def __init__(self, typeid, value):
        self.value = value


class value_image(compiled_value):
    def __init__(self, typeid, value):
        self.value = value


class value_unknown(compiled_value):
    def __init__(self, typeid, value):
        self.typeid = typeid
        self.value = value


decode_map = {
    0: value_null,
    6: value_string,
    8: value_mob,
    9: value_type,
    10: value_type,
    11: value_type,
    12: value_resource,
    32: value_type,
    36: value_savefile_type,
    39: value_file_type,
    40: value_list_type,
    42: value_number,
    59: value_client_type,
    62: value_list,
    63: value_image,
}


def decode(typeid, value):
    global decode_map
    if typeid in decode_map:
        return decode_map[typeid](typeid, value)
    return value_unknown(typeid, value)
