from isaacsim import SimulationApp
app = SimulationApp({"headless": True})

from pxr import Usd, UsdGeom, UsdPhysics
import os

def analyze(usd_path):
    print(f"\nAnalyzing {os.path.basename(usd_path)}")
    stage = Usd.Stage.Open(usd_path)
    root = stage.GetDefaultPrim()
    if not root:
        root = stage.GetPseudoRoot().GetChildren()[0]
    
    # Check physics
    print("Schemas on root:")
    print(" ", root.GetAppliedSchemas())
    
    # Find any RigidBodies
    rb_count = 0
    col_count = 0
    for p in stage.Traverse():
        if p.HasAPI(UsdPhysics.RigidBodyAPI): rb_count += 1
        if p.HasAPI(UsdPhysics.CollisionAPI): col_count += 1
    print(f"RigidBody APIs found: {rb_count}")
    print(f"Collision APIs found: {col_count}")
    
    # Compute bounds
    bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
    bounds = bbox_cache.ComputeWorldBound(root).ComputeAlignedRange()
    mn = bounds.GetMin()
    mx = bounds.GetMax()
    print(f"Bounds: Min({mn[0]:.2f}, {mn[1]:.2f}, {mn[2]:.2f}), Max({mx[0]:.2f}, {mx[1]:.2f}, {mx[2]:.2f})")
    print(f"Size: {mx[0]-mn[0]:.2f} x {mx[1]-mn[1]:.2f} x {mx[2]-mn[2]:.2f}")

analyze("usds/gr2v4_1_0_fourier_hand_6dof/gr2v4_1_0_fourier_hand_6dof.usd")
analyze("usds/thor_table.usd")
analyze("usds/SM_BottleA.usd")

app.close()
