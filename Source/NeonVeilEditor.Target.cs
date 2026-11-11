using UnrealBuildTool;

public class NeonVeilEditorTarget : TargetRules
{
	public NeonVeilEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("NeonVeil");
	}
}
