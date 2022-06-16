# boiga

Boiga is a Python library enabling ergonomic Scratch 3.0 code generation.

Have you ever attempted to author advanced or accelerated algorithms in Scratch? It's not much fun - you might end up making miles of mouse movements for even the most miniscule of modifications.

Boiga (ab)uses Python's operator overloading, to write Scratch expressions with intuitive(ish) Python syntax. We expose a simple AST representation, making it easy to write custom code generators and macros.

See the examples directory for... examples.

## Project Status:

It's a working prototype. Not all blocks are supported, but you can use this to write non-trivial scratch projects.
If you plan to actually use this for something, you might want to make a copy of the code - I'll probably be making lots of breaking changes as I implement more features.

## Features:
- Scratch .sb3 code generation.
- Very basic AST optimisation (e.g. constant folding)
- Optional inlining of "custom blocks".

## TODO
- Static allocation of "sub-lists" within lists
- Dynamic allocation of space within lists (i.e. malloc)?
- For both of the above, we can pass indices around like pointers

## Building Examples:

```sh
python3 -m examples
```

NOTE: Requires Python 3.10 or above!
