from boiga.codegen import Project
from boiga.ast import *

project = Project(template="test_files/Scratch Project.sb3")

cat = project.new_sprite("Sprite1")

stdout = project.stage.new_list("stdout", [])
tmp = cat.new_var("tmp")
tmp2 = cat.new_var("tmp2")
tmp3 = cat.new_var("tmp3")
hex_out = cat.new_list("hex_out")

s20s = [
	cat.new_var(f"s20_s{i}", 0)
	for i in range(16)
]

s20s2 = [
	cat.new_var(f"s20_s2{i}", 0)
	for i in range(16)
]



def rotr(x, n, nbits=32):
	return ((x & 0xffffffff) >> n) + ((x % (1<<n)) << (nbits - n))

def rotl(x, n, nbits=32):
	return rotr(x, nbits-n, nbits)

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

"""
b ^= (a + d) <<< 7;
c ^= (b + a) <<< 9;
d ^= (c + b) <<< 13;
a ^= (d + c) <<< 18;
"""



@cat.proc_def("hex_decode [hex_in]")
def hex_decode(locals, hex_in): return [
	hex_out.delete_all(),
	locals.i[:hex_in.len():2] >> [
		hex_out.append( Literal("0x").join(hex_in[locals.i]).join(hex_in[locals.i+1]) + 0 )
	]
]

def hex_decode_le32(string, offset):
	hexstring = Literal("0x")
	for i in range(0, 8, 2)[::-1]:
		hexstring = hexstring.join(string[offset*8+i]).join(string[offset*8+i+1])
	return hexstring + 0 # "cast" to int

@cat.proc_def("salsa20_set_key [key_hex] [nonce_hex]")
def salsa20_set_key(locals, key_hex, nonce_hex): return [
	s20s[ 0] <= int.from_bytes(b"expa", "little"),
	s20s[ 1] <= hex_decode_le32(key_hex, 0),
	s20s[ 2] <= hex_decode_le32(key_hex, 1),
	s20s[ 3] <= hex_decode_le32(key_hex, 2),
	
	s20s[ 4] <= hex_decode_le32(key_hex, 3),
	s20s[ 5] <= int.from_bytes(b"nd 3", "little"),
	s20s[ 6] <= hex_decode_le32(nonce_hex, 0),
	s20s[ 7] <= hex_decode_le32(nonce_hex, 1),

	#s20s[ 8] <= 0, # pos
	#s20s[ 9] <= 0, # pos
	s20s[10] <= int.from_bytes(b"2-by", "little"),
	s20s[11] <= hex_decode_le32(key_hex, 4),

	s20s[12] <= hex_decode_le32(key_hex, 5),
	s20s[13] <= hex_decode_le32(key_hex, 6),
	s20s[14] <= hex_decode_le32(key_hex, 7),
	s20s[15] <= int.from_bytes(b"te k", "little"),
]

def salsa20_qr_outlined(locals, arrout, arrin, a, b, c, d): return [
	locals.tmp <= rotl(arrin[a] + arrin[d], 7),
	arrout[b] <= bitxor(arrin[b], locals.tmp),

	locals.tmp <= rotl(arrout[b] + arrin[a], 9),
	arrout[c] <= bitxor(arrin[c], locals.tmp),

	locals.tmp <= rotl(arrout[c] + arrout[b], 13),
	arrout[d] <= bitxor(arrin[d], locals.tmp),

	locals.tmp <= rotl(arrout[d] + arrout[c], 18),
	arrout[a] <= bitxor(arrin[a], locals.tmp),
]

def salsa20_qr_outlined2(locals, arrout, arrin, a, b, c, d): return [
	locals.tmp <= arrin[a] + arrin[d],
	locals.tmp <= rotl(locals.tmp, 7),
	arrout[b] <= bitxor(arrin[b], locals.tmp),

	locals.tmp <= arrout[b] + arrin[a],
	locals.tmp <= rotl(locals.tmp, 9),
	arrout[c] <= bitxor(arrin[c], locals.tmp),

	locals.tmp <= arrout[c] + arrout[b],
	locals.tmp <= rotl(locals.tmp, 13),
	arrout[d] <= bitxor(arrin[d], locals.tmp),

	locals.tmp <= arrout[d] + arrout[c],
	locals.tmp <= rotl(locals.tmp, 18),
	arrout[a] <= bitxor(arrin[a], locals.tmp),
]

def salsa20_qr_inlined(locals, arrout, arrin, a, b, c, d): return [
	arrout[b] <= bitxor(arrin[b], rotl(arrin[a] + arrin[d], 7)),
	arrout[c] <= bitxor(arrin[c], rotl(arrout[b] + arrin[a], 9)),
	arrout[d] <= bitxor(arrin[d], rotl(arrout[c] + arrout[b], 13)),
	arrout[a] <= bitxor(arrin[a], rotl(arrout[d] + arrout[c], 18)),
]

salsa20_qr = salsa20_qr_outlined

@cat.proc_def("salsa20_block [pos0] [pos1]")
def salsa20_block(locals, pos0, pos1): return [
	s20s[8] <= pos0,
	s20s[9] <= pos1,

	salsa20_qr(locals, s20s2, s20s,  0,  4,  8, 12),
	salsa20_qr(locals, s20s2, s20s,  5,  9, 13,  1),
	salsa20_qr(locals, s20s2, s20s, 10, 14,  2,  6),
	salsa20_qr(locals, s20s2, s20s, 15,  3,  7, 11),

	repeatn (9) [
		salsa20_qr(locals, s20s2, s20s2,  0,  1,  2,  3),
		salsa20_qr(locals, s20s2, s20s2,  5,  6,  7,  4),
		salsa20_qr(locals, s20s2, s20s2, 10, 11,  8,  9),
		salsa20_qr(locals, s20s2, s20s2, 15, 12, 13, 14),

		salsa20_qr(locals, s20s2, s20s2,  0,  4,  8, 12),
		salsa20_qr(locals, s20s2, s20s2,  5,  9, 13,  1),
		salsa20_qr(locals, s20s2, s20s2, 10, 14,  2,  6),
		salsa20_qr(locals, s20s2, s20s2, 15,  3,  7, 11),
	],

	salsa20_qr(locals, s20s2, s20s2,  0,  1,  2,  3),
	salsa20_qr(locals, s20s2, s20s2,  5,  6,  7,  4),
	salsa20_qr(locals, s20s2, s20s2, 10, 11,  8,  9),
	salsa20_qr(locals, s20s2, s20s2, 15, 12, 13, 14),

	[
		s20s2[i] <= (s20s2[i] + s20s[i]) & 0xffff_ffff
		for i in range(16)
	]

]

@cat.proc_def("benchmark_salsa20")
def benchmark_salsa20(locals): return [
	stdout.append("Benchmarking..."),
	salsa20_set_key("4564e1f895223a397d0eb97551859230c17bb30960b28ef3a2fa860ff26f4068", "b627c09a4f3bf073"),
	locals.bench_start <= millis_now,
	locals.i <= 0,
	repeatuntil ((millis_now - locals.bench_start) > 1000) [
		salsa20_block(locals.i, 0),
		locals.i.changeby(1)
	],
	stdout.append(Literal("Benchmarked ").join((locals.i*64)).join(" Bytes/s"))
]

cat.on_flag([
	stdout.delete_all(),
	salsa20_set_key("4564e1f895223a397d0eb97551859230c17bb30960b28ef3a2fa860ff26f4068", "b627c09a4f3bf073"),
	#[
	#	stdout.append(s20s[i])
	#	for i in range(16)
	#],
	stdout.append("OUT:"),
	salsa20_block(0, 0),
	#[
	#	stdout.append(s20s2[i])
	#	for i in range(16)
	#],
	benchmark_salsa20(),
#	benchmark_sha256(),
#	stdout.append("Demonstration:"),
#	repeatuntil (Answer() == "exit") [
#		stdout.append("Enter input string: (Lowercase-only, for now)"),
#		AskAndWait(),
#		sha256(Answer()),
#		stdout.append(Literal("sha256(").join(Answer()).join(") =")),
#		stdout.append(sha256.out)
#	]
])

project.save("test.sb3")
