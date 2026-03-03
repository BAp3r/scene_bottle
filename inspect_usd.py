import sys
from pxr import Usd, UsdGeom, UsdPhysics

stage_bottle = Usd.Stage.Open("usds/SM_BottleA.usd")
print("Bottle root prims:")
for p in stage_bottle.GetPseudoRoot().GetChildren():
    print(p.GetName(), p.GetAppliedSchemas())

stage_table = Usd.Stage.Open("usds/thor_table.usd")
print("\nTable root prims:")
for p in stage_table.GetPseudoRoot().GetChildren():
    print(p.GetName(), p.GetAppliedSchemas())

