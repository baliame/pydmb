from .dmb import Type, Proc, Arg
from . import json as dmbjson
from . import constants
import json
import struct


def tree_from_json(jdict):
    lprocs = [Proc.from_json(j) for j in jdict["procs"]]
    jprocs = dict((p.id, p) for p in lprocs)
    tree = ObjectTree(tree=jdict["tree"], procref=jprocs)
    tree.resolve_parent_refs_recursive(tree.tree)
    return tree

typemap = {
    0: "null",
    6: "string",
    8: "mob",
    9: "type",
    10: "type",
    11: "type",
    12: "resource",
    32: "type",
    36: "savefile",
    39: "file",
    40: "list",
    42: "float",
    59: "client",
    62: "list",
    63: "image",
}

skips = {
    "null": 1,
    "string": 1,
    "float": 2,
}

datum_vars = set(["parent_type", "tag", "type", "vars"])
atom_vars = set(["alpha", "appearance", "appearance_flags", "blend_mode", "color", "density", "desc", "dir", "gender", "icon", "icon_state", "infra_luminosity", "invisibility", "layer", "loc", "luminosity", "maptext", "maptext_width", "maptext_height", "maptext_x", "maptext_y", "mouse_drag_pointer", "mouse_drop_pointer", "mouse_drop_zone", "mouse_opacity", "mouse_over_pointer", "name", "opacity", "overlays", "override", "pixel_x", "pixel_y", "pixel_z", "plane", "suffix", "text", "transform", "underlays", "verbs", "x", "y", "z"]) | datum_vars
movable_vars = set(["animate_movement", "bound_x", "bound_y", "bound_width", "bound_height", "locs", "glide_size", "screen_loc", "step_size", "step_x", "step_y"]) | atom_vars
base_type_variables = {
    "area": atom_vars,
    "atom": atom_vars,
    "client": set(["address", "authenticate", "bounds", "byond_version", "CGI", "ckey", "color", "command_text", "connection", "control_freak", "computer_id", "default_verb_category", "dir", "edge_limit", "eye", "gender", "images", "inactivity", "key", "lazy_eye", "mob", "mouse_pointer_icon", "perspective", "pixel_x", "pixel_y", "pixel_z", "glide_size", "preload_rsc", "screen", "show_map", "show_popup_menus", "show_verb_panel", "statobj", "statpanel", "verbs", "view", "virtual_eye"]),
    "datum": datum_vars,
    "image": set(["loc"]),
    "list": set(["len"]),
    "mob": movable_vars | set(["ckey", "client", "group", "key", "see_in_dark", "see_infrared", "see_invisible", "sight"]),
    "obj": movable_vars,
    "savefile": set(["cd", "dir", "eof", "name"]),
    "sound": set(["file", "repeat", "wait", "channel", "volume", "frequency", "pan", "priority", "status", "x", "y", "z", "falloff", "environment", "echo"]),
    "turf": atom_vars,
    "world": set(["address", "area", "byond_version", "cache_lifespan", "contents", "cpu", "executor", "fps", "game_state", "host", "hub", "hub_password", "icon_size", "internet_address", "log", "loop_checks", "map_format", "maxx", "maxy", "maxz", "mob", "name", "params", "port", "realtime", "reachable", "sleep_offline", "status", "system_type", "tick_lag", "time", "timeofday", "turf", "url", "version", "view", "visibility"]),
}


def ndupdate(dict1, dict2):
    for k in dict2:
        if k not in dict1:
            dict1[k] = dict2[k]
    return dict1


def base_type_vars(path):
    btv = path.lstrip("/")
    if btv in base_type_variables:
        return set() | base_type_variables[btv]
    return set()


class ObjectTree:
    def __init__(self, tree={}, dmb=None, loaded=False, procref=None):
        if dmb is not None and dmb.string_mode == constants.string_mode_byte_strings:
            raise TypeError("ObjectTrees cannot be used with undecoded strings.")
        self.tree = tree
        if procref is not None:
            self._resolve_proc_references_recursive(self.tree, self.procref)

        if loaded and tree != {}:
            self._resolve_tree_recursive(self.tree)
        if dmb is not None:
            if loaded or tree != {}:
                self._insert_global_type(dmb)
            self._populate_types_from_dmb(dmb)
        if loaded or dmb is not None:
            self._resolve_parents_recursive(self.tree)
        if dmb is not None:
            self._populate_variables_recursive(self.tree, dmb)
            self._assign_procedures(dmb)

    def _insert_global_type(self, dmb):
        g = Type('.global', dmb.no_parent_type)
        g.name = '.global'
        g.desc = None
        g.icon = None
        g.icon_state = None
        g.variables = ["NORTH", "SOUTH", "EAST", "WEST", "NORTHWEST", "NORTHEAST", "SOUTHEAST", "SOUTHWEST", "world"]
        g.procedures = {
            '.': Proc.Global('.', 'Call the current proc. A proc that calls itself is said to be recursive.', [Arg('args', variadic=True)]),
            '..': Proc.Global('..', 'If object O is derived from object P, P is called the parent of O. If a proc (or verb) is defined in both O and P, O can call P\'s version by using ..().', [Arg('args', variadic=True)]),
            'ASSERT': Proc.Global('ASSERT', 'Used to make a sanity check. If the given expression is false, the current procedure crashes, generating diagnostic debugging output, which includes the expression, a stack dump, and so forth.', [Arg('expression')]),
            'CRASH': Proc.Global('CRASH', 'Crashes the current procedure, displaying the specified message and generating diagnostic debugging output, such as a stack dump.', [Arg('msg')]),
            'abs': Proc.Global('abs', 'Returns the absolute value of A.', [Arg('A')]),
            'addtext': Proc.Global('addtext', 'A text string with the arguments concatenated.', [Arg('arg1'), Arg('arg2', variadic=True)]),
            'alert': Proc.Global('alert', 'This sleeps the current proc until the user clicks one of the named buttons. As with input(), the first argument may be entirely left out.', [Arg('Usr', default='usr', optional=True), Arg('Message'), Arg('Title'), Arg('Button1'='Ok', optional=True), Arg('Button2', optional=True), Arg('Button3', optional=True)]),
            'animate': Proc.Global('animate', 'This proc creates an animation sequence that will be displayed to players.', [Arg('object', optional=True), Arg('vars', optional=True, variadic=True)]),
            'arccos': Proc.Global('arccos', 'The inverse cos of X in degrees.', [Arg('X')]),
            'arcsin': Proc.Global('arcsin', 'The inverse sin of X in degrees.', [Arg('X')]),
            'arglist': Proc.Global('arglist', 'Normally, if you were to pass a list directly to a procedure, it would only come through as a singe argument to that procedure. In some cases, you might instead want the items in the list to become the arguments to the procedure. That is what arglist() achieves.', [Arg('list')]),
            'ascii2text': Proc.Global('ascii2text', 'ASCII codes are numerical values corresponding to keyboard and special characters. Among other things, they are used to represent many symbols in HTML. This proc converts an ASCII code to its corresponding text representation.', [Arg('N')]),
            'block': Proc.Global('block', 'Returns the list of turfs in the 3D block defined by start and end (inclusive).', [Arg('start'), Arg('end')]),
            'bounds': Proc.Global('bounds', 'Returns a list of atoms within the given bounding box.\nAlternate signatures:\nbounds(Ref=src, Dist=0)\nbounds(Ref, x_offset, y_offset, extra_width=0, extra_height=0)\nbounds(x, y, width, height, z)', [Arg('ref=src'), Arg('dist|x_offset'), Arg('y_offset', optional=True), Arg('extra_width', default=0, optional=True), Arg('extra_height', default=0, optional=True)]),
            'bounds_dist': Proc.Global('bounds_dist', 'Returns the distance, in pixels, between ref\'s and target\'s bounding boxes.', [Arg('ref'), Arg('target')]),
            'browse': Proc.Global('browse', 'Sends the html text or file to the user and optionally displays it in the web browser.', [Arg('body'), Arg('options', optional=True)]),
            'browse_rsc': Proc.Global('browse_rsc', 'This sends the specified resource file to usr (or anybody else) and stores it in their cache directory with the specified name. In subsequent browse() output, you can then refer to that file.', [Arg('file'), Arg('filename', optional=True)]),
            'call': Proc.Global('call', 'Calls any proc by name.', [Arg("ProcRef|Object|LibName"), Arg("ProcName", optional=True)]),
            'ckey': Proc.Global('ckey', 'Returns the key in canonical form. To do this, it strips all punctuation and space from the key and converts to lowercase. The result is still unique for each different key.', [Arg('key')]),
            'ckeyEx': Proc.Global('ckeyEx', 'Returns the same text stripped of all punctuation and space. Unlike, ckey(), case is preserved as are the \'-\' and \'_\' characters.', [Arg('key')]),
            'cmptext': Proc.Global('cmptext', 'Returns 1 if all arguments are equal, 0 otherwise.', [Arg('text', variadic=True)]),
            'copytext': Proc.Global('copytext', 'Copy characters in T between Start and End. The default end position of 0 stands for the lentext(T)+1, so by default the entire text string is copied.', [Arg('T'), Arg('start', default=1, optional=True), Arg('end', default=0, optional=True)]),
            'cos': Proc.Global('cos', 'The cos of X, where X is in degrees.', [Arg('X')]),
            'EXCEPTION': Proc.Global('EXCEPTION', 'Used to create an /exception datum, and is shorthand for calling new/exception(value, __FILE__, __LINE__). The value you provide will be in exception.name.', [Arg(value)]),
            'fcopy': Proc.Global('fcopy', 'Copies a file on the file system. The source may be a cache file, a savefile or a filename.', [Arg('src'), Arg('dst')]),
            'fcopy_rsc': Proc.Global('fcopy_rsc', 'Copies a file into the resource cache. The source may be a cache file or a filename.', [Arg('src')]),
            'fdel': Proc.Global('fdel', 'Deletes a file on the file system. If the specified file ends in \'/\', it is treated as a directory. Any contents (including sub-directories) are deleted as well.', [Arg('dst')]),
            'file': Proc.Global('file', 'Returns a file object corresponding to the named file.', [Arg('path')]),
            'file2text': Proc.Global('file2text', 'Reads the contents of the file and returns it as text.', [Arg('file')]),
            'findtext': Proc.Global('findtext', 'Returns the position of the needle in the haystack, or 0 if not found.', [Arg('haystack'), Arg('needle'), Arg('start', default=1, optional=True), Arg('end', default=0, optional=True)]),
            'findtextEx': Proc.Global('findtextEx', 'Returns the position of the needle in the haystack, or 0 if not found. This instruction is sensitive to the case of Haystack and Needle.', [Arg('haystack'), Arg('needle'), Arg('start', default=1, optional=True), Arg('end', default=0, optional=True)]),
            'flick': Proc.Global('flick', 'Cause the icon attached to Object to be temporarily replaced with the specified icon or icon state for the duration of the animation. This is a purely visual effect and does not effect the actual value of the object\'s icon variable.', [Arg('icon|icon_state'), Arg('object')]),
            'flist': Proc.Global('flist', 'Returns a list of files contained in the specified directory and whose names begin with the specified text. The names of sub-directories are listed too, and are marked by a trailing "/".', [Arg('path')]),
            'ftp': Proc.Global('ftp', 'Sends a file to a client with the (optional) suggested name for saving to disk.', [Arg('file'), Arg('name', optional=True)]),
            'get_dist': Proc.Global('get_dist', 'The distance between Loc1 and Loc2, in tiles, allowing diagonal movement.', [Arg('loc1'), Arg('loc2')]),
            'get_step_away': Proc.Global('get_step_away', 'Calculate position of a step from Ref on a path to Trg, taking obstacles into account. If Ref is farther than Max steps from Trg, 0 will be returned.', [Arg('ref'), Arg('trg'), Arg('max', optional=True, default=5)]),
            'get_step_rand': Proc.Global('get_step_rand', 'Calculate position of a step from Ref in random motion.', [Arg('ref')]),
            'get_step_to': Proc.Global('get_step_to', 'Calculate position of a step from Ref on a path to Trg, taking obstacles into account.  If Ref is within Min steps of Trg, no step is computed. This is also true if the target is too far away (more than twice world.view steps).', [Arg('ref'), Arg('trg'), Arg('min', optional=True, default=0)]),
            'get_step_towards': Proc.Global('get_step_towards', 'Calculate position of a step from Ref in the direction of Trg.', [Arg('ref'), Arg('trg')]),
            'hascall': Proc.Global('hascall', 'Check if an object has a proc or verb with the appropriate name.', [Arg('object'), Arg('procname')]),
            'hearers': Proc.Global('hearers', 'Return a list of mobs that can hear the center object. Currently, this is computed on the assumption that opaque objects block sound, just like they block light.', [Arg('depth', default='world.view', optional=True), Arg('center', default='usr', optional=True)]),
            'html_decode': Proc.Global('html_decode', 'Unescapes html encoded strings.', [Arg('htmltext')]),
            'html_encode': Proc.Global('html_encode', 'Escapes strings for display in html context.', [Arg('text')]),
            'icon': Proc.Global('icon', 'This is equivalent to new/icon().', [Arg('file'), Arg('state', optional=True), Arg('dir', optional=True), Arg('frame', optional=True), Arg('moving', optional=True)]),
            'icon_states': Proc.Global('icon_states', 'Returns a list of icon states in an icon.', [Arg('icon')]),
            'image': Proc.Global('image', 'This is equivalent to new/image().', [Arg('icon'), Arg('loc', optional=True), Arg('state', optional=True), Arg('layer', optional=True), Arg('dir', optional=True)]),
            'initial': Proc.Global('initial', 'Returns the initial value of a variable.', [Arg('var')]),
            'input': Proc.Global('input', 'This sleeps the current proc until the user responds to the input dialog.', [Arg('Usr', default='usr', optional=True), Arg('Message'), Arg('Title'), Arg('Default')]),
            'isarea': Proc.Global('isarea', 'Returns 1 if all arguments are valid areas.', [Arg('arg', variadic=True)]),
            'isfile': Proc.Global('isfile', 'Returns 1 if the argument is an existing file.' [Arg('arg')]),
            'isicon': Proc.Global('isicon', 'Returns 1 if the argument is an icon.' [Arg('arg')]),
            'isloc': Proc.Global('isloc', 'Returns 1 if all arguments are valid locations (atoms).', [Arg('arg', variadic=True)]),
            'ismob': Proc.Global('ismob', 'Returns 1 if all arguments are valid mobs.', [Arg('arg', variadic=True)]),
            'isnull': Proc.Global('isnull', 'Returns 1 if the argument is null.' [Arg('arg')]),
            'isnum': Proc.Global('isnum', 'Returns 1 if the argument is a number.' [Arg('arg')]),
            'isobj': Proc.Global('isobj', 'Returns 1 if all arguments are valid objs.', [Arg('arg', variadic=True)]),
            'ispath': Proc.Global('ispath', 'Returns 1 if val is a path. If type is provided, also checks if val is derived from type.' [Arg('val'), Arg('type', optional=True)]),
            'issaved': Proc.Global('issaved', 'Returns 1 if the argument is not a tmp var.' [Arg('var')]),
            'istext': Proc.Global('istext', 'Returns 1 if the argument is a text.' [Arg('arg')]),
            'isturf': Proc.Global('isturf', 'Returns 1 if all arguments are valid turfs.', [Arg('arg', variadic=True)]),
            'istype': Proc.Global('istype', 'Returns 1 if val is an instance of a type derived from type.', [Arg('val'), Arg('type')]),
            'length': Proc.Global('length', 'Returns the length of data associated with E. E may be a file, list or text.', [Arg('E')]),
            'lentext': Proc.Global('lentext', 'Deprecated. Returns the length of the provided text.', [Arg('text')]),
            'link': Proc.Global('link', 'Push this to a client to force them to view the provided URL. The URL may be a website or a BYOND address.', [Arg('url')]),
            'list': Proc.Global('list', 'Creates a list that contains the provided elements. The list may be associative.', [Arg('elem', variadic=True)]),
            'list2params': Proc.Global('list2params', 'This instruction converts a list of parameter names and associated values into a single text string suitable for use in a URL or similar situation.', [Arg('list')]),
            'locate': Proc.Global('locate', 'Returns the provided type in a container, the turf at the provided coordinates, the instance bearing the provided tag or the target of the given ref.', [Arg('Type|Tag|TextRef|X'), Arg('Y', optional=True), Arg('Z', optional=True)]),
            'lowertext': Proc.Global('lowertext', 'Converts the provided text to lowercase.', [Arg('text')]),
            'matrix': Proc.Global('matrix', 'Creates a new matrix. If no arguments are provided, an identity matrix is returned.', [Arg('a', optional=True), Arg('b', optional=True), Arg('c', optional=True), Arg('d', optional=True), Arg('e', optional=True), Arg('f', optional=True)]),
            'max': Proc.Global('max', 'Returns the largest provided argument. If only a single argument is provided, it must be a list.', [Arg('values', variadic=True)]),
            'md5': Proc.Global('md5', 'Returns the MD5 hash of the provided text or file.', [Arg('value')]),
            'min': Proc.Global('min', 'Returns the smallest provided argument. If only a single argument is provided, it must be a list.', [Arg('values', variadic=True)]),
            'missile': Proc.Global('missile', 'Send a missile of the given Type between two locations. The effect is purely visual. When Type is an object, its icon is used for the missile.', [Arg('type'), Arg('start'), Arg('end')]),
            'newlist': Proc.Global('newlist', 'Instantiates each type provided as an argument and returns the instances as a list.', [Arg('types', variadic=True)]),
            'num2text': Proc.Global('num2text', 'Send a missile of the given Type between two locations. The effect is purely visual. When Type is an object, its icon is used for the missile.', [Arg('N'), Arg('SigFig', default=6)]),
            'obounds': Proc.Global('obounds', 'Returns a list of atoms within the given bounding box, excluding the atom itself.', [Arg('ref=src'), Arg('dist|x_offset'), Arg('y_offset', optional=True), Arg('extra_width', default=0, optional=True), Arg('extra_height', default=0, optional=True)]),
            'ohearers': Proc.Global('ohearers', 'Return a list of mobs that can hear the center object, excluding the center object itself. Currently, this is computed on the assumption that opaque objects block sound, just like they block light.', [Arg('depth', default='world.view', optional=True), Arg('center', default='usr', optional=True)]),
            'orange': Proc.Global('orange', 'Returns a list of atoms within range of the center object. The center object is excluded.', [Arg('dist'), Arg('center', default='usr', optional=True)]),
            'output': Proc.Global('output', 'This is used in conjunction with the << output operator to send output to a particular control in the player\'s skin. If null is sent, the control will be cleared.', [Arg('msg'), Arg('control')]),
            'oview': Proc.Global('oview', 'Returns a list of atoms within view and range of the center object. The center object is excluded.', [Arg('dist'), Arg('center', default='usr', optional=True)]),
            'oviewers': Proc.Global('oviewers', 'Return a list of mobs that can see the center object, excluding the center object itself.', [Arg('depth', default='world.view', optional=True), Arg('center', default='usr', optional=True)]),
            'params2list': Proc.Global('params2list', 'This instruction converts a parameter text string to a list of individual parameters and associated values.', [Arg('text')]),
            'pick': Proc.Global('pick', 'Returns one of the arguments randomly. If only a single argument is provided, it is assumed to be a list to pick from.', [Arg('choice', variadic=True)]),
            'prob': Proc.Global('prob', 'Returns 1 with P percent chance.', [Arg('P')]),
            'rand': Proc.Global('rand', 'Returns a random integer between L and H inclusive.', [Arg('L', default=0, optional=True), Arg('H')]),
            'rand_seed': Proc.Global('rand_seed', 'Seed the pseudorandom generator with the given number.', [Arg('seed')]),
            'range': Proc.Global('range', 'A list of objects within dist tiles of center, diagonals included.', [Arg('dist'), Arg('center', default='usr', optional=True)]),
            'rgb': Proc.Global('rgb', 'Returns the hexadecimal representation of the provided RGB(A) values.', [Arg('R'), Arg('G'), Arg('B'), Arg('A', optional=True)]),
            'roll': Proc.Global('roll', 'Rolls ndice sides-sided dice and returns the sum of the results.', [Arg('ndice', default=1, optional=True), Arg('sides')]),
            'round': Proc.Global('round', 'Rounds A to the nearest multiple of B. If B is omitted, A is instead floored.', [Arg('A'), Arg('B', optional=True)]),
            'run': Proc.Global('run', 'Sends a file to be opened on the client, via <<.', [Arg('file')]),
            'shell': Proc.Global('shell', 'Invokes the a shell on the server and runs the provided command. Returns the exit code if the command could be run, null otherwise.', [Arg('command')]),
            'shutdown': Proc.Global('shutdown', 'Shuts down the world. If addr is provided, shuts down a child world instead.', [Arg('addr', optional=True), Arg('graceful', optional=True, default=0)]),
            'sin': Proc.Global('sin', 'The sin of X, where X is in degrees.', [Arg('X')]),
            'sleep': Proc.Global('sleep', 'Suspends execution of the current proc for Delay deciseconds.', [Arg('Delay')]),
            'sorttext': Proc.Global('sorttext', 'Returns the sort status of the provided texts. 1 if ascending, -1 if descending, 0 if unsorted.', [Arg('texts', variadic=True)]),
            'sorttextEx': Proc.Global('sorttextEx', 'Returns the case-sensitive sort status of the provided texts. 1 if ascending, -1 if descending, 0 if unsorted.', [Arg('texts', variadic=True)]),
            'sound': Proc.Global('sound', 'Equivalent of new/sound().', [Arg('file'), Arg('repeat', default=0, optional=True), Arg('wait', optional=True), Arg('channel', optional=True), Arg('volume', optional=True)]),
            'spawn': Proc.Global('spawn', 'Spawn a new metathread and execute its block after a delay of Delay deciseconds.', [Arg('Delay')]),
            'sqrt': Proc.Global('sqrt', 'Returns the square root of a number.', [Arg('num')]),
            'startup': Proc.Global('startup', 'Spawns a child world on a different port. A port of 0 means any available port.', [Arg('dmbfile'), Arg('port', default=0), Arg('options', variadic=True)]),
            'stat': Proc.Global('stat', 'This is used in a Stat() proc to send a stat line to the client.', [Arg('name'), Arg('value')]),
            'statpanel': Proc.Global('statpanel', 'If no name and value are provided, it queries whether the user is looking at a statpanel. If it doesn\'t exist, it creates the stat panel. If name and value are provided, a new stat line is sent.', [Arg('panel'), Arg('name', optional=True), Arg('value', optional=True)]),
            'step': Proc.Global('step', 'Moves ref in dir by one tile.', [Arg('ref'), Arg('dir'), Arg('speed', optional=True)]),
            'step_away': Proc.Global('step_away', 'Moves ref away from trg if ref is within max tiles of trg, but no further than twice world.view.', [Arg('ref'), Arg('dir'), Arg('max', default=5, optional=True), Arg('speed', optional=True)]),
            'step_rand': Proc.Global('step_rand', 'Moves ref in a random direction by one tile.', [Arg('ref'), Arg('speed', optional=True)]),
            'step_to': Proc.Global('step_to', 'Move Ref on a path to the location Trg, taking obstacles into account, if ref is at least min tiles of trg, but no further than twice world.view.', [Arg('ref'), Arg('trg'), Arg('min', default=0, optional=True), Arg('speed', optional=True)]),
            'step_towards': Proc.Global('step_towards', 'Move ref in the relative direction of trg by one tile.', [Arg('ref'), Arg('trg'), Arg('speed', optional=True)]),
            'text': Proc.Global('text', 'Insert arguments into a format string.', [Arg('format'), Arg('args', variadic=True)]),
            'text2ascii': Proc.Global('text2ascii', 'Convert the nth character of the text to an ascii value and return it.', [Arg('text'), Arg('n')]),
            'text2file': Proc.Global('text2file', 'Appends the provided text to a file.', [Arg('text'), Arg('file')]),
            'text2num': Proc.Global('text2num', 'Attempts to parse the provided text as a number.', [Arg('text')]),
            'text2path': Proc.Global('text2path', 'Attempts to parse the provided text as a type path.', [Arg('text')]),
            'time2text': Proc.Global('time2text', 'Converts the provided timestamp to a text according to the provided format. <a href="http://www.byond.com/docs/ref/info.html#/proc/time2text">Details on the format here.</a>', [Arg('timestamp'), Arg('format')]),
            'turn': Proc.Global('turn', 'Turns the provided dir, matrix or icon counter-clockwise by the provided degrees.', [Arg('dir|matrix|icon'), Arg('angle')]),
            'typesof': Proc.Global('typesof', 'Returns the subtypes of all provided types.', [Arg('type', variadic=True)]),
            'uppertext': Proc.Global('uppertext', 'Converts the provided text to uppercase.', [Arg('text')]),
            'url_decode': Proc.Global('url_decode', 'Removes URL decoding from the provided string.', [Arg('text')]),
            'url_encode': Proc.Global('url_encode', 'Encodes the provided string in a way that it is safe to be used in a URL.', [Arg('text')]),
            'view': Proc.Global('view', 'Returns a list of atoms within view of the center object.', [Arg('dist'), Arg('center', default='usr', optional=True)]),
            'viewers': Proc.Global('viewers', 'Return a list of mobs that can see the center object.', [Arg('depth', default='world.view', optional=True), Arg('center', default='usr', optional=True)]),
            'walk': Proc.Global('walk', 'Moves ref in a dir continuously.', [Arg('ref'), Arg('dir'), Arg('lag', default=0, optional=True), Arg('speed', optional=True)]),
            'walk_away': Proc.Global('walk_away', 'Moves ref away continuously from trg if ref is within max tiles of trg.', [Arg('ref'), Arg('dir'), Arg('max', default=5, optional=True), Arg('lag', default=0, optional=True), Arg('speed', optional=True)]),
            'walk_rand': Proc.Global('step_rand', 'Moves ref in a random direction continuously.', [Arg('ref'), Arg('lag', default=0, optional=True), Arg('speed', optional=True)]),
            'walk_to': Proc.Global('step_to', 'Move Ref continuously on a path to the location Trg, taking obstacles into account, if ref is at least min tiles of trg.', [Arg('ref'), Arg('trg'), Arg('min', default=0, optional=True), Arg('lag', default=0, optional=True), Arg('speed', optional=True)]),
            'walk_towards': Proc.Global('step_towards', 'Move ref continuously in the relative direction of trg by one tile.', [Arg('ref'), Arg('trg'), Arg('lag', default=0, optional=True), Arg('speed', optional=True)]),
            'winclone': Proc.Global('winclone', 'Creates a clone of a window, pane, menu, or macro set that exists in the world\'s skin file. The original object as it exists in the skin file (not its current state) is used as a template to build the clone. The clone will exist only for the player you choose.', [Arg('player'), Arg('window_name'), Arg('clone_name')]),
            'winexists': Proc.Global('winexists', 'Tells if a control exists and if so, what type it is. The return value is an empty string if the control does not exist, but otherwise it is the type of control.', [Arg('player'), Arg('control_id')]),
            'winget': Proc.Global('winget', 'Retrieves info from a player about the current state of their skin. If control_id and params are each just a single value, then the return value will be a simple string with the value of that parameter. If control_id or params is a semicolon-separated list like the kind used in list2params(), then the result will be in a similar format, and can be converted to a list form using params2list().', [Arg('player'), Arg('control_id'), Arg('params')]),
            'winset': Proc.Global('winset', 'Sets parameters for a player\'s skin. The parameter list can be created by making a list and using list2params(), or it can be done manually by just using a string like "is-visible=true;text-color=#f00".', [Arg('player'), Arg('control_id'), Arg('params')]),
            'winshow': Proc.Global('winshow', 'Shows or hides a window in the player\'s skin.', [Arg('player'), Arg('control_id'), Arg('show', default=1)]),
        }
        self.tree['.global'] = g

    def _populate_types_from_dmb(self, dmb):
        for t in dmb.types:
            if t.flags & 0x10000 != 0:
                continue
            pt = t.parent
            if pt == 65535:
                parent = dmb.no_parent_type
            else:
                parent = dmb._resolve_string(dmb.types[pt].path)
            res = Type(dmb._resolve_string(t.path), parent)
            res.name = dmb._resolve_string(t.name)
            res.desc = dmb._resolve_string(t.desc)
            res.icon = dmb._resolve_resource(res.icon)
            res.icon_state = dmb._resolve_string(t.icon_state)
            res.variable_list = t.variable_list
            res.builtin_variable_list = t.builtin_variable_list
            res.proc_list = t.proc_list
            res.verb_list = t.verb_list

            res.flags = t.flags
            res.dir = t.dir
            res.layer = t.layer
            res.id = t.id
            self.push(res)

    def _resolve_and_collect_vars_recursive(self, t, dmb):
        if t.variables is not None:
            return
        varset = base_type_vars(t.path)
        p = t.parent

        varlist = dmb._resolve_data(t.variable_list)
        if varlist is not None:
            databytes = dmb._unpack_arch(varlist)
            skip = False
            for varid in databytes:
                if skip:
                    skip = False
                    continue
                var = dmb._resolve_var(varid)
                varset.add(dmb._resolve_string(var.name))
                skip = True
        bvarlist = dmb._resolve_data(t.builtin_variable_list)
        if bvarlist is not None:
            databytes = dmb._unpack_arch(bvarlist)
        #     print(t.path)
        #     print(t.builtin_variable_list, "( =", bvarlist, ")")
        #     print(databytes)
            i = 0
            while i < len(databytes):
                # varname = databytes[i]
                vartype = databytes[i+1]
                vartype_str = typemap[vartype]
                if vartype_str not in skips:
                    print(t.builtin_variable_list, "( =", bvarlist, ")")
                    print(databytes)
                    raise ValueError(vartype_str)
                i += 2 + skips[vartype_str]
        #         varset.add(varname)
        # #     skip = False
        # #     for strid in databytes:
        # #         if skip:
        # #             skip = False
        # #             continue
        # #         var = dmb._resolve_string(strid)
        # #         print(strid, "( =", var, ")")
        # #         varset.add(var)
        # #         skip = True
        if p is not dmb.no_parent_type:
            if p.variables is None:
                self._resolve_and_collect_vars_recursive(p, dmb)
            varset |= set(p.variables)
        t.variables = list(varset)

    def _populate_variables_recursive(self, currtree, dmb):
        for k in currtree:
            if k == '.':
                self._resolve_and_collect_vars_recursive(currtree[k], dmb)
            else:
                self._populate_variables_recursive(currtree[k], dmb)

    def _unpack_proc_locals(self, proc, dmb):
        proc.locals = []
        vlist = dmb._resolve_data(proc.variable_list)
        if vlist is not None:
            vs = dmb._unpack_arch(vlist)
            if len(vs) > 0:
                for v in vs:
                    proc.locals.append(dmb._resolve_string(dmb._resolve_var(v).name))

    def _assign_procedures(self, dmb):
        for p in dmb.procs:
            if p.path == 65535:
                continue
            c = Proc()
            c.id = p.id
            c.path = dmb._resolve_string(p.path)
            c.name = dmb._resolve_string(p.name)
            c.desc = dmb._resolve_string(p.desc)
            c.category = dmb._resolve_string(p.category)
            c.range = p.range
            c.access = p.access
            c.flags = p.flags
            c.ext_flags = p.ext_flags
            c.invisibility = p.invisibility
            c.variable_list = p.variable_list
            self._unpack_proc_locals(c, dmb)

            alist = dmb._resolve_data(p.argument_list)
            if alist is not None:
                args = list(dmb._unpack_arch(alist))
                if len(args) > 0:
                    i = 0
                    while i < len(args):
                        args[i+1] = struct.unpack("<BBBB", struct.pack("<I", args[i+1]))
                        v = dmb._resolve_var(args[i+2])
                        argname = dmb._resolve_string(v.name)
                        inrange = args[i+1][1]
                        if args[i+1][0] == 64:
                            argproc = dmb.argprocs[args[i+1][1]]
                            argproc_proc = dmb._resolve_proc(argproc)
                            inrange = Proc()
                            inrange.data = argproc_proc.data
                            inrange.argproc_id = args[i+1][1]
                            inrange.variable_list = argproc_proc.variable_list
                            self._unpack_proc_locals(inrange, dmb)
                        c.parameters.append(Arg(argname, args[i], args[i+1][0], inrange))
                        i += 4

            parts = c.path.rsplit("/", 2)
            is_verb = False
            if parts[1] != "proc":
                if parts[1] != "verb":
                    parts[0] += "/{0}".format(parts[1])
                else:
                    is_verb = True
            stree = self.get_path(parts[0])
            if stree is not None:
                t = stree["."]
                if not is_verb:
                    t.procedures_own[parts[2]] = c
                else:
                    t.verbs_own[parts[2]] = c
                c.defined_on = t

        self._populate_procedures_recursive(self.tree, dmb)

    def _collect_procedures(self, t, dmb):
        t.procedures = {}
        t.verbs = {}
        for pname in t.procedures_own:
            t.procedures[pname] = t.procedures_own[pname]
        for vname in t.verbs_own:
            t.verbs[vname] = t.verbs_own[vname]
        p = t.parent
        if p is dmb.no_parent_type:
            return
        if p.procedures is None:
            self._collect_procedures(p, dmb)
        if p.procedures is not None:
            for pname in p.procedures:
                if pname not in t.procedures:
                    t.procedures[pname] = p.procedures[pname]
        if p.verbs is not None:
            for vname in p.verbs:
                if vname not in t.verbs:
                    t.verbs[pname] = p.verbs[vname]

    def _resolve_proc_references_recursive(self, currtree, proclist):
        for k in currtree:
            if k == ".":
                t = currtree[k]
                pr = {}
                for pid in t.procedures:
                    proc = proclist[pid]
                    prname = proc.path.rsplit('/', 1)[1]
                    pr[prname] = proc
                t.procedures = pr
                vr = {}
                for pid in t.verbs:
                    proc = proclist[pid]
                    prname = proc.path.rsplit('/', 1)[1]
                    vr[prname] = proc
                t.verbs = vr
                pro = {}
                for pid in t.procedures_own:
                    proc = proclist[pid]
                    prname = proc.path.rsplit('/', 1)[1]
                    pro[prname] = proc
                t.procedures_own = pro
                vro = {}
                for pid in t.verbs_own:
                    proc = proclist[pid]
                    prname = proc.path.rsplit('/', 1)[1]
                    vro[prname] = proc
                t.verbs_own = vro
            else:
                self._resolve_proc_references_recursive(currtree[k], proclist)

    def _populate_procedures_recursive(self, currtree, dmb):
        for k in currtree:
            if k == '.':
                self._collect_procedures(currtree[k], dmb)
            else:
                self._populate_procedures_recursive(currtree[k], dmb)

    def _resolve_tree_recursive(self, currtree):
        for k in currtree:
            if k == '.' and isinstance(currtree[k], dict):
                old = currtree[k]
                currtree[k] = Type(old['path'], old['parent'])
                currtree[k].name = old['name']
                currtree[k].desc = old['desc']
                currtree[k].icon = old['icon']
                currtree[k].icon_state = old['icon_state']
                currtree[k].dir = old['dir']
                currtree[k].layer = old['layer']
                currtree[k].id = old['id']
            else:
                self._resolve_tree_recursive(currtree[k])

    def _resolve_parents_recursive(self, currtree):
        for k in currtree:
            if k == '.':
                p = currtree[k].parent
                if isinstance(p, str):
                    parent_tree = self.get_path(p)
                    if parent_tree is not None:
                        currtree[k].parent = parent_tree['.']
            else:
                self._resolve_parents_recursive(currtree[k])

    def __getitem__(self, key):
        return self.tree[key]

    def __iter__(self):
        return self.tree.__iter__()

    def push(self, typeinst):
        path = typeinst.path.split('/')
        curr_tree = self.tree
        for part in path[1:]:
            if part not in curr_tree:
                curr_tree[part] = {}
            curr_tree = curr_tree[part]
        curr_tree["."] = typeinst

    def _aggregate_procedures_recursive(self, currtree):
        res = {}
        for k in currtree:
            if k == ".":
                for p in currtree[k].procedures:
                    proc = currtree[k].procedures[p]
                    res[proc.id] = proc
                for v in currtree[k].verbs:
                    verb = currtree[k].verbs[v]
                    res[verb.id] = verb
            else:
                ndupdate(res, self._aggregate_procedures_recursive(currtree[k]))
        return res

    def _aggregate_procedures(self):
        return self._aggregate_procedures_recursive(self.tree)

    def json(self):
        return json.dumps({"tree": self.tree, "procs": self._aggregate_procedures()}, cls=dmbjson.JSONEncoder, sort_keys=True, indent=2)

    def get_path(self, path):
        slash = b'/'
        if isinstance(path, str):
            slash = "/"
        path = path.lstrip(slash)
        parts = path.split(slash)
        curr_tree = self.tree
        for part in parts:
            if part in curr_tree:
                curr_tree = curr_tree[part]
            else:
                return None
        return ObjectTree(tree=curr_tree)

    def complete_path(self, path):
        parts = path.split('/')
        tree = self.get_path('/'.join(parts[:-1]))
        if tree is None:
            return None
        options = []
        for k in tree:
            if k == ".":
                continue
            if parts[-1] in k:
                options.append(k)
        return {
            "tree": tree,
            "options": options,
        }

    def __repr__(self):
        return self.json()
