from boiga.codegen import Project
from boiga.ast import *

project = Project(template="test_files/Scratch Project.sb3")

cat = project.new_sprite("Sprite1")

my_variable = project.stage.new_var("my variable")
var_foo = cat.new_var("foo", 123)
test_list = cat.new_list("test_list", [1, 2, 3, 4])

cat.on_flag([
	my_variable <= 5,
]+[
	my_variable <= my_variable + my_variable for _ in range(5)
]+[
	var_foo <= my_variable * 123 + 1337,
	test_list[0] <= "foobar",
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
	forever([
		var_foo <= 123
	])
])

@cat.proc_def("add [number a] to [number b] if <my condition>")
def add_proc(number_a, number_b, my_cond): return [
	IF(my_cond, [
		var_foo <= number_a + number_b
	])
]

@cat.proc_def("multiply [number a] with [number b]")
def multiply_proc(number_a, number_b): return [
	var_foo <= number_a * number_b
]

cat.on_flag([
	add_proc(1, Literal(2) + 4, Literal(3) == 3),
	multiply_proc(2, 3)
])

project.save("test.sb3")
