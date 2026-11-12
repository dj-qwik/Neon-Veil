#include "Abilities/NVAbilityComponent.h"
#include "Abilities/NVAbilityData.h"
#include "Abilities/NVReconDrone.h"
#include "Combat/NVHealthComponent.h"
#include "Core/NVGameplayTags.h"
#include "NeonVeil.h"

#include "Camera/CameraComponent.h"
#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"

UNVAbilityComponent::UNVAbilityComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PrePhysics;
}

void UNVAbilityComponent::BeginPlay()
{
	Super::BeginPlay();
	Runtime.SetNum(Abilities.Num());
}

int32 UNVAbilityComponent::FindSlot(FGameplayTag AbilityTag) const
{
	for (int32 i = 0; i < Abilities.Num(); ++i)
	{
		if (Abilities[i] && Abilities[i]->AbilityTag.MatchesTagExact(AbilityTag))
		{
			return i;
		}
	}
	return INDEX_NONE;
}

bool UNVAbilityComponent::TryActivate(FGameplayTag AbilityTag)
{
	return TryActivateSlot(FindSlot(AbilityTag));
}

bool UNVAbilityComponent::TryActivateSlot(int32 Slot)
{
	if (!Abilities.IsValidIndex(Slot) || !Abilities[Slot] || !Runtime.IsValidIndex(Slot))
	{
		OnAbilityFailed.Broadcast(FGameplayTag(), ENVAbilityFailReason::NoAbility);
		return false;
	}
	const UNVAbilityData& Data = *Abilities[Slot];
	FNVAbilityRuntime& R = Runtime[Slot];
	ENVAbilityFailReason Reason = ENVAbilityFailReason::None;
	if (R.bDisabled)
	{
		Reason = ENVAbilityFailReason::Disabled;
	}
	else if (R.ActiveTimeLeft > 0.f)
	{
		Reason = ENVAbilityFailReason::AlreadyActive;
	}
	else if (R.CooldownLeft > 0.f)
	{
		Reason = ENVAbilityFailReason::OnCooldown;
	}
	if (Reason != ENVAbilityFailReason::None)
	{
		UE_LOG(LogNeonVeil, Log, TEXT("Ability %s refused (%s)"), *Data.AbilityTag.ToString(), *UEnum::GetValueAsString(Reason));
		OnAbilityFailed.Broadcast(Data.AbilityTag, Reason);
		return false;
	}
	StartEffect(Slot);
	return true;
}

void UNVAbilityComponent::StartEffect(int32 Slot)
{
	const UNVAbilityData& Data = *Abilities[Slot];
	FNVAbilityRuntime& R = Runtime[Slot];
	R.ActiveTimeLeft = FMath::Max(0.01f, Data.Duration);
	R.CooldownLeft = 0.f;

	if (Data.AbilityTag.MatchesTagExact(NVTags::Ability_KineticShield))
	{
		if (UNVHealthComponent* H = GetOwner()->FindComponentByClass<UNVHealthComponent>())
		{
			H->IncomingDamageScale = 1.f - Data.DamageReduction;
			H->ResetBlockedDamage();
		}
	}
	else if (Data.AbilityTag.MatchesTagExact(NVTags::Ability_DroneUplink))
	{
		const APawn* Pawn = Cast<APawn>(GetOwner());
		FVector Origin = GetOwner()->GetActorLocation() + FVector(0.f, 0.f, 60.f);
		FRotator Aim = GetOwner()->GetActorRotation();
		if (Pawn && Pawn->GetController())
		{
			Aim = Pawn->GetController()->GetControlRotation();
		}
		if (const UCameraComponent* Cam = GetOwner()->FindComponentByClass<UCameraComponent>())
		{
			Origin = Cam->GetComponentLocation();
		}
		UClass* Cls = Data.DroneClass ? Data.DroneClass.Get() : ANVReconDrone::StaticClass();
		FActorSpawnParameters P;
		P.Owner = GetOwner();
		P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		ANVReconDrone* Drone = GetWorld()->SpawnActor<ANVReconDrone>(Cls, Origin + Aim.Vector() * 60.f, Aim, P);
		if (Drone)
		{
			Drone->Launch(this, Aim.Vector(), Data.DroneRange, Data.ScanRadius, Data.MarkDuration, Data.Duration);
			ActiveDrone = Drone;
		}
	}

	if (USoundBase* S = Data.ActivateSound.LoadSynchronous())
	{
		UGameplayStatics::PlaySound2D(this, S);
	}
	UE_LOG(LogNeonVeil, Log, TEXT("Ability %s activated (%.1f s)"), *Data.AbilityTag.ToString(), R.ActiveTimeLeft);
	OnAbilityActivated.Broadcast(Data.AbilityTag);
}

void UNVAbilityComponent::StopEffect(int32 Slot, bool bStartCooldown)
{
	const UNVAbilityData& Data = *Abilities[Slot];
	FNVAbilityRuntime& R = Runtime[Slot];
	R.ActiveTimeLeft = 0.f;
	R.CooldownLeft = bStartCooldown ? Data.Cooldown : 0.f;

	if (Data.AbilityTag.MatchesTagExact(NVTags::Ability_KineticShield))
	{
		if (UNVHealthComponent* H = GetOwner()->FindComponentByClass<UNVHealthComponent>())
		{
			UE_LOG(LogNeonVeil, Log, TEXT("Kinetic shield blocked %.1f damage"), H->GetBlockedDamage());
			H->IncomingDamageScale = 1.f;
		}
	}
	else if (Data.AbilityTag.MatchesTagExact(NVTags::Ability_DroneUplink))
	{
		if (ANVReconDrone* Drone = ActiveDrone.Get())
		{
			Drone->Recall();
		}
		ActiveDrone.Reset();
	}

	if (USoundBase* S = Data.EndSound.LoadSynchronous())
	{
		UGameplayStatics::PlaySound2D(this, S);
	}
	UE_LOG(LogNeonVeil, Log, TEXT("Ability %s ended"), *Data.AbilityTag.ToString());
	OnAbilityEnded.Broadcast(Data.AbilityTag);
}

void UNVAbilityComponent::EndAbility(FGameplayTag AbilityTag)
{
	const int32 Slot = FindSlot(AbilityTag);
	if (Runtime.IsValidIndex(Slot) && Runtime[Slot].ActiveTimeLeft > 0.f)
	{
		StopEffect(Slot, true);
	}
}

void UNVAbilityComponent::NotifyAttacked()
{
	const int32 Slot = FindSlot(NVTags::Ability_OpticalDisruption);
	if (Runtime.IsValidIndex(Slot) && Runtime[Slot].ActiveTimeLeft > 0.f && Abilities[Slot]->bBreaksOnAttack)
	{
		UE_LOG(LogNeonVeil, Log, TEXT("Optical disruption broken by attack"));
		StopEffect(Slot, true);
	}
}

void UNVAbilityComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	for (int32 i = 0; i < Runtime.Num(); ++i)
	{
		FNVAbilityRuntime& R = Runtime[i];
		if (R.ActiveTimeLeft > 0.f)
		{
			R.ActiveTimeLeft -= DeltaTime;
			if (R.ActiveTimeLeft <= 0.f)
			{
				StopEffect(i, true);
			}
		}
		else if (R.CooldownLeft > 0.f)
		{
			R.CooldownLeft = FMath::Max(0.f, R.CooldownLeft - DeltaTime);
		}
	}
	const float Now = GetWorld()->GetTimeSeconds();
	Marks.RemoveAll([Now](const FNVMarkedActor& M)
	{
		const AActor* A = M.Actor.Get();
		return !A || A->IsHidden() || Now >= M.ExpiresAt;
	});
}

bool UNVAbilityComponent::IsAbilityActive(FGameplayTag AbilityTag) const
{
	const int32 Slot = FindSlot(AbilityTag);
	return Runtime.IsValidIndex(Slot) && Runtime[Slot].ActiveTimeLeft > 0.f;
}

bool UNVAbilityComponent::IsAbilityDisabled(FGameplayTag AbilityTag) const
{
	const int32 Slot = FindSlot(AbilityTag);
	return Runtime.IsValidIndex(Slot) && Runtime[Slot].bDisabled;
}

void UNVAbilityComponent::SetAbilityDisabled(FGameplayTag AbilityTag, bool bDisabled)
{
	const int32 Slot = FindSlot(AbilityTag);
	if (!Runtime.IsValidIndex(Slot))
	{
		return;
	}
	if (bDisabled && Runtime[Slot].ActiveTimeLeft > 0.f)
	{
		StopEffect(Slot, false);
	}
	Runtime[Slot].bDisabled = bDisabled;
	UE_LOG(LogNeonVeil, Log, TEXT("Ability %s %s"), *AbilityTag.ToString(), bDisabled ? TEXT("disabled") : TEXT("restored"));
}

float UNVAbilityComponent::GetCooldownFraction(int32 Slot) const
{
	if (!Runtime.IsValidIndex(Slot) || !Abilities[Slot] || Abilities[Slot]->Cooldown <= 0.f)
	{
		return 0.f;
	}
	return FMath::Clamp(Runtime[Slot].CooldownLeft / Abilities[Slot]->Cooldown, 0.f, 1.f);
}

float UNVAbilityComponent::GetActiveFraction(int32 Slot) const
{
	if (!Runtime.IsValidIndex(Slot) || !Abilities[Slot] || Abilities[Slot]->Duration <= 0.f)
	{
		return 0.f;
	}
	return FMath::Clamp(Runtime[Slot].ActiveTimeLeft / Abilities[Slot]->Duration, 0.f, 1.f);
}

bool UNVAbilityComponent::IsActorCloaked(const AActor* Actor)
{
	const UNVAbilityComponent* A = Actor ? Actor->FindComponentByClass<UNVAbilityComponent>() : nullptr;
	return A && A->IsAbilityActive(NVTags::Ability_OpticalDisruption);
}

TArray<AActor*> UNVAbilityComponent::GetMarkedActors() const
{
	TArray<AActor*> Out;
	for (const FNVMarkedActor& M : Marks)
	{
		if (AActor* A = M.Actor.Get())
		{
			Out.Add(A);
		}
	}
	return Out;
}

void UNVAbilityComponent::AddMarks(const TArray<AActor*>& Actors, float Duration)
{
	const float Expires = GetWorld()->GetTimeSeconds() + Duration;
	int32 New = 0;
	for (AActor* A : Actors)
	{
		FNVMarkedActor* Existing = Marks.FindByPredicate([A](const FNVMarkedActor& M) { return M.Actor.Get() == A; });
		if (Existing)
		{
			Existing->ExpiresAt = Expires;
		}
		else
		{
			FNVMarkedActor M;
			M.Actor = A;
			M.ExpiresAt = Expires;
			Marks.Add(M);
			++New;
		}
	}
	if (New > 0)
	{
		UE_LOG(LogNeonVeil, Log, TEXT("Drone uplink marked %d new (%d total)"), New, Marks.Num());
		OnTargetsMarked.Broadcast(New);
	}
}

TArray<FGameplayTag> UNVAbilityComponent::GetDisabledTags() const
{
	TArray<FGameplayTag> Out;
	for (int32 i = 0; i < Runtime.Num(); ++i)
	{
		if (Runtime[i].bDisabled && Abilities[i])
		{
			Out.Add(Abilities[i]->AbilityTag);
		}
	}
	return Out;
}

void UNVAbilityComponent::RestoreDisabledTags(const TArray<FGameplayTag>& Tags)
{
	Runtime.SetNum(Abilities.Num());
	for (int32 i = 0; i < Runtime.Num(); ++i)
	{
		Runtime[i] = FNVAbilityRuntime();
		Runtime[i].bDisabled = Abilities[i] && Tags.Contains(Abilities[i]->AbilityTag);
	}
}

void UNVAbilityComponent::DebugResetCooldowns()
{
	for (FNVAbilityRuntime& R : Runtime)
	{
		R.CooldownLeft = 0.f;
	}
}
