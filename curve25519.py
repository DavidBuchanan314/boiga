from boiga.codegen import Project
from boiga.ast import *

import math

project = Project(template="test_files/Scratch Project.sb3")

cat = project.new_sprite("Sprite1")

stdout = project.stage.new_list("stdout", [])
tmp = cat.new_var("tmp")
tmp2 = cat.new_var("tmp2")
tmp3 = cat.new_var("tmp3")
HEXBITS = cat.new_list("HEXBITS", [f"{i:04b}"[::-1] for i in range(16)])
A = cat.new_list("A")
B = cat.new_list("B")
C = cat.new_list("C")

radices = [2**22, 2**21, 2**21, 2**21] * 6
rtotals = []
for i in range(len(radices)):
	rtotal = 1
	for r in radices[:i]:
		rtotal *= r
	rtotals.append(rtotal)

RADICES = cat.new_list("RADICES", [22, 21, 21, 21] * 6)
RTOTALS = cat.new_list("RTOTALS", rtotals)

# hex string to binary int, with least-significant bit first
def bitstringify(locals, out, inp): return [
	out <= "",
	locals.i[:inp.len()] >> [
		out <= out.join( HEXBITS[Literal("0x").join(inp[inp.len()-locals.i-1])] )
	]
]

def fsplit(locals, out, inp): return [
	out.delete_all(),
	locals.bitindex <= 0,
	locals.i[:12] >> [
		locals.tmp <= 0,
		locals.shift <= 1,
		locals.j[:Literal(21)+((locals.i%4)==0)] >> [
			locals.tmp.changeby(inp[locals.bitindex]*locals.shift),
			locals.shift <= locals.shift * 2,
			locals.bitindex.changeby(1)
		],
		out.append(locals.tmp * RTOTALS[locals.i])
	]
]

"""
def realjoin(floats):
	res = 0
	shiftinator = 1
	for i in range(12):
		blah = int(floats[i] / rtotals[i])
		res |= blah * shiftinator
		shiftinator *= radices[i]
	return res
"""
def fjoin(locals, out, inp): return [
	out <= "",
	locals.i[:12] >> [
		locals.blah <= inp[locals.i] / RTOTALS[locals.i],
		locals.shift <= 1,
		locals.j[:RADICES[locals.i]] >> [
			out <= out.join((locals.blah // locals.shift) & 1),
			locals.shift <= locals.shift * 2
		]
	]
]

def bits2hex(locals, out, inp): return [
	out <= "",
	locals.i[:256:4] >> [
		out <= Literal("0123456789abcdef")[sumchain([
			inp[locals.i + j] << j
			for j in range(4)
		])].join(out)
	]
]

def textbook_mul(out, x, y): return [
	out.append(sumchain([
		x[i - j] * y[j]
		for j in range(
			max(0,  i + 1 - 12),
			min(12, i + 1)
		)
	]))
	for i in range(23)
]

def textbook_square(out, x):
	code = []
	for i in range(23):
		start = max(0,  i + 1 - 12)
		stop  = min(12, i + 1)
		dist = stop - start
		if dist & 1:
			if dist > 1:
				code.append(out.append(sumchain([
					x[i - j] * x[j]
					for j in range(start, start + dist // 2)
				]) * 2 + x[start+dist//2] * x[start+dist//2]))
			else:
				code.append(out.append(sumchain([
					x[i - j] * x[j]
					for j in range(
						max(0,  i + 1 - 12),
						min(12, i + 1)
					)
				])))
		else:
			code.append(out.append(sumchain([
				x[i - j] * x[j]
				for j in range(start, start + dist // 2)
			]) * 2))
	return code

def carry_from(locals, arr, i):
	r = 2.0**math.ceil((i+1)*21.25)
	return [
		#locals.carry <= arr[i] - (arr[i] % r), # TODO: don't use variable?
		#arr[i+1] <= arr[i+1] + locals.carry,
		#arr[i] <= arr[i] - locals.carry,

		# unsure which version is faster
		arr[i+1] <= arr[i+1] + (arr[i] - (arr[i] % r)),
		arr[i] <= arr[i] - (arr[i] - (arr[i] % r)), # note, order of operations is very important here
	]

@cat.proc_def("init_modmul [a] [b]")
def init_modmul(locals, a, b): return [
	bitstringify(locals, locals.abits, a),
	fsplit(locals, A, locals.abits),
	bitstringify(locals, locals.bbits, b),
	fsplit(locals, B, locals.bbits),
]

@cat.proc_def("modmul_body")
def modmul_body(locals): return [
	C.delete_all(),
	textbook_mul(C, A, B),

	carry_from(locals, C, 10),
	carry_from(locals, C, 11),

	[
		[
			C[i-12] <= C[i-12] + (C[i] * (19.0*(2**-255))),
			C[i] <= 0.0
		]
		for i in range(12, 23)
	],

	[
		carry_from(locals, C, i)
		for i in range(11)
	],

	carry_from(locals, C, 11),
	C[0] <= C[0] + (C[12] * (19.0*(2**-255))),
]


@cat.proc_def("modmul_square_body")
def modmul_square_body(locals): return [
	C.delete_all(),
	textbook_square(C, A),

	carry_from(locals, C, 10),
	carry_from(locals, C, 11),

	[
		[
			C[i-12] <= C[i-12] + (C[i] * (19.0*(2**-255))),
			C[i] <= 0.0
		]
		for i in range(12, 23)
	],

	[
		carry_from(locals, C, i)
		for i in range(11)
	],

	carry_from(locals, C, 11),
	C[0] <= C[0] + (C[12] * (19.0*(2**-255))),
]

@cat.proc_def("modmul_decode_output")
def modmul_decode_output(locals): return [
	fjoin(locals, locals.out_bits, C),
	bits2hex(locals, locals.out_hex, locals.out_bits)
]

if 1:
	def int255cpy(dst, src): return [
		dst[i] <= src[i]
		for i in range(12)
	]

	def int255add(dst, src_a, src_b): return [
		dst[i] <= src_a[i] + src_b[i]
		for i in range(12)
	]

	def int255sub(dst, src_a, src_b): return [
		dst[i] <= src_a[i] - src_b[i]
		for i in range(12)
	]
else:
	cpi = cat.new_var("cpi")
	def int255cpy(dst, src): return [
		cpi[:12] >> [
			dst[cpi] <= src[cpi]
		]
	]

	def int255add(dst, src_a, src_b): return [
		cpi[:12] >> [
			dst[cpi] <= src_a[cpi] + src_b[cpi]
		]
	]

	def int255sub(dst, src_a, src_b): return [
		cpi[:12] >> [
			dst[cpi] <= src_a[cpi] - src_b[cpi]
		]
	]

def modmul_copyargs(dst, a, b): return [
	int255cpy(A, a),
	int255cpy(B, b),
	modmul_body(),
	int255cpy(dst, C)
]

def modmul_square_copyargs(dst, a): return [
	int255cpy(A, a),
	modmul_square_body(),
	int255cpy(dst, C)
]


inv_tmp = cat.new_list("INV_TMP", [0]*12)
# input: A, output C
@cat.proc_def("x25519_invert")
def x25519_invert(locals): return [
	int255cpy(inv_tmp, A), # copy of input
	int255cpy(C, A), # c = accumulator
	locals.i[253:-1:-1] >> [
		int255cpy(A, C),
		modmul_square_body(), # C = C * C
		IF ((locals.i != 2).AND(locals.i != 4)) [
			int255cpy(A, C),
			int255cpy(B, inv_tmp),
			modmul_body(), # C = C * inv_tmp
		]
	]
]

# this is like, vaguely constant-time, probably
if 0:
	def cswap(locals, swap, a, b): return [
		locals.swapi[:12] >> [
			locals.swaptmp <= (a[locals.swapi] * swap) + (b[locals.swapi] * (Literal(1) - swap)),
			a[locals.swapi] <= (b[locals.swapi] * swap) + (a[locals.swapi] * (Literal(1) - swap)),
			b[locals.swapi] <= locals.swaptmp
		]
	]
else:
	def cswap(locals, swap, a, b): return [
		[
			locals.swaptmp <= (a[i] * swap) + (b[i] * (Literal(1) - swap)),
			a[i] <= (b[i] * swap) + (a[i] * (Literal(1) - swap)),
			b[i] <= locals.swaptmp
		] for i in range(12)
	]

"""
def X25519(k, u):
	x_1 = u
	x_2 = 1
	z_2 = 0
	x_3 = u
	z_3 = 1
	swap = 0

	for t in range(255)[::-1]:
		k_t = (k >> t) & 1
		swap ^= k_t
		x_2, x_3 = cswap(swap, x_2, x_3)
		z_2, z_3 = cswap(swap, z_2, z_3)
		swap = k_t

		A = x_2 + z_2
		AA = pow(A, 2, p)
		B = x_2 - z_2
		BB = pow(B, 2, p)
		E = AA - BB
		C = x_3 + z_3
		D = x_3 - z_3
		DA = (D * A) % p
		CB = (C * B) % p
		x_3 = pow(DA + CB, 2, p)
		z_3 = (x_1 * pow(DA - CB, 2, p)) % p
		x_2 = (AA * BB) % p
		z_2 = (E * (AA + ((121665 * E) % p))) % p

	x_2, x_3 = cswap(swap, x_2, x_3)
	z_2, z_3 = cswap(swap, z_2, z_3)
	return (x_2 * pow(z_2, p - 2, p)) % p
"""

x_1 = cat.new_list("X_1", [0]*12)
x_2 = cat.new_list("X_2", [0]*12)
z_2 = cat.new_list("Z_2", [0]*12)
x_3 = cat.new_list("X_3", [0]*12)
z_3 = cat.new_list("Z_3", [0]*12)

CONST_121665 = cat.new_list("CONST_121665", [121665, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

smA = cat.new_list("smA", [0]*12)
smB = cat.new_list("smB", [0]*12)

smAA = cat.new_list("smAA", [0]*12)
smBB = cat.new_list("smBB", [0]*12)

smE = cat.new_list("smE", [0]*12)
smC = cat.new_list("smC", [0]*12)
smD = cat.new_list("smD", [0]*12)

smDA = cat.new_list("smDA", [0]*12)
smCB = cat.new_list("smCB", [0]*12)


@cat.proc_def("x25519_scalarmult [scalar] [element]")
def x25519_scalarmult(locals, scalar, element): return [

	# TODO: decodeScalar25519

	bitstringify(locals, locals.scalarbits, scalar),
	bitstringify(locals, locals.elementbits, element),
	fsplit(locals, x_1, locals.elementbits),

	locals.i[1:12] >> [
		x_2[locals.i] <= 0
	],
	x_2[0] <= 1,

	locals.i[:12] >> [
		z_2[locals.i] <= 0
	],

	int255cpy(x_3, x_1),

	locals.i[1:12] >> [
		z_3[locals.i] <= 0
	],
	z_3[0] <= 1,

	locals.swap <= 0,

	locals.t[:255] >> [
		locals.k_t <= locals.scalarbits[Literal(254)-locals.t],
		locals.swap <= (locals.swap + locals.k_t) % 2,
		cswap(locals, locals.swap, x_2, x_3),
		cswap(locals, locals.swap, z_2, z_3),
		locals.swap <= locals.k_t,

		int255add(smA, x_2, z_2),
		modmul_square_copyargs(smAA, smA),

		int255sub(smB, x_2, z_2),
		modmul_square_copyargs(smBB, smB),

		int255sub(smE, smAA, smBB),
		int255add(smC, x_3, z_3),
		int255sub(smD, x_3, z_3),

		modmul_copyargs(smDA, smD, smA),
		modmul_copyargs(smCB, smC, smB),

		int255add(x_3, smDA, smCB),
		modmul_square_copyargs(x_3, x_3),

		int255sub(z_3, smDA, smCB),
		modmul_copyargs(z_3, z_3, z_3),
		modmul_copyargs(z_3, z_3, x_1),

		modmul_copyargs(x_2, smAA, smBB),

		modmul_copyargs(smBB, CONST_121665, smE), # using smBB as tmp here
		int255add(smAA, smAA, smBB),
		modmul_copyargs(z_2, smE, smAA),
	],

	cswap(locals, locals.swap, x_2, x_3),
	cswap(locals, locals.swap, z_2, z_3),

	int255cpy(A, z_2),
	x25519_invert(),

	int255cpy(A, C),
	int255cpy(B, x_2),
	modmul_body(),

	modmul_decode_output(),
	locals.out_hex <= modmul_decode_output.out_hex
]


@cat.proc_def("benchmark_modmul")
def benchmark_modmul(locals): return [
	stdout.append("Benchmarking..."),
	init_modmul("5629e6259c8e0cd24b4068fff626f159b9a25f2ea3b93016ca437303b11996b2",
		"5c95420de6c0ecc96a35a2870a5544c0b54f3041abbb9dac24b1f5b06d6cc0ce"),

	locals.bench_start <= millis_now,
	locals.i <= 0,
	repeatuntil((millis_now - locals.bench_start) > 1000, [
		#modmul_body(),
		modmul_copyargs(C, A, B),
		locals.i.changeby(1)
	]),
	stdout.append(Literal("Benchmarked ").join(locals.i).join(" muls/s")),

	modmul_decode_output(),
	stdout.append(modmul_decode_output.out_hex)
]

@cat.proc_def("benchmark_x25519_scalarmult")
def benchmark_x25519_scalarmult(locals): return [
	locals.bench_start <= millis_now,
	locals.a <= "449a44ba44226a50185afcc10a4c1462dd5e46824b15163b9d7c52f06be346a0",
	locals.b <= "4c1cabd0a603a9103b35b326ec2466727c5fb124a4c19435db3030586768dbe6",
	stdout.append(""),
	stdout.append("a ="),
	stdout.append(locals.a),
	stdout.append("b ="),
	stdout.append(locals.b),
	x25519_scalarmult(locals.a, locals.b),
	stdout.append("x25519_scalarmult(a, b) ="),
	stdout.append(x25519_scalarmult.out_hex),
	stdout.append(Literal("Completed in ").join(millis_now - locals.bench_start).join("ms")),
]



a = cat.new_var("a")
b = cat.new_var("b")

cat.on_flag([
	stdout.delete_all(),
	stdout.append("Test:"),
	a <= "5629e6259c8e0cd24b4068fff626f159b9a25f2ea3b93016ca437303b11996b2",
	b <= "5c95420de6c0ecc96a35a2870a5544c0b54f3041abbb9dac24b1f5b06d6cc0ce",
	stdout.append("a ="),
	stdout.append(a),
	stdout.append("b ="),
	stdout.append(b),
	init_modmul(a, b),
	modmul_body(),
	modmul_decode_output(),
	stdout.append("(a * b) % (2^225-19) ="),
	stdout.append(modmul_decode_output.out_hex),

	init_modmul(a, b),
	x25519_invert(),
	modmul_decode_output(),

	stdout.append("pow(a, -1, 2^225-19) ="),
	stdout.append(modmul_decode_output.out_hex),

	benchmark_x25519_scalarmult()

	#AskAndWait("hello"),
	#stdout.append(Literal("You said: ").join(Answer())),

	#benchmark_modmul()
])

project.save("test.sb3")
