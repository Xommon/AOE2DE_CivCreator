# Micheal Quentin
# 30. August 2025
# Bula - Map Generator

# make_map_from_images.py
from PIL import Image
import numpy as np
from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario
from AoE2ScenarioParser.datasets.terrains import TerrainId

# ---- INPUTS ----
HEIGHTMAP_PATH = "heightmap.png"       # 8-bit or 16-bit grayscale
TERRAINMAP_PATH = "terrainmap.png"     # optional RGB image
OUT_PATH = "ImportedMap.aoe2scenario"

# Terrain palette: map (R,G,B) -> TerrainId (change to taste)
TERRAIN_PALETTE = {
    (34,139,34): TerrainId.GRASS_1,      # foresty green -> grass
    (222,184,135): TerrainId.DIRT_3,     # tan -> dirt
    (0, 105, 148): TerrainId.SHALLOWS,    # teal -> shallows
    (0, 0, 255): TerrainId.WATER_MEDIUM,      # blue -> water
    #(139,137,137): TerrainId.D,       # gray -> rock
}

# Elevation scaling (0–MAX_ELEV, DE caps around ~30–32 effectively for visuals)
MAX_ELEV = 20

# ---- LOAD IMAGES ----
h_img = Image.open(HEIGHTMAP_PATH).convert("I")  # preserves 16-bit if present
h = np.array(h_img, dtype=np.uint32)
# Normalize to 0..MAX_ELEV
h_norm = (h - h.min()) / max(1, (h.max() - h.min()))
elev = (h_norm * MAX_ELEV).astype(np.uint8)

# Terrain map (optional); if not provided, default to grass
if TERRAINMAP_PATH:
    t_img = Image.open(TERRAINMAP_PATH).convert("RGB")
    t = np.array(t_img, dtype=np.uint8)
else:
    t = None

# Square size requirement (DE maps must be square; max 480) :contentReference[oaicite:3]{index=3}
size = max(elev.shape)
if size > 480:
    raise ValueError("Map too large for DE (max 480). Resize your images.")
# Pad/crop to square
def to_square(arr, fill=0):
    if arr is None: return None
    h, w = arr.shape[:2]
    s = max(h, w)
    out = np.full((s, s, *arr.shape[2:]), fill, dtype=arr.dtype) if arr.ndim==3 else np.full((s, s), fill, dtype=arr.dtype)
    out[:h, :w, ...] = arr[:s, :s, ...]
    return out

elev = to_square(elev, 0)
t = to_square(t, 0) if t is not None else None
N = elev.shape[0]

# ---- BUILD SCENARIO ----
scn = AoE2DEScenario.from_empty()  # empty template
mm = scn.map_manager
pm = scn.player_manager

# Set map size (must be square) :contentReference[oaicite:4]{index=4}
mm.set_map_size(N)

# Paint elevation
for y in range(N):
    for x in range(N):
        mm.set_elevation_at(x, y, int(elev[y, x]))

# Paint terrain
if t is not None:
    # Build fast LUT from 24-bit color -> terrain id (fallback grass)
    palette = { (r<<16)|(g<<8)|b: tid for (r,g,b), tid in TERRAIN_PALETTE.items() }
    default_terrain = TerrainId.GRASS_1
    for y in range(N):
        for x in range(N):
            r, g, b = map(int, t[y, x])
            key = (r<<16)|(g<<8)|b
            tid = palette.get(key, default_terrain)
            mm.set_terrain_id_at(x, y, tid)
else:
    mm.fill_terrain(TerrainId.GRASS_1)

# Example: place a Town Center + villagers for P1 at center
cx = cy = N // 2
um = scn.unit_manager
p1 = 1
um.add_unit(player_id=p1, unit_const=109, x=cx+2, y=cy+2)  # Town Center (DE const id)
for i in range(6):
    um.add_unit(player_id=p1, unit_const=83, x=cx+4+i%3, y=cy+4+i//3)  # Villager (male)

# Optional: reveal map for P1, fix resources, etc.
pm.players[p1].food = 200
pm.players[p1].wood = 200
pm.players[p1].stone = 0
pm.players[p1].gold = 0
pm.players[p1].all_technologies = False

# Save the file
scn.write_to_file(OUT_PATH)
print(f"Wrote {OUT_PATH}. Move it to your DE scenario folder and open in the editor.")
