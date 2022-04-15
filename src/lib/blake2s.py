from boiga.ast import *

import struct


class BLAKE2s():
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

	BLAKE2S_CHUNK_START = 2**0
	BLAKE2S_CHUNK_END = 2**1
	BLAKE2S_ROOT = 2**3


	def __init__(self, cat, utils):
		tmp = cat.new_var("blake2s_tmp")
		tmp2 = cat.new_var("blake2s_tmp2")

		# just for debugging!
		#stdout = cat.project.stage.new_list("stdout", [], monitor=[0, 0, 480-2, 292])

		state = cat.new_list("blake2s_state", [0]*16) #monitor=[0,0,200,320])
		state_h = cat.new_list("blake2s_state_h", [0]*8)
		magic = []
		for x in [
			0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
			14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3,
			11, 8, 12, 0, 5, 2, 15, 13, 10, 14, 3, 6, 7, 1, 9, 4,
			7, 9, 3, 1, 13, 12, 11, 14, 2, 6, 5, 10, 4, 0, 15, 8,
			9, 0, 5, 7, 2, 4, 10, 15, 14, 1, 11, 12, 6, 8, 3, 13,
			2, 12, 6, 10, 0, 11, 8, 3, 4, 13, 7, 5, 15, 14, 1, 9,
			12, 5, 1, 15, 14, 13, 4, 10, 0, 7, 6, 3, 9, 2, 8, 11,
			13, 11, 7, 14, 12, 1, 3, 9, 5, 0, 15, 4, 8, 6, 2, 10,
			6, 15, 14, 9, 11, 3, 0, 8, 12, 2, 13, 7, 1, 4, 10, 5,
			10, 2, 8, 4, 7, 6, 1, 5, 15, 11, 9, 14, 3, 12, 13, 0
		]:
			magic += [x+1, -1]
		MSG_SCHEDULE = cat.new_list("BLAKE2S_MSG_SCHEDULE", magic)
		msg = cat.new_list("blake2s_msg", [])

		@cat.proc_def("blake2s_core [t] [last]")
		def blake2s_core(locals, t, last): return [
				locals.i[1:8+1] >> [
					state[locals.i-1] <= state_h[locals.i-1]
				],
				[state[8+i] <= self.IV[i] for i in range(4)],
				state[12] <= utils.bitxor(self.IV[4], t),
				state[13] <= self.IV[5],
				IF (last == 1, [
					state[14] <= self.IV[6] ^ 0xffff_ffff,
				]).ELSE([
					state[14] <= self.IV[6],
				]),
				state[15] <= self.IV[7],
				locals.i <= 0,
				locals.j <= 1,
				repeatn(10*2*4*4) [
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
					state_h[locals.i-1] <= utils.bitxor3(state_h[locals.i-1], state[locals.i-1], state[locals.i-1+8]),
				],
			]


		@cat.proc_def()
		def blake2s_hash(locals, message_hex): return [
			locals.padded <= message_hex.join("0"*128),
			state_h[0] <= self.IV[0] ^ 0x01010020, # static parameter block (rest is zeroes)
			[state_h[i] <= self.IV[i] for i in range(1,8)],

			locals.num_blocks <= math.ceil(message_hex.len()/(64*2)) + (message_hex.len() == 0),
			locals.t <= 0,
			locals.i[:locals.num_blocks] >> [
				IF (locals.i == locals.num_blocks - 1, [
					locals.last <= 1,
					locals.t.changeby((message_hex.len()/2) - ((locals.num_blocks-1)*64))
				]).ELSE([
					locals.t.changeby(64),
					locals.last <= 0
				]),
				msg.delete_all(),
				locals.j[locals.i*128:locals.i*128+128:8] >> [
					locals.tmp <= "",
					locals.k[locals.j:locals.j+8:2] >> [
						locals.tmp <= locals.padded[locals.k].join(locals.padded[locals.k+1]).join(locals.tmp)
					],
					msg.append(Literal("0x0").join(locals.tmp))
				],
				blake2s_core(locals.t, locals.last),
			],
			locals.hex_out <= "",
			locals.i[1:8+1] >> [
				locals.hex_out <= locals.hex_out.join(utils.HEX_LUT[state_h[locals.i-1] & 0xFF])
					.join(utils.HEX_LUT[(state_h[locals.i-1] >> 8) & 0xFF])
					.join(utils.HEX_LUT[(state_h[locals.i-1] >> 16) & 0xFF])
					.join(utils.HEX_LUT[(state_h[locals.i-1] >> 24) & 0xFF])
			]
		]

		self.hash = blake2s_hash

if __name__ == "__main__":
	from boiga.codegen import Project
	from .chat import Chat
	from .utils import Utils

	project = Project()

	cat = project.new_sprite("Sprite1")
	utils = Utils(cat)
	chat = Chat(cat, utils)
	blake2s = BLAKE2s(cat, utils)

	cat.on_flag([
		chat.init(),
		chat.new_message(">", "Enter message:"),
		chat.gui_loop(),
	])

	if True:
		cat.on_flag([
			forever([
				AskAndWait(),
				chat.new_message("<", Answer()),
				chat.wait_for_animation(),
				chat.string_to_hex(Answer()),
				blake2s.hash(chat.string_to_hex.hex_out),
				chat.new_message(">", Literal("BLAKE2s(").join(Answer()).join(") = ").join(blake2s.hash.hex_out)),
			])
		])
	else:

		
		cat.on_flag([
			blake2s.hash(b"hello".hex()),
			chat.new_message(">", blake2s.hash.hex_out),
			blake2s.hash((b"A"*64).hex()),
			chat.new_message(">", blake2s.hash.hex_out),
			blake2s.hash((b"A"*128).hex()),
			chat.new_message(">", blake2s.hash.hex_out),
			blake2s.hash((b"A"*32*3).hex()),
			chat.new_message(">", blake2s.hash.hex_out),
			blake2s.hash((b"").hex()),
			chat.new_message(">", blake2s.hash.hex_out),
		])
		from cryptography.hazmat.primitives import hashes

		def blake2s(seed):
			digest = hashes.Hash(hashes.BLAKE2s(32))
			digest.update(seed)
			return digest.finalize()

		print(blake2s(b"hello").hex())
		print(blake2s(b"A"*64).hex())
		print(blake2s(b"A"*128).hex())
		print(blake2s(b"A"*32*3).hex())
		print(blake2s(b"").hex())
	

	project.save("../test.sb3", execute=False)
