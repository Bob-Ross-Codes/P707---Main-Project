#ifndef PROJECT_TRIPLANAR_LIT_INCLUDED
#define PROJECT_TRIPLANAR_LIT_INCLUDED

// Custom Function code for Assets/3D Assets/TriplanarLit.shadergraph.
// Textures are projected along the world X/Y/Z axes. uvw is world position * tiles per metre.

#define PROJECT_TRIPLANAR_PARALLAX_STEPS 8

float3 ProjectTriplanarWeights(float3 normalWS, float blend)
{
    float3 weights = pow(abs(normalWS), blend);
    return weights / max(weights.x + weights.y + weights.z, 1e-5);
}

// Explicit gradients: the parallax ray march below samples inside a loop, and its
// result would otherwise put mip seams on every height step.
float4 ProjectTriplanarSample(UnityTexture2D tex, float3 uvw, float3 weights, float3 dx, float3 dy)
{
    return SAMPLE_TEXTURE2D_GRAD(tex.tex, tex.samplerstate, uvw.zy, dx.zy, dy.zy) * weights.x
         + SAMPLE_TEXTURE2D_GRAD(tex.tex, tex.samplerstate, uvw.xz, dx.xz, dy.xz) * weights.y
         + SAMPLE_TEXTURE2D_GRAD(tex.tex, tex.samplerstate, uvw.xy, dx.xy, dy.xy) * weights.z;
}

// Vertex stage. Moves the vertex along its normal by the height map.
// Mid-grey is neutral, same convention as VertexDisplacement.hlsl. Amount is in metres.
void TriplanarVertexDisplacement_float(UnityTexture2D HeightMap, float3 PositionWS, float3 NormalWS,
    float Tiles, float Blend, float Amount, out float3 PositionOS)
{
    float3 normalWS = normalize(NormalWS);
    float3 uvw = PositionWS * Tiles;
    float3 weights = ProjectTriplanarWeights(normalWS, Blend);
    float height = SAMPLE_TEXTURE2D_LOD(HeightMap.tex, HeightMap.samplerstate, uvw.zy, 0).g * weights.x
                 + SAMPLE_TEXTURE2D_LOD(HeightMap.tex, HeightMap.samplerstate, uvw.xz, 0).g * weights.y
                 + SAMPLE_TEXTURE2D_LOD(HeightMap.tex, HeightMap.samplerstate, uvw.xy, 0).g * weights.z;
    PositionOS = TransformWorldToObject(PositionWS + normalWS * ((height - 0.5) * Amount));
}

// Fragment stage. All the URP Lit surface inputs, sampled triplanar.
// shortcut: pixel displacement only shifts where the textures are sampled (parallax
// occlusion). It does not change depth or the silhouette. For that, use
// LitWithVertexDisplacement.shader, which Shader Graph cannot reproduce.
void TriplanarLitSurface_float(
    UnityTexture2D BaseMap, UnityTexture2D MetallicMap, UnityTexture2D NormalMap,
    UnityTexture2D OcclusionMap, UnityTexture2D EmissionMap, UnityTexture2D HeightMap,
    float3 PositionWS, float3 NormalWS, float3 ViewDirWS, float Tiles, float Blend,
    float4 BaseColor, float Metallic, float Smoothness, float NormalStrength,
    float OcclusionStrength, float4 EmissionColor, float PixelDisplacement,
    out float3 OutBaseColor, out float3 OutNormalWS, out float OutMetallic,
    out float OutSmoothness, out float OutOcclusion, out float3 OutEmission)
{
    float3 normalWS = normalize(NormalWS);
    float3 weights = ProjectTriplanarWeights(normalWS, Blend);
    float3 uvw = PositionWS * Tiles;
    float3 dx = ddx(uvw);
    float3 dy = ddy(uvw);

    if (PixelDisplacement > 0)
    {
        float3 viewWS = normalize(ViewDirWS);
        float facing = dot(normalWS, viewWS);
        // Sideways travel of the view ray across the surface at full depth, in uvw units.
        // The clamp limits stretching at grazing angles.
        float3 ray = (normalWS * facing - viewWS) * (PixelDisplacement * Tiles / max(facing, 0.2));

        float stepSize = 1.0 / PROJECT_TRIPLANAR_PARALLAX_STEPS;
        float before = 0;
        float depth = 0;
        float difference = 1.0 - ProjectTriplanarSample(HeightMap, uvw, weights, dx, dy).g;
        float previousDifference = difference;
        UNITY_LOOP
        for (int i = 0; i < PROJECT_TRIPLANAR_PARALLAX_STEPS && difference > 0; ++i)
        {
            before = depth;
            previousDifference = difference;
            depth += stepSize;
            difference = 1.0 - ProjectTriplanarSample(HeightMap, uvw + ray * depth, weights, dx, dy).g - depth;
        }
        uvw += ray * lerp(before, depth, saturate(previousDifference / max(previousDifference - difference, 1e-5)));
    }

    float4 albedo = ProjectTriplanarSample(BaseMap, uvw, weights, dx, dy);
    OutBaseColor = albedo.rgb * BaseColor.rgb;

    // Same packing as URP Lit: metallic in R, smoothness in A.
    float4 metallicGloss = ProjectTriplanarSample(MetallicMap, uvw, weights, dx, dy);
    OutMetallic = metallicGloss.r * Metallic;
    OutSmoothness = metallicGloss.a * Smoothness;

    OutOcclusion = lerp(1.0, ProjectTriplanarSample(OcclusionMap, uvw, weights, dx, dy).g, OcclusionStrength);
    OutEmission = ProjectTriplanarSample(EmissionMap, uvw, weights, dx, dy).rgb * EmissionColor.rgb;

    // Whiteout blend, the same maths as Shader Graph's own Triplanar node in Normal mode.
    float3 normalX = UnpackNormalScale(SAMPLE_TEXTURE2D_GRAD(NormalMap.tex, NormalMap.samplerstate, uvw.zy, dx.zy, dy.zy), NormalStrength);
    float3 normalY = UnpackNormalScale(SAMPLE_TEXTURE2D_GRAD(NormalMap.tex, NormalMap.samplerstate, uvw.xz, dx.xz, dy.xz), NormalStrength);
    float3 normalZ = UnpackNormalScale(SAMPLE_TEXTURE2D_GRAD(NormalMap.tex, NormalMap.samplerstate, uvw.xy, dx.xy, dy.xy), NormalStrength);
    normalX = float3(normalX.xy + normalWS.zy, abs(normalX.z) * normalWS.x);
    normalY = float3(normalY.xy + normalWS.xz, abs(normalY.z) * normalWS.y);
    normalZ = float3(normalZ.xy + normalWS.xy, abs(normalZ.z) * normalWS.z);
    OutNormalWS = normalize(normalX.zyx * weights.x + normalY.xzy * weights.y + normalZ.xyz * weights.z);
}

#endif
