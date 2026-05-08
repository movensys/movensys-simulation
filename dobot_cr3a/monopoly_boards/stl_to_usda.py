import struct
import sys
from pathlib import Path


def read_binary_stl(path: Path):
    with path.open("rb") as f:
        f.read(80)  # header
        (tri_count,) = struct.unpack("<I", f.read(4))
        normals = []
        triangles = []
        vertex_map = {}
        vertices = []
        for _ in range(tri_count):
            data = struct.unpack("<12fH", f.read(50))
            nx, ny, nz = data[0:3]
            v0 = data[3:6]
            v1 = data[6:9]
            v2 = data[9:12]
            normals.append((nx, ny, nz))
            tri_indices = []
            for v in (v0, v1, v2):
                idx = vertex_map.get(v)
                if idx is None:
                    idx = len(vertices)
                    vertex_map[v] = idx
                    vertices.append(v)
                tri_indices.append(idx)
            triangles.append(tuple(tri_indices))
    return vertices, triangles, normals


def write_usda(out_path: Path, mesh_name: str, vertices, triangles, normals):
    fmt_pt = lambda v: f"({v[0]}, {v[1]}, {v[2]})"
    points = ", ".join(fmt_pt(v) for v in vertices)
    face_vertex_counts = ", ".join("3" for _ in triangles)
    face_vertex_indices = ", ".join(str(i) for tri in triangles for i in tri)
    face_normals = ", ".join(fmt_pt(n) for n in normals for _ in range(3))

    usda = f'''#usda 1.0
(
    defaultPrim = "{mesh_name}"
    metersPerUnit = 0.001
    upAxis = "Z"
)

def Xform "{mesh_name}"
{{
    def Mesh "mesh"
    {{
        int[] faceVertexCounts = [{face_vertex_counts}]
        int[] faceVertexIndices = [{face_vertex_indices}]
        normal3f[] normals = [{face_normals}] (
            interpolation = "faceVarying"
        )
        point3f[] points = [{points}]
        uniform token subdivisionScheme = "none"
    }}
}}
'''
    out_path.write_text(usda)


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("tray.STL")
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".usda")
    name = src.stem.replace(" ", "_").replace("-", "_")
    if not name[0].isalpha() and name[0] != "_":
        name = "_" + name

    vertices, triangles, normals = read_binary_stl(src)
    write_usda(dst, name, vertices, triangles, normals)
    print(f"Wrote {dst} ({len(vertices)} verts, {len(triangles)} tris)")


if __name__ == "__main__":
    main()
