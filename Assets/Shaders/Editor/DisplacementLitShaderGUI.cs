using System;
using UnityEditor;
using UnityEditor.Rendering;
using UnityEditor.Rendering.Universal.ShaderGUI;
using UnityEngine;
using UnityEngine.Rendering;

namespace Project.Editor
{
    public sealed class DisplacementLitShaderGUI : BaseShaderGUI
    {
        static readonly string[] WorkflowNames = Enum.GetNames(typeof(LitGUI.WorkflowMode));
        static readonly string[] ProjectionNames = { "Mesh UV", "World XZ", "World XY", "World ZY" };
        static readonly string[] DisplacementNames = { "Vertex", "Pixel" };
        static readonly GUIContent ProjectionLabel = new GUIContent("Texture Mapping",
            "World modes project from the undisplaced mesh in world units. Base Map tiling and offset apply to the height and surface textures.");
        static readonly GUIContent DisplacementLabel = new GUIContent("Displacement Mode",
            "Vertex moves the mesh in object units. Pixel ray-marches the height map in world units, with white at the mesh surface and darker values recessed.");

        MaterialProperty[] properties;
        LitGUI.LitProperties lit;

        public override void FindProperties(MaterialProperty[] properties)
        {
            base.FindProperties(properties);
            this.properties = properties;
            lit = new LitGUI.LitProperties(properties);
        }

        public override void ValidateMaterial(Material material)
        {
            SetMaterialKeywords(material, LitGUI.SetMaterialKeywords, SetDetailKeywords);
            bool hasHeightMap = material.GetTexture("_ParallaxMap");
            bool usePixels = material.GetFloat("_DisplacementMode") == 1;
            CoreUtils.SetKeyword(material, "_PARALLAXMAP", hasHeightMap && !usePixels);
            CoreUtils.SetKeyword(material, "_PIXEL_DISPLACEMENT", hasHeightMap && usePixels);
            int projection = (int)material.GetFloat("_Projection");
            CoreUtils.SetKeyword(material, "_PROJECTION_WORLD_XZ", projection == 1);
            CoreUtils.SetKeyword(material, "_PROJECTION_WORLD_XY", projection == 2);
            CoreUtils.SetKeyword(material, "_PROJECTION_WORLD_ZY", projection == 3);
        }

        public override void AssignNewShaderToMaterial(Material material, Shader oldShader, Shader newShader)
        {
            base.AssignNewShaderToMaterial(material, oldShader, newShader);
            ValidateMaterial(material);
        }

        public override void DrawSurfaceOptions(Material material)
        {
            EditorGUIUtility.labelWidth = 0;
            DoPopup(LitGUI.Styles.workflowModeText, lit.workflowMode, WorkflowNames);
            base.DrawSurfaceOptions(material);
        }

        public override void DrawSurfaceInputs(Material material)
        {
            DoPopup(ProjectionLabel, FindProperty("_Projection", properties), ProjectionNames);
            DoPopup(DisplacementLabel, FindProperty("_DisplacementMode", properties), DisplacementNames);
            base.DrawSurfaceInputs(material);
            LitGUI.Inputs(lit, materialEditor, material);
            DrawEmissionProperties(material, true);
            DrawTileOffset(materialEditor, baseMapProp);
        }

        public override void DrawAdvancedOptions(Material material)
        {
            materialEditor.ShaderProperty(lit.highlights, LitGUI.Styles.highlightsText);
            materialEditor.ShaderProperty(lit.reflections, LitGUI.Styles.reflectionsText);
            base.DrawAdvancedOptions(material);
        }

        public override void FillAdditionalFoldouts(MaterialHeaderScopeList scopes)
        {
            scopes.RegisterHeaderScope(new GUIContent("Detail Inputs"), Expandable.Details, _ => DrawDetailInputs());
        }

        void DrawDetailInputs()
        {
            var albedo = FindProperty("_DetailAlbedoMap", properties);
            var normal = FindProperty("_DetailNormalMap", properties);
            materialEditor.TexturePropertySingleLine(new GUIContent("Mask (Alpha)"), FindProperty("_DetailMask", properties));
            materialEditor.TexturePropertySingleLine(new GUIContent("Base Map"), albedo,
                albedo.textureValue ? FindProperty("_DetailAlbedoMapScale", properties) : null);
            materialEditor.TexturePropertySingleLine(new GUIContent("Normal Map"), normal,
                normal.textureValue ? FindProperty("_DetailNormalMapScale", properties) : null);
            materialEditor.TextureScaleOffsetProperty(albedo);
        }

        static void SetDetailKeywords(Material material)
        {
            bool hasDetail = material.GetTexture("_DetailAlbedoMap") || material.GetTexture("_DetailNormalMap");
            bool scaled = material.GetFloat("_DetailAlbedoMapScale") != 1f;
            CoreUtils.SetKeyword(material, "_DETAIL_MULX2", hasDetail && !scaled);
            CoreUtils.SetKeyword(material, "_DETAIL_SCALED", hasDetail && scaled);
        }
    }
}
