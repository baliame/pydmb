mod8 = 2**8
mod16 = 2**16
mod32 = 2**32

class ModularInt:
    def __init__(self, value, mod):
        self.value = value % mod
        self.mod = mod

    def __add__(self, other):   # self + foo
        return ModularInt(self.value + other, self.mod)

    def __radd__(self, other):  # foo + self
        return self.__add__(other)

    def __iadd__(self, other):  # self += foo
        self.value += other
        self.value %= self.mod
        return self

    def __sub__(self, other):   # self - foo
        return ModularInt(self.value - other, self.mod)

    def __rsub__(self, other):  # foo - self
        return ModularInt(other - self.value, self.mod)

    def __isub__(self, other):  # self += foo
        self.value -= other
        self.value %= self.mod
        return self

    def __mul__(self, other):   # self + foo
        return ModularInt(self.value * other, self.mod)

    def __rmul__(self, other):  # foo + self
        return self.__mul__(other)

    def __imul__(self, other):  # self += foo
        self.value *= other
        self.value %= self.mod
        return self

    def __xor__(self, other):
        return self.value ^ other

    def __rxor__(self, other):
        return other ^ self.value

    def __int__(self):
        return self.value

    def __str__(self):
        return "{0}".format(self.value)

    def __repr__(self):
        return "{0}".format(self.value)
