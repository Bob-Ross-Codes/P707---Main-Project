#ifndef PROJECT_DISPLACEMENT_MOTION_VECTORS_INCLUDED
#define PROJECT_DISPLACEMENT_MOTION_VECTORS_INCLUDED

#pragma target 3.5
#pragma vertex DisplacedMotionVertex
#pragma fragment DisplacedMotionFragment
#pragma shader_feature_local _ _PARALLAXMAP _PIXEL_DISPLACEMENT
#pragma shader_feature_local_vertex _ _PROJECTION_WORLD_XZ _PROJECTION_WORLD_XY _PROJECTION_WORLD_ZY
#pragma multi_compile_instancing
#include_with_pragmas "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DOTS.hlsl"
#include_with_pragmas "Packages/com.unity.render-pipelines.core/ShaderLibrary/FoveatedRenderingKeywords.hlsl"

#include "VertexDisplacement.hlsl"
#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/ObjectMotionVectors.hlsl"

struct DisplacementMotionAttributes
{
    float4 position : POSITION;
    float3 normalOS : NORMAL;
    float2 uv : TEXCOORD0;
    float3 positionOld : TEXCOORD4;
#if defined(_ADD_PRECOMPUTED_VELOCITY)
    float3 alembicMotionVector : TEXCOORD5;
#endif
    UNITY_VERTEX_INPUT_INSTANCE_ID
};

Varyings DisplacedMotionVertex(DisplacementMotionAttributes input
#if defined(_PIXEL_DISPLACEMENT)
    , out PixelDisplacementVaryings pixel
#endif
)
{
    Attributes motionInput;
    motionInput.position = input.position;
    motionInput.positionOld = input.positionOld;
#if defined(PROJECT_WORLD_PROJECTION) || defined(PROJECT_VERTEX_DISPLACEMENT) || defined(_PIXEL_DISPLACEMENT)
    UNITY_SETUP_INSTANCE_ID(input);
#endif
    float2 surfaceUV = GetSurfaceUV(input.position.xyz, input.uv);
#if defined(_PIXEL_DISPLACEMENT)
    pixel = GetPixelDisplacementVaryings(input.position.xyz, surfaceUV);
#endif
#if defined(_ALPHATEST_ON)
    motionInput.uv = surfaceUV;
#endif
#if defined(_ADD_PRECOMPUTED_VELOCITY)
    motionInput.alembicMotionVector = input.alembicMotionVector;
#endif
    UNITY_TRANSFER_INSTANCE_ID(input, motionInput);

#if defined(PROJECT_VERTEX_DISPLACEMENT)
    float3 offsetOS = GetDisplacementOffsetOS(input.normalOS, surfaceUV);
    motionInput.position.xyz += offsetOS;
    // Mesh UVs sample the same height in both frames.
    motionInput.positionOld += offsetOS;
#endif

    Varyings output = vert(motionInput);
#if defined(PROJECT_VERTEX_DISPLACEMENT) && defined(PROJECT_WORLD_PROJECTION)
    // Moving through a world-projected texture can change the height from frame to frame.
    float3 previousOS = unity_MotionVectorsParams.x == 1 ? input.positionOld : input.position.xyz;
    #if defined(_ADD_PRECOMPUTED_VELOCITY)
        previousOS -= input.alembicMotionVector;
    #endif
    float3 previousWS = mul(UNITY_PREV_MATRIX_M, float4(previousOS, 1)).xyz;
    float2 previousUV = GetWorldProjectedUV(GetAbsolutePositionWS(previousWS));
    previousOS += GetDisplacementOffsetOS(input.normalOS, previousUV);
    output.previousPositionCSNoJitter = mul(_PrevViewProjMatrix, mul(UNITY_PREV_MATRIX_M, float4(previousOS, 1)));
#endif
    return output;
}

float4 DisplacedMotionFragment(Varyings input
#if defined(_PIXEL_DISPLACEMENT)
    , PixelDisplacementVaryings pixel, out float depth : SV_Depth
#endif
) : SV_Target
{
#if defined(_PIXEL_DISPLACEMENT)
    UNITY_SETUP_INSTANCE_ID(input);
    UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
    float3 restPositionWS = pixel.positionWS;
    depth = ApplyCameraPixelDisplacement(pixel.positionWS, pixel.uv, input.positionCS.z);
    float3 offsetWS = pixel.positionWS - restPositionWS;
    float3 offsetOS = TransformWorldToObjectDir(offsetWS, false);
    input.positionCSNoJitter += mul(_NonJitteredViewProjMatrix, float4(offsetWS, 0));
    input.previousPositionCSNoJitter += mul(_PrevViewProjMatrix, mul(UNITY_PREV_MATRIX_M, float4(offsetOS, 0)));
    #if defined(_ALPHATEST_ON)
        input.uv = pixel.uv;
    #endif
#endif
    return frag(input);
}

#endif
