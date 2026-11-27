#ifndef PROJECT_PARTICLE_SOFT_INCLUDED
#define PROJECT_PARTICLE_SOFT_INCLUDED

// Shader Graph entry point for ParticleHDRP.shadergraph: texture x vertex colour x tint,
// faded out where the particle meets opaque geometry (URP's soft particles).
void ParticleSoft_float(float4 Tex, float4 VertexColor, float4 Tint, float4 ScreenPosRaw, float FadeDistance,
                        out float3 Color, out float Alpha)
{
    float4 c = Tex * VertexColor * Tint;
    float fade = 1.0;
#ifndef SHADERGRAPH_PREVIEW
    if (FadeDistance > 0.0)
    {
        float sceneEye = LinearEyeDepth(SHADERGRAPH_SAMPLE_SCENE_DEPTH(ScreenPosRaw.xy / ScreenPosRaw.w), _ZBufferParams);
        fade = saturate((sceneEye - ScreenPosRaw.w) / FadeDistance);
    }
#endif
    Color = c.rgb;
    Alpha = c.a * fade;
}

#endif
