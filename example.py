from src.boiga.codegen import Project
from src.boiga.ast import *

#project = Project(template="test_files/Scratch Project.sb3")
project = Project()


cat = project.new_sprite("Scratch Cat")
cat.add_costume("scratchcat", "test_files/scratchcat.svg", center=(48, 50))

my_variable = project.stage.new_var("my variable")
var_foo = cat.new_var("foo", 123)
stdout = project.stage.new_list("stdout", [], monitor=[0, 0, 480-2, 140])

"""
cat.on_flag([
	my_variable <= 5,
]+[
	my_variable <= my_variable + my_variable for _ in range(5)
]+[
	var_foo <= my_variable * 123 + 1337,
	stdout[0] <= "foobar",
	repeatn(12, [
		var_foo <= var_foo * 2,
		var_foo <= var_foo * 3,
		IF((var_foo == 3).OR(Literal(2) != 2), [
			var_foo <= 4
		]),
		IF(var_foo == 7, [
			var_foo <= 123
		]).ELSE([
			var_foo <= 456
		])
	]),
	#forever([
	#	var_foo <= 123
	#])
])
"""

""""
@cat.proc_def("add [number a] to [number b] if <my condition>")
def add_proc(locals, number_a, number_b, my_cond): return [
	IF(my_cond, [
		var_foo <= number_a + number_b
	])
]
"""

hex_out = cat.new_list("hex_out")
i = cat.new_var("i")
tmp = cat.new_var("tmp")

@cat.proc_def("hex decode [hex_in]")
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


"""
cat.on_flag(
	i[0:100:5] >> [
		var_foo.changeby(i)
	]
)
"""

project.save("test.sb3")
