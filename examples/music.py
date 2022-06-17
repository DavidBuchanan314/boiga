from boiga import *

project = Project()

cat = project.new_sprite("Scratch Cat")
cat.add_costume("scratchcat", "examples/assets/scratchcat.svg", center=(48, 50))

cat.on_flag([
	SetTempo(50),
	ChangeTempoBy(10),
	SetInstrument(Instruments.ElectricPiano),
	PlayNote(60, 0.25),
	RestFor(0.5),
	PlayDrum(Drums.HandClap, 1),
	Say(GetTempo()),
])

project.save("examples/out/Boiga Examples: Music.sb3")
