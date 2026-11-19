# Modeling from measurements (calipers / photo / existing part)

1. **Reference and coordinates:** make the flattest, largest face the XY plane and a distinct hole/edge the origin. Ask the user which face is "bottom" and which edge is "left", or state it explicitly.
2. **Dimension list:** in `P` at the top of `model.py`, with a comment saying how each was measured (`# outer width, calipers, mean of 3`).
3. **Ask about ambiguities:** wall thickness, chamfers/radii, hole diameter (inner jaws), thread/pitch, symmetry assumption. If you can't ask, mark it as an assumption.
4. **Build:** start from the dominant primitive (box / cylinder / extruded profile), then subtract features from largest to smallest (pockets, holes, slots), chamfers/radii last.
5. **Fit allowance:** if the part mates with another, add clearance (FDM: sliding 0.25–0.35, press 0–0.1). Keep measured and modeled values as separate parameters (`P["hole_measured"]`, `P["hole_model"] = measured + allowance`).
6. **Verify:** show the build images to the user; list critical dimensions as a table ("measured → modeled"). If possible, suggest printing a small test coupon of the critical fit first.
