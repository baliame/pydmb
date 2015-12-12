# DMB file structure
## Header
* Start: 0 bytes
* Length: varying (42 bytes in )
* End: Second `0x0a` (now referred to as `header_len`)
* End in 507:
* Format: plain text
* Example: `world bin v507\nin compatibility v507 501\n`
* Contents:

Content               | Content type           | Assigned meaning                 | Byte length   | Byte length in 507 |
--------------------- | ---------------------- | -------------------------------- | ------------- | ------------------ |
`world bin v`         | Constant string        |                                  | 11            | 11                 |
`[0-9]+`              | Variable length number | Version of DM used to compile    | varying       |  3                 |
`\n` (`0x0a`)         | Constant string        |                                  | 1             |  1                 |
`min compatibility v` | Constant string        |                                  | 19            | 19                 |
`[0-9]+`              | Variable length number | Lowest compatible server version | varying       |  3                 |
` ` (space)           | Constant string        |                                  | 1             |  1                 |
`[0-9]+`              | Variable length number | Lowest compatible client version | varying       |  3                 |
`\n` (`0x0a`)         | Constant string        |                                  | 1             |  1                 |
*Total*               |                        |                                  | varying >= 42 | 42                 |

