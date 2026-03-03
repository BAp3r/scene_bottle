import sys
import os
from pxr import Usd, UsdGeom, UsdPhysics

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

stage_bottle = Usd.Stage.Open(os.path.join(ROOT_DIR, "usds", "objects", "SM_BottleA.usd"))
print("Bottle root prims:")
for p in stage_bottle.GetPseudoRoot().GetChildren():
    print(p.GetName(), p.GetAppliedSchemas())

stage_table = Usd.Stage.Open(os.path.join(ROOT_DIR, "usds", "objects", "thor_table.usd"))
print("\nTable root prims:")
for p in stage_table.GetPseudoRoot().GetChildren():
    print(p.GetName(), p.GetAppliedSchemas())

