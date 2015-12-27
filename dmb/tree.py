from .dmb import Type, Proc, Arg, resolve_astype
from . import json as dmbjson
from . import constants
import json
import struct


def tree_from_json(jdict):
    tree = ObjectTree(tree=jdict)
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
atom_vars = set(["alpha", "appearance", "appearance_flags", "blend_mode", "color", "density", "desc", "dir", "gender", "icon", "icon_state", "infra_luminosity", "invisibility", "layer", "loc", "maptext", "maptext_width", "maptext_height", "maptext_x", "maptext_y", "mouse_drag_pointer", "mouse_drop_pointer", "mouse_drop_zone", "mouse_opacity", "mouse_over_pointer", "name", "opacity", "overlays", "override", "pixel_x", "pixel_y", "pixel_z", "plane", "suffix", "text", "transform", "underlays", "verbs", "x", "y", "z"]) | datum_vars
movable_vars = set(["animate_movement", "bound_x", "bound_y", "bound_width", "bound_height", "locs", "glide_size", "screen_loc", "step_size", "step_x", "step_y"]) | atom_vars
base_type_variables = {
    "area": atom_vars,
    "atom": atom_vars,
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
            self._populate_types_from_dmb(dmb)
        if loaded or dmb is not None:
            self._resolve_parents_recursive(self.tree)
        if dmb is not None:
            self._populate_variables_recursive(self.tree, dmb)
            self._assign_procedures(dmb)

    def _populate_types_from_dmb(self, dmb):
        for t in dmb.types:
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
            varset |= p.variables
        t.variables = varset

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
            t.verbs[pname] = t.verbs_own[vname]
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
                res += self._aggregate_procedures_recursive(currtree[k])

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
