# String table encoding

A string table entry has the following structure:

Content name | Content type | Assigned meaning              | Byte length |
------------ | ------------ | ----------------------------- | ----------- |
len          | sum(uint16)  | Length of the string          | n\*2        |
data         | byte[len]    | Data bytes                    | len         |
*Total*      |              |                               | n\*2 + len  |

To calculate the length, do the following algorithm:
* Take note of your position in the file as a 16-bit integer (c)
* Set total length to 0
* While not done reading length:
	* Read 2 bytes
	* Decode the bytes by XORing it with the current position (c) mod 2^16
	* Add the decoded bytes to the total length
	* If the decoded bytes do not equal 65535 (0xFFFF) then we're done reading length
	* Else advance c by 2.

Then for the next total length bytes do the following to gain the string:
* Take note of your position in the file as a 16-bit integer (c) -- this should be the position of the first data byte and will be used as the key.
* Set result stream to an empty byte array
* Repeat total length times:
	* Read 1 byte
	* Decode the byte by XORing it with the current key (c) mod 2^8
	* Append the decoded to the empty byte array.
	* Advance c by 9.
* Resolve control codes within the byte array according to the supplemented control code list.
* Decode the byte array as ISO-8859-1 to gain the decoded string.

For example, consider the string `foo`. The length of this string is 3. The unencrypted byte stream to expect is then: `03 00 66 6f 6f`, where 03 00 is the two byte little endian length value of 3, 66 is the ascii code for `f`, and 6f is the ascii code for `o`.

If the example string is stored starting at memory address 0x00A02841, then the key for this memory address is also 0x00A02841. XOR encryption is a symmetric operation, meaning A xor B xor B = A. Therefore this example can be played out on the encrypted stream as well in order to decrypt it. The example shows how to encrypt the unencrypted stream.

First, take the length component and XOR it with the address to be stored, mod 65536. In essence, this means only the lower 2 bytes are considered. The XOR operation is carried out as if the value is written in big-endian mode. Encrypting the length therefore is `0x0003 XOR 0x2841 = 0000 0000 0000 0011 XOR 0010 1000 0100 0001 = 0010 1000 0100 0010 = 0x2842`. This value is written in little endian form, so the first two bytes in the file should be `42 28`.

Then, the key is advanced by the length of the length component (2 bytes, thus 2), yielding the key 0x2843. Now, for each byte of the string, we encrypt by XORing mod 256 (in other words, only XOR the lowest byte), and then advance the key by 9. These operations in order:

`0x43 XOR 0x66 = 0100 0011 XOR 0110 0110 = 0010 0101 = 0x25, new key = 0x43 + 0x09 = 0x4C`

`0x4C XOR 0x6F = 0100 1100 XOR 0110 1111 = 0010 0011 = 0x23, new key = 0x4C + 0x09 = 0x55`

`0x55 XOR 0x6F = 0101 0101 XOR 0110 1111 = 0011 1010 = 0x3A`

Taking these bytes in order, the final encrypted string is, in hexadecimal bytes: `42 28 25 23 3A`.