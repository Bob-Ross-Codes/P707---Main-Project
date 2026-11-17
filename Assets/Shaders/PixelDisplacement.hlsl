#ifndef PROJECT_PIXEL_DISPLACEMENT_INCLUDED
#define PROJECT_PIXEL_DISPLACEMENT_INCLUDED

#if defined(_PIXEL_DISPLACEMENT)

struct PixelDisplacementVaryings
{
    float3 positionWS : TEXCOORD11;
    float2 uv : TEXCOORD12;
};

PixelDisplacementVaryings GetPixelDisplacementVaryings(float3 positionOS, float2 uv)
{
    PixelDisplacementVaryings output;
    output.positionWS = TransformObjectToWorld(positionOS);
    output.uv = TRANSFORM_TEX(uv, _BaseMap);
    return output;
}

float GetHeightDepth(float2 uv, float2 uvDX, float2 uvDY)
{
    return 1.0 - SAMPLE_TEXTURE2D_GRAD(_ParallaxMap, sampler_ParallaxMap, uv, uvDX, uvDY).g;
}

float3 TracePixelHeight(float3 positionWS, float3 rayToViewerWS, inout float2 uv)
{
    float3 positionDX = ddx(positionWS);
    float3 positionDY = ddy(positionWS);
    float2 uvDX = ddx(uv);
    float2 uvDY = ddy(uv);
    float3 crossDXDY = cross(positionDX, positionDY);
    float areaSquared = dot(crossDXDY, crossDXDY);
    if (_Parallax <= 0 || areaSquared <= 1e-24)
        return positionWS;

    float inverseArea = rsqrt(areaSquared);
    float3 normalWS = crossDXDY * inverseArea;
    float facing = abs(dot(rayToViewerWS, normalWS));
    // Fade near grazing angles where the height field extends beyond the rasterized face.
    float amplitude = _Parallax * smoothstep(0.06, 0.22, facing);
    if (amplitude <= 0)
        return positionWS;

    float3 rayWS = -rayToViewerWS * (amplitude / max(facing, 0.06));
    // Solve the screen-space UV Jacobian for the ray projected onto the surface.
    // UVs already include the chosen projection, tiling, and offset.
    float2 rayUV = (uvDX * dot(cross(rayWS, positionDY), normalWS)
                  + uvDY * dot(cross(positionDX, rayWS), normalWS)) * inverseArea;

    int steps = (int)lerp(24.0, 10.0, facing);
    float stepSize = rcp((float)steps);
    float before = 0;
    float depth = 0;
    float difference = GetHeightDepth(uv, uvDX, uvDY);
    float previousDifference = difference;
    UNITY_LOOP
    for (int stepIndex = 0; stepIndex < steps && difference > 0; ++stepIndex)
    {
        before = depth;
        previousDifference = difference;
        depth = min(depth + stepSize, 1.0);
        difference = GetHeightDepth(uv + rayUV * depth, uvDX, uvDY) - depth;
    }

    float intersection = lerp(before, depth, saturate(previousDifference / max(previousDifference - difference, 1e-5)));
    uv += rayUV * intersection;
    return positionWS + rayWS * intersection;
}

float ProjectDeviceDepth(float3 positionWS)
{
    float4 positionCS = TransformWorldToHClip(positionWS);
    float depth = positionCS.z / positionCS.w;
#if !defined(UNITY_REVERSED_Z)
    depth = (depth - UNITY_NEAR_CLIP_VALUE) / (1.0 - UNITY_NEAR_CLIP_VALUE);
#endif
    return depth;
}

float ApplyCameraPixelDisplacement(inout float3 positionWS, inout float2 uv, float rasterDepth)
{
    float3 restPositionWS = positionWS;
    positionWS = TracePixelHeight(restPositionWS, SafeNormalize(GetWorldSpaceViewDir(restPositionWS)), uv);
    return saturate(rasterDepth + (ProjectDeviceDepth(positionWS) - ProjectDeviceDepth(restPositionWS)));
}

#endif
#endif
