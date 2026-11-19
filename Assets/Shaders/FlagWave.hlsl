#ifndef PROJECT_FLAG_WAVE_INCLUDED
#define PROJECT_FLAG_WAVE_INCLUDED

// Wind for every flag, set by FlagWind.cs.
// _FlagWind: xy = downwind direction in world XZ, z = strength 0..1, w = gustiness 0..1.
// _FlagWindClock: metres the wind has travelled; it runs faster in strong wind, so ripples speed up smoothly.
float4 _FlagWind;
float _FlagWindClock;

struct FlagParams
{
    float side;      // 1 = front layer, -1 = back layer
    float amplitude;
    float speed;
    float swivel;    // 1 = turns on the pole to face downwind
    float seed;      // 0..1, different for every flag
    float wind;      // wind this flag feels right now, 0..1
    float gust;      // -1..1
    float yaw;       // radians around the pole that point the flag downwind
};

// Flag.cs packs the per-flag settings into the mesh normal; the real normal is computed below.
// x = amplitude (negative on the back layer), y = speed (negative when the flag does not swivel),
// z = wind response.
FlagParams GetFlagParams(float3 packed)
{
    FlagParams p;
    p.side = packed.x < 0 ? -1 : 1;
    p.amplitude = abs(packed.x);
    p.swivel = packed.y < 0 ? 0 : 1;
    p.speed = abs(packed.y);

    float3 pivotWS = GetObjectToWorldMatrix()._m03_m13_m23;
    p.seed = frac(sin(dot(pivotWS, float3(12.9898, 78.233, 37.719))) * 43758.5453);

    float2 dir = dot(_FlagWind.xy, _FlagWind.xy) > 1e-4 ? normalize(_FlagWind.xy) : float2(1, 0);
    // Gusts roll downwind across the scene, so neighbouring flags feel each one a moment apart.
    float g = dot(pivotWS.xz, dir) * 0.12 - _Time.y * 0.7 + p.seed * 2.0;
    p.gust = sin(g) * 0.55 + sin(g * 2.31 + 1.7) * 0.3 + sin(g * 5.13 + 0.4) * 0.15;
    p.wind = saturate(_FlagWind.z * packed.z * (1.0 + _FlagWind.w * 0.7 * p.gust));

    float3 windOS = TransformWorldToObjectDir(float3(dir.x, 0, dir.y));
    float yaw = atan2(-windOS.z, windOS.x) + 0.18 * _FlagWind.w * p.gust;
    p.yaw = yaw * p.swivel;
    return p;
}

// Rest position (x along the flag from the pole, y up the pole, in metres) to deformed position.
float3 FlagDisplace(float x, float y, FlagParams p)
{
    float w = p.wind;
    float travel = _FlagWindClock * p.speed * lerp(0.85, 1.15, p.seed) + p.seed * 37.0;

    // Light wind: slack fabric, big slow billows. Strong wind: taut fabric, small fast ripples.
    float ampScale = p.amplitude * (0.05 + 0.2 * saturate(w * 4.0) * (1.0 - 0.5 * w));
    float pin = x * saturate(x * 2.5);   // the hoist is sewn to the pole

    const float k1 = 6.2832 / 1.6, k2 = 6.2832 / 0.8, k3 = 6.2832 / 0.4;
    float ph1 = k1 * (x - travel) + 0.55 * y + p.seed * 6.2832;
    float ph2 = k2 * (x + 0.30 * y - travel * 1.13) + 1.3;
    float ph3 = k3 * (x - 0.45 * y - travel * 1.37) + 2.1;
    float flutter = saturate(x * 0.8) * (0.6 + 0.4 * w);  // the free end flutters most
    float z = ampScale * pin * (sin(ph1) + 0.6 * sin(ph2) + 0.25 * flutter * sin(ph3));

    // Waving gathers the cloth, so the flag gets a little shorter instead of stretching.
    float slope = ampScale * x * k1;
    x /= sqrt(1.0 + 0.5 * slope * slope);

    // With little wind the flag hangs down from the pole, more so further out.
    float droop = 1.35 * pow(1.0 - saturate(w * 1.5), 2.0) + 0.05;
    float bend = droop * (1.0 - exp(-x * 2.0));
    float3 pos = float3(x * cos(bend), y - x * sin(bend), z);

    float s, c;
    sincos(p.yaw, s, c);
    return float3(pos.x * c + pos.z * s, pos.y, -pos.x * s + pos.z * c);
}

// Replaces the rest position with the waving one and computes its normal and tangent.
void ApplyFlagWave(inout float3 positionOS, inout float3 normalOS, out float4 tangentOS)
{
    FlagParams p = GetFlagParams(normalOS);
    const float e = 0.01;
    float3 pos = FlagDisplace(positionOS.x, positionOS.y, p);
    float3 dx = FlagDisplace(positionOS.x + e, positionOS.y, p) - pos;
    float3 dy = FlagDisplace(positionOS.x, positionOS.y + e, p) - pos;

    positionOS = pos;
    normalOS = normalize(cross(dx, dy)) * p.side;
    tangentOS = float4(normalize(dx), p.side);
}

#endif
