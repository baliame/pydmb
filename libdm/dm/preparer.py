import os.path as path
import os
import re


class Define:
    def __init__(self, name, args, subst):
        self.name = name
        self.args = args
        self.subst = subst

    def sub(self, s):
        if self.args is None:
            if s != self.name:
                raise ValueError("Cannot substitute '{0}' for definition of '{1}': define name mismatch.".format(s, self.name))
            else:
                return self.subst
        else:
            dable = re.search(r'^(\w+)\((.*?)\)$', s)
            if dable is None or dable.group(1) != self.name:
                raise ValueError("Cannot substitute '{0}' for definition of '{1}': define signature mismatch.".format(s, self.name))
            argst = dable.group(2)
            argl = []
            state = 0
            esc = 0
            last = 0
            cn = {0: 0}
            fn = {0: 0}
            for i in range(len(argst)):
                if state < 0:
                    if argst[i] == "'":
                        state = -state - 1
                elif state > 0 and state % 2 == 1:
                    if esc:
                        esc = 0
                    elif argst[i] == '"':
                        state -= 1
                    elif argst[i] == '\\':
                        esc = 1
                    elif argst[i] == '[':
                        state += 1
                        cn[state] = 0
                        fn[state] = 0
                else:
                    if state == 0 and argst[i] == ',':
                        if fn[state] == 0:
                            argl.append(argst[last:i].strip())
                            last = i+1
                    elif argst[i] == '(':
                        fn[state] += 1
                    elif argst[i] == ')':
                        fn[state] -= 1
                    elif argst[i] == '[':
                        cn[state] += 1
                    elif argst[i] == ']':
                        if cn[state] == 0:
                            state -= 1
                        else:
                            cn[state] -= 1
                    elif argst[i] == "'":
                        state = -state - 1
                    elif argst[i] == '"':
                        state += 1
            argl.append(argst[last:].strip())
            if len(argl) != len(self.args):
                raise ValueError("Cannot substitute '{0}' for definition of '{1}': argument count mismatch - expecting {2}, got {3}.".format(s, self.name, len(self.args), len(argl)))
            substs = {self.args[i]: argl[i] for i in range(len(argl))}
            pattern = re.compile('|'.join(['(?<=^|(?<=\W)){0}(?=(?=\W)|$)'.format(k) for k in substs.keys()]))
            return pattern.sub(lambda m: substs[m.group(0)], self.subst)


def parse_arg(args):
    state = 0
    args = args.strip()
    esc = 0
    for i in range(len(args)):
        if state == 0:
            if args[i] in ' \t\r\n':
                return (args[:i], args[i+1:])
            elif args[i] == '"':
                state = 1
            elif args[i] == "'":
                state = -1
        elif state == 1:
            if esc:
                esc = 0
            elif args[i] == '\\':
                esc = 1
            elif args[i] == '"':
                state = 0
        elif state == -1:
            if args[i] == "'":
                state = 0
    return (args, None)


def split_args(args):
    ret = []
    while True:
        arg, n = parse_arg(args)
        ret.append(arg)
        if n is None:
            break
        arg = n
    return ret


class Preparer:
    def __init__(self, base_dir, build_dir):
        self.base_dir = path.abspath(base_dir)
        self.build_dir = path.abspath(build_dir)
        self.main = None
        self.defines = {}
        self.comment_sub = re.compile(r'//(.*?)$')
        self.cond_tree = []
        self.put = True

    def rebuild_put(self):
        self.put = not (False in self.cond_tree)

    def eval_if(self, args):
        a = split_args(args)
        if len(a) == 1:
            arg = a[0].strip()
            if arg == '0' or arg == 'false':
                return False
            m = re.match(r'^defined\((.*?)\)$', arg)
            if m is not None:
                if m.group(1) in self.defines:
                    return True
                else:
                    return False
            return True
        elif len(a) == 3:
            op = a[1]
            if op == '==':
                return a[0] == a[2]
            elif op == '!=' or op == '<>':
                return a[0] != a[2]
            elif op == '<':
                return int(float(a[0])) < int(float(a[2]))
            elif op == '<=':
                return int(float(a[0])) <= int(float(a[2]))
            elif op == '>':
                return int(float(a[0])) > int(float(a[2]))
            elif op == '>=':
                return int(float(a[0])) >= int(float(a[2]))
            else:
                return 'Cannot evaluate expression {0}: unknown operator {1}'.format(args, op)
        else:
            return 'Cannot evaluate expression {0} (parsed arguments: {1})'.format(args, a)

    def prepare(self, filepath, destbuf=None, main=True):
        if path.isabs(filepath):
            if path.commonpath([self.base_dir, filepath]) != self.base_dir:
                raise ValueError("File {0} must be within project base directory.".format(filepath))
            absolute = filepath
            filepath = path.relpath(filepath, self.base_dir)
        else:
            absolute = path.join(self.base_dir, filepath)
        if destbuf is None:
            destfile = path.join(self.build_dir, filepath)
            destdir = path.dirname(destfile)
            if not path.isdir(destdir):
                os.makedirs(destdir)
        lineno = 0
        if main:
            self.cond_tree = []
            self.put = True
            self.main = filepath
            self.defines = {}

        with open(absolute, 'r') as src:
            if destbuf is not None:
                dest = destbuf
            else:
                dest = open(destfile, 'w')
            lastindent = ''
            indents = []
            for line in iter(lambda: src.readline(), ""):
                lineno += 1

                preprocess_special = {
                    "DM_VERSION": 509,
                    "__FILE__": '"{0}"'.format(filepath),
                    "__LINE__": str(lineno),
                    "__MAIN__": '"{0}"'.format(self.main),
                }

                pattern = re.compile('|'.join(preprocess_special.keys()))
                line = pattern.sub(lambda m: preprocess_special[m.group(0)], line)
                line = self.comment_sub.sub('', line)

                if re.match(r'^\s*$', line):
                    continue

                if line[0] == '#':
                    preproc = re.match(r'(?i)^#([a-z]+)\s*(.*)$', line)
                    if preproc is None:
                        raise ValueError("{0}:{1} error: Cannot parse preprocessor instruction: {2}".format(filepath, lineno, line))
                    instr, args = (preproc.group(1), preproc.group(2))
                    if instr == "include":
                        spath = args.strip().strip('"').replace('\\', '/')
                        dest.write("// @{0}\n".format(spath))
                        abspath = path.join(self.base_dir, spath)
                        if path.samefile(absolute, abspath):
                            raise ValueError("{0}:{1} error: Circular import for file {2}.".format(filepath, lineno, filepath))
                        self.prepare(spath, dest, main=False)
                    elif instr == "define":
                        argp = re.match(r'^(\w+)(?:\((.*?)\))?(\s+(.*))?$', args)
                        if argp is None:
                            raise ValueError("{0}:{1} Unable to parse #define args: {2}".format(filepath, lineno, args))
                        defname, defargs, defsubst = argp.groups()
                        if defargs is not None:
                            defargs = re.split(r',\s*', defargs.strip())
                        self.defines[defname] = Define(defname, defargs, defsubst)
                        print("#define {0}{1} {2}".format(defname, '({0})'.format(','.join(defargs)) if defargs is not None else '', defsubst))
                    elif instr == "undef":
                        if args in self.defines:
                            self.defines.pop(args)
                        else:
                            raise ValueError("{0}:{1} error: Undefining undefined define: {2}.".format(filepath, lineno, args))
                    elif instr == "ifdef":
                        if args in self.defines:
                            self.cond_tree.append(True)
                        else:
                            self.cond_tree.append(False)
                        self.rebuild_put()
                    elif instr == "ifndef":
                        if args in self.defines:
                            self.cond_tree.append(False)
                        else:
                            self.cond_tree.append(True)
                        self.rebuild_put()
                    elif instr == "else":
                        if len(self.cond_tree):
                            self.cond_tree.append(not self.cond_tree.pop())
                        else:
                            raise ValueError("{0}:{1} error: #else without preceding #if(n)def.".format(filepath, lineno))
                        self.rebuild_put()
                    elif instr == "endif":
                        if len(self.cond_tree):
                            self.cond_tree.pop()
                        else:
                            raise ValueError("{0}:{1} error: #endif without preceding #if(n)def.".format(filepath, lineno))
                        self.rebuild_put()
                    elif instr == "error":
                        if self.put:
                            raise ValueError("{0}:{1} error: {2}".format(filepath, lineno, args))
                    elif instr == "warn":
                        if self.put:
                            print("{0}:{1} warning: {2}".format(filepath, lineno, args))
                    elif instr == "if":
                        res = self.eval_if(args)
                        if isinstance(res, str):
                            raise ValueError("{0}:{1} error: {2}".format(filepath, lineno, res))
                        self.cond_tree.append(res)
                    elif instr == "elif":
                        if len(self.cond_tree):
                            self.cond_tree.pop()
                        else:
                            raise ValueError("{0}:{1} error: #endif without preceding #if(n)def.".format(filepath, lineno))
                        res = self.eval_if(args)
                        if isinstance(res, str):
                            raise ValueError("{0}:{1} error: {2}".format(filepath, lineno, res))
                    else:
                        raise ValueError("{0}:{1} error: Unknown preprocessor directive: {2}", filepath, lineno, instr)
                    continue

                limatch = re.match(r'^([\t ]*)(.*?)$', line)
                if limatch is None:
                    raise ValueError("{0}:{1} error: Line does not match match-all regex. This is impossible.".format(filepath, lineno))

                indent = limatch.group(1)
                if indent == lastindent:
                    # no indent change
                    pass
                elif indent.find(lastindent) == 0:
                    indents.append(indent[len(lastindent):])
                    dest.write("{ ")
                else:
                    found = False
                    orig_indents = [a.encode('utf-8') for a in indents]
                    while not found:
                        if not len(indents):
                            break
                        indents.pop()
                        dest.write("; } ")
                        if ''.join(indents) == indent:
                            found = True
                    if not found:
                        print(orig_indents)
                        print(lastindent.encode('utf-8'))
                        print(indent.encode('utf-8'))
                        raise ValueError("{0}:{1} error: Inconsistent indentation.".format(filepath, lineno))
                lastindent = indent
                dest.write(line + ";\n")
            for indent in indents:
                dest.write("; } ")
            dest.write(";")
            if main:
                dest.write("\n")
            if destbuf is None:
                dest.close()
