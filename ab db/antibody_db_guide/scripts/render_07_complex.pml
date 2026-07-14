load 07_interface/data/pdb/1A14.cif, cplx
hide everything
show cartoon, chain H or chain L
color skyblue,  chain H
color palegreen, chain L
show surface, chain N
set transparency, 0.30
color wheat, chain N
select para, chain H and resi 52+54+56+99-101
select epi,  chain N and resi 369+370+400+401+403
show sticks, para
show sticks, epi
color orange, para
color red, epi
util.cnc (para or epi)
bg_color white
set ray_opaque_background, 1
set antialias, 2
orient chain H or chain L or chain N
zoom (para or epi), 9
ray 1500, 1100
png 07_interface/07_complex_3d.png, dpi=150
