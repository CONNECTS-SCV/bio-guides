load 06_structure/data/demo_antibody_igfold.pdb, fv
hide everything
show cartoon
bg_color white
set ray_opaque_background, 1
set antialias, 2
spectrum b, blue_white_red, fv
orient fv
turn y, 20
zoom fv, 2
ray 1500, 1100
png 06_structure/06_structure_3d.png, dpi=150
