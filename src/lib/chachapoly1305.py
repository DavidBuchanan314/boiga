from boiga.ast import *

class ChaChaPoly1305():
	def __init__(self, cat, chacha20, utils, testing=False):

		radices = [2**22, 2**22, 2**21] * 4
		rtotals = []
		for i in range(len(radices)):
			rtotal = 1
			for r in radices[:i]:
				rtotal *= r
			rtotals.append(rtotal)

		RADICES = cat.new_list("P1305RADICES", [22, 22, 21] * 4)
		RTOTALS = cat.new_list("P1305RTOTALS", [float(x) for x in rtotals])

		# note: these collide with those declared by x25519, but
		# they aren't used at the same time (probably, lol)
		A = cat.new_list("A")
		B = cat.new_list("B")
		C = cat.new_list("C")

		def extract_bits_from_hex(hexbuf, offset, start, length):
			start_digit = start // 4
			end_digit = (start+length+3) // 4
			hexstring = Literal("0x")
			for i in range(start_digit, end_digit)[::-1]:
				hexstring = hexstring.join(hexbuf[offset + (i^1)])
			hexstring >>= start%4
			hexstring %= 2**length
			return hexstring
		
		def extract_bits_from_bytes(bytearr, start, length):
			start_digit = start // 8
			end_digit = (start+length+7) // 8
			hexstring = Literal(0)
			for i in range(start_digit, end_digit)[::-1]:
				hexstring = hexstring * 256 + bytearr[i]
			hexstring >>= start%8
			hexstring %= 2**length
			return hexstring


		# note: offset is nibble index, and must be a multiple of 2
		@cat.proc_def()
		def poly1305_split(locals, block_hex, offset): return [
			B.delete_all(),
			B.append(extract_bits_from_hex(block_hex, offset, 0, 22)),
			B.append(extract_bits_from_hex(block_hex, offset, 22, 22) * rtotals[1]),
			B.append(extract_bits_from_hex(block_hex, offset, 22+22, 21) * rtotals[2]),
			B.append(extract_bits_from_hex(block_hex, offset, 22+22+21, 22) * rtotals[3]),
			B.append(extract_bits_from_hex(block_hex, offset, 22+22+21+22, 22) * rtotals[4]),
			B.append(extract_bits_from_hex(block_hex, offset, 22+22+21+22+22, 19) * rtotals[5]) # stop after 128 bits
		]

		@cat.proc_def()
		def poly1305_join(locals): return [
			locals.hex_out <= "",
			locals.bytebuf <= 0,
			locals.bitshift <= 1,
			locals.i[1:6+1] >> [
				locals.blah <= C[locals.i-1] / RTOTALS[locals.i-1],
				locals.shift <= 1,
				locals.j[:RADICES[locals.i-1]] >> [
					locals.bytebuf.changeby( ((locals.blah // locals.shift) & 1) * locals.bitshift ),
					locals.bitshift.changeby(locals.bitshift),
					IF (locals.bitshift == 1<<8) [
						locals.bitshift <= 1,
						locals.hex_out <= locals.hex_out.join(utils.HEX_LUT[locals.bytebuf]),
						locals.bytebuf <= 0
					],
					locals.shift <= locals.shift * 2
				]
			]
			# we deliberately discard the last few bits - this is the final % 2**128
		]

		def textbook_mul(out, x, y): return [
			out.append(sumchain([
				x[i - j] * y[j]
				for j in range(
					max(0,  i + 1 - 6),
					min(6, i + 1)
				)
			]))
			for i in range(11)
		]

		def carry_from(locals, arr, i):
			r = rtotals[i+1]
			return [
				#locals.carry <= arr[i] - (arr[i] % r), # TODO: don't use variable?
				#arr[i+1] <= arr[i+1] + locals.carry,
				#arr[i] <= arr[i] - locals.carry,

				# unsure which version is faster
				arr[i+1] <= arr[i+1] + (arr[i] - (arr[i] % r)),
				arr[i] <= arr[i] - (arr[i] - (arr[i] % r)), # note, order of operations is very important here
			]

		@cat.proc_def()
		def poly1305_mul(locals): return [
			C.delete_all(),
			textbook_mul(C, A, B),

			carry_from(locals, C, 4),
			carry_from(locals, C, 5),

			[
				[
					C[i-6] <= C[i-6] + (C[i] * (5.0*(2**-130))),
					#C[i] <= 0.0
				]
				for i in range(6, 11)
			],
			#C[6] <= 0.0,

			[
				carry_from(locals, C, i)
				for i in range(5)
			],

			#carry_from(locals, C, 5),
			locals.tmp <= (C[5] - (C[5] % rtotals[5+1])),
			C[5] <= C[5] - (C[5] - (C[5] % rtotals[5+1])),
			C[0] <= C[0] + (locals.tmp * (5.0*(2**-130))),
		]

		@cat.proc_def()
		def chacha20_poly1305(locals, key_hex, nonce_hex, msg_hex): return [
			chacha20.encrypt(key_hex, 0, nonce_hex, "00"*64),

			# mask r
			chacha20.tmp_buf[3] <= chacha20.tmp_buf[3] & 0xf,
			chacha20.tmp_buf[4] <= (chacha20.tmp_buf[4] >> 2) << 2,
			chacha20.tmp_buf[7] <= chacha20.tmp_buf[7] & 0xf,
			chacha20.tmp_buf[8] <= (chacha20.tmp_buf[8] >> 2) << 2,
			chacha20.tmp_buf[11] <= chacha20.tmp_buf[11] & 0xf,
			chacha20.tmp_buf[12] <= (chacha20.tmp_buf[12] >> 2) << 2,
			chacha20.tmp_buf[15] <= chacha20.tmp_buf[15] & 0xf,

			A.delete_all(),
			A.append(extract_bits_from_bytes(chacha20.tmp_buf, 0, 22)),
			A.append(extract_bits_from_bytes(chacha20.tmp_buf, 22, 22) * rtotals[1]),
			A.append(extract_bits_from_bytes(chacha20.tmp_buf, 22+22, 21) * rtotals[2]),
			A.append(extract_bits_from_bytes(chacha20.tmp_buf, 22+22+21, 22) * rtotals[3]),
			A.append(extract_bits_from_bytes(chacha20.tmp_buf, 22+22+21+22, 22) * rtotals[4]),
			A.append(extract_bits_from_bytes(chacha20.tmp_buf, 22+22+21+22+22, 19) * rtotals[5]),
			
			
			C.delete_all(),
			repeatn(6) [
				C.append(0)
			],
			

			locals.msg_padded <= msg_hex,
			repeatuntil (locals.msg_padded.len() % (16*2) == 0) [
				locals.msg_padded <= locals.msg_padded.join("00"),
			],
			locals.msg_padded <= locals.msg_padded
				.join("00"*8)
				.join(utils.HEX_LUT[(msg_hex.len()/2) & 0xff])
				.join(utils.HEX_LUT[((msg_hex.len()/2) >> 8) & 0xff])
				.join("00"*6), # TODO: support >64k messages????
			
			
			locals.offset <= 0,
			repeatn (locals.msg_padded.len()/(16*2)) [
				poly1305_split(locals.msg_padded, locals.offset),
				B[5] <= B[5] + ((1<<19) * rtotals[5]), # add 1<<128

				locals.i[1:6+1] >> [
					B[locals.i-1] <= B[locals.i-1] + C[locals.i-1]
				],

				poly1305_mul(),

				locals.offset.changeby(16*2),
			],

			poly1305_split(chacha20.encrypt.hex_out, 16*2),

			locals.i[1:6+1] >> [
				C[locals.i-1] <= C[locals.i-1] + B[locals.i-1]
			],

			[
				carry_from(locals, C, i)
				for i in range(4) # XXX: is this correct? look here first if there are bugs...
			],

			poly1305_join(),
		]

		@cat.proc_def()
		def chacha20_poly1305_encrypt(locals, key_hex, nonce_hex, msg_hex): return [
			chacha20.encrypt(key_hex, 1, nonce_hex, msg_hex),
			locals.ct_out <= chacha20.encrypt.hex_out,
			chacha20_poly1305(key_hex, nonce_hex, locals.ct_out),
			locals.tag_out <= poly1305_join.hex_out,
		]

		@cat.proc_def()
		def chacha20_poly1305_decrypt(locals, key_hex, nonce_hex, msg_hex, tag_hex): return [
			chacha20_poly1305(key_hex, nonce_hex, msg_hex),
			IF (poly1305_join.hex_out == tag_hex) [ # TODO: constant time comparison?
				chacha20.decrypt(key_hex, 1, nonce_hex, msg_hex),
				locals.hex_out <= chacha20.decrypt.hex_out,
				locals.msg_valid <= "true",
			].ELSE()[
				locals.hex_out <= "",
				locals.msg_valid <= "false",
			],
			
		]



		if testing:
			self.split = poly1305_split # testing
			self.join = poly1305_join
			self.split_buf = B # testing
			self.rtotals = rtotals
			self.chacha20_poly1305 = chacha20_poly1305
		
		self.encrypt = chacha20_poly1305_encrypt
		self.decrypt = chacha20_poly1305_decrypt

if __name__ == "__main__":
	from boiga.codegen import Project
	from .utils import Utils
	from .chacha20 import ChaCha20

	project = Project()

	cat = project.new_sprite("Sprite1")
	utils = Utils(cat)
	chacha20 = ChaCha20(cat, utils)
	chachapoly1305 = ChaChaPoly1305(cat, chacha20, utils, testing=True)

	stdout = project.stage.new_list("stdout", [], monitor=[0, 0, 480-2, 292])

	tmp = cat.new_var("testtmp")

	from Crypto.Cipher import ChaCha20_Poly1305

	test_nonce = bytes(12)
	test_key = bytes.fromhex("7b9a4bc2c6b951879318e7ffcc92f53938790663109224f75acba604bc598b25")
	msg = b"hello"

	chachapoly_ct, chachapoly_tag = ChaCha20_Poly1305.new(key=test_key, nonce=test_nonce).encrypt_and_digest(msg)

	print("chachapoly_ct:", chachapoly_ct.hex())
	print("chachapoly_tag:", chachapoly_tag.hex())

	cat.on_flag([
		chachapoly1305.chacha20_poly1305(
			test_key.hex(),
			test_nonce.hex(),
			chachapoly_ct.hex()
		),
		stdout.append(chachapoly1305.join.hex_out),
		IF (chachapoly1305.join.hex_out == chachapoly_tag.hex()) [
			stdout.append("Test passed!"),
		],
		
		chachapoly1305.encrypt(
			test_key.hex(),
			test_nonce.hex(),
			msg.hex()
		),
		stdout.append(chachapoly1305.encrypt.ct_out.join(chachapoly1305.encrypt.tag_out)),
		IF (chachapoly1305.encrypt.ct_out.join(chachapoly1305.encrypt.tag_out) == (chachapoly_ct+chachapoly_tag).hex()) [
			stdout.append("Test passed!"),
		],

		chachapoly1305.decrypt(
			test_key.hex(),
			test_nonce.hex(),
			chachapoly1305.encrypt.ct_out,
			chachapoly1305.encrypt.tag_out
		),
		stdout.append(chachapoly1305.decrypt.msg_valid),
		stdout.append(chachapoly1305.decrypt.hex_out),
		IF ((chachapoly1305.decrypt.msg_valid == "true").AND(chachapoly1305.decrypt.hex_out == msg.hex())) [
			stdout.append("Test passed!"),
		],
	])

	project.save("../test.sb3", execute=False)
