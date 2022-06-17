# boiga

Boiga is a Python library enabling ergonomic Scratch 3.0 code generation.

Have you ever attempted to author advanced or accelerated algorithms in Scratch? It's not much fun - you might end up making miles of mouse movements for even the most miniscule of modifications.

Boiga (ab)uses Python's operator overloading, to write Scratch expressions with intuitive(ish) Python syntax. We expose a simple AST representation, making it easy to write custom code generators and macros.

See the examples directory for... examples. Further usage examples can be seen in my [Scratch Cryptography Library](https://github.com/DavidBuchanan314/scratch-cryptography-library).

## Project Status:

It's a working prototype. Not all blocks are supported, but you can use this to write non-trivial scratch projects.
If you plan to actually use this for something, you might want to make a copy of the code - I'll probably be making lots of breaking changes as I implement more features.

## Features:
- Scratch .sb3 code generation.
- Very basic AST optimisation (e.g. constant folding)
- Optional inlining of "custom blocks".
- Some bitwise operators.
- 0-indexed lists.

## TODO
- Documentation (sorry lol - for now, just look at the examples)
- Static allocation of "sub-lists" within lists
- Dynamic allocation of space within lists (i.e. malloc)?
- For both of the above, we can pass indices around like pointers

## Building Examples:

```sh
python3 -m examples
```

NOTE: Requires Python 3.10 or above!

[`examples/helloworld.py`](https://github.com/DavidBuchanan314/boiga/blob/main/examples/helloworld.py) looks like this:

```python
from boiga import *

project = Project()

cat = project.new_sprite("Scratch Cat")
cat.add_costume("scratchcat", "examples/assets/scratchcat.svg", center=(48, 50))

cat.on_flag([
	Say("Hello, world!"),
])

project.save("examples/out/Boiga Examples: Hello World.sb3")
```

Which compiles to the following scratch project:

<img width="1019" alt="image" src="https://user-images.githubusercontent.com/13520633/174166081-4aa1f495-ac20-411d-aa53-0546c55339bd.png">

Obviously, it's probably easier to write programs like that using the drag-and-drop interface. Conversely, [`examples/branflakes.py`](https://github.com/DavidBuchanan314/boiga/blob/main/examples/branflakes.py) implements a brainf\*ck to Scratch compiler, which compiles a "99 bottles of beer" program into the following:

<img width="256" alt="image" src="https://user-images.githubusercontent.com/13520633/174167667-56332085-44df-4768-a718-bfa00ab798ce.png">

This is just a preview, the whole script doesn't even come close to fitting in a single screenshot! You can see the full scratch code [here](https://scratch.mit.edu/projects/677776603/).
