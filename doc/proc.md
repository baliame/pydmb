# Proc structure

This is the structure of DMB-packed procs.

We differentiate between 16 and 32-bit DMBs. These are the first and second value in the length column respectively.

Note: for both 16-bit and 32-bit DMBs, the value 65535 for an ID represents "no value". Essentially, a name value of 65535 means the proc has no name.

Procs are stored in ID order in the DMB. That means the first proc read is ID 0.

Procs are varying length, according to some flags in the DMB. The condition column defines when a value should be expected.

Certain procs may be initializers. In this case, the path will be the no value string (65535).

Field name     | Length     | Condition                 | Type        | Purpose                                          |
-------------- | ---------- | ------------------------- | ----------- | ------------------------------------------------ |
Path           | 2/4 bytes  | Always present            | String ID   | Defines the full path of this proc.              |
Name           | 2/4 bytes  | Always present            | String ID   | The value of `set name`                          |
Desc           | 2/4 bytes  | Always present            | String ID   | The value of `set desc`                          |
Category       | 2/4 bytes  | Always present            | String ID   | The value of `set category`                      |
Range          | 1 byte     | Always present            | Integer     | The parameter of `set src in [o]view()`          |
Access         | 1 byte     | Always present            | Integer     | The access of the proc, see table below          |
Flags          | 1 byte     | Always present            | Flags       | Flag for certain settings.                       |
Extended flags | 4 bytes    | bit 7 of flags set        | Flags       | Additional flags for proc settings               |
Invisibility   | 1 byte     | bit 7 of flags set        | Integer     | The value of `set invisibility`                  |
Data           | 2/4 bytes  | Always present            | Data ID     | Pointer to the implementation of the proc.       |
Variable list  | 2/4 bytes  | Always present            | Data ID     | The list of local variables in this proc.        |
Argument list  | 2/4 bytes  | Always present            | Data ID     | The list of arguments passed to this proc.       |

Everything should be easy to resolve according to ID except the data, variable list and the argument list.

For documentation of the data, refer to the instruction table to decode the BYOND bytecode.

The structure of the lists is as follows:

## Variable list

In the data array, the variable list is present as a list of variable IDs. Each variable may appear several times in the variable list. Each variable appears in the order of definition, regardless of scope.

The format of the entries in the list is as follows:

Field name  | Length    | Type        | Purpose                                           |
----------- | --------- | ----------- | ------------------------------------------------- |
Variable ID | 2/4 bytes | Variable ID | References the ID of a variable used in this proc |

For reference on how to resolve variables, see the variable documentation.

## Argument list

In the data array, the argument list is represented as a list of four component values. All arguments are present and complete with the encoded version of all DM syntax candy.

Each entry in the argument list has the following structure:

Field name  | Length    | Type        | Purpose                                                                 |
----------- | --------- | ----------- | ------------------------------------------------------------------------|
Type flags  | 2/4 bytes | Flags       | A bitfield including each type after the `as` for an argument.          |
Value list  | 2/4 bytes | Varying     | Only the first two bytes are used. See the note below on how to decode. |
Name        | 2/4 bytes | String ID   | Refers to the name of this argument                                     |
0           | 2/4 bytes | Unknown     | As far as I observed, this is always 0.                                 |

### Type flags

Any arbitrary combination of these flags may appear in the argument list, even absurd ones such as `obj|anything`. A flag value of 0 denotes that there is no type restriction on the argument.

Type flag bit | Designated type |
------------- | --------------- |
bit 0 (1)     | obj             |
bit 1 (2)     | mob             |
bit 2 (4)     | text            |
bit 3 (8)     | num             |
bit 4 (16)    | file            |
bit 5 (32)    | turf            |
bit 7 (128)   | null            |
bit 8 (256)   | area            |
bit 10 (1024) | sound           |
bit 11 (2048) | message         |
bit 12 (4096) | anything        |

The type flags appear in the parameter list after an `as` keyword, for example: `proc/foo(bar as mob|obj|null)`

### Value list

The value list contains two useful bytes. The first byte is the used to determine the type of the list of valid value. The valid type values:

Type value | Value list  |
---------- | ----------- |
1          | view()      |
2          | oview()     |
3          | usr.loc     |
8          | usr         |
16         | world       |
64         | custom proc |

The second byte is the parameter to the value list generator. For view() and oview(), this value may go up to 124, with 125 denoting that view() or oview() is called with no parameter. For usr.loc, usr, and world this value is unused. For a custom proc, this value denotes the argproc ID that describes the custom proc used to generate the value list.

The value list appears in the parameter list after an `in` keyword, for example: `proc/foo(bar in view(5))`
