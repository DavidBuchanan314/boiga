from boiga.codegen import Project
from boiga.ast import *

import struct

project = Project(template="test_files/Scratch Project.sb3")

cat = project.new_sprite("Sprite1")

stdout = project.stage.new_list("stdout", [], monitor=[0, 0, 480-2, 292])
tmp = cat.new_var("tmp")
tmp2 = cat.new_var("tmp2")
tmp3 = cat.new_var("tmp3")

HEX_LUT = cat.new_list("HEX_LUT", [f"{x:02x}" for x in range(0x100)])



def rotr(x, n, nbits=32):
	return (x >> n) + ((x % (1<<n)) << (nbits - n))

def rotl(x, n, nbits=32):
	return rotr(x, nbits-n, nbits)

# note: we can elide the "+1" required to adjust for 1-indexing by simply chopping off the
# first entry of the table. Looking up the 0th item of a scratch array returns "", which is zero-ish
# when used in subsequent math ops
# note also: the array index ends up with a -1+1 on the end, which the ast optimisation pass strips out
XOR_LUT = cat.new_list("XOR_LUT", [a^b for a in range(0x100) for b in range(0x100)][1:])
def bitxor(a, b, nbits=32):
	result = XOR_LUT[(a&0xff)*256+(b&0xff)-1]
	for i in range(8, nbits, 8):
		result += XOR_LUT[((a>>i)&0xff)*256+((b>>i)&0xff)-1] << i
	return result

"""
CHACHA20 CSPRNG

Design goals:

Compact code
Reasonable perf
Reasonable security
"""

CHACHA20_INIT_STATE = list(struct.unpack("<IIII", b"expand 32-byte k")) + [0]*12
rng_state = cat.new_list("rng_state", CHACHA20_INIT_STATE)
rng_tmp = cat.new_list("rng_tmp", [])
QR_OFFSETS = [
	#  Odd round
	0, 4,  8, 12,  # 1st column
	1, 5,  9, 13,  # 2nd column
	2, 6, 10, 14,  # 3rd column
	3, 7, 11, 15,  # 4th column
	# Even round
	0, 5, 10, 15,  # diagonal 1 (main diagonal)
	1, 6, 11, 12,  # diagonal 2
	2, 7,  8, 13,  # diagonal 3
	3, 4,  9, 14,  # diagonal 4
]
magic = []
for i in range(0, len(QR_OFFSETS), 4):
	a, b, c, d = [x+1 for x in QR_OFFSETS[i:i+4]]
	magic += [a, b, d, 2**16, 2**(32-16)]
	magic += [c, d, b, 2**12, 2**(32-12)]
	magic += [a, b, d, 2**8, 2**(32-8)]
	magic += [c, d, b, 2**7, 2**(32-7)]

RNG_LUT = cat.new_list("RNG_LUT", magic)

@cat.proc_def("chacha20_rng_core")
def chacha20_rng_core(locals): return [
		locals.i[4+1:12+1] >> [
			rng_state[locals.i-1] <= (rng_state[locals.i-1] + pickrandom(0, 0xffff_ffff)) & 0xffff_ffff
		],
		rng_tmp.delete_all(),
		locals.i[1:16+1] >> [
			rng_tmp.append(rng_state[locals.i-1])
		],
		locals.i <= 0,
		repeatn(20*4*4) [
			tmp <= rng_tmp[RNG_LUT[locals.i+2]-1],

			tmp2 <= (rng_tmp[RNG_LUT[locals.i+0]-1] + rng_tmp[RNG_LUT[locals.i+1]-1]) & 0xffff_ffff,
			tmp <= bitxor(tmp, tmp2),
			rng_tmp[RNG_LUT[locals.i+2]-1] <= (tmp // RNG_LUT[locals.i+4]) + ((tmp % RNG_LUT[locals.i+4]) * RNG_LUT[locals.i+3]),
			rng_tmp[RNG_LUT[locals.i+0]-1] <= tmp2,

			locals.i <= (locals.i + 5) % len(magic),
		],
		locals.i[1:16+1] >> [
			rng_tmp[locals.i-1] <= (rng_tmp[locals.i-1] + rng_state[locals.i-1]) & 0xffff_ffff
		],
		rng_state[12] <= rng_state[12] + 1, # probably safe to assume this will never overflow, in a scratch project
		rng_state[13] <= rng_tmp[13], # feed output back into the nonce, preventing retroactive compromise
		rng_state[14] <= rng_tmp[14],
		rng_state[15] <= rng_tmp[15],
	]


@cat.proc_def("rng_add_entropy")
def rng_add_entropy(locals): return [
	locals.i[4:12] >> [
		locals.shift <= 1,
		repeatn (32) [
			locals.counter <= 0,
			repeatuntil (locals.counter > 100) [
				locals.start <= DaysSince2k(),
				repeatuntil(DaysSince2k() > locals.start) [
					locals.counter <= locals.counter + 1
				]
			],
			rng_state[locals.i] <= (rng_state[locals.i] + locals.counter * locals.shift) & 0xffff_ffff,
			locals.shift <= locals.shift * 2,
		]
	],
]

@cat.proc_def("rng_init")
def rng_init(locals): return [
	rng_state.delete_all(),
	[
		rng_state.append(CHACHA20_INIT_STATE[i])
		for i in range(4)
	],
	repeatn (12) [
		rng_state.append(0),
	],
	rng_add_entropy(),
]

rng_bytes_out = cat.new_list("rng_bytes_out", [])
@cat.proc_def("rng_get_bytes [length]")
def rng_get_bytes(locals, length): return [
	rng_bytes_out.delete_all(),
	repeatn (math.ceil(length/64)) [
		chacha20_rng_core(),
		locals.i[:16] >> [
			rng_bytes_out.append(rng_tmp[locals.i] & 0xff),
			rng_bytes_out.append((rng_tmp[locals.i] >> 8) & 0xff),
			rng_bytes_out.append((rng_tmp[locals.i] >> 16) & 0xff),
			rng_bytes_out.append((rng_tmp[locals.i] >> 24) & 0xff)
		]
	],
	repeatuntil (rng_bytes_out.len() == length) [
		rng_bytes_out.delete_at(rng_bytes_out.len() - 1)
	]
]

rng_hex_out = cat.new_var("rng_hex_out")
@cat.proc_def("rng_get_hex [length]")
def rng_get_hex(locals, length): return [
	rng_get_bytes(length),
	rng_hex_out <= "",
	locals.i[:length] >> [
		rng_hex_out <= rng_hex_out.join(HEX_LUT[rng_bytes_out[locals.i]])
	]
]

cat.on_flag([
	stdout.delete_all(),
	stdout.append("Initialising entropy pool..."),

	Wait(0),

	rng_init(),

	stdout.append("Done! Generating 10 random bytes..."),

	rng_get_hex(10),
	stdout.append(rng_hex_out),

	stdout.append("Done! Generating 64 random bytes..."),

	rng_get_hex(64),
	stdout.append(rng_hex_out),

	stdout.append("Done! Generating 4096 random bytes..."),

	rng_get_hex(4096),
	stdout.append(rng_hex_out),

	stdout.append("Done!"),

	AskAndWait(),
])

project.save("test.sb3", execute=False)

"""
from Crypto.Cipher import ChaCha20
foo = ChaCha20.new(key=bytes(32), nonce=bytes(12))
res = foo.encrypt(bytes(128))
import struct
print(struct.unpack("<IIIIIIIIIIIIIIII", res[:64]))
print(struct.unpack("<IIIIIIIIIIIIIIII", res[64:]))
"""
