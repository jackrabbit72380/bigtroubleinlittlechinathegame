"""Rasterise a stage's own .glb into the picture the stage draws.

The three Third Heights stages are an island that the pack ships as glTF, and the
cards for them have been painted pictures of the arena rather than the arena:
whatever the painting, a card that is not the stage's own view does not look like
the stage. This renders the model instead - geometry and UVs read straight out of
the glTF, the material's own texture sampled per pixel, a z-buffer, and the same
vertical field of view the stage defs give the camera ([Camera] fov = 30).

Everything the pack's materials express is already core glTF: the extension was
baked away by tools/build_stage3d_models.py, so each material is a texture drawn
at full brightness whatever the lighting is. That is what makes this render the
stage's colours rather than a guess at a light rig the scene does not have.

    import glb_render
    picture = glb_render.render("stages/stage3d.glb", (960, 316), fov=30.0)

No camera animation, no skinning and no mipmaps: the islands are static meshes
over a still sky, which is what these cards show.
"""

import io
import json
import struct

import numpy as np
from PIL import Image

GLB_MAGIC = 0x46546C67
CHUNK_JSON = 0x4E4F534A
CHUNK_BIN = 0x004E4942

COMPONENT = {5120: np.int8, 5121: np.uint8, 5122: np.int16,
             5123: np.uint16, 5125: np.uint32, 5126: np.float32}
WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def read_glb(path):
    """(glTF json, binary chunk) of a GLB."""
    with open(path, "rb") as handle:
        data = handle.read()
    magic, version, _length = struct.unpack("<III", data[:12])
    if magic != GLB_MAGIC or version != 2:
        raise SystemExit("%s is not a glTF 2.0 binary" % path)
    gltf, blob, off = None, b"", 12
    while off < len(data):
        clen, ctype = struct.unpack("<II", data[off:off + 8])
        payload = data[off + 8:off + 8 + clen]
        if ctype == CHUNK_JSON:
            gltf = json.loads(payload.decode("utf-8"))
        elif ctype == CHUNK_BIN:
            blob = payload
        off += 8 + clen + (-clen % 4)
    if gltf is None:
        raise SystemExit("%s has no JSON chunk" % path)
    return gltf, blob


def accessor(gltf, blob, index):
    """One accessor as an (count, components) array, honouring byteStride."""
    acc = gltf["accessors"][index]
    view = gltf["bufferViews"][acc["bufferView"]]
    dtype = np.dtype(COMPONENT[acc["componentType"]])
    width = WIDTH[acc["type"]]
    count = acc["count"]
    start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = view.get("byteStride") or dtype.itemsize * width
    span = stride * (count - 1) + dtype.itemsize * width
    buf = np.frombuffer(blob, dtype=np.uint8, count=span, offset=start)
    if stride == dtype.itemsize * width:
        out = buf.view(dtype).reshape(count, width)
    else:
        out = np.stack([buf[i * stride:i * stride + dtype.itemsize * width]
                        .view(dtype).reshape(width) for i in range(count)])
    return out.astype(np.float64) if dtype.kind == "f" else out


def quat_matrix(quat):
    """Rotation matrix from a glTF (x, y, z, w) quaternion."""
    x, y, z, w = quat
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), 0.0],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), 0.0],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), 0.0],
        [0.0, 0.0, 0.0, 1.0]])


def node_matrix(node):
    """A node's local transform."""
    if "matrix" in node:
        return np.array(node["matrix"], dtype=np.float64).reshape(4, 4).T
    out = quat_matrix(node["rotation"]) if "rotation" in node else np.eye(4)
    scale = node.get("scale", (1.0, 1.0, 1.0))
    out = out @ np.diag([scale[0], scale[1], scale[2], 1.0])
    out[:3, 3] = node.get("translation", (0.0, 0.0, 0.0))
    return out


def image_of(gltf, blob, index):
    """One of the GLB's embedded textures, as a float array in 0..1."""
    source = gltf["images"][gltf["textures"][index]["source"]]
    view = gltf["bufferViews"][source["bufferView"]]
    start = view.get("byteOffset", 0)
    with Image.open(io.BytesIO(blob[start:start + view["byteLength"]])) as img:
        return np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0


def draw_meshes(gltf, blob):
    """Every mesh in the scene as (world positions, uv, triangles, texture)."""
    parents = {}
    for i, node in enumerate(gltf.get("nodes", [])):
        for child in node.get("children", ()):  # not used by these models
            parents[child] = i
    out = []
    for i, node in enumerate(gltf.get("nodes", [])):
        if "mesh" not in node:
            continue
        world = node_matrix(node)
        parent = parents.get(i)
        while parent is not None:
            world = node_matrix(gltf["nodes"][parent]) @ world
            parent = parents.get(parent)
        for prim in gltf["meshes"][node["mesh"]]["primitives"]:
            attrs = prim["attributes"]
            if "TEXCOORD_0" not in attrs:
                continue
            pos = accessor(gltf, blob, attrs["POSITION"])
            uv = accessor(gltf, blob, attrs["TEXCOORD_0"])
            idx = accessor(gltf, blob, prim["indices"]).reshape(-1).astype(np.int64)
            world_pos = pos @ world[:3, :3].T + world[:3, 3]
            material = gltf["materials"][prim["material"]]
            base = material.get("pbrMetallicRoughness", {}).get("baseColorTexture")
            texture = image_of(gltf, blob, base["index"]) if base else None
            out.append((world_pos, uv, idx.reshape(-1, 3), texture,
                        material.get("name", "")))
    return out


def sample(texture, u, v, wrap):
    """Bilinear tap of a texture at UV in [0, 1]."""
    height, width = texture.shape[:2]
    x = u * width - 0.5
    y = v * height - 0.5
    x0 = np.floor(x)
    y0 = np.floor(y)
    fx = (x - x0)[..., None]
    fy = (y - y0)[..., None]
    x0 = x0.astype(np.int64)
    y0 = y0.astype(np.int64)
    if wrap:
        x1, y1 = (x0 + 1) % width, (y0 + 1) % height
        x0, y0 = x0 % width, y0 % height
    else:
        x1 = np.clip(x0 + 1, 0, width - 1)
        y1 = np.clip(y0 + 1, 0, height - 1)
        x0 = np.clip(x0, 0, width - 1)
        y0 = np.clip(y0, 0, height - 1)
    top = texture[y0, x0] * (1 - fx) + texture[y0, x1] * fx
    bottom = texture[y1, x0] * (1 - fx) + texture[y1, x1] * fx
    return top * (1 - fy) + bottom * fy


def clip_near(poly, near):
    """Clip a polygon in clip space to w >= near, so nothing is lost up close."""
    out = []
    for i in range(len(poly)):
        a = poly[i]
        b = poly[(i + 1) % len(poly)]
        da = a[3] - near
        db = b[3] - near
        if da >= 0:
            out.append(a)
        if (da >= 0) != (db >= 0):
            t = da / (da - db) if da != db else 0.0
            out.append(a + (b - a) * t)
    return np.array(out) if len(out) >= 3 else None


def render(path, size, fov=30.0, camera=(0.0, 1.6, 0.0), near=0.05,
           far=400.0, wrap_sky=True):
    """Render a stage's model to a picture of ``size``, camera looking down -Z."""
    gltf, blob = read_glb(path)
    width, height = size
    aspect = width / float(height)
    focal = 1.0 / np.tan(np.radians(fov) / 2.0)
    projection = np.array([
        [focal / aspect, 0.0, 0.0, 0.0],
        [0.0, focal, 0.0, 0.0],
        [0.0, 0.0, (far + near) / (near - far), 2 * far * near / (near - far)],
        [0.0, 0.0, -1.0, 0.0]])
    # the camera looks down -Z with +Y up, which is glTF's own convention, so the
    # view matrix is only the camera's inverse translation
    view = np.eye(4)
    view[:3, 3] = (-camera[0], -camera[1], -camera[2])

    colour = np.zeros((height, width, 3), dtype=np.float32)
    # 1/w is linear in screen space, so it is both the depth test and the divisor
    depth = np.zeros((height, width), dtype=np.float32)

    for positions, uv, triangles, texture, _name in draw_meshes(gltf, blob):
        clip = positions @ (projection @ view)[:3, :3].T + (projection @ view)[:3, 3]
        clip = np.concatenate([clip, (positions @ (projection @ view)[3, :3].T
                                      + (projection @ view)[3, 3])[:, None]], axis=1)
        for tri in triangles:
            poly = clip[tri]
            if np.all(poly[:, 3] < near):
                continue
            poly_uv = uv[tri]
            if np.any(poly[:, 3] < near):
                # rebuild the polygon (and its UVs) against the near plane, in
                # the order the clips fall, then fan it back into triangles
                verts, tex = [], []
                for i in range(3):
                    a, b = poly[i], poly[(i + 1) % 3]
                    da, db = a[3] - near, b[3] - near
                    if da >= 0:
                        verts.append(a)
                        tex.append(poly_uv[i])
                    if (da >= 0) != (db >= 0):
                        t = da / (da - db)
                        verts.append(a + (b - a) * t)
                        tex.append(poly_uv[i] + (poly_uv[(i + 1) % 3] - poly_uv[i]) * t)
                poly = np.array(verts)
                poly_uv = np.array(tex)
            inv_w = 1.0 / poly[:, 3]
            screen = np.empty((len(poly), 2))
            screen[:, 0] = (poly[:, 0] * inv_w * 0.5 + 0.5) * width
            screen[:, 1] = (0.5 - poly[:, 1] * inv_w * 0.5) * height
            for k in range(1, len(poly) - 1):
                _triangle(screen[[0, k, k + 1]], inv_w[[0, k, k + 1]],
                          poly_uv[[0, k, k + 1]], texture, colour, depth, wrap_sky)
    return Image.fromarray(np.clip(colour * 255.0 + 0.5, 0, 255).astype(np.uint8))


def _triangle(pts, inv_w, uv, texture, colour, depth, wrap):
    """One triangle into the colour and depth buffers, perspective correct."""
    xs = pts[:, 0]
    ys = pts[:, 1]
    x0 = max(0, int(np.floor(xs.min())))
    x1 = min(colour.shape[1] - 1, int(np.ceil(xs.max())))
    y0 = max(0, int(np.floor(ys.min())))
    y1 = min(colour.shape[0] - 1, int(np.ceil(ys.max())))
    if x0 > x1 or y0 > y1:
        return
    # signed area in screen space; either winding is drawn, the z-buffer decides
    area = ((xs[1] - xs[0]) * (ys[2] - ys[0]) - (xs[2] - xs[0]) * (ys[1] - ys[0]))
    if abs(area) < 1e-9:
        return
    px = np.arange(x0, x1 + 1) + 0.5
    py = np.arange(y0, y1 + 1) + 0.5
    gx, gy = np.meshgrid(px, py)
    w0 = ((xs[1] - gx) * (ys[2] - gy) - (xs[2] - gx) * (ys[1] - gy)) / area
    w1 = ((xs[2] - gx) * (ys[0] - gy) - (xs[0] - gx) * (ys[2] - gy)) / area
    w2 = 1.0 - w0 - w1
    inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
    if not inside.any():
        return
    d = w0 * inv_w[0] + w1 * inv_w[1] + w2 * inv_w[2]
    patch = depth[y0:y1 + 1, x0:x1 + 1]
    hit = inside & (d > patch)
    if not hit.any():
        return
    if texture is None:
        colour[y0:y1 + 1, x0:x1 + 1][hit] = 1.0
    else:
        uu = (w0 * uv[0, 0] * inv_w[0] + w1 * uv[1, 0] * inv_w[1]
              + w2 * uv[2, 0] * inv_w[2]) / d
        vv = (w0 * uv[0, 1] * inv_w[0] + w1 * uv[1, 1] * inv_w[1]
              + w2 * uv[2, 1] * inv_w[2]) / d
        colour[y0:y1 + 1, x0:x1 + 1][hit] = sample(texture, uu[hit], vv[hit], wrap)
    patch[hit] = d[hit]
