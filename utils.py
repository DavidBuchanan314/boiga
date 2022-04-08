from boiga.ast import *

class Utils():
	def __init__(self, cat):
		self.HEX_LUT = cat.new_list("HEX_LUT", [f"{x:02x}" for x in range(0x100)])

		# note: we can elide the "+1" required to adjust for 1-indexing by simply chopping off the
		# first entry of the table. Looking up the 0th item of a scratch array returns "", which is zero-ish
		# when used in subsequent math ops
		# note also: the array index ends up with a -1+1 on the end, which the ast optimisation pass strips out
		XOR_LUT = cat.new_list("XOR_LUT", [a^b for a in range(0x100) for b in range(0x100)][1:])
		def bitxor(a, b, nbits=32):
			result = XOR_LUT[(a&0xff)*256+(b&0xff)-1]
			for i in range(8, nbits, 8):
				result += XOR_LUT[((a>>i)&0xff)*256+((b>>i)&0xff)-1] << i
			return result
		
		self.XOR_LUT = XOR_LUT
		self.bitxor = bitxor
