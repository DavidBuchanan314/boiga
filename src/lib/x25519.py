from boiga.codegen import Project
from boiga.ast import *

import math

class X25519():
	BASE_POINT = "0900000000000000000000000000000000000000000000000000000000000000"
	
	def __init__(self, cat, utils, testing=False):
		tmp = cat.new_var("tmp25519")

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
		RTOTALS = cat.new_list("RTOTALS", [float(x) for x in rtotals])

		# hex string to binary int, with least-significant bit first
		def bitstringify(locals, out, inp): return [
			out <= "",
			locals.i[:inp.len()] >> [
				out <= out.join( HEXBITS[Literal("0x").join(inp[inp.len()-locals.i-1])] )
			]
		]

		# input little-endian hex, output binary int string, lsb first
		def bitstringify_le(locals, out, inp): return [
			out <= "",
			locals.i[:inp.len():2] >> [
				out <= out.join( HEXBITS[Literal("0x").join(inp[locals.i + 1])] ).join( HEXBITS[Literal("0x").join(inp[locals.i])] )
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

		def fjoin(locals, out, inp): return [
			out <= "",
			locals.i[1:12+1] >> [
				locals.blah <= inp[locals.i-1] / RTOTALS[locals.i-1],
				locals.shift <= 1,
				locals.j[:RADICES[locals.i-1]] >> [
					out <= out.join((locals.blah // locals.shift) & 1),
					locals.shift <= locals.shift * 2
				]
			]
		]

		def fjoin_hex_le(locals, out, inp): return [
			out <= "",
			locals.bytebuf <= 0,
			locals.bitshift <= 1,
			locals.i[1:12+1] >> [
				locals.blah <= inp[locals.i-1] / RTOTALS[locals.i-1],
				locals.shift <= 1,
				locals.j[:RADICES[locals.i-1]] >> [
					locals.bytebuf.changeby( ((locals.blah // locals.shift) & 1) * locals.bitshift ),
					locals.bitshift.changeby(locals.bitshift),
					IF (locals.bitshift == 1<<8) [
						locals.bitshift <= 1,
						out <= out.join(utils.HEX_LUT[locals.bytebuf]),
						locals.bytebuf <= 0
					],
					locals.shift <= locals.shift * 2
				]
			],
			out <= out.join(utils.HEX_LUT[locals.bytebuf]),
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

		def bits2hex_le(locals, out, inp): return [
			out <= "",
			locals.i[:256:8] >> [
				locals.hextmp <= 0,
				locals.j[:8] >> [
					locals.hextmp <= locals.hextmp * 2 + inp[locals.i-locals.j+7]
				],
				out <= out.join(utils.HEX_LUT[locals.hextmp])
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

		@cat.proc_def("modmul_body", turbo=True)
		def modmul_body(locals): return [
			C.delete_all(),
			textbook_mul(C, A, B),

			carry_from(locals, C, 10),
			carry_from(locals, C, 11),

			[
				[
					C[i-12] <= C[i-12] + (C[i] * (19.0*(2**-255))),
					#C[i] <= 0.0
				]
				for i in range(12, 23)
			],
			#C[12] <= 0.0,

			[
				carry_from(locals, C, i)
				for i in range(11)
			],

			#carry_from(locals, C, 11),
			tmp <= (C[11] - (C[11] % rtotals[11+1])),
			C[11] <= C[11] - (C[11] - (C[11] % rtotals[11+1])),
			C[0] <= C[0] + (tmp * (19.0*(2**-255))),
		]

		if testing:
			@cat.proc_def("modmul_decode_output")
			def modmul_decode_output(locals): return [
				fjoin(locals, locals.out_bits, C),
				bits2hex(locals, locals.out_hex, locals.out_bits)
			]
			self.modmul_decode_output = modmul_decode_output

		cpi = cat.new_var("cpi")
		def int255cpy(dst, src): return [
			dst.delete_all(),
			cpi[1:12+1] >> [
				dst.append(src[cpi-1])
			]
		] if dst.uid != src.uid else []

		def int255add(dst, src_a, src_b): return [
			dst.delete_all(),
			cpi[1:12+1] >> [
				dst.append(src_a[cpi-1] + src_b[cpi-1])
			]
		] if dst.uid != src_a.uid and dst.uid != src_b.uid else [
			cpi[1:12+1] >> [
				dst[cpi-1] <= src_a[cpi-1] + src_b[cpi-1]
			]
		]

		def int255sub(dst, src_a, src_b): return [
			dst.delete_all(),
			cpi[1:12+1] >> [
				dst.append(src_a[cpi-1] - src_b[cpi-1])
			]
		] if dst.uid != src_a.uid and dst.uid != src_b.uid else [
			cpi[1:12+1] >> [
				dst[cpi-1] <= src_a[cpi-1] - src_b[cpi-1]
			]
		]

		def modmul_copyargs(dst, a, b): return [
			#int255cpy(A, a),
			#int255cpy(B, b),
			[
				A.delete_all(),
				B.delete_all(),
				cpi[1:12+1] >> [
					A.append(a[cpi-1]),
					B.append(b[cpi-1])
				]
			] if a.uid != A.uid and b.uid != B.uid else [
				int255cpy(A, a),
				int255cpy(B, b),
			],
			modmul_body(),
			int255cpy(dst, C)
		]

		inv_tmp = cat.new_list("INV_TMP", [0]*12)
		# input: A, output C
		@cat.proc_def("x25519_invert", turbo=True)
		def x25519_invert(locals): return [
			int255cpy(inv_tmp, A), # copy of input
			int255cpy(C, A), # c = accumulator
			locals.i[253:-1:-1] >> [
				int255cpy(A, C),
				int255cpy(B, C),
				modmul_body(), # C = C * C
				IF ((locals.i != 2).AND(locals.i != 4)) [
					int255cpy(A, C),
					int255cpy(B, inv_tmp),
					modmul_body(), # C = C * inv_tmp
				],
			]
		]

		# this is like, vaguely constant-time, probably
		def cswap(locals, swap, a, b, c, d): return [
			locals.swapi[1:12+1] >> [
				locals.swaptmp <= (a[locals.swapi-1] * swap) + (b[locals.swapi-1] * (Literal(1) - swap)),
				a[locals.swapi-1] <= (b[locals.swapi-1] * swap) + (a[locals.swapi-1] * (Literal(1) - swap)),
				b[locals.swapi-1] <= locals.swaptmp,
				locals.swaptmp <= (c[locals.swapi-1] * swap) + (d[locals.swapi-1] * (Literal(1) - swap)),
				c[locals.swapi-1] <= (d[locals.swapi-1] * swap) + (c[locals.swapi-1] * (Literal(1) - swap)),
				d[locals.swapi-1] <= locals.swaptmp
			]
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


		@cat.proc_def("x25519_scalarmult [scalar] [element]", turbo=True)
		def x25519_scalarmult(locals, scalar, element): return [

			#bitstringify_le(locals, locals.scalarbits, scalar),
			locals.scalarbits <= "",
			locals.scalarbits <= locals.scalarbits.join( HEXBITS[(Literal("0x").join(scalar[1]) >> 3) << 3] ).join( HEXBITS[Literal("0x").join(scalar[0])] ),
			locals.i[2:scalar.len()-2:2] >> [
				locals.scalarbits <= locals.scalarbits.join( HEXBITS[Literal("0x").join(scalar[locals.i + 1])] ).join( HEXBITS[Literal("0x").join(scalar[locals.i])] )
			],
			locals.scalarbits <= locals.scalarbits.join( HEXBITS[Literal("0x").join(scalar[locals.i + 1])] ).join( HEXBITS[(Literal("0x").join(scalar[locals.i]) & 3) + 4] ),

			#stdout.append(locals.scalarbits),

			bitstringify_le(locals, locals.elementbits, element),
			fsplit(locals, x_1, locals.elementbits),

			locals.i[1+1:12+1] >> [
				x_2[locals.i-1] <= 0
			],
			x_2[0] <= 1,

			locals.i[1:12+1] >> [
				z_2[locals.i-1] <= 0
			],

			int255cpy(x_3, x_1),

			locals.i[1+1:12+1] >> [
				z_3[locals.i-1] <= 0
			],
			z_3[0] <= 1,

			locals.swap <= 0,

			locals.t[:255] >> [
				locals.k_t <= locals.scalarbits[Literal(254)-locals.t],
				locals.swap <= (locals.swap + locals.k_t) % 2,
				cswap(locals, locals.swap, x_2, x_3, z_2, z_3),
				locals.swap <= locals.k_t,

				smA.delete_all(),
				smB.delete_all(),
				cpi[1:12+1] >> [
					smA.append(x_2[cpi-1] + z_2[cpi-1]),
					smB.append(x_2[cpi-1] - z_2[cpi-1])
				],

				modmul_copyargs(smAA, smA, smA),
				modmul_copyargs(smBB, smB, smB),

				smE.delete_all(),
				smC.delete_all(),
				smD.delete_all(),
				cpi[1:12+1] >> [
					smE.append(smAA[cpi-1] - smBB[cpi-1]),
					smC.append(x_3[cpi-1] + z_3[cpi-1]),
					smD.append(x_3[cpi-1] - z_3[cpi-1]),
				],

				modmul_copyargs(smDA, smD, smA),
				modmul_copyargs(smCB, smC, smB),

				int255add(x_3, smDA, smCB),
				modmul_copyargs(x_3, x_3, x_3),

				int255sub(z_3, smDA, smCB),
				modmul_copyargs(z_3, z_3, z_3),
				modmul_copyargs(z_3, z_3, x_1),

				modmul_copyargs(x_2, smAA, smBB),

				modmul_copyargs(C, CONST_121665, smE),
				int255add(B, smAA, C),
				modmul_copyargs(z_2, smE, B),
			],

			cswap(locals, locals.swap, x_2, x_3, z_2, z_3),

			int255cpy(A, z_2),
			x25519_invert(),

			int255cpy(A, C),
			int255cpy(B, x_2),
			modmul_body(),

			#fjoin(locals, locals.out_bits, C),
			#bits2hex_le(locals, locals.out_hex, locals.out_bits)
			fjoin_hex_le(locals, locals.out_hex, C)
		]

		# these are just exposed for testing
		if testing:
			self.init_modmul = init_modmul
			self.modmul_body = modmul_body
			self.modmul_copyargs = modmul_copyargs
			self.x25519_invert = x25519_invert

		# this is the actual API
		self.scalarmult = x25519_scalarmult

if __name__ == "__main__":
	from .utils import Utils

	project = Project(template="../test_files/Scratch Project.sb3")

	cat = project.new_sprite("Sprite1")

	stdout = project.stage.new_list("stdout", [], monitor=[0, 0, 480-2, 292])

	utils = Utils(cat)
	x25519 = X25519(cat, utils, testing=True)

	"""@cat.proc_def("benchmark_modmul")
	def benchmark_modmul(locals): return [
		stdout.append("Benchmarking..."),
		x25519.init_modmul("5629e6259c8e0cd24b4068fff626f159b9a25f2ea3b93016ca437303b11996b2",
			"5c95420de6c0ecc96a35a2870a5544c0b54f3041abbb9dac24b1f5b06d6cc0ce"),

		locals.bench_start <= millis_now,
		locals.i <= 0,
		repeatuntil((millis_now - locals.bench_start) > 1000, [
			#modmul_body(),
			x25519.modmul_copyargs(C, A, B),
			locals.i.changeby(1)
		]),
		stdout.append(Literal("Benchmarked ").join(locals.i).join(" muls/s")),

		x25519.modmul_decode_output(),
		stdout.append(x25519.modmul_decode_output.out_hex)
	]"""

	@cat.proc_def("benchmark_x25519_scalarmult", turbo=True)
	def benchmark_x25519_scalarmult(locals): return [
		locals.bench_start <= millis_now,
		#locals.a <= "a546e36bf0527c9d3b16154b82465edd62144c0ac1fc5a18506a2244ba449ac4",
		#locals.b <= "e6db6867583030db3594c1a424b15f7c726624ec26b3353b10a903a6d0ab1c4c",
		#locals.b <= "a546e36bf0527c9d3b16154b82465edd62144c0ac1fc5a18506a2244ba449ac4",
		#locals.a <= "e6db6867583030db3594c1a424b15f7c726624ec26b3353b10a903a6d0ab1c4c",
		locals.a <= "4b66e9d4d1b4673c5ad22691957d6af5c11b6421e0ea01d42ca4169e7918ba0d",
		locals.b <= "e5210f12786811d3f4b7959d0538ae2c31dbe7106fc03c3efc4cd549c715a493",
		stdout.append(""),
		stdout.append("a ="),
		stdout.append(locals.a),
		stdout.append("b ="),
		stdout.append(locals.b),
		x25519.scalarmult(locals.a, locals.b),
		stdout.append("x25519_scalarmult(a, b) ="),
		stdout.append(x25519.scalarmult.out_hex),
		stdout.append(Literal("Completed in ").join(millis_now - locals.bench_start).join("ms")),

		stdout.append(""),
		stdout.append("Testing:"),

		repeatuntil(Literal(1)==1)[
			stdout.append("Enter Scalar value (little-endian hex):"),
			AskAndWait("Scalar:"),
			locals.a <= Answer(),
			stdout.append("Enter Element value (little-endian hex):"),
			AskAndWait("Element:"),
			locals.b <= Answer(),

			x25519.scalarmult(locals.a, locals.b),
			stdout.append("x25519_scalarmult(Scalar, Element) ="),
			stdout.append(x25519.scalarmult.out_hex),
		]
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
		Wait(0),
		x25519.init_modmul(a, b),
		x25519.modmul_body(),
		x25519.modmul_decode_output(),
		stdout.append("(a * b) % (2^225-19) ="),
		stdout.append(x25519.modmul_decode_output.out_hex),
		Wait(0),

		x25519.init_modmul(a, b),
		x25519.x25519_invert(),
		x25519.modmul_decode_output(),

		stdout.append("pow(a, -1, 2^225-19) ="),
		stdout.append(x25519.modmul_decode_output.out_hex),
		Wait(0),

		benchmark_x25519_scalarmult()

		#AskAndWait("hello"),
		#stdout.append(Literal("You said: ").join(Answer())),

		#benchmark_modmul()
	])

	project.save("../test.sb3", execute=False)
