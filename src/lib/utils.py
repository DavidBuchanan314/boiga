from boiga.ast import *

class Utils():
	def __init__(self, cat):
		self.HEX_LUT = cat.new_list("HEX_LUT", [f"{x:02x}" for x in range(0x100)])

		# note: we can elide the "+1" required to adjust for 1-indexing by simply chopping off the
		# first entry of the table. Looking up the 0th item of a scratch array returns "", which is zero-ish
		# when used in subsequent math ops
		# note also: the array index ends up with a -1+1 on the end, which the ast optimisation pass strips out
		self.XOR_LUT = cat.new_list("XOR_LUT", [a^b for a in range(0x100) for b in range(0x100)][1:])

		# CHACHA stuff here is common between CSPRNG, BLAKE3, and CHACHA20
		QR_OFFSETS = [
			#  Odd round
			0, 4,  8, 12,  # 1st column
			1, 5,  9, 13,  # 2nd column
			2, 6, 10, 14,  # 3rd column
			3, 7, 11, 15,  # 4th column
			# Even round
			0, 5, 10, 15,  # diagonal 1 (main diagonal)
			1, 6, 11, 12,  # diagonal 2
			2, 7,  8, 13,  # diagonal 3
			3, 4,  9, 14,  # diagonal 4
		]
		magic = []
		for i in range(0, len(QR_OFFSETS), 4):
			a, b, c, d = [x+1 for x in QR_OFFSETS[i:i+4]]
			magic += [a, b, d, 2**16, 2**(32-16)]
			magic += [c, d, b, 2**12, 2**(32-12)]
			magic += [a, b, d, 2**8, 2**(32-8)]
			magic += [c, d, b, 2**7, 2**(32-7)]

		self.CHACHA_LUT = cat.new_list("CHACHA_LUT", magic)
		self.CHACHA_LUT_LEN = len(magic)
	
	def bytexor(self, a, b):
		return self.XOR_LUT[a*256+b-1]

	def bitxor(self, a, b, nbits=32):
		result = self.XOR_LUT[ensure_expression((a&0xff)*256)+(b&0xff)-1]
		for i in range(8, nbits, 8):
			result += self.XOR_LUT[ensure_expression(((a>>i)&0xff)*256)+((b>>i)&0xff)-1] << i
		return result

	def bitxor3(self, a, b, c, nbits=32):
		result = self.XOR_LUT[(a&0xff)*256+self.XOR_LUT[(b&0xff)*256+(c&0xff)-1]-1]
		for i in range(8, nbits, 8):
			result += self.XOR_LUT[((a>>i)&0xff)*256+self.XOR_LUT[((b>>i)&0xff)*256+((c>>i)&0xff)-1]-1] << i
		return result
