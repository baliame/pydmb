# String control codes

Control codes will appear in strings in the string table according to different text macros that DM uses. This is a translation table between the control codes and the actual macroes.

Each control code consists of two bytes. The first byte is `0xFF`, and the second byte determines the macro being used.

Second byte | Text macro | Note                                                                 |
----------- | ---------- | -------------------------------------------------------------------- |
0x01        | [var]      | Used if 'the' should be inserted before the name if it is a ref.     |
0x02        | [var]      | Used if 'The' should be inserted before the name if it is a ref.     |
0x03        | [var]      | Used if 'the' should not be inserted before the name if it is a ref. |
0x06        | \a         |                                                                      |
0x07        | \A         |                                                                      |
0x08        | \the       |                                                                      |
0x09        | \The       |                                                                      |
0x0a        | \he        |                                                                      |
0x0b        | \He        |                                                                      |
0x0c        | \his       |                                                                      |
0x0d        | \His       |                                                                      |
0x10        | \him       |                                                                      |
0x11        | \himself   |                                                                      |
0x12        | \...       |                                                                      |
0x14        | \s         |                                                                      |
0x15        | \proper    |                                                                      |
0x16        | \improper  |                                                                      |
0x17        | \bold      |                                                                      |
0x18        | \italic    |                                                                      |
0x19        | \underline |                                                                      |
0x1b        | \font      |                                                                      |
0x1c        | \color     |                                                                      |
0x1f        | \red       |                                                                      |
0x20        | \green     |                                                                      |
0x21        | \blue      |                                                                      |
0x22        | \black     |                                                                      |
0x23        | \white     |                                                                      |
0x24        | \yellow    |                                                                      |
0x25        | \cyan      |                                                                      |
0x26        | \magenta   |                                                                      |
0x27        | \beep      |                                                                      |
0x28        | \link      |                                                                      |
0x2a        | \ref       |                                                                      |
0x2b        | \icon      |                                                                      |
