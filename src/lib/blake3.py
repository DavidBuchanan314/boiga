from boiga.ast import *

import struct


class BLAKE3():
	IV = [
		0x6a09e667,
		0xbb67ae85,
		0x3c6ef372,
		0xa54ff53a,
		0x510e527f,
		0x9b05688c,
		0x1f83d9ab,
		0x5be0cd19
	]

	BLAKE3_CHUNK_START = 2**0
	BLAKE3_CHUNK_END = 2**1
	BLAKE3_ROOT = 2**3


	def __init__(self, cat, utils):
		tmp = cat.new_var("blake3_tmp")
		tmp2 = cat.new_var("blake3_tmp2")

		state = cat.new_list("blake3_state", [0]*16) #monitor=[0,0,200,320])
		magic = []
		for x in [
			0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
			2, 6, 3, 10, 7, 0, 4, 13, 1, 11, 12, 5, 9, 14, 15, 8,
			3, 4, 10, 12, 13, 2, 7, 14, 6, 5, 9, 0, 11, 15, 8, 1,
			10, 7, 12, 9, 14, 3, 13, 15, 4, 0, 11, 2, 5, 8, 1, 6,
			12, 13, 9, 11, 15, 10, 14, 8, 7, 2, 5, 3, 0, 1, 6, 4,
			9, 14, 11, 5, 8, 12, 15, 1, 13, 3, 0, 10, 2, 6, 4, 7,
			11, 15, 5, 0, 1, 9, 8, 6, 14, 10, 2, 12, 3, 4, 7, 13,
		]:
			magic += [x+1, -1]
		MSG_SCHEDULE = cat.new_list("BLAKE3_MSG_SCHEDULE", magic)
		msg = cat.new_list("blake3_msg", [])

		@cat.proc_def("blake3_core [b] [d]")
		def blake3_core(locals, b, d): return [
				[state[8+i] <= self.IV[i] for i in range(4)],
				state[12] <= 0,
				state[13] <= 0,
				state[14] <= b,
				state[15] <= d,
				locals.i <= 0,
				locals.j <= 1,
				repeatn(7*2*4*4) [
					tmp <= state[utils.CHACHA_LUT[locals.i+2]-1],

					tmp2 <= (state[utils.CHACHA_LUT[locals.i+0]-1] +
						state[utils.CHACHA_LUT[locals.i+1]-1] +
						msg[MSG_SCHEDULE[locals.j-1]-1]) & 0xffff_ffff,

					tmp <= utils.bitxor(tmp, tmp2),

					state[utils.CHACHA_LUT[locals.i+2]-1] <=
						(tmp // utils.CHACHA_LUT[locals.i+3]) +
						((tmp % utils.CHACHA_LUT[locals.i+3]) * utils.CHACHA_LUT[locals.i+4]),

					state[utils.CHACHA_LUT[locals.i+0]-1] <= tmp2,

					locals.i <= (locals.i + 5) % utils.CHACHA_LUT_LEN,
					locals.j.changeby(1),
				],
				locals.i[1:8+1] >> [
					state[locals.i-1] <= utils.bitxor(state[locals.i-1], state[locals.i-1+8])
				],
			]


		@cat.proc_def()
		def blake3_hash(locals, message_hex): return [
			locals.padded <= message_hex.join("0"*128),
			[state[i] <= self.IV[i] for i in range(8)],

			locals.num_blocks <= math.ceil(message_hex.len()/(64*2)) + (message_hex.len() == 0),
			locals.i[:locals.num_blocks] >> [
				locals.d <= 0,
				IF (locals.i == 0) [
					locals.d.changeby(self.BLAKE3_CHUNK_START)
				],
				IF (locals.i == locals.num_blocks - 1, [
					locals.d.changeby(self.BLAKE3_CHUNK_END | self.BLAKE3_ROOT),
					locals.block_len <= (message_hex.len()/2) - ((locals.num_blocks-1)*64)
				]).ELSE([
					locals.block_len <= 64
				]),
				msg.delete_all(),
				locals.j[locals.i*128:locals.i*128+128:8] >> [
					locals.tmp <= "",
					locals.k[locals.j:locals.j+8:2] >> [
						locals.tmp <= locals.padded[locals.k].join(locals.padded[locals.k+1]).join(locals.tmp)
					],
					msg.append(Literal("0x0").join(locals.tmp))
				],
				blake3_core(locals.block_len, locals.d),
			],
			locals.hex_out <= "",
			locals.i[1:8+1] >> [
				locals.hex_out <= locals.hex_out.join(utils.HEX_LUT[state[locals.i-1] & 0xFF])
					.join(utils.HEX_LUT[(state[locals.i-1] >> 8) & 0xFF])
					.join(utils.HEX_LUT[(state[locals.i-1] >> 16) & 0xFF])
					.join(utils.HEX_LUT[(state[locals.i-1] >> 24) & 0xFF])
			]
		]

		self.hash = blake3_hash

if __name__ == "__main__":
	from boiga.codegen import Project
	from .chat import Chat
	from .utils import Utils

	project = Project()

	cat = project.new_sprite("Sprite1")
	utils = Utils(cat)
	chat = Chat(cat, utils)
	blake3 = BLAKE3(cat, utils)

	cat.on_flag([
		chat.init(),
		chat.new_message(">", "Enter message:"),
		chat.gui_loop(),
	])

	cat.on_flag([
		Forever [
			AskAndWait(),
			chat.new_message("<", Answer()),
			chat.wait_for_animation(),
			chat.string_to_hex(Answer()),
			blake3.hash(chat.string_to_hex.hex_out),
			chat.new_message(">", Literal("BLAKE3(").join(Answer()).join(") = ").join(blake3.hash.hex_out)),
		]
	])

	"""
	cat.on_flag([
		blake3.hash(b"hello".hex()),
		chat.new_message(">", blake3.hash.hex_out),
		blake3.hash((b"A"*64).hex()),
		chat.new_message(">", blake3.hash.hex_out),
		blake3.hash((b"A"*128).hex()),
		chat.new_message(">", blake3.hash.hex_out),
		blake3.hash((b"A"*32*3).hex()),
		chat.new_message(">", blake3.hash.hex_out),
	])
	"""

	project.save("../test.sb3", execute=False)
