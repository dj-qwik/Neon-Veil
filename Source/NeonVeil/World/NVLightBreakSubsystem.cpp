#include "World/NVLightBreakSubsystem.h"
#include "NeonVeil.h"

#include "Components/LightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "Sound/SoundBase.h"
#include "TimerManager.h"

const TCHAR* UNVLightBreakSubsystem::GroupPrefix = TEXT("NVLightGroup_");
const TCHAR* UNVLightBreakSubsystem::FlagPrefix = TEXT("LightOut:");
const FName UNVLightBreakSubsystem::FixtureTag(TEXT("NVLightFixture"));

namespace
{
	const TCHAR* DeadLampPath = TEXT("/Game/NeonVeil/Materials/Fx/MI_NV_LampDead.MI_NV_LampDead");
	const TCHAR* SparkPath = TEXT("/Game/NiagaraExamples/FX_Sparks/NS_Spark_Burst.NS_Spark_Burst");
	const TCHAR* GlassPath = TEXT("/Game/NiagaraExamples/FX_Weapons/Impacts/NS_Impact_Glass.NS_Impact_Glass");
	const TCHAR* ShatterPath = TEXT("/Game/NeonVeil/Audio/SFX/SFX_NV_LightShatter.SFX_NV_LightShatter");
	const TCHAR* ShatterFallbackPath = TEXT("/Game/SciFiUISFX/Cues/Impacts/Impact_2_Top_End_Cue.Impact_2_Top_End_Cue");

	template <typename T>
	T* LoadQuiet(const TCHAR* Path)
	{
		return Cast<T>(StaticLoadObject(T::StaticClass(), nullptr, Path, nullptr, LOAD_NoWarn | LOAD_Quiet));
	}
}

UNVLightBreakSubsystem* UNVLightBreakSubsystem::Get(const UObject* WorldContext)
{
	const UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	return World ? World->GetSubsystem<UNVLightBreakSubsystem>() : nullptr;
}

FName UNVLightBreakSubsystem::GroupOf(const AActor* Actor)
{
	if (Actor)
	{
		for (const FName& Tag : Actor->Tags)
		{
			if (Tag.ToString().StartsWith(GroupPrefix))
			{
				return Tag;
			}
		}
	}
	return NAME_None;
}

void UNVLightBreakSubsystem::BuildIndex()
{
	bIndexed = true;
	Groups.Reset();
	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
		const FName G = GroupOf(*It);
		if (!G.IsNone())
		{
			Groups.FindOrAdd(G).Add(*It);
		}
	}
	UE_LOG(LogNeonVeil, Log, TEXT("Shootable lights: %d groups"), Groups.Num());
}

bool UNVLightBreakSubsystem::TryBreak(const FHitResult& Hit)
{
	AActor* A = Hit.GetActor();
	if (!A || !A->ActorHasTag(FixtureTag))
	{
		return false;
	}
	return BreakGroup(GroupOf(A), false, Hit.ImpactPoint);
}

bool UNVLightBreakSubsystem::BreakGroup(FName Group, bool bInstant, FVector EffectLocation)
{
	if (Group.IsNone() || Broken.Contains(Group))
	{
		return false;
	}
	if (!bIndexed)
	{
		BuildIndex();
	}
	const TArray<TWeakObjectPtr<AActor>>* Members = Groups.Find(Group);
	if (!Members)
	{
		return false;
	}
	Broken.Add(Group);
	UE_LOG(LogNeonVeil, Log, TEXT("Light %s shot out%s"), *Group.ToString(), bInstant ? TEXT(" (restored)") : TEXT(""));

	for (const TWeakObjectPtr<AActor>& M : *Members)
	{
		if (AActor* Actor = M.Get(); Actor && Actor->ActorHasTag(FixtureTag))
		{
			DarkenFixture(Actor);
			if (EffectLocation.IsZero())
			{
				EffectLocation = Actor->GetComponentsBoundingBox().GetCenter();
			}
		}
	}

	SetGroupLights(Group, false);
	if (bInstant)
	{
		return true;
	}

	// effects: a small spark burst and glass at the lamp (the example systems are sized for big impacts), the shatter
	if (UNiagaraSystem* Sparks = LoadQuiet<UNiagaraSystem>(SparkPath))
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, Sparks, EffectLocation, FRotator(-90.f, 0.f, 0.f), FVector(0.3f));
	}
	if (UNiagaraSystem* Glass = LoadQuiet<UNiagaraSystem>(GlassPath))
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, Glass, EffectLocation, FRotator(-90.f, 0.f, 0.f), FVector(0.4f));
	}
	USoundBase* Shatter = LoadQuiet<USoundBase>(ShatterPath);
	if (!Shatter)
	{
		Shatter = LoadQuiet<USoundBase>(ShatterFallbackPath);
	}
	if (Shatter)
	{
		UGameplayStatics::PlaySoundAtLocation(this, Shatter, EffectLocation, 1.f, FMath::FRandRange(0.94f, 1.06f));
	}

	// the light dies with a short stutter: off, a weak flash back, off for good
	FTimerManager& TM = GetWorld()->GetTimerManager();
	FTimerHandle H1, H2;
	TM.SetTimer(H1, FTimerDelegate::CreateWeakLambda(this, [this, Group]() { SetGroupLights(Group, true); }), 0.07f, false);
	TM.SetTimer(H2, FTimerDelegate::CreateWeakLambda(this, [this, Group]() { SetGroupLights(Group, false); }), 0.16f, false);
	return true;
}

void UNVLightBreakSubsystem::SetGroupLights(FName Group, bool bOn)
{
	const TArray<TWeakObjectPtr<AActor>>* Members = Groups.Find(Group);
	if (!Members)
	{
		return;
	}
	for (const TWeakObjectPtr<AActor>& M : *Members)
	{
		if (AActor* Actor = M.Get())
		{
			TArray<ULightComponent*> Lights;
			Actor->GetComponents(Lights);
			for (ULightComponent* L : Lights)
			{
				L->SetVisibility(bOn);
			}
		}
	}
}

void UNVLightBreakSubsystem::DarkenFixture(AActor* Fixture)
{
	if (!DeadLampMaterial)
	{
		DeadLampMaterial = LoadQuiet<UMaterialInterface>(DeadLampPath);
	}
	TArray<UStaticMeshComponent*> Meshes;
	Fixture->GetComponents(Meshes);
	bool bAnyTagged = false;
	for (UStaticMeshComponent* C : Meshes)
	{
		for (const FName& T : C->ComponentTags)
		{
			bAnyTagged |= T.ToString().StartsWith(TEXT("NVLampSlot_"));
		}
	}
	for (UStaticMeshComponent* C : Meshes)
	{
		for (int32 Slot = 0; Slot < C->GetNumMaterials(); ++Slot)
		{
			if (bAnyTagged && !C->ComponentHasTag(FName(*FString::Printf(TEXT("NVLampSlot_%d"), Slot))))
			{
				continue;
			}
			if (DeadLampMaterial)
			{
				C->SetMaterial(Slot, DeadLampMaterial);
			}
			else if (UMaterialInstanceDynamic* MID = C->CreateAndSetMaterialInstanceDynamic(Slot))
			{
				for (const TCHAR* P : { TEXT("Glow"), TEXT("Emissive"), TEXT("EmissiveStrength"), TEXT("Emissive Intensity"), TEXT("Brightness") })
				{
					MID->SetScalarParameterValue(P, 0.f);
				}
			}
		}
	}
}

void UNVLightBreakSubsystem::AppendSaveFlags(TArray<FName>& Flags) const
{
	for (const FName& G : Broken)
	{
		Flags.AddUnique(FName(*(FString(FlagPrefix) + G.ToString())));
	}
}

void UNVLightBreakSubsystem::RestoreFromFlags(const TArray<FName>& Flags)
{
	for (const FName& F : Flags)
	{
		FString S = F.ToString();
		if (S.RemoveFromStart(FlagPrefix))
		{
			BreakGroup(FName(*S), true);
		}
	}
}
