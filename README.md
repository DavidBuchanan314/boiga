# boiga
Boiga is a Python library enabling ergonomic Scratch 3.0 code generation.

Have you ever attempted to author advanced or accelerated algorithms in Scratch? It's not much fun - you might end up making miles of mouse movements for even the most miniscule of modifications.

Boiga (ab)uses Python's operator overloading, to write Scratch expressions with intuitive(ish) Python syntax. We expose a simple AST representation, making it easy to write custom code generators and macros. 

## Features:
- Scratch .sb3 code generation. (Status: Prototype)
- AST optimisation (e.g. constant folding) (Status: Some very basic optimisations)

## TODO
- Static allocation of "sub-lists" within lists
- Dynamic allocation of space within lists (i.e. malloc)?
- For both of the above, we can pass indices around like pointers
