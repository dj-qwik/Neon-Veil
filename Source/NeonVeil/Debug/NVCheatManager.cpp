#include "Debug/NVCheatManager.h"
#include "Character/NVPlayerCharacter.h"
#include "Combat/NVHealthComponent.h"
#include "Combat/NVWeaponComponent.h"
#include "Combat/NVWeaponData.h"
#include "Combat/NVTrainingTarget.h"
#include "Interaction/NVInteractionComponent.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "NeonVeil.h"

#include "Camera/CameraComponent.h"
#include "Components/StaticMeshComponent.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "TimerManager.h"

ANVPlayerCharacter* UNVCheatManager::GetNVPlayer() const
{
	const APlayerController* PC = GetPlayerController();
	return PC ? Cast<ANVPlayerCharacter>(PC->GetPawn()) : nullptr;
}

AActor* UNVCheatManager::FindActor(const FString& Name) const
{
	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
#if WITH_EDITOR
		if (It->GetActorLabel().Contains(Name))
		{
			return *It;
		}
#endif
		if (It->GetName().Contains(Name))
		{
			return *It;
		}
	}
	UE_LOG(LogNeonVeil, Warning, TEXT("NVCheat: no actor matching '%s'"), *Name);
	return nullptr;
}

void UNVCheatManager::NVAimAt(const FString& Name, int32 WeakPoint)
{
	ANVPlayerCharacter* Player = GetNVPlayer();
	AActor* Target = FindActor(Name);
	if (!Player || !Target)
	{
		return;
	}
	FVector Point = Target->GetComponentsBoundingBox().GetCenter();
	TArray<UStaticMeshComponent*> Meshes;
	Target->GetComponents(Meshes);
	for (UStaticMeshComponent* M : Meshes)
	{
		const bool bIsWeak = M->ComponentHasTag(TEXT("WeakPoint"));
		if ((WeakPoint != 0) == bIsWeak && M->IsVisible() && M->GetStaticMesh())
		{
			Point = M->Bounds.Origin;
			if (bIsWeak || M->GetName() == TEXT("Body"))
			{
				break;
			}
		}
	}
	const FVector Eye = Player->GetFirstPersonCamera()->GetComponentLocation();
	GetPlayerController()->SetControlRotation((Point - Eye).Rotation());
	UE_LOG(LogNeonVeil, Log, TEXT("NVCheat: aim at %s (%s) dist %.0f cm"), *Target->GetName(), WeakPoint ? TEXT("weak point") : TEXT("body"), FVector::Dist(Eye, Point));
}

void UNVCheatManager::NVFire(int32 Shots)
{
	ShotsRemaining = FMath::Max(1, Shots);
	FireTick();
}

void UNVCheatManager::FireTick()
{
	ANVPlayerCharacter* Player = GetNVPlayer();
	if (!Player || ShotsRemaining <= 0)
	{
		return;
	}
	UNVWeaponComponent* W = Player->GetWeapons();
	W->StartFire();
	W->StopFire();
	--ShotsRemaining;
	const UNVWeaponData* Data = W->GetCurrentWeapon();
	const float Interval = Data ? (60.f / Data->RoundsPerMinute) + 0.02f : 0.2f;
	if (ShotsRemaining > 0)
	{
		GetWorld()->GetTimerManager().SetTimer(FireTimer, this, &UNVCheatManager::FireTick, Interval, false);
	}
}

void UNVCheatManager::NVReload()
{
	if (ANVPlayerCharacter* P = GetNVPlayer())
	{
		P->GetWeapons()->Reload();
	}
}

void UNVCheatManager::NVAim(int32 bOn)
{
	if (ANVPlayerCharacter* P = GetNVPlayer())
	{
		P->GetWeapons()->SetAiming(bOn != 0);
	}
}

void UNVCheatManager::NVEquip(int32 Slot)
{
	if (ANVPlayerCharacter* P = GetNVPlayer())
	{
		P->GetWeapons()->EquipSlot(Slot);
	}
}

void UNVCheatManager::NVGoTo(const FString& Name, float Distance, float ApproachYaw)
{
	ANVPlayerCharacter* Player = GetNVPlayer();
	AActor* Target = FindActor(Name);
	if (!Player || !Target)
	{
		return;
	}
	FVector Dir = ApproachYaw >= 0.f ? -FRotator(0.f, ApproachYaw, 0.f).Vector() : (Player->GetActorLocation() - Target->GetActorLocation()).GetSafeNormal2D();
	if (Dir.IsNearlyZero())
	{
		Dir = FVector::ForwardVector;
	}
	FVector Dest = Target->GetActorLocation() + Dir * Distance;
	Dest.Z = Player->GetActorLocation().Z + 2.f;
	Player->TeleportTo(Dest, (-Dir).Rotation());
	GetPlayerController()->SetControlRotation((-Dir).Rotation());
	UE_LOG(LogNeonVeil, Log, TEXT("NVCheat: moved to %s"), *Target->GetName());
}

void UNVCheatManager::NVUse(float Hold)
{
	ANVPlayerCharacter* Player = GetNVPlayer();
	if (!Player)
	{
		return;
	}
	AActor* Focus = Player->GetInteraction()->GetFocusedActor();
	UE_LOG(LogNeonVeil, Log, TEXT("NVCheat: use, focused=%s hold=%.2f"), Focus ? *Focus->GetName() : TEXT("None"), Hold);
	Player->GetInteraction()->BeginUse();
	if (Hold > 0.f)
	{
		GetWorld()->GetTimerManager().SetTimer(UseTimer, this, &UNVCheatManager::UseRelease, Hold, false);
	}
	else
	{
		UseRelease();
	}
}

void UNVCheatManager::UseRelease()
{
	if (ANVPlayerCharacter* Player = GetNVPlayer())
	{
		Player->GetInteraction()->EndUse();
	}
}

void UNVCheatManager::NVHurtSelf(float Amount)
{
	if (ANVPlayerCharacter* Player = GetNVPlayer())
	{
		Player->GetHealth()->ApplyDamage(Amount, nullptr, FGameplayTag());
	}
}

void UNVCheatManager::NVReport()
{
	UE_LOG(LogNeonVeil, Log, TEXT("===== NVReport t=%.2f ====="), GetWorld()->GetTimeSeconds());
	if (ANVPlayerCharacter* P = GetNVPlayer())
	{
		const UNVWeaponComponent* W = P->GetWeapons();
		const UNVWeaponData* D = W->GetCurrentWeapon();
		const TArray<FNVWeaponSlot>& Slots = W->GetSlots();
		UE_LOG(LogNeonVeil, Log, TEXT("Player health %.1f/%.1f  speed %.0f  sprint %d crouch %d  FOV %.1f  ADS %.2f"),
			P->GetHealth()->GetHealth(), P->GetHealth()->GetMaxHealth(), P->GetVelocity().Size2D(), P->IsSprinting(), P->bIsCrouched,
			P->GetFirstPersonCamera()->FieldOfView, W->GetAdsAlpha());
		for (int32 i = 0; i < Slots.Num(); ++i)
		{
			UE_LOG(LogNeonVeil, Log, TEXT("  slot %d %s mag %d reserve %d %s"), i, *GetNameSafe(Slots[i].Data), Slots[i].AmmoInMag, Slots[i].ReserveAmmo,
				i == W->GetCurrentSlotIndex() ? TEXT("<equipped>") : TEXT(""));
		}
		AActor* Focus = P->GetInteraction()->GetFocusedActor();
		UE_LOG(LogNeonVeil, Log, TEXT("  focus %s  location %s"), Focus ? *Focus->GetName() : TEXT("None"), *P->GetActorLocation().ToCompactString());
	}
	for (TActorIterator<ANVTrainingTarget> It(GetWorld()); It; ++It)
	{
		const UNVHealthComponent* H = It->FindComponentByClass<UNVHealthComponent>();
		UE_LOG(LogNeonVeil, Log, TEXT("  target %s  hp %.1f shield %.1f cleared %d  loc %s"), *It->GetName(), H->GetHealth(), H->GetShield(), It->IsCleared(), *It->GetActorLocation().ToCompactString());
	}
	if (const UNVObjectiveSubsystem* O = UNVObjectiveSubsystem::Get(this))
	{
		for (const FNVObjectiveDef& Def : O->GetActiveObjectives())
		{
			UE_LOG(LogNeonVeil, Log, TEXT("  objective ACTIVE %s"), *Def.ObjectiveID.ToString());
		}
		if (const UNVMissionData* M = O->GetCurrentMission())
		{
			for (const FNVObjectiveDef& Def : M->Objectives)
			{
				if (O->IsObjectiveComplete(Def.ObjectiveID))
				{
					UE_LOG(LogNeonVeil, Log, TEXT("  objective DONE %s"), *Def.ObjectiveID.ToString());
				}
			}
			UE_LOG(LogNeonVeil, Log, TEXT("  mission %s complete %d"), *M->MissionID.ToString(), O->IsMissionComplete());
		}
	}
}

void UNVCheatManager::NVSampleAds(float Seconds, int32 Samples)
{
	if (ANVPlayerCharacter* P = GetNVPlayer())
	{
		P->GetWeapons()->SetAiming(true);
	}
	SamplesRemaining = FMath::Max(1, Samples);
	SampleStart = GetWorld()->GetTimeSeconds();
	const float Interval = Seconds / SamplesRemaining;
	GetWorld()->GetTimerManager().SetTimer(SampleTimer, this, &UNVCheatManager::SampleTick, Interval, true, 0.f);
}

void UNVCheatManager::SampleTick()
{
	if (ANVPlayerCharacter* P = GetNVPlayer())
	{
		UE_LOG(LogNeonVeil, Log, TEXT("  ADS sample t=+%.3f alpha %.2f FOV %.1f"), GetWorld()->GetTimeSeconds() - SampleStart, P->GetWeapons()->GetAdsAlpha(), P->GetFirstPersonCamera()->FieldOfView);
	}
	if (--SamplesRemaining <= 0)
	{
		GetWorld()->GetTimerManager().ClearTimer(SampleTimer);
	}
}

void UNVCheatManager::NVMove(float Forward, float Right, float Seconds, int32 Sprint)
{
	ANVPlayerCharacter* P = GetNVPlayer();
	if (!P)
	{
		return;
	}
	P->SetDebugMoveInput(FVector2D(Right, Forward), Sprint != 0);
	MoveEndTime = GetWorld()->GetTimeSeconds() + Seconds;
	UE_LOG(LogNeonVeil, Log, TEXT("NVMove fwd %.1f right %.1f for %.2fs sprint %d"), Forward, Right, Seconds, Sprint);
	GetWorld()->GetTimerManager().SetTimer(MoveTimer, this, &UNVCheatManager::MoveTick, 0.25f, true);
}

void UNVCheatManager::MoveTick()
{
	ANVPlayerCharacter* P = GetNVPlayer();
	if (!P)
	{
		GetWorld()->GetTimerManager().ClearTimer(MoveTimer);
		return;
	}
	UE_LOG(LogNeonVeil, Log, TEXT("  move: speed %.0f sprint %d crouch %d slide %d vault %d z %.0f"),
		P->GetVelocity().Size2D(), P->IsSprinting(), P->bIsCrouched, P->IsSliding(), P->IsVaulting(), P->GetActorLocation().Z);
	if (GetWorld()->GetTimeSeconds() >= MoveEndTime)
	{
		P->SetDebugMoveInput(FVector2D::ZeroVector, false);
		GetWorld()->GetTimerManager().ClearTimer(MoveTimer);
		UE_LOG(LogNeonVeil, Log, TEXT("NVMove done at %s"), *P->GetActorLocation().ToCompactString());
	}
}

void UNVCheatManager::NVJump()
{
	if (ANVPlayerCharacter* P = GetNVPlayer())
	{
		P->DebugJump();
	}
}

void UNVCheatManager::NVCrouch(int32 bPressed)
{
	if (ANVPlayerCharacter* P = GetNVPlayer())
	{
		P->DebugCrouch(bPressed != 0);
	}
}

void UNVCheatManager::NVFace(float Yaw)
{
	if (APlayerController* PC = GetPlayerController())
	{
		PC->SetControlRotation(FRotator(0.f, Yaw, 0.f));
	}
}
