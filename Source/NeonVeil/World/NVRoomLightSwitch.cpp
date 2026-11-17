#include "World/NVRoomLightSwitch.h"

#include "NeonVeil.h"
#include "Interaction/NVInteractableActor.h"
#include "Components/LightComponent.h"
#include "Components/MeshComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstance.h"
#include "Sound/SoundBase.h"

ANVRoomLightSwitch::ANVRoomLightSwitch()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = false;
	SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));
}

void ANVRoomLightSwitch::BeginPlay()
{
	Super::BeginPlay();
	for (AActor* A : Lights)
	{
		if (!A) { continue; }
		TArray<ULightComponent*> Ls;
		A->GetComponents(Ls);
		for (ULightComponent* L : Ls) { LightBases.Add({ L, L->Intensity }); }
	}
	for (AActor* A : MaterialActors)
	{
		if (!A) { continue; }
		TArray<UMeshComponent*> Ms;
		A->GetComponents(Ms);
		for (UMeshComponent* M : Ms)
		{
			for (int32 i = 0; i < M->GetNumMaterials(); ++i)
			{
				UMaterialInstance* MI = Cast<UMaterialInstance>(M->GetMaterial(i));
				if (MI && MI->Parent && MI->GetName().EndsWith(DimSuffix))
				{
					MatSlots.Add({ M, i, MI, MI->Parent });
				}
			}
		}
	}
	for (ANVInteractableActor* P : Panels)
	{
		if (P) { P->OnInteracted.AddDynamic(this, &ANVRoomLightSwitch::HandleUsed); }
	}
	UpdatePrompts();
	UE_LOG(LogNeonVeil, Log, TEXT("%s: %d lights, %d material slots, %d holograms, %d panels"), *GetName(), LightBases.Num(), MatSlots.Num(), Holograms.Num(), Panels.Num());
}

void ANVRoomLightSwitch::HandleUsed(ANVInteractableActor*, AActor*)
{
	Toggle();
}

void ANVRoomLightSwitch::Toggle()
{
	bWorkLights = !bWorkLights;
	if (USoundBase* S = bWorkLights ? LightsUpSound.Get() : ShowSound.Get())
	{
		UGameplayStatics::PlaySound2D(this, S);
	}
	FlickerTime = 0.f;
	NextFlicker = 0.f;
	UpdatePrompts();
	SetActorTickEnabled(true);
}

void ANVRoomLightSwitch::UpdatePrompts()
{
	for (ANVInteractableActor* P : Panels)
	{
		if (P) { P->Configure(bWorkLights ? PromptShow : PromptLightsUp, 0.f, false, nullptr); }
	}
}

void ANVRoomLightSwitch::SetMaterials(bool bFull)
{
	bMaterialsFull = bFull;
	for (const FMatSlot& S : MatSlots)
	{
		if (S.Mesh.IsValid()) { S.Mesh->SetMaterial(S.Index, bFull ? S.Full.Get() : S.Dim.Get()); }
	}
}

void ANVRoomLightSwitch::SetHologramsVisible(bool bVisible)
{
	for (AActor* A : Holograms)
	{
		if (!A) { continue; }
		TArray<USceneComponent*> Cs;
		A->GetComponents(Cs);
		for (USceneComponent* C : Cs) { C->SetVisibility(bVisible); }
	}
}

void ANVRoomLightSwitch::Tick(float Dt)
{
	Super::Tick(Dt);
	Alpha = FMath::FInterpConstantTo(Alpha, bWorkLights ? 1.f : 0.f, Dt, 1.f / FMath::Max(RampTime, 0.05f));
	const float E = FMath::InterpEaseInOut(0.f, 1.f, Alpha, 2.f);
	for (const FLightBase& L : LightBases)
	{
		if (L.Light.IsValid()) { L.Light->SetIntensity(L.Base * FMath::Lerp(1.f, BrightScale, E)); }
	}
	if ((Alpha > 0.5f) != bMaterialsFull) { SetMaterials(Alpha > 0.5f); }

	// holograms stutter for ~0.5 s, then settle off (work lights) or on (show)
	if (FlickerTime >= 0.f)
	{
		FlickerTime += Dt;
		if (FlickerTime < 0.55f)
		{
			if (FlickerTime >= NextFlicker)
			{
				SetHologramsVisible(FMath::FRand() < (bWorkLights ? 0.45f : 0.6f));
				NextFlicker = FlickerTime + FMath::FRandRange(0.03f, 0.09f);
			}
		}
		else
		{
			SetHologramsVisible(!bWorkLights);
			FlickerTime = -1.f;
		}
	}
	if (FlickerTime < 0.f && FMath::IsNearlyEqual(Alpha, bWorkLights ? 1.f : 0.f))
	{
		SetActorTickEnabled(false);
	}
}
