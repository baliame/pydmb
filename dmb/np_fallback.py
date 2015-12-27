class uint8:
    def __init__(self, val):
        self.val = val & 0xFF

    def __add__(self, val):
        return uint8(self.val + val)

    def __radd__(self, val):
        return uint8(self.val + val)

    def __iadd__(self, val):
        self.val = (self.val + val) & 0xFF
        return self

    def __sub__(self, val):
        return uint8(self.val - val)

    def __rsub__(self, val):
        return uint8(val - self.val)

    def __isub__(self, val):
        self.val = (self.val - val) & 0xFF

    def __mod__(self, val):
        return uint8(self.val % val)

    def __rmod__(self, val):
        return uint8(val % self.val)

    def __imod__(self, val):
        self.val = (self.val % val) & 0xFF
        return self

    def __lshift__(self, val):
        return uint8(self.val << val)

    def __rlshift__(self, val):
        return uint8(val << self.val)

    def __ilshift__(self, val):
        self.val = (self.val << val) & 0xFF
        return self

    def __rshift__(self, val):
        return uint8(self.val >> val)

    def __rrshift__(self, val):
        return uint8(val >> self.val)

    def __irshift__(self, val):
        self.val = (self.val >> val) & 0xFF
        return self

    def __and__(self, val):
        return uint8(self.val & val)

    def __rand__(self, val):
        return uint8(self.val & val)

    def __iand__(self, val):
        self.val &= val
        return self

    def __or__(self, val):
        return uint8(self.val | val)

    def __ror__(self, val):
        return uint8(self.val | val)

    def __ior__(self, val):
        self.val |= (val & 0xFF)
        return self

    def __xor__(self, val):
        return uint8(self.val ^ val)

    def __rxor__(self, val):
        return uint8(self.val ^ val)

    def __ixor__(self, val):
        self.val ^= (val & 0xFF)
        return self

    def __mul__(self, val):
        return uint8(self.val * val)

    def __rmul__(self, val):
        return uint8(self.val * val)

    def __imul__(self, val):
        self.val = (self.val * val) & 0xFF
        return self

    def __invert__(self):
        return uint8(self.val ^ 0xFF)

    def __abs__(self):
        return uint8(self.val)

    def __round__(self):
        return self.val

    def __int__(self):
        return self.val

    def __float__(self):
        return float(self.val)

    def __str__(self):
        return "{0}".format(self.val)

    def __repr__(self):
        return "uint8({0})".format(repr(self.val))


class uint32:
    def __init__(self, val):
        self.val = val & 0xFFFFFFFF

    def __add__(self, val):
        return uint32(self.val + val)

    def __radd__(self, val):
        return uint32(self.val + val)

    def __iadd__(self, val):
        self.val = (self.val + val) & 0xFFFFFFFF
        return self

    def __sub__(self, val):
        return uint32(self.val - val)

    def __rsub__(self, val):
        return uint32(val - self.val)

    def __isub__(self, val):
        self.val = (self.val - val) & 0xFFFFFFFF

    def __mod__(self, val):
        return uint32(self.val % val)

    def __rmod__(self, val):
        return uint32(val % self.val)

    def __imod__(self, val):
        self.val = (self.val % val) & 0xFFFFFFFF
        return self

    def __lshift__(self, val):
        return uint32(self.val << val)

    def __rlshift__(self, val):
        return uint32(val << self.val)

    def __ilshift__(self, val):
        self.val = (self.val << val) & 0xFFFFFFFF
        return self

    def __rshift__(self, val):
        return uint32(self.val >> val)

    def __rrshift__(self, val):
        return uint32(val >> self.val)

    def __irshift__(self, val):
        self.val = (self.val >> val) & 0xFFFFFFFF
        return self

    def __and__(self, val):
        return uint32(self.val & val)

    def __rand__(self, val):
        return uint32(self.val & val)

    def __iand__(self, val):
        self.val &= val
        return self

    def __or__(self, val):
        return uint32(self.val | val)

    def __ror__(self, val):
        return uint32(self.val | val)

    def __ior__(self, val):
        self.val |= (val & 0xFFFFFFFF)
        return self

    def __xor__(self, val):
        return uint32(self.val ^ val)

    def __rxor__(self, val):
        return uint32(self.val ^ val)

    def __ixor__(self, val):
        self.val ^= (val & 0xFFFFFFFF)
        return self

    def __mul__(self, val):
        return uint32(self.val * val)

    def __rmul__(self, val):
        return uint32(self.val * val)

    def __imul__(self, val):
        self.val = (self.val * val) & 0xFFFFFFFF
        return self

    def __invert__(self):
        return uint32(self.val ^ 0xFFFFFFFF)

    def __abs__(self):
        return uint32(self.val)

    def __round__(self):
        return self.val

    def __int__(self):
        return self.val

    def __float__(self):
        return float(self.val)

    def __str__(self):
        return "{0}".format(self.val)

    def __repr__(self):
        return "uint32({0})".format(repr(self.val))
