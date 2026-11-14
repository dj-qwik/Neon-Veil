#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "NVWeaponComponent.generated.h"

class UNVWeaponData;
class USkeletalMeshComponent;
class UStaticMeshComponent;
class UAudioComponent;
class UCameraComponent;

USTRUCT(BlueprintType)
struct FNVWeaponSlot
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Weapon")
	TObjectPtr<UNVWeaponData> Data = nullptr;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Weapon")
	int32 AmmoInMag = 0;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Weapon")
	int32 ReserveAmmo = 0;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FNVOnAmmoChanged, int32, AmmoInMag, int32, ReserveAmmo);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FNVOnWeaponEquipped, UNVWeaponData*, Weapon);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FNVOnHitConfirmed, AActor*, HitActor, bool, bWeakPoint);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FNVOnWeaponFired);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FNVOnReloadStateChanged, bool, bReloading);

/**
 * Equip, fire (hitscan), reload, ADS, recoil and spread. All numbers come from UNVWeaponData.
 */
UCLASS(ClassGroup = (NeonVeil), meta = (BlueprintSpawnableComponent))
class NEONVEIL_API UNVWeaponComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UNVWeaponComponent();

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** The character hands over the camera and the first-person weapon mesh components. */
	void Initialize(UCameraComponent* InCamera, USkeletalMeshComponent* InWeaponMesh, UStaticMeshComponent* InWeaponStaticMesh);

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Weapon")
	void StartFire();

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Weapon")
	void StopFire();

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Weapon")
	void Reload();

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Weapon")
	void SetAiming(bool bAim);

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Weapon")
	bool EquipSlot(int32 SlotIndex);

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Weapon")
	void CycleWeapon(int32 Direction);

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Weapon")
	void GiveWeapon(UNVWeaponData* Weapon, bool bEquip);

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Weapon")
	UNVWeaponData* GetCurrentWeapon() const;

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Weapon")
	float GetAdsAlpha() const { return AdsAlpha; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Weapon")
	bool IsAiming() const { return bWantsAim; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Weapon")
	bool IsReloading() const { return bReloading; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Weapon")
	float GetCurrentSpreadDeg() const;

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Weapon")
	const TArray<FNVWeaponSlot>& GetSlots() const { return Slots; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Weapon")
	int32 GetCurrentSlotIndex() const { return CurrentSlot; }

	/** First pawn along the aim if it is friendly (weapon safety engaged), else null. */
	UFUNCTION(BlueprintPure, Category = "NeonVeil|Weapon")
	AActor* GetFriendlyInSights() const;

	/** Restore ammo counts from a save without firing events per slot. */
	void RestoreSlots(const TArray<FNVWeaponSlot>& InSlots, int32 InCurrentSlot);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil|Weapon")
	TArray<TObjectPtr<UNVWeaponData>> StartingWeapons;

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Weapon")
	FNVOnAmmoChanged OnAmmoChanged;

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Weapon")
	FNVOnWeaponEquipped OnWeaponEquipped;

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Weapon")
	FNVOnHitConfirmed OnHitConfirmed;

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Weapon")
	FNVOnWeaponFired OnWeaponFired;

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Weapon")
	FNVOnReloadStateChanged OnReloadStateChanged;

	/** Global camera shake scale from settings (Bible §10 camera shake slider). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil|Weapon")
	float CameraShakeScale = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil|Weapon")
	bool bDrawDebugTraces = false;

protected:
	virtual void BeginPlay() override;

private:
	void FireShot();
	void FinishReload();
	void ApplyRecoil(const UNVWeaponData& Data);
	void PlayFireEffects(const UNVWeaponData& Data, const FVector& TraceEnd, const FHitResult* Hit, bool bPrimary = true);

	/** Where the muzzle appears on screen, as a world position for world-space effects (tracers). The viewmodel is
	 *  drawn with the first-person FOV and scale, so its true transform sits further out than it looks. */
	FVector GetVisualMuzzleLocation(const UNVWeaponData& Data) const;
	void RefreshWeaponVisual();
	void BroadcastAmmo();
	FNVWeaponSlot* CurrentSlotPtr();

	UPROPERTY(Transient)
	TArray<FNVWeaponSlot> Slots;

	UPROPERTY(Transient)
	TObjectPtr<UCameraComponent> Camera;

	UPROPERTY(Transient)
	TObjectPtr<USkeletalMeshComponent> WeaponMesh;

	UPROPERTY(Transient)
	TObjectPtr<UStaticMeshComponent> WeaponStaticMesh;

	int32 CurrentSlot = INDEX_NONE;
	bool bTriggerHeld = false;
	bool bWantsAim = false;
	bool bReloading = false;
	float AdsAlpha = 0.f;
	float LastFireTime = -1000.f;
	float BloomDeg = 0.f;
	float PendingRecoveryPitch = 0.f;
	float RecoveryTimeLeft = 0.f;
	FTimerHandle ReloadTimer;

	/** Layered fire audio: picks a variant (no immediate repeat), plays shot + tail + accent. */
	void PlayFireAudio(const UNVWeaponData& Data);
	void StartReloadAudio(const UNVWeaponData& Data);
	void StopReloadAudio();
	int32 PickVariant(int32 Num, int32& Last) const;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UAudioComponent>> TailVoices;

	TArray<FTimerHandle> ReloadSoundTimers;
	int32 LastShotVariant = INDEX_NONE;
	int32 LastTailVariant = INDEX_NONE;
	int32 LastLayerVariant = INDEX_NONE;
};
