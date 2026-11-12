#include "Combat/NVWeaponComponent.h"
#include "Combat/NVFriendly.h"
#include "Combat/NVWeaponData.h"
#include "Combat/NVHealthComponent.h"
#include "Core/NVGameplayTags.h"
#include "NeonVeil.h"
#include "Camera/CameraComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Controller.h"
#include "Kismet/GameplayStatics.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "Engine/StaticMesh.h"
#include "Engine/SkeletalMesh.h"
#include "Sound/SoundBase.h"
#include "Animation/AnimMontage.h"
#include "Materials/MaterialInterface.h"
#include "Camera/CameraShakeBase.h"
#include "DrawDebugHelpers.h"
#include "Engine/World.h"
#include "TimerManager.h"

static const FName NVWeakPointComponentTag(TEXT("WeakPoint"));

UNVWeaponComponent::UNVWeaponComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UNVWeaponComponent::BeginPlay()
{
	Super::BeginPlay();
	for (UNVWeaponData* W : StartingWeapons)
	{
		GiveWeapon(W, CurrentSlot == INDEX_NONE);
	}
}

void UNVWeaponComponent::Initialize(UCameraComponent* InCamera, USkeletalMeshComponent* InWeaponMesh, UStaticMeshComponent* InWeaponStaticMesh)
{
	Camera = InCamera;
	WeaponMesh = InWeaponMesh;
	WeaponStaticMesh = InWeaponStaticMesh;
	RefreshWeaponVisual();
}

FNVWeaponSlot* UNVWeaponComponent::CurrentSlotPtr()
{
	return Slots.IsValidIndex(CurrentSlot) ? &Slots[CurrentSlot] : nullptr;
}

UNVWeaponData* UNVWeaponComponent::GetCurrentWeapon() const
{
	return Slots.IsValidIndex(CurrentSlot) ? Slots[CurrentSlot].Data.Get() : nullptr;
}

void UNVWeaponComponent::GiveWeapon(UNVWeaponData* Weapon, bool bEquip)
{
	if (!Weapon)
	{
		return;
	}
	int32 Index = Slots.IndexOfByPredicate([Weapon](const FNVWeaponSlot& S) { return S.Data == Weapon; });
	if (Index == INDEX_NONE)
	{
		FNVWeaponSlot Slot;
		Slot.Data = Weapon;
		Slot.AmmoInMag = Weapon->MagazineSize;
		Slot.ReserveAmmo = Weapon->StartingReserveAmmo;
		Index = Slots.Add(Slot);
	}
	else
	{
		Slots[Index].ReserveAmmo += Weapon->MagazineSize;
	}
	if (bEquip)
	{
		EquipSlot(Index);
	}
	else if (Index == CurrentSlot)
	{
		BroadcastAmmo();
	}
}

bool UNVWeaponComponent::EquipSlot(int32 SlotIndex)
{
	if (!Slots.IsValidIndex(SlotIndex) || SlotIndex == CurrentSlot)
	{
		return false;
	}
	StopFire();
	if (bReloading)
	{
		GetWorld()->GetTimerManager().ClearTimer(ReloadTimer);
		bReloading = false;
		OnReloadStateChanged.Broadcast(false);
	}
	CurrentSlot = SlotIndex;
	BloomDeg = 0.f;
	RefreshWeaponVisual();

	UNVWeaponData* Data = GetCurrentWeapon();
	if (ACharacter* Char = Cast<ACharacter>(GetOwner()))
	{
		if (UAnimMontage* Equip = Data ? Data->EquipMontage.LoadSynchronous() : nullptr)
		{
			Char->PlayAnimMontage(Equip);
		}
	}
	OnWeaponEquipped.Broadcast(Data);
	BroadcastAmmo();
	return true;
}

void UNVWeaponComponent::CycleWeapon(int32 Direction)
{
	if (Slots.Num() < 2)
	{
		return;
	}
	const int32 Next = (CurrentSlot + (Direction >= 0 ? 1 : -1) + Slots.Num()) % Slots.Num();
	EquipSlot(Next);
}

void UNVWeaponComponent::RestoreSlots(const TArray<FNVWeaponSlot>& InSlots, int32 InCurrentSlot)
{
	Slots = InSlots;
	CurrentSlot = INDEX_NONE;
	if (!EquipSlot(FMath::Clamp(InCurrentSlot, 0, FMath::Max(0, Slots.Num() - 1))))
	{
		RefreshWeaponVisual();
		BroadcastAmmo();
	}
}

void UNVWeaponComponent::RefreshWeaponVisual()
{
	UNVWeaponData* Data = GetCurrentWeapon();
	USkeletalMesh* Skel = Data ? Data->WeaponMesh.LoadSynchronous() : nullptr;
	UStaticMesh* Stat = (Data && !Skel) ? Data->WeaponStaticMesh.LoadSynchronous() : nullptr;
	if (WeaponMesh)
	{
		WeaponMesh->SetSkeletalMesh(Skel);
		WeaponMesh->SetVisibility(Skel != nullptr);
	}
	if (WeaponStaticMesh)
	{
		WeaponStaticMesh->SetStaticMesh(Stat);
		WeaponStaticMesh->SetVisibility(Stat != nullptr);
	}
}

void UNVWeaponComponent::BroadcastAmmo()
{
	const FNVWeaponSlot* Slot = Slots.IsValidIndex(CurrentSlot) ? &Slots[CurrentSlot] : nullptr;
	OnAmmoChanged.Broadcast(Slot ? Slot->AmmoInMag : 0, Slot ? Slot->ReserveAmmo : 0);
}

void UNVWeaponComponent::StartFire()
{
	bTriggerHeld = true;
	const UNVWeaponData* Data = GetCurrentWeapon();
	if (!Data)
	{
		return;
	}
	const float Interval = 60.f / Data->RoundsPerMinute;
	if (GetWorld()->GetTimeSeconds() - LastFireTime >= Interval)
	{
		FireShot();
	}
}

void UNVWeaponComponent::StopFire()
{
	bTriggerHeld = false;
}

void UNVWeaponComponent::SetAiming(bool bAim)
{
	bWantsAim = bAim;
}

AActor* UNVWeaponComponent::GetFriendlyInSights() const
{
	const UNVWeaponData* Data = GetCurrentWeapon();
	if (!Data || !Camera)
	{
		return nullptr;
	}
	FVector AimDir = Camera->GetForwardVector();
	if (const APawn* Pawn = Cast<APawn>(GetOwner()))
	{
		if (const AController* C = Pawn->GetController())
		{
			AimDir = C->GetControlRotation().Vector();
		}
	}
	// Pawn channel: walls stop it and character capsules block it, so cover still counts.
	const FVector Start = Camera->GetComponentLocation();
	FCollisionQueryParams Params(SCENE_QUERY_STAT(NVWeaponSafety), false, GetOwner());
	FHitResult Hit;
	if (GetWorld()->SweepSingleByChannel(Hit, Start, Start + AimDir * Data->Range, FQuat::Identity, ECC_Pawn, FCollisionShape::MakeSphere(12.f), Params)
		&& NVFriendly::IsFriendly(Hit.GetActor()))
	{
		return Hit.GetActor();
	}
	return nullptr;
}

float UNVWeaponComponent::GetCurrentSpreadDeg() const
{
	const UNVWeaponData* Data = GetCurrentWeapon();
	if (!Data)
	{
		return 0.f;
	}
	return FMath::Lerp(Data->HipSpreadDeg, Data->AdsSpreadDeg, AdsAlpha) + BloomDeg;
}

void UNVWeaponComponent::FireShot()
{
	UNVWeaponData* Data = GetCurrentWeapon();
	FNVWeaponSlot* Slot = CurrentSlotPtr();
	if (!Data || !Slot || bReloading || !Camera)
	{
		return;
	}

	// Weapon safety: never fire into a friendly. No round is spent; the trigger stays live so
	// fire resumes as soon as the sights move off them.
	if (const AActor* Friendly = GetFriendlyInSights())
	{
		UE_LOG(LogNeonVeil, Log, TEXT("Weapon safety: %s in the sights, not firing"), *Friendly->GetName());
		return;
	}

	LastFireTime = GetWorld()->GetTimeSeconds();

	if (Slot->AmmoInMag <= 0)
	{
		if (USoundBase* Dry = Data->DryFireSound.LoadSynchronous())
		{
			UGameplayStatics::PlaySound2D(this, Dry);
		}
		bTriggerHeld = false;
		Reload();
		return;
	}

	--Slot->AmmoInMag;

	// Trace from the camera along the controller's current aim. The camera component's rotation
	// is only refreshed once per frame, so using it would fire along last frame's view.
	const FVector Start = Camera->GetComponentLocation();
	FVector AimDir = Camera->GetForwardVector();
	if (const APawn* Pawn = Cast<APawn>(GetOwner()))
	{
		if (const AController* C = Pawn->GetController())
		{
			AimDir = C->GetControlRotation().Vector();
		}
	}
	const float SpreadRad = FMath::DegreesToRadians(GetCurrentSpreadDeg());
	const FVector Dir = FMath::VRandCone(AimDir, SpreadRad);
	const FVector End = Start + Dir * Data->Range;

	FCollisionQueryParams Params(SCENE_QUERY_STAT(NVWeaponTrace), true, GetOwner());
	Params.bReturnPhysicalMaterial = true;
	FHitResult Hit;
	const bool bHit = GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Params);

	if (bDrawDebugTraces)
	{
		DrawDebugLine(GetWorld(), Start, bHit ? Hit.ImpactPoint : End, bHit ? FColor::Red : FColor::Green, false, 1.f);
	}

	if (bHit)
	{
		AActor* HitActor = Hit.GetActor();
		const bool bWeak = Hit.GetComponent() && Hit.GetComponent()->ComponentHasTag(NVWeakPointComponentTag);
		if (HitActor)
		{
			if (UNVHealthComponent* Health = HitActor->FindComponentByClass<UNVHealthComponent>())
			{
				const float Dmg = Data->Damage * (bWeak ? Data->WeakPointBonus : 1.f);
				const float Applied = Health->ApplyDamage(Dmg, GetOwner(), Data->DamageType, bWeak);
				UE_LOG(LogNeonVeil, Log, TEXT("Hit %s (%s) applied %.1f, hp %.1f shield %.1f"), *HitActor->GetName(), *GetNameSafe(Hit.GetComponent()), Applied, Health->GetHealth(), Health->GetShield());
				if (Applied > 0.f)
				{
					if (USoundBase* Confirm = Data->HitConfirmSound.LoadSynchronous())
					{
						UGameplayStatics::PlaySound2D(this, Confirm, bWeak ? 1.f : 0.6f);
					}
					OnHitConfirmed.Broadcast(HitActor, bWeak);
				}
			}
		}
		if (UPrimitiveComponent* Prim = Hit.GetComponent())
		{
			if (Prim->IsSimulatingPhysics())
			{
				Prim->AddImpulseAtLocation(Dir * Data->ImpactImpulse, Hit.ImpactPoint);
			}
		}
	}

	if (!bHit || !Hit.GetActor() || !Hit.GetActor()->FindComponentByClass<UNVHealthComponent>())
	{
		UE_LOG(LogNeonVeil, Verbose, TEXT("Shot hit %s"), bHit ? *GetNameSafe(Hit.GetActor()) : TEXT("nothing"));
	}

	PlayFireEffects(*Data, bHit ? Hit.ImpactPoint : End, bHit ? &Hit : nullptr);
	ApplyRecoil(*Data);
	BloomDeg = FMath::Min(Data->MaxBloomDeg, BloomDeg + Data->SpreadPerShotDeg);

	OnWeaponFired.Broadcast();
	BroadcastAmmo();

	if (Data->FireMode == ENVFireMode::SemiAuto)
	{
		bTriggerHeld = false;
	}
}

void UNVWeaponComponent::ApplyRecoil(const UNVWeaponData& Data)
{
	APawn* Pawn = Cast<APawn>(GetOwner());
	APlayerController* PC = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
	if (!PC)
	{
		return;
	}
	const float Scale = FMath::Lerp(1.f, Data.AdsRecoilScale, AdsAlpha);
	const float Pitch = Data.RecoilPitch * Scale;
	const float Yaw = FMath::FRandRange(-Data.RecoilYawRandom, Data.RecoilYawRandom) * Scale;

	// Rotation input is applied directly to the control rotation (degrees), unaffected by mouse sensitivity.
	FRotator Rot = PC->GetControlRotation();
	Rot.Pitch += Pitch;
	Rot.Yaw += Yaw;
	PC->SetControlRotation(Rot);

	PendingRecoveryPitch += Pitch * Data.RecoilRecoveryFraction;
	RecoveryTimeLeft = Data.RecoilRecoveryTime;

	if (Data.FireCameraShake && CameraShakeScale > 0.f)
	{
		PC->ClientStartCameraShake(Data.FireCameraShake, CameraShakeScale);
	}
}

void UNVWeaponComponent::PlayFireEffects(const UNVWeaponData& Data, const FVector& TraceEnd, const FHitResult* Hit)
{
	USceneComponent* MuzzleParent = WeaponMesh && WeaponMesh->GetSkeletalMeshAsset() ? static_cast<USceneComponent*>(WeaponMesh) : static_cast<USceneComponent*>(WeaponStaticMesh);
	const bool bHasSocket = MuzzleParent && MuzzleParent->DoesSocketExist(Data.MuzzleSocket);
	const FVector MuzzleLoc = bHasSocket ? MuzzleParent->GetSocketLocation(Data.MuzzleSocket) : (Camera ? Camera->GetComponentLocation() + Camera->GetForwardVector() * 60.f : FVector::ZeroVector);

	if (UNiagaraSystem* Flash = Data.MuzzleFlash.LoadSynchronous())
	{
		if (bHasSocket)
		{
			UNiagaraFunctionLibrary::SpawnSystemAttached(Flash, MuzzleParent, Data.MuzzleSocket, FVector::ZeroVector, FRotator::ZeroRotator, EAttachLocation::SnapToTarget, true);
		}
	}
	if (UNiagaraSystem* Tracer = Data.Tracer.LoadSynchronous())
	{
		if (UNiagaraComponent* TracerComp = UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, Tracer, MuzzleLoc))
		{
			TracerComp->SetVectorParameter(TEXT("BeamEnd"), TraceEnd);
		}
	}
	if (UNiagaraSystem* Casing = Data.CasingEject.LoadSynchronous())
	{
		if (MuzzleParent && MuzzleParent->DoesSocketExist(TEXT("Eject")))
		{
			UNiagaraFunctionLibrary::SpawnSystemAttached(Casing, MuzzleParent, TEXT("Eject"), FVector::ZeroVector, FRotator::ZeroRotator, EAttachLocation::SnapToTarget, true);
		}
	}
	if (USoundBase* Shot = Data.FireSound.LoadSynchronous())
	{
		UGameplayStatics::PlaySoundAtLocation(this, Shot, MuzzleLoc);
	}
	if (ACharacter* Char = Cast<ACharacter>(GetOwner()))
	{
		if (UAnimMontage* Montage = Data.FireMontage.LoadSynchronous())
		{
			Char->PlayAnimMontage(Montage);
		}
	}
	if (Hit)
	{
		if (UNiagaraSystem* Impact = Data.ImpactEffect.LoadSynchronous())
		{
			UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, Impact, Hit->ImpactPoint, Hit->ImpactNormal.Rotation());
		}
		if (UMaterialInterface* Decal = Data.ImpactDecal.LoadSynchronous())
		{
			UGameplayStatics::SpawnDecalAttached(Decal, FVector(4.f, 6.f, 6.f), Hit->GetComponent(), NAME_None, Hit->ImpactPoint, (-Hit->ImpactNormal).Rotation(), EAttachLocation::KeepWorldPosition, 20.f);
		}
	}
}

void UNVWeaponComponent::Reload()
{
	UNVWeaponData* Data = GetCurrentWeapon();
	FNVWeaponSlot* Slot = CurrentSlotPtr();
	if (!Data || !Slot || bReloading || Slot->AmmoInMag >= Data->MagazineSize || Slot->ReserveAmmo <= 0)
	{
		return;
	}
	bReloading = true;
	OnReloadStateChanged.Broadcast(true);
	if (USoundBase* Snd = Data->ReloadSound.LoadSynchronous())
	{
		UGameplayStatics::PlaySound2D(this, Snd);
	}
	if (ACharacter* Char = Cast<ACharacter>(GetOwner()))
	{
		if (UAnimMontage* Montage = Data->ReloadMontage.LoadSynchronous())
		{
			Char->PlayAnimMontage(Montage);
		}
	}
	GetWorld()->GetTimerManager().SetTimer(ReloadTimer, this, &UNVWeaponComponent::FinishReload, Data->ReloadTime, false);
}

void UNVWeaponComponent::FinishReload()
{
	UNVWeaponData* Data = GetCurrentWeapon();
	FNVWeaponSlot* Slot = CurrentSlotPtr();
	bReloading = false;
	if (Data && Slot)
	{
		const int32 Needed = Data->MagazineSize - Slot->AmmoInMag;
		const int32 Taken = FMath::Min(Needed, Slot->ReserveAmmo);
		Slot->AmmoInMag += Taken;
		Slot->ReserveAmmo -= Taken;
	}
	OnReloadStateChanged.Broadcast(false);
	BroadcastAmmo();
}

void UNVWeaponComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	const UNVWeaponData* Data = GetCurrentWeapon();
	if (!Data)
	{
		return;
	}

	// ADS blend: linear in time so the transition length matches AdsTime exactly.
	const float Target = (bWantsAim && !bReloading) ? 1.f : 0.f;
	AdsAlpha = FMath::FInterpConstantTo(AdsAlpha, Target, DeltaTime, 1.f / Data->AdsTime);

	// Spread recovery
	BloomDeg = FMath::Max(0.f, BloomDeg - Data->SpreadRecoveryPerSec * DeltaTime);

	// Recoil recovery: return part of the kick smoothly.
	if (RecoveryTimeLeft > 0.f && PendingRecoveryPitch > 0.f)
	{
		APawn* Pawn = Cast<APawn>(GetOwner());
		if (APlayerController* PC = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr)
		{
			const float Step = FMath::Min(PendingRecoveryPitch, PendingRecoveryPitch * (DeltaTime / RecoveryTimeLeft));
			FRotator Rot = PC->GetControlRotation();
			Rot.Pitch -= Step;
			PC->SetControlRotation(Rot);
			PendingRecoveryPitch -= Step;
		}
		RecoveryTimeLeft -= DeltaTime;
		if (RecoveryTimeLeft <= 0.f)
		{
			PendingRecoveryPitch = 0.f;
		}
	}

	// Full-auto
	if (bTriggerHeld && Data->FireMode == ENVFireMode::FullAuto)
	{
		const float Interval = 60.f / Data->RoundsPerMinute;
		if (GetWorld()->GetTimeSeconds() - LastFireTime >= Interval)
		{
			FireShot();
		}
	}
}
