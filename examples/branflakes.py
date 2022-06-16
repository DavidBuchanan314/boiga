from boiga import *

ASCII_LUT = Literal("�"*0x1f + bytes(range(0x20, 0x7f)).decode())

project = Project()

stdout = project.stage.new_list("stdout", [], monitor=[0, 0, 480-2, 292])

sprite = project.new_sprite("Branflakes")
bfmem = sprite.new_list("bfmem")
memptr = sprite.new_var("memptr")

@sprite.proc_def()
def putchar(locals, codepoint): return [
	If (codepoint == 0x0a) [
		stdout.append(locals.line_buffer),
		locals.line_buffer <= ""
	].Else [
		If (codepoint == 0x0d) [
			locals.line_buffer <= ""
		].Else [
			locals.line_buffer <= locals.line_buffer.join(ASCII_LUT[codepoint-1])
		]
	]
]

def compile_bf(prog, is_subblock=False):
	compiled = []
	i = 0
	ptrshift = 0
	while i < len(prog):
		if prog[i] in "+-":
			delta = 0
			while i < len(prog) and prog[i] in "+-":
				delta += 1 if prog[i] == "+" else -1
				i += 1
			compiled.append(
				bfmem[memptr+ptrshift] <= (bfmem[memptr+ptrshift] + delta) & 0xff
			)
		elif prog[i] in "><":
			delta = 0
			while i < len(prog) and prog[i] in "><":
				delta += 1 if prog[i] == ">" else -1
				i += 1
			ptrshift += delta
		elif prog[i] == "[":
			depth = 0
			i += 1
			body = ""
			while i < len(prog):
				if prog[i] == "[":
					depth += 1
				elif prog[i] == "]":
					if depth:
						depth -= 1
					else:
						i += 1
						break
				body += prog[i]
				i += 1
			else:
				raise Exception("Unexpected EOF")

			compiled += [
				memptr.changeby(ptrshift) if ptrshift else [],
				RepeatUntil (bfmem[memptr] == 0) [
					compile_bf(body, is_subblock=True)
				]
			]
			ptrshift = 0

		elif prog[i] == "]":
			raise Exception("Unexpected ]")
		elif prog[i] == ",":
			raise Exception("Not implemented: ,")
		elif prog[i] == ".":
			compiled.append(
				putchar(bfmem[memptr+ptrshift])
			)
			i += 1
		else:
			i += 1
	
	if is_subblock and ptrshift:
		compiled.append(
			memptr.changeby(ptrshift)
		)
	
	return compiled

@sprite.proc_def(turbo=False)
def bf_main(locals):
	return compile_bf(open("examples/assets/beer.b").read())

sprite.on_flag([
	stdout.delete_all(),
	bfmem.delete_all(),
	Repeat (30000) [
		bfmem.append(0)
	],
	memptr <= 0,
	bf_main()
])

project.save("examples/out/Boiga Examples: Branflakes.sb3")
