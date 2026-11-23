// Additive glow of smouldering embers. Use as an extra material slot on top of the mesh's normal material:
// the mesh renders a second time and adds glowing cracks that fade out from _Center.
Shader "Project/EmberGlow"
{
    Properties
    {
        [HDR] _HotColor ("Hot Color", Color) = (4, 1.2, 0.2, 1)
        [HDR] _CoolColor ("Cool Color", Color) = (0.6, 0.05, 0, 1)
        _Center ("Fire Center (world)", Vector) = (0, 0, 0, 0)
        _Radius ("Glow Radius (m)", Float) = 0.35
        _NoiseScale ("Crack Scale", Float) = 18
        _Coverage ("Crack Coverage", Range(0, 1)) = 0.45
        _Speed ("Smoulder Speed", Float) = 0.25
    }
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "Queue"="Transparent" "RenderType"="Transparent" }
        Pass
        {
            Tags { "LightMode"="UniversalForward" }
            Blend One One
            ZWrite Off
            ZTest LEqual
            Cull Back

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _HotColor, _CoolColor;
                float4 _Center;
                float _Radius, _NoiseScale, _Coverage, _Speed;
            CBUFFER_END

            struct Attributes { float4 positionOS : POSITION; };
            struct Varyings { float4 positionCS : SV_POSITION; float3 positionWS : TEXCOORD0; };

            float hash(float3 p) { p = frac(p * 0.3183099 + 0.1); p *= 17.0; return frac(p.x * p.y * p.z * (p.x + p.y + p.z)); }

            float noise(float3 p)
            {
                float3 i = floor(p), f = frac(p);
                f = f * f * (3.0 - 2.0 * f);
                return lerp(lerp(lerp(hash(i), hash(i + float3(1,0,0)), f.x), lerp(hash(i + float3(0,1,0)), hash(i + float3(1,1,0)), f.x), f.y),
                            lerp(lerp(hash(i + float3(0,0,1)), hash(i + float3(1,0,1)), f.x), lerp(hash(i + float3(0,1,1)), hash(i + float3(1,1,1)), f.x), f.y), f.z);
            }

            Varyings vert(Attributes v)
            {
                Varyings o;
                o.positionWS = TransformObjectToWorld(v.positionOS.xyz);
                o.positionCS = TransformWorldToHClip(o.positionWS);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                float t = _Time.y * _Speed;
                float3 p = i.positionWS * _NoiseScale;
                // Cracks: thresholded two-octave noise; a slow third noise makes patches breathe brighter and dimmer.
                float n = noise(p + float3(0, t, 0)) * 0.65 + noise(p * 2.3 - float3(t, 0, t)) * 0.35;
                float cracks = smoothstep(1.0 - _Coverage, 1.0 - _Coverage + 0.15, n);
                float breathe = 0.55 + 0.45 * noise(i.positionWS * 3.0 + t * 2.0);
                float mask = saturate(1.0 - distance(i.positionWS, _Center.xyz) / _Radius);
                float heat = cracks * breathe * mask * mask;
                return half4(lerp(_CoolColor.rgb, _HotColor.rgb, heat) * heat, 1);
            }
            ENDHLSL
        }
    }
}
