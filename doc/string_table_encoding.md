# String table encoding

A string table entry has the following structure:
Content name | Content type | Assigned meaning              | Byte length |
------------ | ------------ | ----------------------------- | ----------- |
len          | sum(uint16)  | Length of the string          | n*2         |
data         | byte[len]    | Data bytes                    | len         |
*Total*      |              |                               | n*2 + len   |

To calculate the length, do the following algorithm:
* Take note of your position in the file as a 16-bit integer (c)
* Set total length to 0
* While not done reading length:
* * Read 2 bytes
* * Decode the bytes by XORing it with the current position (c) mod 2^16
* * Add the decoded bytes to the total length
* * If the decoded bytes do not equal 65535 (0xFFFF) then we're done reading length
* * Else advance c by 2.

Then for the next total length bytes do the following to gain the string:
* Take note of your position in the file as a 16-bit integer (c) -- this should be the position of the first data byte and will be used as the key.
* Set result stream to an empty byte array
* Repeat total length times:
* * Read 1 byte
* * Decode the byte by XORing it with the current key (c) mod 2^8
* * Append the decoded to the empty byte array.
* * Advance c by 9.
* Resolve control codes within the byte array according to the supplemented control code list.
* Decode the byte array as ISO-8859-1 to gain the decoded string.
