from boiga.codegen import Project
from boiga.ast import *

project = Project(template="test_files/Scratch Project.sb3")

cat = project.new_sprite("Sprite1")

stdout = project.stage.new_list("stdout", [])
tmp = (cat.new_var("tmpa"), cat.new_var("tmpb"))
tmp2 = (cat.new_var("tmp2a"), cat.new_var("tmp2b"))
tmp3 = (cat.new_var("tmp3a"), cat.new_var("tmp3b"))
t = cat.new_var("t")
H = (cat.new_list("Ha"), cat.new_list("Hb"))
hex_out = cat.new_list("hex_out")
T1 = (cat.new_var("T1a"), cat.new_var("T1b"))
T2 = (cat.new_var("T2a"), cat.new_var("T2b"))
W = (cat.new_list("Wa"), cat.new_list("Wb"))
W0, W1 = W
ASCII = cat.new_list("ASCII", [chr(x) for x in range(32, 127)][::-1])
XOR_LUT = cat.new_list("XOR_LUT", [a^b for a in range(0x100) for b in range(0x100)])
AND_LUT = cat.new_list("AND_LUT", [a&b for a in range(0x100) for b in range(0x100)])

KCONST = [
	0x428a2f98d728ae22, 0x7137449123ef65cd, 0xb5c0fbcfec4d3b2f, 0xe9b5dba58189dbbc,
	0x3956c25bf348b538, 0x59f111f1b605d019, 0x923f82a4af194f9b, 0xab1c5ed5da6d8118,
	0xd807aa98a3030242, 0x12835b0145706fbe, 0x243185be4ee4b28c, 0x550c7dc3d5ffb4e2,
	0x72be5d74f27b896f, 0x80deb1fe3b1696b1, 0x9bdc06a725c71235, 0xc19bf174cf692694,
	0xe49b69c19ef14ad2, 0xefbe4786384f25e3, 0x0fc19dc68b8cd5b5, 0x240ca1cc77ac9c65,
	0x2de92c6f592b0275, 0x4a7484aa6ea6e483, 0x5cb0a9dcbd41fbd4, 0x76f988da831153b5,
	0x983e5152ee66dfab, 0xa831c66d2db43210, 0xb00327c898fb213f, 0xbf597fc7beef0ee4,
	0xc6e00bf33da88fc2, 0xd5a79147930aa725, 0x06ca6351e003826f, 0x142929670a0e6e70,
	0x27b70a8546d22ffc, 0x2e1b21385c26c926, 0x4d2c6dfc5ac42aed, 0x53380d139d95b3df,
	0x650a73548baf63de, 0x766a0abb3c77b2a8, 0x81c2c92e47edaee6, 0x92722c851482353b,
	0xa2bfe8a14cf10364, 0xa81a664bbc423001, 0xc24b8b70d0f89791, 0xc76c51a30654be30,
	0xd192e819d6ef5218, 0xd69906245565a910, 0xf40e35855771202a, 0x106aa07032bbd1b8,
	0x19a4c116b8d2d0c8, 0x1e376c085141ab53, 0x2748774cdf8eeb99, 0x34b0bcb5e19b48a8,
	0x391c0cb3c5c95a63, 0x4ed8aa4ae3418acb, 0x5b9cca4f7763e373, 0x682e6ff3d6b2b8a3,
	0x748f82ee5defb2fc, 0x78a5636f43172f60, 0x84c87814a1f0ab72, 0x8cc702081a6439ec,
	0x90befffa23631e28, 0xa4506cebde82bde9, 0xbef9a3f7b2c67915, 0xc67178f2e372532b,
	0xca273eceea26619c, 0xd186b8c721c0c207, 0xeada7dd6cde0eb1e, 0xf57d4f7fee6ed178,
	0x06f067aa72176fba, 0x0a637dc5a2c898a6, 0x113f9804bef90dae, 0x1b710b35131c471b,
	0x28db77f523047d84, 0x32caab7b40c72493, 0x3c9ebe0a15c9bebc, 0x431d67c49c100d4c,
	0x4cc5d4becb3e42b6, 0x597f299cfc657e2a, 0x5fcb6fab3ad6faec, 0x6c44198c4a475817
]

K = (
	cat.new_list("Ka", [k&0xffffffff for k in KCONST]),
	cat.new_list("Kb", [k>>32 for k in KCONST])
)

HCONST = [
	0x6a09e667f3bcc908,
	0xbb67ae8584caa73b,
	0x3c6ef372fe94f82b,
	0xa54ff53a5f1d36f1,
	0x510e527fade682d1,
	0x9b05688c2b3e6c1f,
	0x1f83d9abfb41bd6b,
	0x5be0cd19137e2179,
]

initial_H = (
	[h&0xffffffff for h in HCONST],
	[h>>32 for h in HCONST]
)

rtmp = cat.new_var("rtmp")
def rotr(out, x, n): return [
	rtmp <= (x[1] >> n) + ((x[0] % (1<<n)) << (32 - n)),
	out[0] <= (x[0] >> n) + ((x[1] % (1<<n)) << (32 - n)),
	out[1] <= rtmp,
] if n < 32 else [
	rtmp <= (x[1] >> (n-32)) + ((x[0] % (1<<(n-32))) << (64 - n)),
	out[1] <= (x[0] >> (n-32)) + ((x[1] % (1<<(n-32))) << (64 - n)),
	out[0] <= rtmp,
]

def shr(out, x, n): return [
	out[0] <= (x[0] >> n) + ((x[1] % (1<<n)) << (32 - n)),
	out[1] <= (x[1] >> n),
] if n < 32 else [
	out[0] <= (out[1] >> (n-32)),
	out[1] <= 0
]

def _bitneg(x):
	return (Literal(-1) - x) & 0xffffffff

def bitneg(out, x): return [
	out[0] <= _bitneg(x[0]),
	out[1] <= _bitneg(x[1])
]

def _bitxor(a, b, nbits=32):
	result = XOR_LUT[(a&0xff)*256+(b&0xff)]
	for i in range(8, nbits, 8):
		result += XOR_LUT[((a>>i)&0xff)*256+((b>>i)&0xff)] << i
	return result

def bitxor(out, a, b): return [
	out[0] <= _bitxor(a[0], b[0]),
	out[1] <= _bitxor(a[1], b[1])
]

def _bitand(a, b, nbits=32):
	result = AND_LUT[(a&0xff)*256+(b&0xff)]
	for i in range(8, nbits, 8):
		result += AND_LUT[((a>>i)&0xff)*256+((b>>i)&0xff)] << i
	return result

def bitand(out, a, b): return [
	out[0] <= _bitand(a[0], b[0]),
	out[1] <= _bitand(a[1], b[1])
]

# Section 4.1.2 (4.2)
def Ch(x, y, z): return [
	bitneg(tmp, x),
	bitand(tmp, tmp, z),
	bitand(tmp2, x, y),
	bitxor(tmp, tmp, tmp2)
]

# Section 4.1.2 (4.3)
def Maj(x, y, z): return [
	bitand(tmp, x, y),
	bitand(tmp2, x, z),
	bitxor(tmp, tmp, tmp2),
	bitand(tmp2, y, z),
	bitxor(tmp, tmp, tmp2)
]

# Section 4.1.2 (4.4)
def S0(x): return [
	rotr(tmp, x, 28),
	rotr(tmp2, x, 34),
	bitxor(tmp, tmp, tmp2),
	rotr(tmp2, x, 39),
	bitxor(T2, tmp, tmp2),
]

# Section 4.1.2 (4.5)
def S1(x): return [
	rotr(tmp, x, 14),
	rotr(tmp2, x, 18),
	bitxor(tmp, tmp, tmp2),
	rotr(tmp2, x, 41),
	bitxor(tmp, tmp, tmp2),
]

# Section 4.1.2 (4.6)
def s0(x): return [
	rotr(tmp, x, 1),
	rotr(tmp2, x, 8),
	bitxor(tmp, tmp, tmp2),
	shr(tmp2, x, 7),
	bitxor(tmp, tmp, tmp2),
]

# Section 4.1.2 (4.7)
def s1(x): return [
	rotr(tmp, x, 19),
	rotr(tmp2, x, 61),
	bitxor(tmp, tmp, tmp2),
	shr(tmp2, x, 6),
	bitxor(tmp, tmp, tmp2),
]

a = (cat.new_var("a0"), cat.new_var("a1"))
b = (cat.new_var("b0"), cat.new_var("b1"))
c = (cat.new_var("c0"), cat.new_var("c1"))
d = (cat.new_var("d0"), cat.new_var("d1"))
e = (cat.new_var("e0"), cat.new_var("e1"))
f = (cat.new_var("f0"), cat.new_var("f1"))
g = (cat.new_var("g0"), cat.new_var("g1"))
h = (cat.new_var("h0"), cat.new_var("h1"))
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

@cat.proc_def("sha512 [sha512_in]")
def sha512(locals, sha512_in): return [
	H[0].delete_all(),
	H[1].delete_all(),
	W[0].delete_all(),
	W[1].delete_all(),

	ascii_decode(sha512_in),
	hex_out.append(0x80),

	repeatuntil(hex_out.len() == 60, [
		hex_out.append(0)
	]),

	locals.i[:120:8] >> [
		W[1].append(hex_out[locals.i + 3] + (hex_out[locals.i + 2] << 8) + (hex_out[locals.i + 1] << 16) + (hex_out[locals.i] << 24)),
		W[0].append(hex_out[locals.i + 7] + (hex_out[locals.i + 6] << 8) + (hex_out[locals.i + 5] << 16) + (hex_out[locals.i + 4] << 24))
	],

	W[0].append(sha512_in.len() * 8),
	W[1].append(0),

	# 6.2.1, 1) Initialize H
	[
		[
			H[0].append(initial_H[0][i]),
			H[1].append(initial_H[1][i]),
		]
		for i in range(8)
	],

	# 1. Prepare the message schedule
	t[16:80] >> [
		s1((W0[t - 2], W1[t - 2])),
		tmp3[0] <= tmp[0] + W[0][t - 7],
		tmp3[1] <= tmp[1] + W[1][t - 7],
		s0((W0[t - 15], W1[t - 15])),
		tmp3[0] <= tmp3[0] + tmp[0] + W[0][t - 16],
		tmp3[1] <= tmp3[1] + tmp[1] + W[1][t - 16],
		W0.append(tmp3[0] & 0xffffffff),
		W1.append((tmp3[1] + (tmp3[0] >> 32)) & 0xffffffff)
	],

	[
		[
			Hvars[i][0] <= H[0][i],
			Hvars[i][1] <= H[1][i],
		]
		for i in range(8)
	],

	# 3.
	t[:80] >> [
		S1(e),
		T1[0] <= h[0] + tmp[0],
		T1[1] <= h[1] + tmp[1],
		Ch(e, f, g),
		T1[0] <= T1[0] + tmp[0] + K[0][t] + W[0][t],
		T1[1] <= T1[1] + tmp[1] + K[1][t] + W[1][t],

		S0(a),
		#T2[0] <= tmp[0], # XXX: this copy could probably be elided if S0 writes directly to T2
		#T2[1] <= tmp[1],
		Maj(a, b, c),
		T2[0] <= T2[0] + tmp[0],
		T2[1] <= T2[1] + tmp[1],

		h[0] <= g[0],
		h[1] <= g[1],
		g[0] <= f[0],
		g[1] <= f[1],
		f[0] <= e[0],
		f[1] <= e[1],
		e[0] <= (d[0] + T1[0]) & 0xffffffff,
		e[1] <= (d[1] + T1[1] + ( (d[0] + T1[0]) >> 32 )) & 0xffffffff,
		d[0] <= c[0],
		d[1] <= c[1],
		c[0] <= b[0],
		c[1] <= b[1],
		b[0] <= a[0],
		b[1] <= a[1],
		a[0] <= (T1[0] + T2[0]) & 0xffffffff,
		a[1] <= (T1[1] + T2[1] + ( (T1[0] + T2[0]) >> 32 )) & 0xffffffff
	],

	# 4. Calculate the next Hash value
	[
		[
			H[1][i] <= (H[1][i] + Hvars[i][1] + ( (H[0][i] + Hvars[i][0]) >> 32 )) & 0xffffffff,
			H[0][i] <= (H[0][i] + Hvars[i][0]) & 0xffffffff,
		]
		for i in range(8)
	],

	# hexlify the output
	locals.out <= "",
	t[:8] >> ([
		locals.out <= locals.out.join(Literal("0123456789abcdef")[(H[1][t] >> i) & 0xf])
		for i in range(0, 32, 4)[::-1]
	]+[
		locals.out <= locals.out.join(Literal("0123456789abcdef")[(H[0][t] >> i) & 0xf])
		for i in range(0, 32, 4)[::-1]
	])
]

@cat.proc_def("benchmark_sha512")
def benchmark_sha512(locals): return [
	stdout.append("Benchmarking..."),
	locals.bench_start <= millis_now,
	locals.i <= 0,
	repeatuntil((millis_now - locals.bench_start) > 1000, [
		sha512(Literal("hello").join(locals.i)),
		locals.i.changeby(1)
	]),
	stdout.append(Literal("Benchmarked ").join(locals.i).join("H/s"))
]

cat.on_flag([
	stdout.delete_all(),
	benchmark_sha512(),
	sha512("hello"),
	stdout.append(sha512.out),
])

project.save("test.sb3")