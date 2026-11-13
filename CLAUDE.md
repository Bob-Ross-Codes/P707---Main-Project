# P707 — Rådhuspladsen timeline

An immersive installation: a visitor stands in front of a large screen and sees Rådhuspladsen in Copenhagen through history. An Azure Kinect tracks their head, and the camera projection shifts with their position so the screen behaves like a window.

## Stack

- Unity 6000.3.25f1, URP (`Assets/Settings/PC_RPAsset.asset`). The HDRP package is in the manifest but unused.
- Input System, Timeline, ProBuilder, Terrain Tools, AI Navigation, uGUI.
- Audio is Wwise, not Unity audio. The Wwise project is `P707---Main-Project_WwiseProject/`; post events with `AkSoundEngine.PostEvent`.
- Azure Kinect Sensor and Body Tracking SDKs (`Assets/From Sample/Plugins`). Body tracking runs on Windows only. On macOS, press Tab in play mode for the WASD debug mode in `PlayerModeController`.

## Layout

- `Assets/Scripts/` — project code. Everything else under `Assets/` with scripts is third-party; do not edit it.
  - `HeadcoupledPerspective.cs` — off-axis projection from head position and physical screen size (metres).
  - `TimelineController.cs` — maps `timelineValue` (0–100) onto the `PlayableDirector`.
  - `BuildingFade.cs`, `TreeFade.cs` — fade era content in and out; buildings use the `_Fade` property of `Assets/3D Assets/Fadeshader.shadergraph`.
  - `Player/` — smoothing of the tracked head (`PlayerManager`), play-area mapping (`PlayerAreaTracker`), zone events (`PlayerZoneTrigger`).
  - `WWise/` — audio triggers and debug helpers.
- `Assets/From Sample/` — Microsoft's Kinect body-tracking sample (skeleton, tracker, puppet avatar).
- `Assets/Config/` and `Assets/StreamingAssets/config.json` — Kinect sample configuration.
- `Assets/Scenes/` — eras are separate scenes named by year (4000 f.v.t., 1130, 1620, 1650). Each teammate has a `<Name> Testing/` folder; work in your own.
- `Assets/Prefabs/Setup/` — Kinect and screen rig prefabs.

## Conventions

- World units are metres and match the physical installation; keep models at real-world scale.
- Scenes and prefabs are shared binary-like YAML with no merge tool configured. Do not edit another person's scene; ask before touching `SampleScene` or anything outside the current branch owner's folder.
- New `.cs` files need their `.meta` committed alongside.
- No test suite exists. Verify changes in play mode with the debug mode above.
