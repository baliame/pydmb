# Primitive types

Each primitive type is identified by one byte, which determines the variable type. This type may also have an assigned value, the structure of which depends on the type.

As usual, the length of values is architecture-dependent.

Primitive type name | Type byte | Value length | Notes                                   |
------------------- | --------- | ------------ | --------------------------------------- |
Null                | 0x00      | 2/4 bytes    | Null type and value. Value is always 0. |

String              | 0x06      | 2/4 bytes    | Value is a string ID.                   |
Float               | 0x2A      | 4/8 bytes    | Is always a 4 byte float. See note 1.   |

Note 1: For floats, the two architecture-length values provided are always less than or equal to 0xFFFF. To gain the value of the float, take the first value as the upper 2 bytes, and the second value as the lower 2 bytes. For 16-bits, this is straightforward, as the two 16-bits (0xAAAA 0xBBBB) look exactly like the 32-bit float (0xAAAABBBB). For 32-bits this is slightly awkward, but maintains backwards compatibility. In essence the lower two bytes of the two 32-bits (0x0000AAAA 0x0000BBBB) make up the 32-bit float (0xAAAABBBB).

To be continued as more types are explored.