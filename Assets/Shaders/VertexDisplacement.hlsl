#ifndef PROJECT_VERTEX_DISPLACEMENT_INCLUDED
#define PROJECT_VERTEX_DISPLACEMENT_INCLUDED

// Keep the URP Lit inspector's Height Map binding and keyword. Hide the
// keyword from the stock passes so they shade the displaced mesh without a UV offset.
#if defined(_PARALLAXMAP)
    #define PROJECT_VERTEX_DISPLACEMENT
    #undef _PARALLAXMAP
#endif

#include "Packages/com.unity.render-pipelines.universal/Shaders/LitInput.hlsl"
#include "PixelDisplacement.hlsl"

#if defined(_PROJECTION_WORLD_XZ) || defined(_PROJECTION_WORLD_XY) || defined(_PROJECTION_WORLD_ZY)
    #define PROJECT_WORLD_PROJECTION

void GetWorldProjectionAxes(out float3 axisU, out float3 axisV)
{
#if defined(_PROJECTION_WORLD_ZY)
    axisU = float3(0, 0, 1);
#else
    axisU = float3(1, 0, 0);
#endif
#if defined(_PROJECTION_WORLD_XZ)
    axisV = float3(0, 0, 1);
#else
    axisV = float3(0, 1, 0);
#endif
}

float2 GetWorldProjectedUV(float3 positionWS)
{
    float3 axisU, axisV;
    GetWorldProjectionAxes(axisU, axisV);
    return float2(dot(positionWS, axisU), dot(positionWS, axisV));
}

float4 GetProjectedTangentOS(float3 normalOS, float4 tangentOS)
{
    float3 axisU, axisV;
    GetWorldProjectionAxes(axisU, axisV);
    float3 normalWS = TransformObjectToWorldNormal(normalOS);
    float orientation = dot(cross(axisU, axisV), normalWS);
    if (abs(orientation) < 1e-5)
        return tangentOS;

    float handedness = sign(orientation);
    float uSign = _BaseMap_ST.x < 0 ? -1 : 1;
    float vSign = _BaseMap_ST.y < 0 ? -1 : 1;
    float3 tangentWS = cross(axisV, normalWS) * (handedness * uSign);
    return float4(TransformWorldToObjectDir(tangentWS), handedness * uSign * vSign * GetOddNegativeScale());
}
#endif

// Use the position before displacement so the surface textures and height map
// stay aligned even when a vertex moves sideways in the projection plane.
float2 GetSurfaceUV(float3 restPositionOS, float2 meshUV)
{
#if defined(PROJECT_WORLD_PROJECTION)
    return GetWorldProjectedUV(GetAbsolutePositionWS(TransformObjectToWorld(restPositionOS)));
#else
    return meshUV;
#endif
}

#if defined(PROJECT_VERTEX_DISPLACEMENT)
float3 GetDisplacementOffsetOS(float3 normalOS, float2 uv)
{
    float2 heightUV = TRANSFORM_TEX(uv, _BaseMap);
    float height = SAMPLE_TEXTURE2D_LOD(_ParallaxMap, sampler_ParallaxMap, heightUV, 0).g;
    // Mid-gray is neutral, and the amount is the peak-to-peak range in object units.
    return SafeNormalize(normalOS) * ((height - 0.5) * _Parallax);
}
#endif

#endif
