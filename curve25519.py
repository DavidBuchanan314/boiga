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

@cat.proc_def("modmul_decode_output")
def modmul_decode_output(locals): return [
	fjoin(locals, locals.out_bits, C),
	bits2hex(locals, locals.out_hex, locals.out_bits)
]

@cat.proc_def("benchmark_modmul")
def benchmark_modmul(locals): return [
	stdout.append("Benchmarking..."),
	init_modmul("5629e6259c8e0cd24b4068fff626f159b9a25f2ea3b93016ca437303b11996b2",
		"5c95420de6c0ecc96a35a2870a5544c0b54f3041abbb9dac24b1f5b06d6cc0ce"),

	locals.bench_start <= millis_now,
	locals.i <= 0,
	repeatuntil((millis_now - locals.bench_start) > 1000, [
		modmul_body(),
		locals.i.changeby(1)
	]),
	stdout.append(Literal("Benchmarked ").join(locals.i).join(" muls/s")),

	modmul_decode_output(),
	stdout.append(modmul_decode_output.out_hex)
]

def int255cpy(dst, src): return [
	dst[i] < src[i]
	for i in range(12)
]

def modmul_copyargs(dst, a, b): return [
	int255cpy(A, a),
	int255cpy(B, b),
	modmul_body(),
	int255cpy(dst, C)
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

	#AskAndWait("hello"),
	#stdout.append(Literal("You said: ").join(Answer())),

	benchmark_modmul()
])

project.save("test.sb3")