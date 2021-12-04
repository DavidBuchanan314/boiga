from boiga.codegen import *
from boiga.ast import *

project = Project(template="test_files/Scratch Project.sb3")

cat = project.new_sprite("Sprite1")

my_variable = project.stage.new_var("my variable")
var_foo = cat.new_var("foo", 123)
test_list = cat.new_list("test_list", [1, 2, 3, 4])

cat.add_script(on_flag([
	my_variable <= 5,
]+[
	my_variable <= my_variable + my_variable for _ in range(5)
]+[
	var_foo <= my_variable * 123 + 1337,
	test_list[0] <= "foobar",
]))

add_proc = cat.proc_def("add [number a] to [number b]",
	lambda number_a, number_b: [
		var_foo <= number_a + number_b
	]
)

cat.add_script(on_flag([
#	add_proc(1, 2)
]))

project.save("test.sb3")
