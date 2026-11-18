#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "InputActionValue.h"
#include "NVPlayerCharacter.generated.h"

class UCameraComponent;
class USkeletalMeshComponent;
class UStaticMeshComponent;
class UInputMappingContext;
class UInputAction;
class UNVHealthComponent;
class UNVWeaponComponent;
class UNVInteractionComponent;
class UNVAbilityComponent;
class UNVMeleeComponent;
class UAnimInstance;
class UNVWeaponData;
class UAnimationAsset;
class USkeletalMesh;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FNVOnSprintChanged, bool, bSprinting);

/**
 * Ghost-7. First-person movement, camera and input routing; owns health, weapon and interaction.
 * Tuning numbers are starting targets from Bible §7.
 */
/** One procedural melee move for the first-person viewmodel: a wind-up pose, a strike pose, then recovery. */
USTRUCT(BlueprintType)
struct FNVMeleeMotion
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	FRotator WindRot = FRotator::ZeroRotator;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	FVector WindOffset = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	FRotator StrikeRot = FRotator::ZeroRotator;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	FVector StrikeOffset = FVector::ZeroVector;

	/** Swing fraction where the wind-up pose is reached. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float WindEnd = 0.35f;

	/** Swing fraction where the strike pose is reached (the hit lands about here: match the melee WindUp). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float StrikeEnd = 0.5f;

	/** Swing fraction where recovery starts. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float HoldEnd = 0.6f;
};

UCLASS()
class NEONVEIL_API ANVPlayerCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	ANVPlayerCharacter(const FObjectInitializer& ObjectInitializer);

	virtual void Tick(float DeltaSeconds) override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual void PawnClientRestart() override;
	virtual void OnStartCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust) override;
	virtual void OnEndCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust) override;
	virtual void OnConstruction(const FTransform& Transform) override;

	UFUNCTION(BlueprintPure, Category = "NeonVeil")
	UCameraComponent* GetFirstPersonCamera() const { return FirstPersonCamera; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil")
	UNVHealthComponent* GetHealth() const { return Health; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil")
	UNVWeaponComponent* GetWeapons() const { return Weapons; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil")
	UNVInteractionComponent* GetInteraction() const { return Interaction; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil")
	UNVAbilityComponent* GetAbilities() const { return Abilities; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil")
	UNVMeleeComponent* GetMelee() const { return Melee; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil")
	bool IsSprinting() const { return bSprinting; }

	/** Scoped weapon fully aimed: the viewmodel is hidden and the HUD draws the scope. */
	bool IsScopedIn() const { return bScopedIn; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil")
	bool IsSliding() const { return SlideTimeLeft > 0.f; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil")
	bool IsVaulting() const { return bVaulting; }

	/** Settings hooks (Bible §10). */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Settings")
	void SetBaseFOV(float NewHorizontalFOV);

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Settings")
	void SetLookSensitivity(float NewSensitivity) { LookSensitivity = NewSensitivity; }

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Settings")
	void SetInvertY(bool bInvert) { bInvertY = bInvert; }

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Settings")
	void SetToggleSettings(bool bToggleSprint, bool bToggleCrouch, bool bToggleAim);

	/** Lock or unlock player input for scripted moments, without blocking camera look if bAllowLook. */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil")
	void SetGameplayInputLocked(bool bLocked, bool bAllowLook = true);

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil")
	FNVOnSprintChanged OnSprintChanged;

	/** QA: simulate held movement / sprint input (cleared with zero input). */
	void SetDebugMoveInput(FVector2D Input, bool bSprint);
	/** QA: same paths as the melee and ability buttons. */
	void DebugMelee() { MeleePressed(); }
	void DebugAbility(int32 Slot);

	/** QA: same path as pressing jump (vaults when facing a vaultable obstacle). */
	void DebugJump() { JumpPressed(); }
	/** QA: same path as pressing crouch (slides when sprinting). */
	void DebugCrouch(bool bPressed) { if (bPressed) { CrouchPressed(); } else { CrouchReleased(); } }

protected:
	virtual void BeginPlay() override;

	// --- Components
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UCameraComponent> FirstPersonCamera;

	/** Parent of the weapon viewmodel; moved between hip and ADS offsets each frame. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<USceneComponent> ViewmodelRoot;

	/** First-person arms, rendered only for the owner. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<USkeletalMeshComponent> FirstPersonMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<USkeletalMeshComponent> WeaponMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> WeaponStaticMesh;

	/** The body is only seen as Ghost's shadow: how its right hand holds a weapon when the weapon data gives no grip. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Body")
	FTransform BodyWeaponOffset = FTransform(FRotator(0.f, 90.f, 0.f), FVector(-2.f, 4.f, 0.f));

	/** Retired: the shock baton is now its own weapon slot (DA_Weapon_Baton). Kept so existing Blueprint data still loads; never shown. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> BatonMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UNVHealthComponent> Health;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UNVWeaponComponent> Weapons;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UNVInteractionComponent> Interaction;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UNVAbilityComponent> Abilities;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UNVMeleeComponent> Melee;

	// --- Input (assigned in BP_NVPlayerCharacter)
	/** Added in order, first = highest priority. */
	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TArray<TObjectPtr<UInputMappingContext>> MappingContexts;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputAction> MouseLookAction;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputAction> MoveAction;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputAction> LookAction;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputAction> JumpAction;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputAction> SprintAction;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputAction> CrouchAction;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputAction> FireAction;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputAction> AimAction;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputAction> ReloadAction;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputAction> InteractAction;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputAction> NextWeaponAction;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputAction> PrevWeaponAction;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputAction> MeleeAction;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputAction> HolsterAction;

	/** Ability slots 0..2 (optical disruption, kinetic shield, drone uplink). */
	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputAction> Ability1Action;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputAction> Ability2Action;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputAction> Ability3Action;

	// --- Movement tuning (Bible §7)
	UPROPERTY(EditDefaultsOnly, Category = "Movement")
	float WalkSpeed = 450.f;

	UPROPERTY(EditDefaultsOnly, Category = "Movement")
	float SprintSpeed = 650.f;

	UPROPERTY(EditDefaultsOnly, Category = "Movement")
	float CrouchSpeed = 250.f;

	UPROPERTY(EditDefaultsOnly, Category = "Movement")
	float SlideImpulse = 500.f;

	UPROPERTY(EditDefaultsOnly, Category = "Movement")
	float SlideDuration = 0.75f;

	UPROPERTY(EditDefaultsOnly, Category = "Movement")
	float SlideCooldown = 0.6f;

	UPROPERTY(EditDefaultsOnly, Category = "Movement|Vault")
	float VaultMinHeight = 50.f;

	UPROPERTY(EditDefaultsOnly, Category = "Movement|Vault")
	float VaultMaxHeight = 120.f;

	UPROPERTY(EditDefaultsOnly, Category = "Movement|Vault")
	float VaultReach = 90.f;

	UPROPERTY(EditDefaultsOnly, Category = "Movement|Vault")
	float VaultDuration = 0.35f;

	// --- Camera (Bible §3: 95 default, 80-110 adjustable)
	UPROPERTY(EditDefaultsOnly, Category = "Camera")
	float BaseFOV = 95.f;

	UPROPERTY(EditDefaultsOnly, Category = "Camera")
	float SprintFOVBoost = 4.f;

	UPROPERTY(EditDefaultsOnly, Category = "Camera")
	float StandingEyeHeight = 165.f;

	UPROPERTY(EditDefaultsOnly, Category = "Camera")
	float CrouchedEyeHeightCm = 95.f;

	UPROPERTY(EditDefaultsOnly, Category = "Camera")
	float LookSensitivity = 1.f;

	UPROPERTY(EditDefaultsOnly, Category = "Camera")
	bool bInvertY = false;

	/** Gamepad stick look rate in degrees/second at full deflection (yaw). */
	UPROPERTY(EditDefaultsOnly, Category = "Camera")
	float GamepadLookRate = 170.f;

	/** Pitch rate relative to yaw (vertical aim is usually tuned slower). */
	UPROPERTY(EditDefaultsOnly, Category = "Camera")
	float GamepadPitchScale = 0.7f;

	/** Response curve on stick deflection (1 = linear; higher = finer control on small deflections). */
	UPROPERTY(EditDefaultsOnly, Category = "Camera", meta = (ClampMin = "1.0", ClampMax = "4.0"))
	float GamepadLookExponent = 2.2f;

	/** Gamepad-only extra scale while fully aimed down sights (on top of the weapon's AdsSensitivityScale). */
	UPROPERTY(EditDefaultsOnly, Category = "Camera", meta = (ClampMin = "0.1", ClampMax = "1.0"))
	float GamepadAdsScale = 0.5f;

	// --- Full-body mesh (shadow + other views). Arms are a separate asset task.
	UPROPERTY(EditDefaultsOnly, Category = "Body")
	TObjectPtr<USkeletalMesh> BodyMeshAsset;

	UPROPERTY(EditDefaultsOnly, Category = "Body")
	TSubclassOf<UAnimInstance> BodyAnimClass;

	/** Material for every slot of the body mesh (Ghost-7 look). Empty = /Game/NeonVeil/Characters/Ghost7/MI_NV_Ghost7 if present. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Body")
	TObjectPtr<class UMaterialInterface> BodyMaterial;

	/** Drive the body with the native gun-aware animation (UNVBodyAnimInstance) instead of BodyAnimClass. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Body")
	bool bNativeBodyAnim = true;

	/** Rifle left-hand hold point in weapon space when the weapon data doesn't give one; X = along the barrel. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Body")
	float DefaultForegripFraction = 0.62f;

	// --- First-person arms (KINEMATION SKM_SciFi_Arms, Manny skeleton). Shown for weapons with ArmsIdleAnim.
	UPROPERTY(EditDefaultsOnly, Category = "Arms")
	TObjectPtr<USkeletalMesh> ArmsMeshAsset;

	/** Arms placement under the viewmodel root: turns the Manny +Y forward to +X and puts the eyes on the camera. */
	UPROPERTY(EditDefaultsOnly, Category = "Arms")
	FTransform ArmsOffset = FTransform(FRotator(0.f, -90.f, 0.f), FVector(-10.f, 0.3f, -158.f));

	// --- Viewmodel motion
	UPROPERTY(EditDefaultsOnly, Category = "Viewmodel")
	float ViewmodelSwayAmount = 0.6f;

	UPROPERTY(EditDefaultsOnly, Category = "Viewmodel")
	float ViewmodelBobAmount = 0.5f;

	/** Rendered distance (cm) the nearest part of an aimed weapon keeps from the eye; the near clip plane is 5 cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Viewmodel", meta = (ClampMin = "0"))
	float ViewmodelNearClearance = 14.f;

	/** Aimed down the sights, the arms are hidden once an upper arm comes closer to the eye than this (cm, camera space):
	 *  the rifle poses bring the shoulder/sleeve right across the view. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Viewmodel", meta = (ClampMin = "0"))
	float ArmsAdsHideDepth = 32.f;

	/** Unarmed punch (Melee with nothing in hand): arms animation and where the arms sit for it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Viewmodel")
	TSoftObjectPtr<UAnimationAsset> FistPunchAnim = TSoftObjectPtr<UAnimationAsset>(FSoftObjectPath(TEXT("/Game/KINEMATION/Sci-fi_FPS_Pack/Animations/Character/UE5/General/A_FP_LeftHand_Punch.A_FP_LeftHand_Punch")));

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Viewmodel")
	FVector FistViewmodelOffset = FVector(8.f, 1.f, 12.f);

	// --- Melee viewmodel motion (rotations turn the viewmodel about the hand holding the weapon; offsets are in view
	// space: X forward, Y right, Z up). Tunable here without a rebuild.
	/** Shock baton: raise it above the head, then chop down and across to the bottom left. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Viewmodel|Melee")
	FNVMeleeMotion BatonMotion;

	/** Rifles and SMGs: turn the gun and drive the butt forward into the target. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Viewmodel|Melee")
	FNVMeleeMotion RifleBashMotion;

	/** Pistols: raise the gun and smash the grip down, overhead. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Viewmodel|Melee")
	FNVMeleeMotion PistolBashMotion;

	/** Punch: the arms are shown for this fraction of the punch animation (it ends in a weapon pose). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Viewmodel|Melee", meta = (ClampMin = "0.1", ClampMax = "1"))
	float FistPunchShowFraction = 0.5f;

	/** Punch: start this far into the animation (its first frames are the open hand on a foregrip). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Viewmodel|Melee", meta = (ClampMin = "0", ClampMax = "0.9"))
	float FistPunchStartFraction = 0.12f;

	/** While swinging, the arms hide only if an upper arm comes closer to the eye than this (cm). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Viewmodel|Melee", meta = (ClampMin = "0"))
	float MeleeArmsHideDepth = 10.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Viewmodel")
	float FistPunchRate = 1.25f;

private:
	void Move(const FInputActionValue& Value);
	void Look(const FInputActionValue& Value);
	void MouseLook(const FInputActionValue& Value);
	void ApplyLook(FVector2D Axis);
	void SprintPressed();
	void SprintReleased();
	void CrouchPressed();
	void CrouchReleased();
	void JumpPressed();
	void FirePressed();
	void FireReleased();
	void AimPressed();
	void AimReleased();
	void ReloadPressed();
	void InteractPressed();
	void InteractReleased();
	void NextWeapon();
	void HolsterPressed();
	void NavGuidePressed();
	void UpdateArmsVisibility();
	void ShowFistArms();
	void RefreshBodyHold();
	class UNVBodyAnimInstance* GetBodyAnim() const;
	void ApplyBodyAnimClass();

	UFUNCTION()
	void HandleMeleeSwing();
public:
	/** QA: live-tune the body (shadow) grip of the current weapon (relative to hand_r) and the left-hand point. */
	void DebugSetGrip(const FTransform& Grip, const FVector& LeftHand);
	FString DebugDescribeBody() const;
private:
	TOptional<FTransform> DebugGripOverride;
	TOptional<FVector> DebugLeftOverride;
	void ApplyViewmodelVisibility(bool bScoped);
	bool bViewmodelHidden = false;
	void PrevWeapon();
	void MeleePressed();
	void Ability1Pressed();
	void Ability2Pressed();
	void Ability3Pressed();

	void SetSprinting(bool bNewSprinting);
	bool CanSprint() const;
	void StartSlide();
	void TickSlide(float DeltaSeconds);
	bool TryVault();
	void TickVault(float DeltaSeconds);
	void UpdateCamera(float DeltaSeconds);
	void UpdateMoveSpeed();
	void UpdateViewmodel(float DeltaSeconds);

	UFUNCTION()
	void HandleWeaponFired();

	/** Lethal damage (M01 on): lock input, fade, "signal lost", then reload the last checkpoint. */
	UFUNCTION()
	void HandleDeath(UNVHealthComponent* HealthComp, AActor* Killer);
	void ReloadAfterDeath();
	FTimerHandle DeathTimer;
	bool bDeathHandled = false;

	UFUNCTION()
	void HandleWeaponEquipped(UNVWeaponData* Weapon);

	UFUNCTION()
	void HandleReloadState(bool bReloading);

	/** Plays an arms animation; one-shots return to the weapon's idle loop when they end. */
	void PlayArms(UAnimationAsset* Anim, bool bLoop, float Rate = 1.f);
	void ReturnArmsToIdle();
	bool HasArms() const { return ArmsWeapon != nullptr; }

	UPROPERTY(Transient)
	TObjectPtr<UNVWeaponData> ArmsWeapon;

	bool bScopedIn = false;

	FTimerHandle ArmsReturnTimer;

	bool bSprinting = false;
	bool bSprintHeld = false;
	bool bToggleSprintSetting = false;
	bool bToggleCrouchSetting = false;
	bool bToggleAimSetting = false;
	bool bAimToggledOn = false;
	bool bInputLocked = false;
	bool bLookAllowedWhileLocked = true;
	FVector2D LastMoveInput = FVector2D::ZeroVector;
	FVector2D DebugMoveInput = FVector2D::ZeroVector;

	float SlideTimeLeft = 0.f;
	float LastSlideEndTime = -100.f;
	float DefaultGroundFriction = 8.f;
	float DefaultBrakingDecel = 2048.f;

	bool bVaulting = false;
	float VaultElapsed = 0.f;
	FVector VaultStart;
	FVector VaultApex;
	FVector VaultEnd;

	float CurrentEyeHeight = 165.f;
	float ViewmodelKick = 0.f;
	float SmoothedSprintFOV = 0.f;
	float BobPhase = 0.f;
	FVector2D LookDeltaThisFrame = FVector2D::ZeroVector;
	FVector2D SmoothedSway = FVector2D::ZeroVector;
	/** Forward push (cm) that keeps the weapon's rear clear of the camera near plane while aiming. */
	float NearClearPush = 0.f;
	/** Runtime mapping for holster / view toggle, so those keys work even if the IMC asset lacks them. */
	UPROPERTY(Transient)
	TObjectPtr<UInputMappingContext> RuntimeViewContext;

	/** Wayfinding arrow (N / tap D-pad Down): made at runtime, shown on demand. */
	UPROPERTY(Transient)
	TObjectPtr<UInputAction> NavGuideAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> NavGuidePadAction;

	/** Holster on the pad: hold D-pad Down (a tap is the wayfinding arrow). */
	UPROPERTY(Transient)
	TObjectPtr<UInputAction> HolsterPadAction;

	bool bArmsAdsHidden = false;
	FVector SmoothedViewmodelLoc = FVector::ZeroVector;
	FRotator SmoothedViewmodelRot = FRotator::ZeroRotator;
	bool bFistArms = false;

	UPROPERTY(Transient)
	TObjectPtr<class ANVNavArrow> NavArrow;
	void EnsureViewInput();
};
