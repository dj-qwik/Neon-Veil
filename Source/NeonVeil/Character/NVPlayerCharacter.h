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

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FNVOnSprintChanged, bool, bSprinting);

/**
 * Ghost-7. First-person movement, camera and input routing; owns health, weapon and interaction.
 * Tuning numbers are starting targets from Bible §7.
 */
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

	UFUNCTION(BlueprintPure, Category = "NeonVeil")
	UCameraComponent* GetFirstPersonCamera() const { return FirstPersonCamera; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil")
	UNVHealthComponent* GetHealth() const { return Health; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil")
	UNVWeaponComponent* GetWeapons() const { return Weapons; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil")
	UNVInteractionComponent* GetInteraction() const { return Interaction; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil")
	bool IsSprinting() const { return bSprinting; }

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

protected:
	virtual void BeginPlay() override;

	// --- Components
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UCameraComponent> FirstPersonCamera;

	/** First-person arms, rendered only for the owner. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<USkeletalMeshComponent> FirstPersonMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<USkeletalMeshComponent> WeaponMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> WeaponStaticMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UNVHealthComponent> Health;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UNVWeaponComponent> Weapons;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UNVInteractionComponent> Interaction;

	// --- Input (assigned in BP_NVPlayerCharacter)
	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputMappingContext> DefaultMappingContext;

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
	float VaultMinHeight = 60.f;

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

private:
	void Move(const FInputActionValue& Value);
	void Look(const FInputActionValue& Value);
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
	void PrevWeapon();

	void SetSprinting(bool bNewSprinting);
	bool CanSprint() const;
	void StartSlide();
	void TickSlide(float DeltaSeconds);
	bool TryVault();
	void TickVault(float DeltaSeconds);
	void UpdateCamera(float DeltaSeconds);
	void UpdateMoveSpeed();

	bool bSprinting = false;
	bool bSprintHeld = false;
	bool bToggleSprintSetting = false;
	bool bToggleCrouchSetting = false;
	bool bToggleAimSetting = false;
	bool bAimToggledOn = false;
	bool bInputLocked = false;
	bool bLookAllowedWhileLocked = true;
	FVector2D LastMoveInput = FVector2D::ZeroVector;

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
};
