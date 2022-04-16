from boiga import *

project = Project()

cat = project.new_sprite("Scratch Cat")
cat.add_costume("scratchcat", "examples/assets/scratchcat.svg", center=(48, 50))

my_variable = project.stage.new_var("my variable")
var_foo = cat.new_var("foo", 123)
stdout = project.stage.new_list("stdout", [], monitor=[0, 0, 480-2, 140])


hex_out = cat.new_list("hex_out")
i = cat.new_var("i")
tmp = cat.new_var("tmp")

@cat.proc_def()
def hex_decode(locals, hex_in): return [
	hex_out.delete_all(),
	locals.i[:hex_in.len():2] >> [
		hex_out.append( Literal("0x").join(hex_in[locals.i]).join(hex_in[locals.i+1]) + 0 )
	]
]

@cat.proc_def("multiply [number a] with [number b]")
def multiply_proc(locals, number_a, number_b): return [
	locals.result <= number_a * number_b
]

cat.on_flag([
	stdout.delete_all(),
	stdout.append("Hello, world!"),
	multiply_proc(7, 9),
	stdout.append(multiply_proc.result),
	hex_decode("deadbeefcafebabe"),
	tmp <= "",
	i[:hex_out.len()] >> [
		tmp <= tmp.join(hex_out[i]),
		If (i != hex_out.len() - 1) [
			tmp <= tmp.join(", ")
		]
	],
	stdout.append(tmp),
	stdout.append(hex_out)
])

project.save("examples/out/Boiga Examples: Basics.sb3")
