"""Where each fighter's arm art actually bends.

``char_rig`` cuts a one-piece arm into upper arm, forearm and hand so that the
elbow can bend. The cut has to land on the joints the ART draws - not on
``METRICS``. The painters draw a bent arm whose forearm already runs at about
45 degrees and whose whole length is ~80px, while the metric arm is 144px long;
cutting at ``pivot + uarm`` therefore severed the forearm in mid-tube, landed
past the drawn wrist, and left the "hand" slice empty. That is why the arms
read as broken.

Values are ``(elbow, wrist)`` in part pixels, taken from each painter's
``arm()``. The far arm is the near one flipped left-right by the painter, so its
x is mirrored about the part width. The shoulder is not listed: it is the
part's own ``rig.json`` pivot.

If a painter's arm geometry changes, update its row - the rest-pose render
(``char_rig.py --rest <id>``) compares the assembled rig against the art and
will show any drift as a gap or an offset limb.
"""

ARM_JOINTS = {
    #            near (elbow, wrist)        far (elbow, wrist)
    "lightning": (((62, 62), (84, 84)), ((86, 62), (64, 84))),
    "rain": (((58, 156), (82, 178)), ((88, 160), (68, 182))),
    "thunder": (((58, 162), (82, 186)), ((150, 166), (130, 190))),
    # Lo Pan's arm is a hanging bell sleeve: the bare forearm leaves the cloth
    # at y~150 and the hand starts at y~176. Cutting at 158/186 landed on the
    # sleeve hem, so the "forearm" and "hand" pieces were two chips of navy
    # floating below his real arm.
    "lopan": (((56, 150), (84, 176)), ((132, 150), (104, 176))),
    "eggshen": (((60, 60), (80, 82)), ((86, 62), (70, 84))),
    "wangchi": (((62, 60), (82, 82)), ((84, 62), (68, 84))),
    # Eddie's arm is cut on Wang Chi's numbers: the sleeve ends and the bare
    # forearm starts at the same place, so the joints land identically.
    "eddilee": (((62, 60), (82, 82)), ((84, 62), (68, 84))),
    "gracielaw": (((60, 60), (80, 82)), ((88, 60), (68, 82))),
    "jade": (((60, 60), (80, 82)), ((88, 60), (68, 82))),
    "jackburton": (((27, 74), (33, 126)), ((22, 74), (16, 126))),
}
