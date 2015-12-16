from .dmb import type as btype
from . import json as dmbjson
import json


def tree_from_json(jdict):
    tree = ObjectTree(jdict)
    tree.resolve_parent_refs_recursive(tree.tree)
    return tree


class ObjectTree:
    def __init__(self, tree={}):
        self.tree = tree

    def resolve_parent_refs_recursive(self, currtree):
        for k in currtree:
            if k == '.' and isinstance(currtree[k], dict):
                old = currtree[k]
                currtree[k] = btype(old['path'], old['parent'])
                currtree[k].name = old['name']
                currtree[k].desc = old['desc']
                p = currtree[k].parent
                if isinstance(p, str):
                    parent_tree = self.get_path(p)
                    if parent_tree is not None:
                        currtree[k].parent = parent_tree['.']
            else:
                self.resolve_parent_refs_recursive(currtree[k])

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

    def json(self):
        return json.dumps(self.tree, cls=dmbjson.JSONEncoder, sort_keys=True, indent=2)

    def get_path(self, path):
        path = path.lstrip("/")
        parts = path.split("/")
        curr_tree = self.tree
        for part in parts:
            if part in curr_tree:
                curr_tree = curr_tree[part]
            else:
                return None
        return ObjectTree(curr_tree)

    def complete_path(self, path):
        parts = path.split("/")
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
