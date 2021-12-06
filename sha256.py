from boiga.codegen import Project
from boiga.ast import *

project = Project(template="test_files/Scratch Project.sb3")

cat = project.new_sprite("Sprite1")

stdout = project.stage.new_list("stdout", [])
tmp = cat.new_var("tmp", 123)
tmp2 = cat.new_var("tmp2", 123)
tmp3 = cat.new_var("tmp3", 123)
t = cat.new_var("t", 123)
H = cat.new_list("H")
hex_out = cat.new_list("hex_out")
T1 = cat.new_var("T1")
T2 = cat.new_var("T2")
W = cat.new_list("W")
ASCII = cat.new_list("ASCII", ([""]*32 + [chr(x) for x in range(32, 127)])[::-1])
XOR_LUT = cat.new_list("XOR_LUT", [a^b for a in range(0x100) for b in range(0x100)])
AND_LUT = cat.new_list("AND_LUT", [a&b for a in range(0x100) for b in range(0x100)])

K = cat.new_list("K", [
	0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
	0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
	0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
	0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
	0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
	0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
	0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
	0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
])

initial_H = [
	0x6a09e667,
	0xbb67ae85,
	0x3c6ef372,
	0xa54ff53a,
	0x510e527f,
	0x9b05688c,
	0x1f83d9ab,
	0x5be0cd19,
]

def rotr(x, n, nbits=32):
	return (x >> n) + ((x % (1<<n)) << (nbits - n))

def shr(x, n):
	return x >> n

def bitneg(x):
	return (Literal(-1) - x) & 0xffffffff

"""
def bitxor(a, b, nbits=32):
	result = (a + b) & 1
	for i in range(1, nbits):
		result += (((a>>i)+(b>>i))&1) << i
	return result
"""
def bitxor(a, b, nbits=32):
	result = XOR_LUT[(a&0xff)*256+(b&0xff)]
	for i in range(8, nbits, 8):
		result += XOR_LUT[((a>>i)&0xff)*256+((b>>i)&0xff)] << i
	return result

"""
def bitand(a, b, nbits=32):
	result = (a&1) * (b&1)
	for i in range(1, nbits):
		result += ((((a>>i)&1)*((b>>i)&1))) << i
	return result
"""
def bitand(a, b, nbits=32):
	result = AND_LUT[(a&0xff)*256+(b&0xff)]
	for i in range(8, nbits, 8):
		result += AND_LUT[((a>>i)&0xff)*256+((b>>i)&0xff)] << i
	return result

# Section 4.1.2 (4.2)
def Ch(x, y, z): return [
	tmp <= bitneg(x),
	tmp <= bitand(tmp, z),
	tmp2 <= bitand(x, y),
	tmp <= bitxor(tmp, tmp2)
]

# Section 4.1.2 (4.3)
def Maj(x, y, z): return [
	tmp <= bitand(x, y),
	tmp2 <= bitand(x, z),
	tmp <= bitxor(tmp, tmp2),
	tmp2 <= bitand(y, z),
	tmp <= bitxor(tmp, tmp2)
]

# Section 4.1.2 (4.4)
def S0(x): return [
	tmp <= rotr(x, 2),
	tmp2 <= rotr(x, 13),
	tmp <= bitxor(tmp, tmp2),
	tmp2 <= rotr(x, 22),
	tmp <= bitxor(tmp, tmp2),
]

# Section 4.1.2 (4.5)
def S1(x): return [
	tmp <= rotr(x, 6),
	tmp2 <= rotr(x, 11),
	tmp <= bitxor(tmp, tmp2),
	tmp2 <= rotr(x, 25),
	tmp <= bitxor(tmp, tmp2),
]

# Section 4.1.2 (4.6)
def s0(x): return [
	tmp <= rotr(x, 7),
	tmp2 <= rotr(x, 18),
	tmp <= bitxor(tmp, tmp2),
	tmp2 <= shr(x, 3),
	tmp <= bitxor(tmp, tmp2),
]

# Section 4.1.2 (4.7)
def s1(x): return [
	tmp <= rotr(x, 17),
	tmp2 <= rotr(x, 19),
	tmp <= bitxor(tmp, tmp2),
	tmp2 <= shr(x, 10),
	tmp <= bitxor(tmp, tmp2),
]

a = cat.new_var("a")
b = cat.new_var("b")
c = cat.new_var("c")
d = cat.new_var("d")
e = cat.new_var("e")
f = cat.new_var("f")
g = cat.new_var("g")
h = cat.new_var("h")
Hvars = [a, b, c, d, e, f, g, h]

@cat.proc_def("hex decode [hex_in]")
def hex_decode(locals, hex_in): return [
	hex_out.delete_all(),
	locals.i[:hex_in.len():2] >> [
		hex_out.append( Literal("0x").join(hex_in[locals.i]).join(hex_in[locals.i+1]) + 0 )
	]
]

@cat.proc_def("ascii decode [ascii_in]")
def ascii_decode(locals, ascii_in): return [
	hex_out.delete_all(),
	locals.i[:ascii_in.len()] >> [
		hex_out.append(Literal(126)-ASCII.index(ascii_in[locals.i]))
	]
]

@cat.proc_def("sha256 [sha256_in]")
def sha256(locals, sha256_in): return [
	H.delete_all(),
	W.delete_all(),

	ascii_decode(sha256_in),
	hex_out.append(0x80),

	repeatuntil(hex_out.len() == 60, [
		hex_out.append(0)
	]),

	locals.i[:60:4] >> [
		W.append(hex_out[locals.i+3] + (hex_out[locals.i+2] << 8) + (hex_out[locals.i+1] << 16) + (hex_out[locals.i] << 24))
	],

	W.append(sha256_in.len() * 8),

	# 6.2.1, 1) Initialize H
	[ H.append(initial_H[i]) for i in range(8) ],

	# 1. Prepare the message schedule
	t[16:64] >> [
		s1(W[t-2]),
		tmp3 <= tmp + W[t-7],
		s0(W[t-15]),
		tmp3 <= tmp3 + tmp + W[t-16],
		W.append(tmp3 & 0xffffffff)
	],

	[ Hvars[i] <= H[i] for i in range(8) ],

	# 3.
	t[:64] >> [
		S1(e),
		T1 <= h + tmp,
		Ch(e, f, g),
		T1 <= T1 + tmp + K[t] + W[t],

		S0(a),
		T2 <= tmp,
		Maj(a, b, c),
		T2 <= T2 + tmp,

		h <= g,
		g <= f,
		f <= e,
		e <= (d + T1) & 0xffffffff,
		d <= c,
		c <= b,
		b <= a,
		a <= (T1 + T2) & 0xffffffff
	],

	# 4. Calculate the next Hash value
	[ H[i] <= (H[i] + Hvars[i]) & 0xffffffff for i in range(8) ],

	# hexlify the output
	locals.out <= "",
	t[:8] >> [
		[
			locals.out <= locals.out.join(Literal("0123456789abcdef")[(H[t]>>i)&0xf])
			for i in range(0, 32, 4)[::-1]
		]
	]
]

cat.on_flag([
	stdout.delete_all(),
	stdout.append("OUTPUT:"),
	sha256("hello"),
	stdout.append(sha256.out),
])

project.save("test.sb3")