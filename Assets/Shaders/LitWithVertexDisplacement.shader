// Pass definitions adapted from URP 17.3 Lit, copyright (c) 2020 Unity Technologies ApS.
// Unity Companion License: https://unity.com/legal/licenses/Unity_Companion_License
// Lighting and surface shading use the URP package includes.
Shader "Project/Lit with Vertex Displacement"
{
    Properties
    {
        _WorkflowMode("WorkflowMode", Float) = 1.0
        _Projection("Texture Mapping", Float) = 0.0
        _DisplacementMode("Displacement Mode", Float) = 0.0

        [MainTexture] _BaseMap("Albedo", 2D) = "white" {}
        [MainColor] _BaseColor("Color", Color) = (1,1,1,1)

        _Cutoff("Alpha Cutoff", Range(0.0, 1.0)) = 0.5

        _Smoothness("Smoothness", Range(0.0, 1.0)) = 0.5
        _SmoothnessTextureChannel("Smoothness texture channel", Float) = 0

        _Metallic("Metallic", Range(0.0, 1.0)) = 0.0
        _MetallicGlossMap("Metallic", 2D) = "white" {}

        _SpecColor("Specular", Color) = (0.2, 0.2, 0.2)
        _SpecGlossMap("Specular", 2D) = "white" {}

        [ToggleOff] _SpecularHighlights("Specular Highlights", Float) = 1.0
        [ToggleOff] _EnvironmentReflections("Environment Reflections", Float) = 1.0

        _BumpScale("Scale", Float) = 1.0
        _BumpMap("Normal Map", 2D) = "bump" {}

        _Parallax("Displacement Amount", Range(0.0, 1.0)) = 0.005
        [NoScaleOffset] _ParallaxMap("Height Map", 2D) = "black" {}

        _OcclusionStrength("Strength", Range(0.0, 1.0)) = 1.0
        _OcclusionMap("Occlusion", 2D) = "white" {}

        [HDR] _EmissionColor("Color", Color) = (0,0,0)
        _EmissionMap("Emission", 2D) = "white" {}

        _DetailMask("Detail Mask", 2D) = "white" {}
        _DetailAlbedoMapScale("Scale", Range(0.0, 2.0)) = 1.0
        _DetailAlbedoMap("Detail Albedo x2", 2D) = "linearGrey" {}
        _DetailNormalMapScale("Scale", Range(0.0, 2.0)) = 1.0
        [Normal] _DetailNormalMap("Normal Map", 2D) = "bump" {}

        [HideInInspector] _ClearCoatMask("_ClearCoatMask", Float) = 0.0
        [HideInInspector] _ClearCoatSmoothness("_ClearCoatSmoothness", Float) = 0.0

        _Surface("__surface", Float) = 0.0
        _Blend("__blend", Float) = 0.0
        _Cull("__cull", Float) = 2.0
        [ToggleUI] _AlphaClip("__clip", Float) = 0.0
        [HideInInspector] _SrcBlend("__src", Float) = 1.0
        [HideInInspector] _DstBlend("__dst", Float) = 0.0
        [HideInInspector] _SrcBlendAlpha("__srcA", Float) = 1.0
        [HideInInspector] _DstBlendAlpha("__dstA", Float) = 0.0
        [HideInInspector] _ZWrite("__zw", Float) = 1.0
        [HideInInspector] _BlendModePreserveSpecular("_BlendModePreserveSpecular", Float) = 1.0
        [HideInInspector] _AlphaToMask("__alphaToMask", Float) = 0.0
        [HideInInspector] _AddPrecomputedVelocity("_AddPrecomputedVelocity", Float) = 0.0
        [HideInInspector] _XRMotionVectorsPass("_XRMotionVectorsPass", Float) = 1.0

        [ToggleUI] _ReceiveShadows("Receive Shadows", Float) = 1.0

        _QueueOffset("Queue offset", Float) = 0.0

        [HideInInspector] _MainTex("BaseMap", 2D) = "white" {}
        [HideInInspector] _Color("Base Color", Color) = (1, 1, 1, 1)
        [HideInInspector] _GlossMapScale("Smoothness", Float) = 0.0
        [HideInInspector] _Glossiness("Smoothness", Float) = 0.0
        [HideInInspector] _GlossyReflections("EnvironmentReflections", Float) = 0.0

        [HideInInspector][NoScaleOffset]unity_Lightmaps("unity_Lightmaps", 2DArray) = "" {}
        [HideInInspector][NoScaleOffset]unity_LightmapsInd("unity_LightmapsInd", 2DArray) = "" {}
        [HideInInspector][NoScaleOffset]unity_ShadowMasks("unity_ShadowMasks", 2DArray) = "" {}
    }

    SubShader
    {
        Tags
        {
            "RenderType" = "Opaque"
            "RenderPipeline" = "UniversalPipeline"
            "UniversalMaterialType" = "Lit"
            "IgnoreProjector" = "True"
        }
        LOD 300

        Pass
        {
            Name "ForwardLit"
            Tags
            {
                "LightMode" = "UniversalForward"
            }

            Blend[_SrcBlend][_DstBlend], [_SrcBlendAlpha][_DstBlendAlpha]
            ZWrite[_ZWrite]
            Cull[_Cull]
            AlphaToMask[_AlphaToMask]

            HLSLPROGRAM
            #pragma target 2.0

            #pragma vertex DisplacedVertex
            #pragma shader_feature_local_vertex _ _PROJECTION_WORLD_XZ _PROJECTION_WORLD_XY _PROJECTION_WORLD_ZY
            #pragma shader_feature_local _ _PARALLAXMAP _PIXEL_DISPLACEMENT
            #pragma target 3.5 _PARALLAXMAP _PIXEL_DISPLACEMENT
            #pragma fragment DisplacementForwardFragment

            #pragma shader_feature_local _NORMALMAP
            #pragma shader_feature_local _RECEIVE_SHADOWS_OFF
            #pragma shader_feature_local _ _DETAIL_MULX2 _DETAIL_SCALED
            #pragma shader_feature_local_fragment _SURFACE_TYPE_TRANSPARENT
            #pragma shader_feature_local_fragment _ALPHATEST_ON
            #pragma shader_feature_local_fragment _ _ALPHAPREMULTIPLY_ON _ALPHAMODULATE_ON
            #pragma shader_feature_local_fragment _EMISSION
            #pragma shader_feature_local_fragment _METALLICSPECGLOSSMAP
            #pragma shader_feature_local_fragment _SMOOTHNESS_TEXTURE_ALBEDO_CHANNEL_A
            #pragma shader_feature_local_fragment _OCCLUSIONMAP
            #pragma shader_feature_local_fragment _SPECULARHIGHLIGHTS_OFF
            #pragma shader_feature_local_fragment _ENVIRONMENTREFLECTIONS_OFF
            #pragma shader_feature_local_fragment _SPECULAR_SETUP

            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile _ EVALUATE_SH_MIXED EVALUATE_SH_VERTEX
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_BLENDING
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_BOX_PROJECTION
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_ATLAS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fragment _ _SCREEN_SPACE_OCCLUSION
            #pragma multi_compile_fragment _ _SCREEN_SPACE_IRRADIANCE
            #pragma multi_compile_fragment _ _DBUFFER_MRT1 _DBUFFER_MRT2 _DBUFFER_MRT3
            #pragma multi_compile_fragment _ _LIGHT_COOKIES
            #pragma multi_compile _ _LIGHT_LAYERS
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #include_with_pragmas "Packages/com.unity.render-pipelines.core/ShaderLibrary/FoveatedRenderingKeywords.hlsl"
            #include_with_pragmas "Packages/com.unity.render-pipelines.universal/ShaderLibrary/RenderingLayers.hlsl"

            #pragma multi_compile _ LIGHTMAP_SHADOW_MIXING
            #pragma multi_compile _ SHADOWS_SHADOWMASK
            #pragma multi_compile _ DIRLIGHTMAP_COMBINED
            #pragma multi_compile _ LIGHTMAP_ON
            #pragma multi_compile_fragment _ LIGHTMAP_BICUBIC_SAMPLING
            #pragma multi_compile_fragment _ REFLECTION_PROBE_ROTATION
            #pragma multi_compile _ DYNAMICLIGHTMAP_ON
            #pragma multi_compile _ USE_LEGACY_LIGHTMAPS
            #pragma multi_compile _ LOD_FADE_CROSSFADE
            #pragma multi_compile_fragment _ DEBUG_DISPLAY
            #include_with_pragmas "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Fog.hlsl"
            #include_with_pragmas "Packages/com.unity.render-pipelines.universal/ShaderLibrary/ProbeVolumeVariants.hlsl"

            #pragma multi_compile_instancing
            #pragma instancing_options renderinglayer
            #include_with_pragmas "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DOTS.hlsl"

            #include "VertexDisplacement.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/Shaders/LitForwardPass.hlsl"

            Varyings DisplacedVertex(Attributes input)
            {
            #if defined(PROJECT_WORLD_PROJECTION) || defined(PROJECT_VERTEX_DISPLACEMENT)
                UNITY_SETUP_INSTANCE_ID(input);
            #endif
            #if defined(PROJECT_WORLD_PROJECTION)
                input.texcoord = GetSurfaceUV(input.positionOS.xyz, input.texcoord);
                input.tangentOS = GetProjectedTangentOS(input.normalOS, input.tangentOS);
            #endif
            #if defined(PROJECT_VERTEX_DISPLACEMENT)
                input.positionOS.xyz += GetDisplacementOffsetOS(input.normalOS, input.texcoord);
            #endif
                return LitPassVertex(input);
            }

            void DisplacementForwardFragment(Varyings input, out half4 color : SV_Target0
            #if defined(_WRITE_RENDERING_LAYERS)
                , out uint renderingLayers : SV_Target1
            #endif
            #if defined(_PIXEL_DISPLACEMENT)
                , out float depth : SV_Depth
            #endif
            )
            {
            #if defined(_PIXEL_DISPLACEMENT)
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
                depth = ApplyCameraPixelDisplacement(input.positionWS, input.uv, input.positionCS.z);
                input.positionCS.z = depth;
                #if defined(REQUIRES_VERTEX_SHADOW_COORD_INTERPOLATOR) && !defined(_MAIN_LIGHT_SHADOWS_SCREEN)
                    input.shadowCoord = TransformWorldToShadowCoord(input.positionWS);
                #endif
            #endif
                LitPassFragment(input, color
                #if defined(_WRITE_RENDERING_LAYERS)
                    , renderingLayers
                #endif
                );
            }
            ENDHLSL
        }

        Pass
        {
            Name "ShadowCaster"
            Tags
            {
                "LightMode" = "ShadowCaster"
            }

            ZWrite On
            ZTest LEqual
            ColorMask 0
            Cull[_Cull]

            HLSLPROGRAM
            #pragma target 2.0

            #pragma vertex DisplacedVertex
            #pragma shader_feature_local_vertex _ _PROJECTION_WORLD_XZ _PROJECTION_WORLD_XY _PROJECTION_WORLD_ZY
            #pragma shader_feature_local _ _PARALLAXMAP _PIXEL_DISPLACEMENT
            #pragma target 3.5 _PARALLAXMAP _PIXEL_DISPLACEMENT
            #pragma fragment DisplacementShadowFragment

            #pragma shader_feature_local _ALPHATEST_ON
            #pragma shader_feature_local_fragment _SMOOTHNESS_TEXTURE_ALBEDO_CHANNEL_A

            #pragma multi_compile_instancing
            #include_with_pragmas "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DOTS.hlsl"

            #pragma multi_compile _ LOD_FADE_CROSSFADE

            #pragma multi_compile _ _CASTING_PUNCTUAL_LIGHT_SHADOW

            #include "VertexDisplacement.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/Shaders/ShadowCasterPass.hlsl"

            Varyings DisplacedVertex(Attributes input
            #if defined(_PIXEL_DISPLACEMENT)
                , out PixelDisplacementVaryings pixel
            #endif
            )

            {
            #if defined(PROJECT_WORLD_PROJECTION) || defined(PROJECT_VERTEX_DISPLACEMENT) || defined(_PIXEL_DISPLACEMENT)
                UNITY_SETUP_INSTANCE_ID(input);
            #endif
            #if defined(PROJECT_WORLD_PROJECTION)
                input.texcoord = GetSurfaceUV(input.positionOS.xyz, input.texcoord);
            #endif
            #if defined(PROJECT_VERTEX_DISPLACEMENT)
                input.positionOS.xyz += GetDisplacementOffsetOS(input.normalOS, input.texcoord);
            #endif
            #if defined(_PIXEL_DISPLACEMENT)
                pixel = GetPixelDisplacementVaryings(input.positionOS.xyz, input.texcoord);
            #endif
                return ShadowPassVertex(input);
            }

            half4 DisplacementShadowFragment(Varyings input
            #if defined(_PIXEL_DISPLACEMENT)
                , PixelDisplacementVaryings pixel, out float depth : SV_Depth
            #endif
            ) : SV_Target
            {
            #if defined(_PIXEL_DISPLACEMENT)
                UNITY_SETUP_INSTANCE_ID(input);
                #if defined(_CASTING_PUNCTUAL_LIGHT_SHADOW)
                    float3 lightDirectionWS = SafeNormalize(_LightPosition - pixel.positionWS);
                #else
                    float3 lightDirectionWS = _LightDirection;
                #endif
                float3 hitWS = TracePixelHeight(pixel.positionWS, lightDirectionWS, pixel.uv);
                // Keep the raster depth's shadow bias and apply only the displacement delta.
                depth = saturate(input.positionCS.z + (ProjectDeviceDepth(hitWS) - ProjectDeviceDepth(pixel.positionWS)));
                #if defined(_ALPHATEST_ON)
                    input.uv = pixel.uv;
                #endif
            #endif
                return ShadowPassFragment(input);
            }
            ENDHLSL
        }

        Pass
        {

            Name "GBuffer"
            Tags
            {
                "LightMode" = "UniversalGBuffer"
            }

            ZWrite[_ZWrite]
            ZTest LEqual
            Cull[_Cull]

            HLSLPROGRAM
            #pragma target 4.5

            #pragma exclude_renderers gles3 glcore

            #pragma vertex DisplacedVertex
            #pragma shader_feature_local_vertex _ _PROJECTION_WORLD_XZ _PROJECTION_WORLD_XY _PROJECTION_WORLD_ZY
            #pragma shader_feature_local _ _PARALLAXMAP _PIXEL_DISPLACEMENT
            #pragma fragment DisplacementGBufferFragment

            #pragma shader_feature_local _NORMALMAP
            #pragma shader_feature_local_fragment _ALPHATEST_ON

            #pragma shader_feature_local_fragment _EMISSION
            #pragma shader_feature_local_fragment _METALLICSPECGLOSSMAP
            #pragma shader_feature_local_fragment _SMOOTHNESS_TEXTURE_ALBEDO_CHANNEL_A
            #pragma shader_feature_local_fragment _OCCLUSIONMAP
            #pragma shader_feature_local _ _DETAIL_MULX2 _DETAIL_SCALED

            #pragma shader_feature_local_fragment _SPECULARHIGHLIGHTS_OFF
            #pragma shader_feature_local_fragment _ENVIRONMENTREFLECTIONS_OFF
            #pragma shader_feature_local_fragment _SPECULAR_SETUP
            #pragma shader_feature_local _RECEIVE_SHADOWS_OFF

            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN

            #pragma multi_compile_fragment _ _REFLECTION_PROBE_BLENDING
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_BOX_PROJECTION
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fragment _ _DBUFFER_MRT1 _DBUFFER_MRT2 _DBUFFER_MRT3
            #pragma multi_compile_fragment _ _RENDER_PASS_ENABLED
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #pragma multi_compile _ EVALUATE_SH_MIXED EVALUATE_SH_VERTEX
            #include_with_pragmas "Packages/com.unity.render-pipelines.core/ShaderLibrary/FoveatedRenderingKeywords.hlsl"
            #include_with_pragmas "Packages/com.unity.render-pipelines.universal/ShaderLibrary/RenderingLayers.hlsl"

            #pragma multi_compile _ LIGHTMAP_SHADOW_MIXING
            #pragma multi_compile _ SHADOWS_SHADOWMASK
            #pragma multi_compile _ DIRLIGHTMAP_COMBINED
            #pragma multi_compile _ LIGHTMAP_ON
            #pragma multi_compile_fragment _ LIGHTMAP_BICUBIC_SAMPLING
            #pragma multi_compile_fragment _ REFLECTION_PROBE_ROTATION
            #pragma multi_compile _ DYNAMICLIGHTMAP_ON
            #pragma multi_compile _ USE_LEGACY_LIGHTMAPS
            #pragma multi_compile _ LOD_FADE_CROSSFADE
            #pragma multi_compile_fragment _ _GBUFFER_NORMALS_OCT
            #pragma multi_compile_fragment _ _SCREEN_SPACE_IRRADIANCE
            #include_with_pragmas "Packages/com.unity.render-pipelines.universal/ShaderLibrary/ProbeVolumeVariants.hlsl"

            #pragma multi_compile_instancing
            #pragma instancing_options renderinglayer
            #include_with_pragmas "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DOTS.hlsl"

            #include "VertexDisplacement.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/Shaders/LitGBufferPass.hlsl"

            Varyings DisplacedVertex(Attributes input)
            {
            #if defined(PROJECT_WORLD_PROJECTION) || defined(PROJECT_VERTEX_DISPLACEMENT)
                UNITY_SETUP_INSTANCE_ID(input);
            #endif
            #if defined(PROJECT_WORLD_PROJECTION)
                input.texcoord = GetSurfaceUV(input.positionOS.xyz, input.texcoord);
                input.tangentOS = GetProjectedTangentOS(input.normalOS, input.tangentOS);
            #endif
            #if defined(PROJECT_VERTEX_DISPLACEMENT)
                input.positionOS.xyz += GetDisplacementOffsetOS(input.normalOS, input.texcoord);
            #endif
                return LitGBufferPassVertex(input);
            }
            #include_with_pragmas "Packages/com.unity.render-pipelines.universal/ShaderLibrary/GBufferOutputFormat.hlsl"

            GBufferFragOutput DisplacementGBufferFragment(Varyings input
            #if defined(_PIXEL_DISPLACEMENT)
                , out float depth : SV_Depth
            #endif
            )
            {
            #if defined(_PIXEL_DISPLACEMENT)
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
                depth = ApplyCameraPixelDisplacement(input.positionWS, input.uv, input.positionCS.z);
                input.positionCS.z = depth;
                #if defined(REQUIRES_VERTEX_SHADOW_COORD_INTERPOLATOR) && !defined(_MAIN_LIGHT_SHADOWS_SCREEN)
                    input.shadowCoord = TransformWorldToShadowCoord(input.positionWS);
                #endif
            #endif
                return LitGBufferPassFragment(input);
            }
            ENDHLSL
        }

        Pass
        {
            Name "DepthOnly"
            Tags
            {
                "LightMode" = "DepthOnly"
            }

            ZWrite On
            ColorMask R
            Cull[_Cull]

            HLSLPROGRAM
            #pragma target 2.0

            #pragma vertex DisplacedVertex
            #pragma shader_feature_local_vertex _ _PROJECTION_WORLD_XZ _PROJECTION_WORLD_XY _PROJECTION_WORLD_ZY
            #pragma shader_feature_local _ _PARALLAXMAP _PIXEL_DISPLACEMENT
            #pragma target 3.5 _PARALLAXMAP _PIXEL_DISPLACEMENT
            #pragma fragment DisplacementDepthFragment

            #pragma shader_feature_local _ALPHATEST_ON
            #pragma shader_feature_local_fragment _SMOOTHNESS_TEXTURE_ALBEDO_CHANNEL_A

            #pragma multi_compile _ LOD_FADE_CROSSFADE

            #pragma multi_compile_instancing
            #include_with_pragmas "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DOTS.hlsl"

            #include "VertexDisplacement.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/Shaders/DepthOnlyPass.hlsl"

            Varyings DisplacedVertex(Attributes input, float3 normalOS : NORMAL
            #if defined(_PIXEL_DISPLACEMENT)
                , out PixelDisplacementVaryings pixel
            #endif
            )

            {
            #if defined(PROJECT_WORLD_PROJECTION) || defined(PROJECT_VERTEX_DISPLACEMENT) || defined(_PIXEL_DISPLACEMENT)
                UNITY_SETUP_INSTANCE_ID(input);
            #endif
            #if defined(PROJECT_WORLD_PROJECTION)
                input.texcoord = GetSurfaceUV(input.position.xyz, input.texcoord);
            #endif
            #if defined(PROJECT_VERTEX_DISPLACEMENT)
                input.position.xyz += GetDisplacementOffsetOS(normalOS, input.texcoord);
            #endif
            #if defined(_PIXEL_DISPLACEMENT)
                pixel = GetPixelDisplacementVaryings(input.position.xyz, input.texcoord);
            #endif
                return DepthOnlyVertex(input);
            }

            half DisplacementDepthFragment(Varyings input
            #if defined(_PIXEL_DISPLACEMENT)
                , PixelDisplacementVaryings pixel, out float depth : SV_Depth
            #endif
            ) : SV_Target
            {
            #if defined(_PIXEL_DISPLACEMENT)
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
                depth = ApplyCameraPixelDisplacement(pixel.positionWS, pixel.uv, input.positionCS.z);
                input.positionCS.z = depth;
                #if defined(_ALPHATEST_ON)
                    input.uv = pixel.uv;
                #endif
            #endif
                return DepthOnlyFragment(input);
            }
            ENDHLSL
        }

        Pass
        {
            Name "DepthNormals"
            Tags
            {
                "LightMode" = "DepthNormals"
            }

            ZWrite On
            Cull[_Cull]

            HLSLPROGRAM
            #pragma target 2.0

            #pragma vertex DisplacedVertex
            #pragma shader_feature_local_vertex _ _PROJECTION_WORLD_XZ _PROJECTION_WORLD_XY _PROJECTION_WORLD_ZY
            #pragma shader_feature_local _ _PARALLAXMAP _PIXEL_DISPLACEMENT
            #pragma target 3.5 _PARALLAXMAP _PIXEL_DISPLACEMENT
            #pragma fragment DisplacementDepthNormalsFragment

            #pragma shader_feature_local _NORMALMAP
            #pragma shader_feature_local _ _DETAIL_MULX2 _DETAIL_SCALED
            #pragma shader_feature_local _ALPHATEST_ON
            #pragma shader_feature_local_fragment _SMOOTHNESS_TEXTURE_ALBEDO_CHANNEL_A

            #pragma multi_compile _ LOD_FADE_CROSSFADE

            #include_with_pragmas "Packages/com.unity.render-pipelines.universal/ShaderLibrary/RenderingLayers.hlsl"

            #pragma multi_compile_instancing
            #include_with_pragmas "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DOTS.hlsl"

            #include "VertexDisplacement.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/Shaders/LitDepthNormalsPass.hlsl"

            Varyings DisplacedVertex(Attributes input
            #if defined(_PIXEL_DISPLACEMENT)
                , out PixelDisplacementVaryings pixel
            #endif
            )

            {
            #if defined(PROJECT_WORLD_PROJECTION) || defined(PROJECT_VERTEX_DISPLACEMENT) || defined(_PIXEL_DISPLACEMENT)
                UNITY_SETUP_INSTANCE_ID(input);
            #endif
            #if defined(PROJECT_WORLD_PROJECTION)
                input.texcoord = GetSurfaceUV(input.positionOS.xyz, input.texcoord);
                input.tangentOS = GetProjectedTangentOS(input.normal, input.tangentOS);
            #endif
            #if defined(PROJECT_VERTEX_DISPLACEMENT)
                input.positionOS.xyz += GetDisplacementOffsetOS(input.normal, input.texcoord);
            #endif
            #if defined(_PIXEL_DISPLACEMENT)
                pixel = GetPixelDisplacementVaryings(input.positionOS.xyz, input.texcoord);
            #endif
                return DepthNormalsVertex(input);
            }

            void DisplacementDepthNormalsFragment(Varyings input, out half4 normal : SV_Target0
            #if defined(_WRITE_RENDERING_LAYERS)
                , out uint renderingLayers : SV_Target1
            #endif
            #if defined(_PIXEL_DISPLACEMENT)
                , PixelDisplacementVaryings pixel, out float depth : SV_Depth
            #endif
            )
            {
            #if defined(_PIXEL_DISPLACEMENT)
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
                depth = ApplyCameraPixelDisplacement(pixel.positionWS, pixel.uv, input.positionCS.z);
                #if defined(REQUIRES_UV_INTERPOLATOR)
                    input.uv = pixel.uv;
                #endif
            #endif
                DepthNormalsFragment(input, normal
                #if defined(_WRITE_RENDERING_LAYERS)
                    , renderingLayers
                #endif
                );
            }
            ENDHLSL
        }

        Pass
        {
            Name "Meta"
            Tags
            {
                "LightMode" = "Meta"
            }

            Cull Off

            HLSLPROGRAM
            #pragma target 2.0

            #pragma vertex ProjectedMetaVertex
            #pragma shader_feature_local_vertex _ _PROJECTION_WORLD_XZ _PROJECTION_WORLD_XY _PROJECTION_WORLD_ZY
            #pragma fragment UniversalFragmentMetaLit

            #pragma shader_feature_local_fragment _SPECULAR_SETUP
            #pragma shader_feature_local_fragment _EMISSION
            #pragma shader_feature_local_fragment _METALLICSPECGLOSSMAP
            #pragma shader_feature_local_fragment _ALPHATEST_ON
            #pragma shader_feature_local_fragment _ _SMOOTHNESS_TEXTURE_ALBEDO_CHANNEL_A
            #pragma shader_feature_local _ _DETAIL_MULX2 _DETAIL_SCALED
            #pragma shader_feature_local_fragment _SPECGLOSSMAP
            #pragma shader_feature EDITOR_VISUALIZATION

            #include "Packages/com.unity.render-pipelines.universal/Shaders/LitInput.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/Shaders/LitMetaPass.hlsl"

            Varyings ProjectedMetaVertex(Attributes input)
            {
            #if defined(PROJECT_WORLD_PROJECTION)
                UNITY_SETUP_INSTANCE_ID(input);
                input.uv0 = GetSurfaceUV(input.positionOS.xyz, input.uv0);
            #endif
                return UniversalVertexMeta(input);
            }

            ENDHLSL
        }

        Pass
        {
            Name "Universal2D"
            Tags
            {
                "LightMode" = "Universal2D"
            }

            Blend[_SrcBlend][_DstBlend]
            ZWrite[_ZWrite]
            Cull[_Cull]

            HLSLPROGRAM
            #pragma target 2.0

            #pragma vertex DisplacedVertex
            #pragma shader_feature_local_vertex _ _PROJECTION_WORLD_XZ _PROJECTION_WORLD_XY _PROJECTION_WORLD_ZY
            #pragma shader_feature_local _ _PARALLAXMAP _PIXEL_DISPLACEMENT
            #pragma target 3.5 _PARALLAXMAP _PIXEL_DISPLACEMENT
            #pragma fragment Displacement2DFragment

            #pragma shader_feature_local_fragment _ALPHATEST_ON
            #pragma shader_feature_local_fragment _ALPHAPREMULTIPLY_ON

            #include_with_pragmas "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DOTS.hlsl"

            #include "VertexDisplacement.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/Shaders/Utils/Universal2D.hlsl"

            Varyings DisplacedVertex(Attributes input, float3 normalOS : NORMAL
            #if defined(_PIXEL_DISPLACEMENT)
                , out PixelDisplacementVaryings pixel
            #endif
            )

            {
            #if defined(PROJECT_WORLD_PROJECTION) || defined(PROJECT_VERTEX_DISPLACEMENT) || defined(_PIXEL_DISPLACEMENT)
                UNITY_SETUP_INSTANCE_ID(input);
            #endif
            #if defined(PROJECT_WORLD_PROJECTION)
                input.uv = GetSurfaceUV(input.positionOS.xyz, input.uv);
            #endif
            #if defined(PROJECT_VERTEX_DISPLACEMENT)
                input.positionOS.xyz += GetDisplacementOffsetOS(normalOS, input.uv);
            #endif
            #if defined(_PIXEL_DISPLACEMENT)
                pixel = GetPixelDisplacementVaryings(input.positionOS.xyz, input.uv);
            #endif
                return vert(input);
            }

            half4 Displacement2DFragment(Varyings input
            #if defined(_PIXEL_DISPLACEMENT)
                , PixelDisplacementVaryings pixel, out float depth : SV_Depth
            #endif
            ) : SV_Target
            {
            #if defined(_PIXEL_DISPLACEMENT)
                UNITY_SETUP_INSTANCE_ID(input);
                depth = ApplyCameraPixelDisplacement(pixel.positionWS, input.uv, input.vertex.z);
            #endif
                return frag(input);
            }
            ENDHLSL
        }

        Pass
        {
            Name "MotionVectors"
            Tags { "LightMode" = "MotionVectors" }
            ColorMask RG

            HLSLPROGRAM
            #pragma shader_feature_local _ALPHATEST_ON
            #pragma multi_compile _ LOD_FADE_CROSSFADE
            #pragma shader_feature_local_vertex _ADD_PRECOMPUTED_VELOCITY

            #include_with_pragmas "DisplacementMotionVectors.hlsl"
            ENDHLSL
        }

        Pass
        {
            Name "XRMotionVectors"
            Tags { "LightMode" = "XRMotionVectors" }
            ColorMask RGBA

            Stencil
            {
                WriteMask 1
                Ref 1
                Comp Always
                Pass Replace
            }

            HLSLPROGRAM
            #pragma shader_feature_local _ALPHATEST_ON
            #pragma multi_compile _ LOD_FADE_CROSSFADE
            #pragma shader_feature_local_vertex _ADD_PRECOMPUTED_VELOCITY
            #define APPLICATION_SPACE_WARP_MOTION 1

            #include_with_pragmas "DisplacementMotionVectors.hlsl"
            ENDHLSL
        }
    }

    FallBack "Hidden/Universal Render Pipeline/FallbackError"
    CustomEditor "Project.Editor.DisplacementLitShaderGUI"
}
