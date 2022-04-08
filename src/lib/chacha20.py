from boiga.ast import *
import struct

class ChaCha20():
	def __init__(self, cat, utils):
		tmp = cat.new_var("chacha_tmp")
		tmp2 = cat.new_var("chacha_tmp2")

		CHACHA20_INIT_STATE = list(struct.unpack("<IIII", b"expand 32-byte k")) + [0]*12
		state = cat.new_list("chacha_state", CHACHA20_INIT_STATE)
		state_tmp = cat.new_list("chacha_stmp", [])
		tmp_buf = cat.new_list("chacha_tmp_buf", [])

		@cat.proc_def("chacha20_rng_core")
		def chacha20_core(locals): return [
			state_tmp.delete_all(),
			locals.i[1:16+1] >> [
				state_tmp.append(state[locals.i-1])
			],
			locals.i <= 0,
			repeatn(20*4*4) [
				tmp <= state_tmp[utils.CHACHA_LUT[locals.i+2]-1],

				tmp2 <= (state_tmp[utils.CHACHA_LUT[locals.i+0]-1] +
					state_tmp[utils.CHACHA_LUT[locals.i+1]-1]) & 0xffff_ffff,

				tmp <= utils.bitxor(tmp, tmp2),

				state_tmp[utils.CHACHA_LUT[locals.i+2]-1] <=
					(tmp // utils.CHACHA_LUT[locals.i+4]) +
					((tmp % utils.CHACHA_LUT[locals.i+4]) * utils.CHACHA_LUT[locals.i+3]),

				state_tmp[utils.CHACHA_LUT[locals.i+0]-1] <= tmp2,

				locals.i <= (locals.i + 5) % utils.CHACHA_LUT_LEN,
			],
			locals.i[1:16+1] >> [
				state_tmp[locals.i-1] <= (state_tmp[locals.i-1] + state[locals.i-1]) & 0xffff_ffff
			],
			state[12] <= state[12] + 1, # probably safe to assume this will never overflow, in a scratch project
		]

		@cat.proc_def("chacha20_encrypt [key_hex] [ctr] [nonce_hex] [msg_hex]")
		def chacha20_encrypt(locals, key_hex, ctr, nonce_hex, msg_hex): return [
			locals.i[:8] >> [
				locals.tmp <= "",
				locals.j[locals.i*8:locals.i*8+8:2] >> [
					locals.tmp <= key_hex[locals.j].join(key_hex[locals.j+1]).join(locals.tmp)
				],
				state[locals.i+4] <= Literal("0x0").join(locals.tmp),
			],
			state[12] <= ctr,
			locals.i[:3] >> [
				locals.tmp <= "",
				locals.j[locals.i*8:locals.i*8+8:2] >> [
					locals.tmp <= nonce_hex[locals.j].join(nonce_hex[locals.j+1]).join(locals.tmp)
				],
				state[locals.i+13] <= Literal("0x0").join(locals.tmp),
			],
			tmp_buf.delete_all(),
			repeatn(math.ceil(msg_hex.len()/128)) [
				chacha20_core(),
				locals.i[1:16+1] >> [
					tmp_buf.append(state_tmp[locals.i-1] & 0xFF),
					tmp_buf.append((state_tmp[locals.i-1] >> 8) & 0xFF),
					tmp_buf.append((state_tmp[locals.i-1] >> 16) & 0xFF),
					tmp_buf.append((state_tmp[locals.i-1] >> 24) & 0xFF),
				],
			],
			locals.hex_out <= "",
			locals.i[:msg_hex.len():2] >> [
				locals.hex_out <= locals.hex_out.join(utils.HEX_LUT[utils.bytexor(
					tmp_buf[locals.i/2],
					Literal("0x").join(msg_hex[locals.i]).join(msg_hex[locals.i+1])
				)])
			]
		]

		self.encrypt = chacha20_encrypt
		self.decrypt = chacha20_encrypt # it's the same thing!


if __name__ == "__main__":
	from boiga.codegen import Project
	from .utils import Utils

	project = Project(template="../test_files/Scratch Project.sb3")

	cat = project.new_sprite("Sprite1")
	utils = Utils(cat)
	chacha20 = ChaCha20(cat, utils)

	stdout = project.stage.new_list("stdout", [], monitor=[0, 0, 480-2, 292])

	test_key = bytes.fromhex("deadbeef"*8)
	test_nonce = bytes.fromhex("cafebabe"*3)
	test_msg = bytes(range(100))

	from Crypto.Cipher import ChaCha20
	test_result = ChaCha20.new(key=test_key, nonce=test_nonce).encrypt(test_msg)

	cat.on_flag([
		stdout.delete_all(),
		stdout.append("Hello, world!"),

		chacha20.encrypt(
			test_key.hex(),
			0,
			test_nonce.hex(),
			test_msg.hex()
		),

		stdout.append(chacha20.encrypt.hex_out),

		IF (chacha20.encrypt.hex_out == test_result.hex()) [
			stdout.append("Test passed!")
		]
	])

	project.save("../test.sb3", execute=False)
