# Type structure

This is the structure of DMB-packed types.

We differentiate between 16 and 32-bit DMBs. These are the first and second value in the length column respectively.

Note: for both 16-bit and 32-bit DMBs, the value 65535 for an ID represents "no value". Essentially, a parent value of 65535 means the type has no parent_type.

Types are stored in ID order in the DMB. That means the first type read is ID 0.

Types are varying length, according to some flags in the DMB. The condition column defines when a value should be expected.

Field name    | Length     | Condition                  | Type        | Purpose                                          |
------------- | ---------- | -------------------------- | ----------- | ------------------------------------------------ |
Path          | 2/4 bytes  | Always present             | String ID   | Defines the full path of this type.              |
Parent        | 2/4 bytes  | Always present             | Type ID     | The value of the parent_type builtin.            |
Name          | 2/4 bytes  | Always present             | String ID   | The initial value of the name builtin.           |
Desc          | 2/4 bytes  | Always present             | String ID   | The initial value of the desc builtin.           |
Icon          | 2/4 bytes  | Always present             | Resource ID | The initial value of the icon builtin.           |
Icon state    | 2/4 bytes  | Always present             | String ID   | The initial value of the icon_state builtin.     |
Dir           | 1 byte     | Always present             | Integer     | The initial value of the dir builtin.            |
Unknown 1     | 1 byte     | Always present             | Unknown     | Appears to be a flag.                            |
Unknown 2     | 4 bytes    | unknown 1 == 15            | Unknown     | No known purpose.                                |
Text          | 2/4 bytes  | Always present             | String ID   | The initial value of the text builtin.           |
Suffix        | 2/4 bytes  | Always present             | String ID   | The initial value of the suffix builtin.         |
Maptext W     | 2 bytes    | Always present             | Integer     | The initial value of the maptext_width builtin.  |
Maptext H     | 2 bytes    | Always present             | Integer     | The initial value of the maptext_height builtin. |
Maptext X     | 2 bytes    | min_client > 507           | Integer     | The initial value of the maptext_x builtin.      |
Maptext Y     | 2 bytes    | min_client > 507           | Integer     | The initial value of the maptext_y builtin.      |
Maptext       | 2/4 bytes  | Always present             | String ID   | The initial value of the maptext builtin.        |
Flags         | 4 bytes    | Always present             | Integer     | A large number of binary variables as bitflags.  |
Verb list     | 2/16 bytes | Always present             | Data ID     | The list of proc IDs for verbs on this type.     |
Proc list     | 2/4 bytes  | Always present             | Data ID     | The list of proc IDs for procs on this type.     |
Unknown 3     | 2/4 bytes  | Always present             | Unknown ID  | Not yet determined, probably initializer.        |
Unknown 4     | 2/4 bytes  | Always present             | Unknown ID  | Unknown purpose.                                 |
Variable list | 2/4 bytes  | Always present             | Data ID     | The list of user-defined vars on this type.      |
Layer         | 4 bytes    | Always present             | Float       | The initial value of the layer builtin.          |
Unknown 5     | 1 byte     | min_client >= 500          | Unknown     | No known purpose.                                |
Unknown 6     | 24 bytes   | unknown 5 > 0              | Unknown     | No known purpose.                                |
Builtins      | 2/4 bytes  | Always present             | Data ID     | The list of builtins with altered values         |

## Flags

Bit ID | Controlled variable    |
------ | ---------------------- |
0      | Opacity                |
1      | Density                |
2      | Visibility             |
3      | ?                      |
4      | ?                      |
5      | ?                      |
6      | Gender bit 1           |
7      | Gender bit 0           |
8      | Mouse drop zone        |
9      | ?                      |
10     | Animate movement bit 2 |
11     | ?                      |
12     | Mouse opacity bit 1    |
13     | Mouse opacity bit 0    |
14     | Animate movement bit 1 |
15     | Animate movement bit 0 |
16-31  | ?                      |

### Gender

Using bit 6 and 7 of the flags, the gender of the object is:

Bit 6 | Bit 7 | Gender |
----- | ----- | ------ |
0     | 0     | Neuter |
0     | 1     | Female |
1     | 0     | Male   |
1     | 1     | Plural |

### Mouse opacity

This bit is unverified, it is directly lifted from the N3X15/YotaXP documentation.

Bit 12 | Bit 13 | Mouse opacity |
------ | ------ | ------------- |
0      | 0      | Transparent   |
0      | 1      | ?             |
1      | 0      | Fully opaque  |
1      | 1      | Normal        |

### Animate movement

This bit is unverified, it is directly lifted from the N3X15/YotaXP documentation.

Bit 10 | Bit 14 | Bit 15 | Constant      |
------ | ------ | ------ | ------------- |
0      | 0      | 0      | FORWARD_STEPS |
0      | 0      | 1      | SYNC_STEPS    |
0      | 1      | 0      | SLIDE_STEPS   |
1      | 1      | 1      | NO_STEPS      |


## Lists

Everything should be easy to resolve according to ID except the variable list and the builtins list.

The structure of each is as follows:

### Proc & verb list

In the data array, the proc and verb lists are present as lists of proc IDs. These lists are not a full list of proc and verbs. They are a list of procs and verbs defined or overridden on this exact type. For a full list of procs and verbs, they must be aggregated from parent types.

The format of the list is as follows:

Field name  | Length    | Type        | Purpose                                               |
----------- | --------- | ----------- | ----------------------------------------------------- |
Proc ID     | 2/4 bytes | Proc ID     | References the ID of a proc or verb used on this type |

### Variable list

In the data array, the variable list is present as a list of variable IDs. The variable list is not a full list of variables. It is a list of variables defined or modified on this exact type. For a full list of variables, all variables must be aggregated from parent types.

The format of the entries in the list is as follows:

Field name  | Length    | Type        | Purpose                                           |
----------- | --------- | ----------- | ------------------------------------------------- |
Variable ID | 2/4 bytes | Variable ID | References the ID of a variable used on this type |
0           | 2/4 bytes | Constant    | A null byte.                                      |

For reference on how to resolve variables, see the variable documentation.

### Builtin variable list (Builtins)

In the data array, the builtin variable list is present as a builtins which do not have their own primary field in the type definition and whose initial value is non-default. To be perfectly precise, this is not a complete list of all builtin variables.

The structure of an element for the builtin list is:

Field name  | Length    | Type        | Purpose                                                               |
----------- | --------- | ----------- | --------------------------------------------------------------------- |
Name        | 2/4 bytes | String ID   | The name of the builtin variable whose value is being changed.        |
Type        | 1 byte    | Value type  | The identifier of the primitive type of the value being assigned.     |
Value       | Varying   | Value       | The value being assigned. For size, refer to the primitive types doc. |

For reference on how to resolve primitive types, see the primitive type documentation.
