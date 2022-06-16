from boiga import *

project = Project()

cat = project.new_sprite("Scratch Cat")
cat.add_costume("scratchcat", "examples/assets/scratchcat.svg", center=(48, 50))

cat.on_flag([
	Say("Hello, world!"),
])

project.save("examples/out/Boiga Examples: Hello World.sb3")
