#!/bin/python

import pyrandr as randr

# get connected screens
cs = randr.connected_screens()
es = randr.enabled_screens()

for enabled, connected in zip(cs, es):
    # available resolutions as a tuple in the form of (width, height)
    reslist = enabled.available_resolutions()
    print(type(enabled))
    print(max(reslist))

# cs.set_resolution((1024, 768))
# cs.set_as_primary(True)
#
# # rotate output contents by 90 degrees in the clockwise direction
# cs.rotate(randr.RotateDirection.Right)
#
# cs.apply_settings()
