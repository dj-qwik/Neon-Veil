using UnrealBuildTool;

public class NeonVeilTarget : TargetRules
{
	public NeonVeilTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("NeonVeil");
	}
}
