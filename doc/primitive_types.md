# Primitive types

Each primitive type is identified by one byte, which determines the variable type. This type may also have an assigned value, the structure of which depends on the type.

For variables and other data types which take a primitive type and value pair, the structure is fixed length: the type ID is 1 byte and the type parameter is 4 bytes, architecture-independently.

In this case, the following table applies:

Primitive type name | Type ID | Purpose of value | Type description                                 |
------------------- | ------- | ---------------- | ------------------------------------------------ |
Null                | 0x00    | None. Is 0.      | The BYOND null value.                            |
String              | 0x06    | String ID.       | Represents any constant string.                  |
Mob                 | 0x08    | TODO             | TODO                                             |
Type                | 0x09    | TODO             | TODO                                             |
Type                | 0x0A    | TODO             | TODO                                             |
Type                | 0x0B    | TODO             | TODO                                             |
Resource            | 0x0C    | Resource ID      | References a resource compiled into the RSC.     |
Type                | 0x20    | TODO             | TODO                                             |
Savefile            | 0x24    | TODO             | TODO                                             |
File                | 0x27    | TODO             | TODO                                             |
List                | 0x28    | TODO             | TODO                                             |
Number (float)      | 0x2A    | 32-bit float     | Represents a number as a single precision float. |
Client              | 0x3B    | TODO             | TODO                                             |
List                | 0x3E    | TODO             | TODO                                             |
Image               | 0x3F    | TODO             | TODO                                             |

When encountering type-value pairs in the data arrays, they may be decoded as follows:

As usual, the length of values in the data array is architecture-dependent.

Primitive type name | Type byte | Value length | Notes                                   |
------------------- | --------- | ------------ | --------------------------------------- |
Null                | 0x00      | 2/4 bytes    | Null type and value. Value is always 0. |
String              | 0x06      | 2/4 bytes    | Value is a string ID.                   |
Float               | 0x2A      | 4/8 bytes    | Is always a 4 byte float. See note 1.   |

Note 1: For floats, the two architecture-length values provided are always less than or equal to 0xFFFF. To gain the value of the float, take the first value as the upper 2 bytes, and the second value as the lower 2 bytes. For 16-bits, this is straightforward, as the two 16-bits (0xAAAA 0xBBBB) look exactly like the 32-bit float (0xAAAABBBB). For 32-bits this is slightly awkward, but maintains backwards compatibility. In essence the lower two bytes of the two 32-bits (0x0000AAAA 0x0000BBBB) make up the 32-bit float (0xAAAABBBB).

To be continued as more types are explored.