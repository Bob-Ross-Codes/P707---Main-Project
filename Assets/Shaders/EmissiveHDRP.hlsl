#ifndef PROJECT_EMISSIVE_HDRP_INCLUDED
#define PROJECT_EMISSIVE_HDRP_INCLUDED

// Shader Graph entry points for the additive HDRP graphs (EmberGlowHDRP, ParticleAdditiveHDRP).
// Their colours were tuned in URP, where nothing is exposed; dividing out HDRP's exposure keeps
// them as bright on screen as they were. The graphs blend premultiplied with alpha 0, which is additive.

float EmissiveExposureScale()
{
#ifdef SHADERGRAPH_PREVIEW
    return 1.0;
#else
    return GetInverseCurrentExposureMultiplier();
#endif
}

float EmberHash(float3 p) { p = frac(p * 0.3183099 + 0.1); p *= 17.0; return frac(p.x * p.y * p.z * (p.x + p.y + p.z)); }

float EmberNoise(float3 p)
{
    float3 i = floor(p), f = frac(p);
    f = f * f * (3.0 - 2.0 * f);
    return lerp(lerp(lerp(EmberHash(i), EmberHash(i + float3(1,0,0)), f.x), lerp(EmberHash(i + float3(0,1,0)), EmberHash(i + float3(1,1,0)), f.x), f.y),
                lerp(lerp(EmberHash(i + float3(0,0,1)), EmberHash(i + float3(1,0,1)), f.x), lerp(EmberHash(i + float3(0,1,1)), EmberHash(i + float3(1,1,1)), f.x), f.y), f.z);
}

// Same maths as EmberGlow.shader (URP): glowing cracks that fade out from Center.
void EmberGlow_float(float3 PositionAWS, float4 HotColor, float4 CoolColor, float4 Center, float Radius, float NoiseScale,
                     float Coverage, float Speed, out float3 Color, out float Alpha)
{
    float t = _Time.y * Speed;
    float3 p = PositionAWS * NoiseScale;
    float n = EmberNoise(p + float3(0, t, 0)) * 0.65 + EmberNoise(p * 2.3 - float3(t, 0, t)) * 0.35;
    float cracks = smoothstep(1.0 - Coverage, 1.0 - Coverage + 0.15, n);
    float breathe = 0.55 + 0.45 * EmberNoise(PositionAWS * 3.0 + t * 2.0);
    float mask = saturate(1.0 - distance(PositionAWS, Center.xyz) / Radius);
    float heat = cracks * breathe * mask * mask;
    Color = lerp(CoolColor.rgb, HotColor.rgb, heat) * heat * EmissiveExposureScale();
    Alpha = 0.0;
}

// URP Particles/Unlit in additive mode: texture x vertex colour x tint, weighted by alpha.
void ParticleAdditive_float(float4 Tex, float4 VertexColor, float4 Tint, out float3 Color, out float Alpha)
{
    float4 c = Tex * VertexColor * Tint;
    Color = c.rgb * c.a * EmissiveExposureScale();
    Alpha = 0.0;
}

#endif
