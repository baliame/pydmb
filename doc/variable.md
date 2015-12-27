# Variable structure

Variables refer to anything declared as a variable within the code, including function parameters and locals within procs. Each variable is defined by a name and an initializer procedure.

We differentiate between 16 and 32-bit DMBs. These are the first and second value in the length column respectively.

Note: for both 16-bit and 32-bit DMBs, the value 65535 for an ID represents "no value". Essentially, a name value of 65535 means the variable is unnamed.

Variables are stored in ID order in the DMB. That means the first variable read is ID 0.

Field name  | Length    | Type      | Purpose                                                                  |
----------- | --------- | --------- | ------------------------------------------------------------------------ |
Type ID     | 1 byte    | Primitive | The primitive data type of the variable.                                 |
Type arg    | 4 bytes   | Varying   | An appropriate value for the type. For example, a string ID for strings. |
Name        | 2/4 bytes | String ID | The declared name of the variable.                                       |
