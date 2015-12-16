# DMB file structure
## Header
* Start: 0
* Start in 507: 0
* Length: varying (42 bytes in 507)
* End: Second `0x0a` (now referred to as `header_len`)
* End in 507: 42
* Format: plain text
* Example: `world bin v507\nin compatibility v507 501\n`
* Contents:

Content               | Content type           | Assigned meaning                 | Byte length    | Byte length in 507 |
--------------------- | ---------------------- | -------------------------------- | -------------- | ------------------ |
`world bin v`         | Constant string        |                                  | 11             | 11                 |
`[0-9]+`              | Variable length number | Version of DM used to compile    | varying        |  3                 |
`\n` (`0x0a`)         | Constant string        |                                  | 1              |  1                 |
`min compatibility v` | Constant string        |                                  | 19             | 19                 |
`[0-9]+`              | Variable length number | Lowest compatible server version | varying        |  3                 |
` ` (space)           | Constant string        |                                  | 1              |  1                 |
`[0-9]+`              | Variable length number | Lowest compatible client version | varying        |  3                 |
`\n` (`0x0a`)         | Constant string        |                                  | 1              |  1                 |
*Total*               |                        |                                  | varying (>=42) | 42                 |

## Binary header
* Start: `header_len`
* Start in 507: 42
* Length: 4
* End: `header_len`+4
* End in 507: 46
* Format: binary, little-endian
* Example: `0x0501E648`
* Contents:

Content name | Content type | Assigned meaning | Byte length |
------------ | ------------ | ---------------- | ----------- |
flags        | uint32       | Unknown          | 4           |
*Total*      |              |                  | 4           |

## Map
### Data structure: `map_tile`
* Length: 13
* Format: binary, little-endian
* Example: `0100000002000000FFFF0000FF`

Content name | Content type | Assigned meaning               | Byte length |
------------ | ------------ | ------------------------------ | ----------- |
area_id      | uint32       | ID of area of tile             | 4           |
turf_id      | uint32       | ID of turf of tile             | 4           |
unknown      | uint32       | Unknown                        | 4           |
count        | uint8        | RLE repeat count               | 1           |
*Total*      |              |                                | 13          |

### Map header
* Start: `header_len`+4
* Start in 507: 46
* Length: 6
* End: `header_len`+10
* End in 507: 52
* Format: binary, little-endian
* Example: `0x0A000A000100`
* Contents:

Content name | Content type | Assigned meaning   | Byte length |
------------ | ------------ | ------------------ | ----------- |
map_x        | uint16       | Map width          | 2           |
map_y        | uint16       | Map height         | 2           |
map_z        | uint16       | Number of Z-levels | 2           |
*Total*      |              |                    | 6           |

### Map tile listing
* Start: `header_len`+10
* Start in 507: 52
* Length: Incalculable. At most, `map_x * map_y * map_z`.
* Format: binary, little-endian`
* Contents:

Content name | Content type | Assigned meaning                     | Byte length       | Multiplicity           |
------------ | ------------ | ------------------------------------ | ----------------- | ---------------------- |
map_tile     | map_tile     | Up to 255 tiles defined at once      | 13                | varying (`tile_types`) |
*Total*      |              |                                      | 13 * `tile_types` |                        |
