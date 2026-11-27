#ifndef PROJECT_FLAG_WAVE_SG_INCLUDED
#define PROJECT_FLAG_WAVE_SG_INCLUDED

// Shader Graph entry point for FlagHDRP.shadergraph (Custom Function node, vertex stage).
#include "FlagWave.hlsl"

void FlagWave_float(float3 PositionIn, float3 NormalIn, out float3 Position, out float3 Normal, out float3 Tangent)
{
    Position = PositionIn;
    Normal = NormalIn;
    float4 tangentOS;
    ApplyFlagWave(Position, Normal, tangentOS);
    Tangent = tangentOS.xyz;
}

#endif
