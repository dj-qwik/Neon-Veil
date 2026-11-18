#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "NVLightBreakSubsystem.generated.h"

class UMaterialInterface;
class UNiagaraSystem;
class USoundBase;

/**
 * Shootable lights. Editor setup (Scripts/Python/nv_shootable_lights.py) gives each light fixture mesh and the light
 * actors it drives a shared actor tag "NVLightGroup_<id>" and the fixture the tag "NVLightFixture" (its emissive
 * material slots carry component tags "NVLampSlot_<index>"). A bullet that hits a fixture breaks its group: sparks,
 * a shatter, the lights flicker and die, and the lamp goes dark. Broken groups stay out for the rest of the visit and
 * are written to checkpoints (save Flags "LightOut:<group>"), so they stay out after a reload too.
 */
UCLASS()
class NEONVEIL_API UNVLightBreakSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	static UNVLightBreakSubsystem* Get(const UObject* WorldContext);

	/** A bullet hit world geometry. Breaks the fixture's group if it was a live light fixture. */
	bool TryBreak(const FHitResult& Hit);

	/** Break one group. bInstant skips the flicker and effects (checkpoint restore). */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Lights")
	bool BreakGroup(FName Group, bool bInstant = false, FVector EffectLocation = FVector::ZeroVector, FVector ShotDirection = FVector::ZeroVector);

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Lights")
	bool IsBroken(FName Group) const { return Broken.Contains(Group); }

	/** Save flags for every broken group ("LightOut:<group>"). */
	void AppendSaveFlags(TArray<FName>& Flags) const;
	/** Break every group named in the save flags, instantly. */
	void RestoreFromFlags(const TArray<FName>& Flags);

	static FName GroupOf(const AActor* Actor);

	static const TCHAR* GroupPrefix;
	static const TCHAR* FlagPrefix;
	static const FName FixtureTag;

private:
	void BuildIndex();
	void SetGroupLights(FName Group, bool bOn);
	void DarkenFixture(AActor* Fixture);

	TMap<FName, TArray<TWeakObjectPtr<AActor>>> Groups;
	bool bIndexed = false;
	TSet<FName> Broken;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInterface> DeadLampMaterial;
};
