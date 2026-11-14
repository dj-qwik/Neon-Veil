#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "GameplayTagContainer.h"
#include "NVWeaponData.generated.h"

class USkeletalMesh;
class UStaticMesh;
class UNiagaraSystem;
class USoundBase;
class UAnimMontage;
class UMaterialInterface;
class UCameraShakeBase;
class UAnimationAsset;

/** One step of a timed sound sequence (e.g. reload: mag out / mag in / charge). */
USTRUCT(BlueprintType)
struct FNVTimedSound
{
	GENERATED_BODY()

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Audio")
	TSoftObjectPtr<USoundBase> Sound;

	/** When to play, as a fraction of the action's duration (0 = start, 1 = end). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Audio", meta = (ClampMin = "0", ClampMax = "1"))
	float Time = 0.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Audio")
	float Volume = 1.f;
};

UENUM(BlueprintType)
enum class ENVFireMode : uint8
{
	SemiAuto,
	FullAuto
};

/**
 * All balancing and presentation for one weapon (Bible §7: no hardcoded weapon balancing).
 * Create one DA_Weapon_* per gun: VX-9, Kestrel, Harrow.
 */
UCLASS(BlueprintType)
class NEONVEIL_API UNVWeaponData : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	virtual FPrimaryAssetId GetPrimaryAssetId() const override { return FPrimaryAssetId(TEXT("NVWeapon"), GetFName()); }

	// --- Identity
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
	FText DisplayName;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
	FGameplayTag WeaponTag;

	// --- Damage
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Damage")
	float Damage = 20.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Damage")
	FGameplayTag DamageType;

	/** Extra multiplier on weak points, stacked with the target's own. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Damage")
	float WeakPointBonus = 1.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Damage")
	float Range = 10000.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Damage")
	float ImpactImpulse = 1500.f;

	// --- Handling
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Handling")
	ENVFireMode FireMode = ENVFireMode::SemiAuto;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Handling", meta = (ClampMin = "1"))
	float RoundsPerMinute = 400.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Handling", meta = (ClampMin = "1"))
	int32 MagazineSize = 12;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Handling", meta = (ClampMin = "0"))
	int32 StartingReserveAmmo = 48;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Handling", meta = (ClampMin = "0.1"))
	float ReloadTime = 1.6f;

	/** Cone half-angle in degrees, hip fire. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Handling")
	float HipSpreadDeg = 1.5f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Handling")
	float AdsSpreadDeg = 0.2f;

	/** Spread added per shot, recovering at SpreadRecoveryPerSec. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Handling")
	float SpreadPerShotDeg = 0.3f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Handling")
	float MaxBloomDeg = 3.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Handling")
	float SpreadRecoveryPerSec = 6.f;

	// --- Recoil (degrees of view kick per shot)
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Recoil")
	float RecoilPitch = 0.8f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Recoil")
	float RecoilYawRandom = 0.25f;

	/** Fraction of kick returned automatically over RecoilRecoveryTime. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Recoil", meta = (ClampMin = "0", ClampMax = "1"))
	float RecoilRecoveryFraction = 0.6f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Recoil")
	float RecoilRecoveryTime = 0.25f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Recoil")
	float AdsRecoilScale = 0.7f;

	// --- Aim down sights (Bible §7: 0.15-0.25 s, weapon-specific FOV and sensitivity)
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ADS", meta = (ClampMin = "0.05", ClampMax = "0.6"))
	float AdsTime = 0.2f;

	/** Horizontal FOV while fully aimed. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ADS")
	float AdsFOV = 75.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ADS")
	float AdsSensitivityScale = 0.75f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ADS")
	float AdsMoveSpeedScale = 0.7f;

	// --- Viewmodel placement relative to the camera (cm / degrees)
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel")
	FVector ViewmodelHipOffset = FVector(28.f, 12.f, -14.f);

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel")
	FVector ViewmodelAdsOffset = FVector(20.f, 0.f, -7.5f);

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel")
	FRotator ViewmodelRotation = FRotator::ZeroRotator;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel")
	FVector ViewmodelScale = FVector(1.f);

	/** Backward kick of the viewmodel per shot (cm). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel")
	float ViewmodelKickBack = 3.f;

	// --- Presentation (soft so unused weapons cost no memory)
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	TSoftObjectPtr<USkeletalMesh> WeaponMesh;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	TSoftObjectPtr<UStaticMesh> WeaponStaticMesh;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	FName MuzzleSocket = TEXT("Muzzle");

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	FName GripSocket = TEXT("GripPoint");

	/** Muzzle position in the weapon mesh's local space, used when the mesh has no MuzzleSocket. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	FVector MuzzleOffset = FVector::ZeroVector;

	/** Played on the weapon's own skeletal mesh (trigger/slide/bolt) when firing. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	TSoftObjectPtr<UAnimationAsset> WeaponFireAnim;

	/** Played on the weapon's own skeletal mesh when reloading (magazine out/in). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	TSoftObjectPtr<UAnimationAsset> WeaponReloadAnim;

	/** Playback rate for WeaponReloadAnim so it fits ReloadTime; 0 = auto-fit. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	float WeaponReloadAnimRate = 0.f;

	// --- First-person arms (KINEMATION Sci-fi FPS pack). When ArmsIdleAnim is set and the player has an arms mesh,
	// the weapon is held by the arms (attached to ArmsWeaponBone) instead of floating at the viewmodel root.
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Arms")
	TSoftObjectPtr<UAnimationAsset> ArmsIdleAnim;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Arms")
	TSoftObjectPtr<UAnimationAsset> ArmsFireAnim;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Arms")
	TSoftObjectPtr<UAnimationAsset> ArmsReloadAnim;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Arms")
	TSoftObjectPtr<UAnimationAsset> ArmsDrawAnim;

	/** Arms bone the weapon rides on. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Arms")
	FName ArmsWeaponBone = TEXT("ik_hand_gun");

	/** Weapon transform relative to ArmsWeaponBone. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Arms")
	FTransform ArmsWeaponOffset = FTransform::Identity;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	TSoftObjectPtr<UNiagaraSystem> MuzzleFlash;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	TSoftObjectPtr<UNiagaraSystem> Tracer;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	TSoftObjectPtr<UNiagaraSystem> ImpactEffect;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	TSoftObjectPtr<UNiagaraSystem> CasingEject;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	TSoftObjectPtr<UMaterialInterface> ImpactDecal;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	TSoftObjectPtr<USoundBase> FireSound;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	TSoftObjectPtr<USoundBase> DryFireSound;

	// --- Layered weapon audio (used instead of FireSound/ReloadSound when set)
	/** Close shot variants; one is picked at random each shot, never the same twice in a row. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Audio")
	TArray<TSoftObjectPtr<USoundBase>> FireSoundVariants;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Audio")
	float FireVolume = 1.f;

	/** Random pitch per shot (applied to every layer of that shot). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Audio")
	FVector2D FirePitchRange = FVector2D(0.97f, 1.03f);

	/** Room/reverb tails; voices are capped so full-auto fire doesn't stack dozens of tails. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Audio")
	TArray<TSoftObjectPtr<USoundBase>> FireTailVariants;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Audio")
	float FireTailVolume = 0.6f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Audio", meta = (ClampMin = "1"))
	int32 MaxFireTailVoices = 3;

	/** Sci-fi/tech accent layered on each shot (Directorate hardware). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Audio")
	TArray<TSoftObjectPtr<USoundBase>> FireLayerVariants;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Audio")
	float FireLayerVolume = 0.3f;

	/** Reload foley timed against ReloadTime. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Audio")
	TArray<FNVTimedSound> ReloadSequence;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Audio")
	TSoftObjectPtr<USoundBase> EquipSound;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	TSoftObjectPtr<USoundBase> ReloadSound;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	TSoftObjectPtr<USoundBase> HitConfirmSound;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	TSoftObjectPtr<UAnimMontage> FireMontage;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	TSoftObjectPtr<UAnimMontage> ReloadMontage;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	TSoftObjectPtr<UAnimMontage> EquipMontage;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	TSoftObjectPtr<UAnimMontage> InspectMontage;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
	TSubclassOf<UCameraShakeBase> FireCameraShake;
};
