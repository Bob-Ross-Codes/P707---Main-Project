using UnityEngine;

/// <summary>
/// Builds a flag mesh for the "Project/Flag" shader, which waves it on the GPU.
/// The object's origin is the bottom of the hoist: the flag runs up local Y along the pole
/// and out along local X. Every flag moves differently, from its settings and its position.
/// </summary>
[ExecuteAlways]
[RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
public class Flag : MonoBehaviour
{
    [Header("Size (metres)")]
    [Tooltip("From the pole to the free end.")]
    [Min(0.05f)] public float length = 1.5f;
    [Tooltip("Along the pole.")]
    [Min(0.05f)] public float height = 1f;
    [Tooltip("Mesh density. Ripples are 0.4 m long at their shortest, so keep at least 15.")]
    [Range(4, 64)] public int segmentsPerMetre = 20;

    [Header("Motion")]
    [Tooltip("Depth of the ripples. Lower for heavy cloth.")]
    [Range(0f, 2f)] public float amplitude = 1f;
    [Tooltip("How fast the ripples travel. Higher for light cloth.")]
    [Range(0.25f, 3f)] public float speed = 1f;
    [Tooltip("How much of the global wind this flag feels. Lower for sheltered flags.")]
    [Range(0f, 2f)] public float windResponse = 1f;
    [Tooltip("Turn on the pole to fly downwind. Off for flags fixed to a wall.")]
    public bool swivel = true;

    private Mesh mesh;
    private bool dirty;

    private void OnEnable() => Build();
    private void OnValidate() => dirty = true;

    private void Update()
    {
        if (dirty) Build();
    }

    private void OnDestroy()
    {
        if (mesh != null) DestroyImmediate(mesh);
    }

    private void Build()
    {
        dirty = false;
        if (mesh == null)
            mesh = new Mesh { name = "Flag (generated)", hideFlags = HideFlags.DontSave };

        int nx = Mathf.Max(2, Mathf.CeilToInt(length * segmentsPerMetre)) + 1;
        int ny = Mathf.Max(2, Mathf.CeilToInt(height * segmentsPerMetre)) + 1;
        int layer = nx * ny;

        var positions = new Vector3[layer * 2];
        var uvs = new Vector2[layer * 2];
        var settings = new Vector3[layer * 2];
        var triangles = new int[(nx - 1) * (ny - 1) * 12];

        // The shader computes the real normal and reads these settings from the normal instead
        // (see FlagWave.hlsl): sign of x = layer, sign of y = swivel.
        float amp = Mathf.Max(amplitude, 0.001f);
        float spd = swivel ? speed : -speed;
        for (int j = 0; j < ny; j++)
        for (int i = 0; i < nx; i++)
        {
            int v = j * nx + i;
            var uv = new Vector2(i / (nx - 1f), j / (ny - 1f));
            positions[v] = positions[v + layer] = new Vector3(uv.x * length, uv.y * height, 0f);
            uvs[v] = uvs[v + layer] = uv;
            settings[v] = new Vector3(amp, spd, windResponse);
            settings[v + layer] = new Vector3(-amp, spd, windResponse);
        }

        int t = 0;
        for (int j = 0; j < ny - 1; j++)
        for (int i = 0; i < nx - 1; i++)
        {
            int a = j * nx + i, b = a + 1, c = a + nx, d = c + 1;
            // Front layer faces +Z, back layer faces -Z.
            triangles[t++] = a; triangles[t++] = b; triangles[t++] = c;
            triangles[t++] = b; triangles[t++] = d; triangles[t++] = c;
            triangles[t++] = a + layer; triangles[t++] = c + layer; triangles[t++] = b + layer;
            triangles[t++] = b + layer; triangles[t++] = c + layer; triangles[t++] = d + layer;
        }

        mesh.Clear();
        mesh.indexFormat = positions.Length > 65535 ? UnityEngine.Rendering.IndexFormat.UInt32 : UnityEngine.Rendering.IndexFormat.UInt16;
        mesh.vertices = positions;
        mesh.uv = uvs;
        mesh.normals = settings;
        mesh.triangles = triangles;
        // Room for any swivel direction and for the flag hanging straight down.
        float r = length + 0.2f;
        mesh.bounds = new Bounds(new Vector3(0f, (height - length) * 0.5f, 0f), new Vector3(2f * r, height + 2f * r, 2f * r));

        GetComponent<MeshFilter>().sharedMesh = mesh;
    }
}
