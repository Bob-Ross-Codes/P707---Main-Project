using System;
using System.IO;
using UnityEditor;
using UnityEditor.Rendering.HighDefinition;
using UnityEngine;

public static class FabDecalMaterialGenerator
{
    private const string Root = "Assets/2D Assets/Decals";

    public static void Generate()
    {
        var shader = Shader.Find("HDRP/Decal");
        if (shader == null)
            throw new Exception("Could not find HDRP/Decal shader.");

        var folders = Directory.GetDirectories(Root);
        var created = 0;

        foreach (var folderPath in folders)
        {
            var folderName = Path.GetFileName(folderPath);
            var folderAssetPath = Root + "/" + folderName;
            var jpgs = Directory.GetFiles(folderPath, "*.jpg");
            var basePath = Find(jpgs, "_basecolor.jpg");
            var opacityPath = Find(jpgs, "_opacity.jpg");
            var normalPath = Find(jpgs, "_normal.jpg");
            var aoPath = Find(jpgs, "_ao.jpg");
            var roughnessPath = Find(jpgs, "_roughness.jpg");

            if (basePath == null || opacityPath == null || normalPath == null || aoPath == null || roughnessPath == null)
                throw new Exception("Missing a required BaseColor, Opacity, Normal, AO, or Roughness map in " + folderName);

            ConfigureTexture(normalPath, TextureImporterType.NormalMap, false, false);

            var colorAlphaAssetPath = folderAssetPath + "/" + folderName + "_BaseColorOpacity.png";
            var maskAssetPath = folderAssetPath + "/" + folderName + "_Mask.png";
            var colorAlphaDiskPath = Path.GetFullPath(colorAlphaAssetPath);
            var maskDiskPath = Path.GetFullPath(maskAssetPath);

            var color = LoadTexture(basePath, false);
            var opacity = LoadTexture(opacityPath, true);
            var ao = LoadTexture(aoPath, true);
            var roughness = LoadTexture(roughnessPath, true);

            var colorPixels = color.GetPixels32();
            var opacityPixels = opacity.GetPixels32();
            var aoPixels = ao.GetPixels32();
            var roughnessPixels = roughness.GetPixels32();
            var packedMask = new Color32[colorPixels.Length];

            for (var y = 0; y < color.height; y++)
            {
                for (var x = 0; x < color.width; x++)
                {
                    var i = y * color.width + x;
                    var ox = x * opacity.width / color.width;
                    var oy = y * opacity.height / color.height;
                    var ax = x * ao.width / color.width;
                    var ay = y * ao.height / color.height;
                    var rx = x * roughness.width / color.width;
                    var ry = y * roughness.height / color.height;
                    var alpha = opacityPixels[oy * opacity.width + ox].r;
                    colorPixels[i].a = alpha;
                    packedMask[i] = new Color32(
                        0,
                        aoPixels[ay * ao.width + ax].r,
                        alpha,
                        (byte)(255 - roughnessPixels[ry * roughness.width + rx].r));
                }
            }

            var colorAlpha = new Texture2D(color.width, color.height, TextureFormat.RGBA32, false, false);
            colorAlpha.SetPixels32(colorPixels);
            colorAlpha.Apply(false, false);
            File.WriteAllBytes(colorAlphaDiskPath, colorAlpha.EncodeToPNG());

            var mask = new Texture2D(color.width, color.height, TextureFormat.RGBA32, false, true);
            mask.SetPixels32(packedMask);
            mask.Apply(false, false);
            File.WriteAllBytes(maskDiskPath, mask.EncodeToPNG());

            UnityEngine.Object.DestroyImmediate(color);
            UnityEngine.Object.DestroyImmediate(opacity);
            UnityEngine.Object.DestroyImmediate(ao);
            UnityEngine.Object.DestroyImmediate(roughness);
            UnityEngine.Object.DestroyImmediate(colorAlpha);
            UnityEngine.Object.DestroyImmediate(mask);

            AssetDatabase.ImportAsset(colorAlphaAssetPath, ImportAssetOptions.ForceSynchronousImport);
            AssetDatabase.ImportAsset(maskAssetPath, ImportAssetOptions.ForceSynchronousImport);
            ConfigureTexture(colorAlphaDiskPath, TextureImporterType.Default, true, true);
            ConfigureTexture(maskDiskPath, TextureImporterType.Default, false, false);

            var colorAlphaTexture = AssetDatabase.LoadAssetAtPath<Texture2D>(colorAlphaAssetPath);
            var maskTexture = AssetDatabase.LoadAssetAtPath<Texture2D>(maskAssetPath);
            var normalTexture = AssetDatabase.LoadAssetAtPath<Texture2D>(ToAssetPath(normalPath));
            if (colorAlphaTexture == null || maskTexture == null || normalTexture == null)
                throw new Exception("Could not load imported decal textures for " + folderName);

            var materialAssetPath = folderAssetPath + "/" + folderName + ".mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(materialAssetPath);

            if (material == null)
            {
                var placeholder = folderAssetPath + "/New Material.mat";
                if (File.Exists(Path.GetFullPath(placeholder)))
                {
                    var moveError = AssetDatabase.MoveAsset(placeholder, materialAssetPath);
                    if (!string.IsNullOrEmpty(moveError))
                        throw new Exception("Could not rename placeholder material in " + folderName + ": " + moveError);
                    material = AssetDatabase.LoadAssetAtPath<Material>(materialAssetPath);
                }
                else
                {
                    material = new Material(shader);
                    AssetDatabase.CreateAsset(material, materialAssetPath);
                }
            }

            material.name = folderName;
            material.shader = shader;
            material.SetColor("_BaseColor", Color.white);
            material.SetTexture("_BaseColorMap", colorAlphaTexture);
            material.SetTexture("_MaskMap", maskTexture);
            material.SetTexture("_NormalMap", normalTexture);
            material.SetFloat("_DecalBlend", 1f);
            material.SetFloat("_DecalMaskMapBlueScale", 1f);
            material.SetFloat("_MaskBlendSrc", 1f);
            material.SetFloat("_NormalBlendSrc", 0f);
            material.SetFloat("_AffectAlbedo", 1f);
            material.SetFloat("_AffectNormal", 1f);
            material.SetFloat("_AffectAO", 1f);
            material.SetFloat("_AffectMetal", 0f);
            material.SetFloat("_AffectSmoothness", 1f);

            if (!HDShaderUtils.ResetMaterialKeywords(material))
                throw new Exception("HDRP could not validate the decal material for " + folderName);

            EditorUtility.SetDirty(material);
            created++;
            Debug.Log("FAB_DECAL_MATERIAL_CREATED: " + materialAssetPath);
        }

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("FAB_DECAL_MATERIALS_DONE: " + created);
    }

    private static string Find(string[] paths, string suffix)
    {
        foreach (var path in paths)
            if (path.EndsWith(suffix, StringComparison.OrdinalIgnoreCase))
                return path;
        return null;
    }

    private static string ToAssetPath(string absolutePath)
    {
        var full = Path.GetFullPath(absolutePath).Replace('\\', '/');
        var assets = Path.GetFullPath("Assets").Replace('\\', '/');
        return full.Substring(assets.Length + 1);
    }

    private static Texture2D LoadTexture(string path, bool linear)
    {
        var texture = new Texture2D(2, 2, TextureFormat.RGBA32, false, linear);
        if (!ImageConversion.LoadImage(texture, File.ReadAllBytes(path), false))
            throw new Exception("Could not decode texture " + path);
        return texture;
    }

    private static void ConfigureTexture(string absolutePath, TextureImporterType type, bool srgb, bool alphaIsTransparency)
    {
        var assetPath = ToAssetPath(absolutePath);
        var importer = AssetImporter.GetAtPath(assetPath) as TextureImporter;
        if (importer == null)
            throw new Exception("No texture importer for " + assetPath);

        importer.textureType = type;
        importer.sRGBTexture = srgb;
        importer.alphaIsTransparency = alphaIsTransparency;
        importer.mipmapEnabled = true;
        importer.textureCompression = TextureImporterCompression.Compressed;
        importer.SaveAndReimport();
    }
}
