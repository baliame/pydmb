from .preparer import Preparer
import os.path as path
import os
from lrparsing import *


class DMGrammar(Grammar):
    class T(TokenRegistry):
        number = Token(re=r'[+-]?(?:[0-9]+|(?:[0-9]*\.[0-9]+))(?:e[+-]?[0-9]+)?')
        ident = Token(re=r'\w+')
        eos = Token(re=r'[\n;]')
    expr = Ref("expr")
    atom = T.ident | T.number
    terminator = T.eos
    #path_component = T.ident << Token('/')
    #var_def = Opt(Token('/')) << Keyword('var') << Token('/') << Many(path_component) << T.ident << Opt(Token('=') << expr)
    #var_block = Opt(Token('/')) << Keyword('var') + Token('{') + Many(var_def_headless | var_block_inner) + Token('}')
    expr = Prio(
        atom,
        Token('(') + expr + Token(')'),
        Tokens("! ~ + - ++ --") >> THIS,
        THIS >> Token("**") >> THIS,
        THIS << Tokens("* / %") << THIS,
        THIS << Tokens("+ -") << THIS,
        THIS << Tokens("< <= > >=") << THIS,
        THIS << Tokens("<< >>") << THIS,
        THIS << (Tokens("== != <>") | Keyword("in") | Keyword("as")) << THIS,
        THIS << Tokens("& | ^") << THIS,
        THIS << Token("&&") << THIS,
        THIS << Token("||") << THIS,
        THIS << Token("?") << THIS << Token(":") << THIS,
        THIS << Tokens("= += -= *= /= %= &= |= ^= <<= >>=")
    )
    #definitions = var_def | var_block
    #global_scope = Many(definitions + Many(terminator))
    START = expr


class Parser:
    def __init__(self, dme):
        self.dme = dme
        self.root = path.dirname(dme)
        self.build_dir = path.join(self.root, '.dmbuild')
        if not path.isdir(self.build_dir):
            os.mkdir(self.build_dir)

        self.preparer = Preparer(self.root, self.build_dir)

    def process(self):
        self.preparer.prepare(self.dme)
