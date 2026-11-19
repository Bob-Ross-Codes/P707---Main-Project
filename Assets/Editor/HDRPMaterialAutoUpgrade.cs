using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEngine;

[InitializeOnLoad]
internal static class HDRPMaterialAutoUpgrade
{
    private const string TempFolder = "Assets/__HDRPConversionTemp";
    private const string GeneratedFolder = "Assets/HDRPGeneratedMasks";
    private const string ReportPath = "Assets/HDRP_Material_Conversion_Report.txt";
    private const string SessionKey = "HDRP.URPMaterialConversion.RanThisSession";

    static HDRPMaterialAutoUpgrade()
    {
        if (SessionState.GetBool(SessionKey, false)) return;
        SessionState.SetBool(SessionKey, true);
        EditorApplication.delayCall += Run;
    }

    private static void Run()
    {
        if (File.Exists(AbsolutePath(ReportPath))) return;

        var converted = new List<string>();
        var failures = new List<string>();
        string fatalError = null;

        try
        {
            Shader hdrpLit = Shader.Find("HDRP/Lit");
            Shader standard = Shader.Find("Standard");
            Shader standardSpecular = Shader.Find("Standard (Specular setup)");
            if (hdrpLit == null || standard == null || standardSpecular == null)
                throw new InvalidOperationException("Could not find HDRP/Lit or a built-in Standard shader in this Unity editor.");

            EnsureFolder("Assets", "__HDRPConversionTemp");
            EnsureFolder("Assets", "HDRPGeneratedMasks");

            var upgraderCache = new Dictionary<string, object>();
            var materialPaths = AssetDatabase.FindAssets("t:Material", new[] { "Assets" })
                .Select(AssetDatabase.GUIDToAssetPath)
                .Where(path => path.EndsWith(".mat", StringComparison.OrdinalIgnoreCase))
                .Distinct()
                .ToArray();

            foreach (string path in materialPaths)
            {
                Material original = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (original == null || original.shader == null) continue;
                string shaderName = original.shader.name;
                if (shaderName != "Universal Render Pipeline/Lit" && shaderName != "Universal Render Pipeline/Simple Lit") continue;

                string originalGuid = AssetDatabase.AssetPathToGUID(path);
                string tempPath = TempFolder + "/Source_" + originalGuid + ".mat";
                Material convertedMaterial = null;

                try
                {
                    bool specularWorkflow = shaderName.EndsWith("Simple Lit", StringComparison.Ordinal)
                        && original.HasProperty("_WorkflowMode")
                        && original.GetFloat("_WorkflowMode") < 0.5f;
                    Shader sourceShader = specularWorkflow ? standardSpecular : standard;
                    Material source = new Material(sourceShader);
                    source.name = "Source_" + originalGuid;
                    CopyTexture(original, source, "_BaseMap", "_MainTex");
                    CopyTexture(original, source, "_MetallicGlossMap", "_MetallicGlossMap");
                    CopyTexture(original, source, "_OcclusionMap", "_OcclusionMap");
                    CopyTexture(original, source, "_BumpMap", "_BumpMap");
                    CopyTexture(original, source, "_ParallaxMap", "_ParallaxMap");
                    CopyTexture(original, source, "_EmissionMap", "_EmissionMap");
                    CopyTexture(original, source, "_DetailAlbedoMap", "_DetailAlbedoMap");
                    CopyTexture(original, source, "_DetailMask", "_DetailMask");
                    CopyTexture(original, source, "_DetailNormalMap", "_DetailNormalMap");
                    CopyTexture(original, source, "_SpecGlossMap", "_SpecGlossMap");
                    CopyColor(original, source, "_BaseColor", "_Color");
                    CopyColor(original, source, "_SpecColor", "_SpecColor");
                    CopyColor(original, source, "_EmissionColor", "_EmissionColor");
                    CopyFloat(original, source, "_Smoothness", "_Glossiness");
                    CopyFloat(original, source, "_GlossMapScale", "_GlossMapScale");
                    CopyFloat(original, source, "_SmoothnessTextureChannel", "_SmoothnessTextureChannel");
                    CopyFloat(original, source, "_Metallic", "_Metallic");
                    CopyFloat(original, source, "_OcclusionStrength", "_OcclusionStrength");
                    CopyFloat(original, source, "_BumpScale", "_BumpScale");
                    CopyFloat(original, source, "_Parallax", "_Parallax");
                    CopyFloat(original, source, "_Cutoff", "_Cutoff");
                    CopyFloat(original, source, "_DetailAlbedoMapScale", "_DetailAlbedoMapScale");
                    CopyFloat(original, source, "_DetailNormalMapScale", "_DetailNormalMapScale");
                    CopyFloat(original, source, "_UVSec", "_UVSec");

                    bool alphaClip = original.HasProperty("_AlphaClip") && original.GetFloat("_AlphaClip") > 0.5f;
                    bool transparent = original.HasProperty("_Surface") && original.GetFloat("_Surface") > 0.5f;
                    source.SetFloat("_Mode", transparent ? 3f : (alphaClip ? 1f : 0f));
                    if (original.IsKeywordEnabled("_EMISSION")) source.EnableKeyword("_EMISSION");
                    if (alphaClip || original.IsKeywordEnabled("_ALPHATEST_ON")) source.EnableKeyword("_ALPHATEST_ON");

                    AssetDatabase.CreateAsset(source, tempPath);
                    AssetDatabase.SaveAssets();
                    source = AssetDatabase.LoadAssetAtPath<Material>(tempPath);
                    convertedMaterial = new Material(hdrpLit);
                    convertedMaterial.name = original.name;

                    string upgraderSource = specularWorkflow ? "Standard (Specular setup)" : "Standard";
                    object upgrader = GetUpgrader(upgraderSource, upgraderCache);
                    MethodInfo convert = upgrader.GetType().GetMethod("Convert", BindingFlags.Instance | BindingFlags.Public);
                    if (convert == null) throw new MissingMethodException("HDRP's Standard material upgrader has no Convert method.");
                    convert.Invoke(upgrader, new object[] { source, convertedMaterial });

                    if (transparent)
                    {
                        convertedMaterial.SetFloat("_SurfaceType", 1f);
                        if (alphaClip) convertedMaterial.SetFloat("_AlphaCutoffEnable", 1f);
                    }
                    if (alphaClip)
                    {
                        convertedMaterial.SetFloat("_AlphaCutoffEnable", 1f);
                        convertedMaterial.EnableKeyword("_ALPHATEST_ON");
                    }

                    MoveGeneratedTexture(tempPath, "_MaskMap.png", original, originalGuid);
                    MoveGeneratedTexture(tempPath, "_DetailMap.png", original, originalGuid);

                    original.shader = hdrpLit;
                    original.CopyPropertiesFromMaterial(convertedMaterial);
                    original.name = Path.GetFileNameWithoutExtension(path);
                    EditorUtility.SetDirty(original);
                    converted.Add(path + "  (" + shaderName + (specularWorkflow ? ", specular workflow" : ", metallic workflow") + ")");
                }
                catch (Exception e)
                {
                    failures.Add(path + " :: " + (e.InnerException != null ? e.InnerException.Message : e.Message));
                    Debug.LogError("HDRP material conversion failed for " + path + ": " + e);
                }
                finally
                {
                    if (convertedMaterial != null) UnityEngine.Object.DestroyImmediate(convertedMaterial);
                    if (AssetDatabase.LoadAssetAtPath<Material>(tempPath) != null) AssetDatabase.DeleteAsset(tempPath);
                }
            }

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
        }
        catch (Exception e)
        {
            fatalError = e.ToString();
            Debug.LogError("HDRP material conversion stopped: " + e);
        }

        var remaining = new Dictionary<string, List<string>>();
        foreach (string path in AssetDatabase.FindAssets("t:Material", new[] { "Assets" }).Select(AssetDatabase.GUIDToAssetPath).Distinct())
        {
            Material material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (material == null || material.shader == null || !material.shader.name.StartsWith("Universal Render Pipeline/", StringComparison.Ordinal)) continue;
            if (!remaining.ContainsKey(material.shader.name)) remaining[material.shader.name] = new List<string>();
            remaining[material.shader.name].Add(path);
        }

        var report = new List<string>
        {
            "HDRP material conversion report",
            "Converted URP Lit and Simple Lit materials using HDRP's built-in Standard-to-HDRP Lit upgrader.",
            "Generated packed mask/detail textures are stored in Assets/HDRPGeneratedMasks.",
            "",
            "Converted: " + converted.Count
        };
        report.AddRange(converted.Select(path => "  " + path));
        report.Add("");
        report.Add("Failed: " + failures.Count);
        report.AddRange(failures.Select(path => "  " + path));
        report.Add("");
        report.Add("Remaining URP-shader materials requiring a shader-specific HDRP replacement: " + remaining.Values.Sum(paths => paths.Count));
        foreach (var group in remaining.OrderBy(group => group.Key))
        {
            report.Add("");
            report.Add(group.Key + " (" + group.Value.Count + ")");
            report.AddRange(group.Value.OrderBy(path => path).Select(path => "  " + path));
        }
        if (!string.IsNullOrEmpty(fatalError))
        {
            report.Add("");
            report.Add("Fatal error:");
            report.Add(fatalError);
        }
        File.WriteAllLines(AbsolutePath(ReportPath), report);
        AssetDatabase.Refresh();
        Debug.Log("HDRP material conversion finished. Converted " + converted.Count + ", failed " + failures.Count + ", remaining URP materials " + remaining.Values.Sum(paths => paths.Count) + ". See " + ReportPath + ".");
    }

    private static object GetUpgrader(string sourceShader, Dictionary<string, object> cache)
    {
        if (cache.TryGetValue(sourceShader, out object existing)) return existing;
        Assembly assembly = AppDomain.CurrentDomain.GetAssemblies().FirstOrDefault(a => a.GetName().Name == "Unity.RenderPipelines.HighDefinition.Editor");
        Type type = assembly == null ? null : assembly.GetType("UnityEditor.Rendering.HighDefinition.StandardsToHDLitMaterialUpgrader");
        if (type == null) throw new TypeLoadException("HDRP's StandardsToHDLitMaterialUpgrader type was not found.");
        ConstructorInfo constructor = type.GetConstructors(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)
            .FirstOrDefault(c => c.GetParameters().Length == 3);
        if (constructor == null) throw new MissingMethodException("HDRP's material upgrader constructor was not found.");
        object value = constructor.Invoke(new object[] { sourceShader, "HDRP/Lit", null });
        cache[sourceShader] = value;
        return value;
    }

    private static void CopyTexture(Material from, Material to, string oldName, string newName)
    {
        if (!from.HasProperty(oldName) || !to.HasProperty(newName)) return;
        to.SetTexture(newName, from.GetTexture(oldName));
        to.SetTextureScale(newName, from.GetTextureScale(oldName));
        to.SetTextureOffset(newName, from.GetTextureOffset(oldName));
    }

    private static void CopyColor(Material from, Material to, string oldName, string newName)
    {
        if (from.HasProperty(oldName) && to.HasProperty(newName)) to.SetColor(newName, from.GetColor(oldName));
    }

    private static void CopyFloat(Material from, Material to, string oldName, string newName)
    {
        if (from.HasProperty(oldName) && to.HasProperty(newName)) to.SetFloat(newName, from.GetFloat(oldName));
    }

    private static string AbsolutePath(string assetPath)
    {
        string projectRoot = Directory.GetParent(Application.dataPath).FullName;
        return Path.Combine(projectRoot, assetPath.Replace('/', Path.DirectorySeparatorChar));
    }
    private static void EnsureFolder(string parent, string name)
    {
        string path = parent + "/" + name;
        if (!AssetDatabase.IsValidFolder(path)) AssetDatabase.CreateFolder(parent, name);
    }

    private static void MoveGeneratedTexture(string sourceMaterialPath, string suffix, Material original, string originalGuid)
    {
        string sourceTexturePath = sourceMaterialPath.Substring(0, sourceMaterialPath.Length - 4) + suffix;
        if (!File.Exists(AbsolutePath(sourceTexturePath))) return;
        string safeName = string.Join("_", Path.GetFileNameWithoutExtension(AssetDatabase.GetAssetPath(original)).Split(Path.GetInvalidFileNameChars()));
        string destination = GeneratedFolder + "/" + safeName + "_" + originalGuid.Substring(0, Math.Min(8, originalGuid.Length)) + suffix;
        destination = AssetDatabase.GenerateUniqueAssetPath(destination);
        string error = AssetDatabase.MoveAsset(sourceTexturePath, destination);
        if (!string.IsNullOrEmpty(error)) throw new IOException("Could not move generated texture " + sourceTexturePath + ": " + error);
    }
}


