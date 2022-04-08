from boiga.ast import *

import struct


class CSPRNG():
	def __init__(self, cat, utils):
		tmp = cat.new_var("csprng_tmp")
		tmp2 = cat.new_var("csprng_tmp2")

		CHACHA20_INIT_STATE = list(struct.unpack("<IIII", b"expand 32-byte k")) + [0]*12
		rng_state = cat.new_list("rng_state", CHACHA20_INIT_STATE)
		rng_tmp = cat.new_list("rng_tmp", [])

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
					tmp <= rng_tmp[utils.CHACHA_LUT[locals.i+2]-1],

					tmp2 <= (rng_tmp[utils.CHACHA_LUT[locals.i+0]-1] +
						rng_tmp[utils.CHACHA_LUT[locals.i+1]-1]) & 0xffff_ffff,

					tmp <= utils.bitxor(tmp, tmp2),

					rng_tmp[utils.CHACHA_LUT[locals.i+2]-1] <=
						(tmp // utils.CHACHA_LUT[locals.i+4]) +
						((tmp % utils.CHACHA_LUT[locals.i+4]) * utils.CHACHA_LUT[locals.i+3]),

					rng_tmp[utils.CHACHA_LUT[locals.i+0]-1] <= tmp2,

					locals.i <= (locals.i + 5) % utils.CHACHA_LUT_LEN,
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

		@cat.proc_def("rng_get_hex [length]")
		def rng_get_hex(locals, length): return [
			rng_get_bytes(length),
			locals.hex_out <= "",
			locals.i[:length] >> [
				locals.hex_out <= locals.hex_out.join(utils.HEX_LUT[rng_bytes_out[locals.i]])
			]
		]

		self.rng_init = rng_init
		self.rng_get_hex = rng_get_hex

if __name__ == "__main__":
	from boiga.codegen import Project
	from .utils import Utils

	project = Project(template="../test_files/Scratch Project.sb3")

	cat = project.new_sprite("Sprite1")
	utils = Utils(cat)
	csprng = CSPRNG(cat, utils)

	stdout = project.stage.new_list("stdout", [], monitor=[0, 0, 480-2, 292])

	cat.on_flag([
		stdout.delete_all(),
		stdout.append("Initialising entropy pool..."),

		Wait(0),

		csprng.rng_init(),

		stdout.append("Done! Generating 10 random bytes..."),

		csprng.rng_get_hex(10),
		stdout.append(csprng.rng_get_hex.hex_out),

		stdout.append("Done! Generating 64 random bytes..."),

		csprng.rng_get_hex(64),
		stdout.append(csprng.rng_get_hex.hex_out),

		stdout.append("Done! Generating 4096 random bytes..."),

		csprng.rng_get_hex(4096),
		stdout.append(csprng.rng_get_hex.hex_out),

		stdout.append("Done!"),

		AskAndWait(),
	])

	project.save("../test.sb3", execute=False)
