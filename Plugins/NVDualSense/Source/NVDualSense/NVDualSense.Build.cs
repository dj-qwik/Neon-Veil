using UnrealBuildTool;

public class NVDualSense : ModuleRules
{
	public NVDualSense(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		PrivateDependencyModuleNames.AddRange(new string[] { "Core", "ApplicationCore", "InputCore", "InputDevice" });
		if (Target.Platform == UnrealTargetPlatform.Win64)
		{
			PublicSystemLibraries.AddRange(new string[] { "hid.lib", "setupapi.lib" });
		}
	}
}
