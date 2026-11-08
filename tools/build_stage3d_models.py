"""Bake the 3D stages' unlit intent into core glTF.

The three Storms stages draw a floating island from SuperFromND's Third Heights
pack. Both .glb files describe their materials as KHR_materials_unlit, which is
an extension: a renderer that does not implement it falls back to ordinary
lighting, and the scene carries no lights at all, so the island came out as a
black field with only the stages' 2D weather drawn over it.

Core glTF can express the same thing without the extension: a material whose
emissive texture is its own base texture and whose emissive factor is white is
drawn at full texture brightness whatever the lighting is. That is what
"unlit" means, so the models are rewritten that way and the extension is
dropped from the material and from extensionsUsed. Nothing else in the file is
touched - geometry, nodes, animations and the embedded PNG textures are carried
through byte for byte.

Run:  python3 tools/build_stage3d_models.py
"""

from __future__ import annotations

import json
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = ("stages/stage3d.glb", "stages/stage3d_outline.glb")

GLB_MAGIC = 0x46546C67
CHUNK_JSON = 0x4E4F534A
CHUNK_BIN = 0x004E4942
UNLIT = "KHR_materials_unlit"


def read_glb(path):
    with open(path, "rb") as f:
        data = f.read()
    magic, version, _length = struct.unpack("<III", data[:12])
    if magic != GLB_MAGIC or version != 2:
        raise SystemExit(f"{path} is not a glTF 2.0 binary")
    chunks, off = [], 12
    while off < len(data):
        clen, ctype = struct.unpack("<II", data[off:off + 8])
        chunks.append((ctype, data[off + 8:off + 8 + clen]))
        off += 8 + clen + (-clen % 4)
    gltf: dict | None = None
    blob = b""
    for ctype, payload in chunks:
        if ctype == CHUNK_JSON:
            gltf = json.loads(payload.decode("utf-8"))
        elif ctype == CHUNK_BIN:
            blob = payload
    if gltf is None:
        raise SystemExit(f"{path} has no JSON chunk")
    return gltf, blob


def write_glb(path, gltf, blob):
    payload = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    payload += b" " * (-len(payload) % 4)
    body = struct.pack("<II", len(payload), CHUNK_JSON) + payload
    if blob:
        padded = blob + b"\0" * (-len(blob) % 4)
        body += struct.pack("<II", len(padded), CHUNK_BIN) + padded
    header = struct.pack("<III", GLB_MAGIC, 2, 12 + len(body))
    with open(path + ".tmp", "wb") as f:
        f.write(header + body)
    os.replace(path + ".tmp", path)


def bake_unlit(path):
    """Rewrite one model: unlit materials become emissive-at-full-brightness."""
    gltf, blob = read_glb(path)
    changed = 0
    for material in gltf.get("materials", []):
        ext = material.get("extensions") or {}
        if UNLIT not in ext:
            continue
        ext.pop(UNLIT, None)
        if ext:
            material["extensions"] = ext
        else:
            material.pop("extensions", None)
        pbr = material.setdefault("pbrMetallicRoughness", {})
        base = pbr.get("baseColorTexture")
        if base is not None:
            material["emissiveTexture"] = {"index": base["index"]}
            if "texCoord" in base:
                material["emissiveTexture"]["texCoord"] = base["texCoord"]
        material["emissiveFactor"] = [1.0, 1.0, 1.0]
        changed += 1
    used = [e for e in gltf.get("extensionsUsed", []) if e != UNLIT]
    if "extensionsUsed" in gltf:
        if used:
            gltf["extensionsUsed"] = used
        else:
            del gltf["extensionsUsed"]
    required = [e for e in gltf.get("extensionsRequired", []) if e != UNLIT]
    if "extensionsRequired" in gltf:
        if required:
            gltf["extensionsRequired"] = required
        else:
            del gltf["extensionsRequired"]
    write_glb(path, gltf, blob)
    return changed


def main(argv=()):
    for rel in MODELS:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            raise SystemExit(f"{rel} is missing")
        changed = bake_unlit(path)
        gltf, blob = read_glb(path)
        names = [m.get("name") for m in gltf.get("materials", [])]
        emissive = [m.get("emissiveFactor") for m in gltf.get("materials", [])]
        print(f"{rel}: {changed} unlit material(s) baked to emissive "
              f"({len(gltf.get('materials', []))} material(s): {names})")
        print(f"  emissive factors {emissive}, "
              f"extensions {gltf.get('extensionsUsed', 'none')}, "
              f"{os.path.getsize(path) / 1e6:.1f} MB")


if __name__ == "__main__":
    main(sys.argv[1:])
