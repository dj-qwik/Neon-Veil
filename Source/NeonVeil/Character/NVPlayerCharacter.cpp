#include "Character/NVPlayerCharacter.h"
#include "Combat/NVHealthComponent.h"
#include "Combat/NVWeaponComponent.h"
#include "Combat/NVWeaponData.h"
#include "Interaction/NVInteractionComponent.h"
#include "NeonVeil.h"

#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "InputMappingContext.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"

ANVPlayerCharacter::ANVPlayerCharacter(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	PrimaryActorTick.bCanEverTick = true;

	GetCapsuleComponent()->InitCapsuleSize(34.f, 96.f);

	FirstPersonCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FirstPersonCamera"));
	FirstPersonCamera->SetupAttachment(GetCapsuleComponent());
	FirstPersonCamera->SetRelativeLocation(FVector(0.f, 0.f, StandingEyeHeight - 96.f));
	FirstPersonCamera->bUsePawnControlRotation = true;
	FirstPersonCamera->SetFieldOfView(BaseFOV);
	// Arms and weapon get their own FOV so they don't stretch when the player widens the world FOV.
	FirstPersonCamera->bEnableFirstPersonFieldOfView = true;
	FirstPersonCamera->FirstPersonFieldOfView = 70.f;
	FirstPersonCamera->bEnableFirstPersonScale = true;
	FirstPersonCamera->FirstPersonScale = 0.6f;

	FirstPersonMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("FirstPersonMesh"));
	FirstPersonMesh->SetupAttachment(FirstPersonCamera);
	FirstPersonMesh->SetOnlyOwnerSee(true);
	FirstPersonMesh->FirstPersonPrimitiveType = EFirstPersonPrimitiveType::FirstPerson;
	FirstPersonMesh->CastShadow = false;
	FirstPersonMesh->SetCollisionProfileName(TEXT("NoCollision"));

	WeaponMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("WeaponMesh"));
	WeaponMesh->SetupAttachment(FirstPersonMesh, TEXT("HandGrip_R"));
	WeaponMesh->SetOnlyOwnerSee(true);
	WeaponMesh->FirstPersonPrimitiveType = EFirstPersonPrimitiveType::FirstPerson;
	WeaponMesh->CastShadow = false;
	WeaponMesh->SetCollisionProfileName(TEXT("NoCollision"));

	WeaponStaticMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WeaponStaticMesh"));
	WeaponStaticMesh->SetupAttachment(FirstPersonMesh, TEXT("HandGrip_R"));
	WeaponStaticMesh->SetOnlyOwnerSee(true);
	WeaponStaticMesh->FirstPersonPrimitiveType = EFirstPersonPrimitiveType::FirstPerson;
	WeaponStaticMesh->CastShadow = false;
	WeaponStaticMesh->SetCollisionProfileName(TEXT("NoCollision"));

	// Full-body mesh: hidden from the owner, still casts a shadow (Bible §13: full-body shadow mesh).
	GetMesh()->SetOwnerNoSee(true);
	GetMesh()->FirstPersonPrimitiveType = EFirstPersonPrimitiveType::WorldSpaceRepresentation;
	GetMesh()->bCastHiddenShadow = true;
	GetMesh()->SetRelativeLocation(FVector(0.f, 0.f, -96.f));
	GetMesh()->SetRelativeRotation(FRotator(0.f, -90.f, 0.f));

	Health = CreateDefaultSubobject<UNVHealthComponent>(TEXT("Health"));
	Weapons = CreateDefaultSubobject<UNVWeaponComponent>(TEXT("Weapons"));
	Interaction = CreateDefaultSubobject<UNVInteractionComponent>(TEXT("Interaction"));

	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->MaxWalkSpeed = WalkSpeed;
	Move->MaxWalkSpeedCrouched = CrouchSpeed;
	Move->NavAgentProps.bCanCrouch = true;
	Move->SetCrouchedHalfHeight(58.f);
	Move->bCanWalkOffLedgesWhenCrouching = true;
	Move->JumpZVelocity = 460.f;
	Move->AirControl = 0.3f;
	Move->GroundFriction = 8.f;
	Move->BrakingDecelerationWalking = 2048.f;
	Move->MaxStepHeight = 45.f;
	Move->SetWalkableFloorAngle(46.f);

	bUseControllerRotationYaw = true;
	CurrentEyeHeight = StandingEyeHeight;
}

void ANVPlayerCharacter::BeginPlay()
{
	Super::BeginPlay();

	DefaultGroundFriction = GetCharacterMovement()->GroundFriction;
	DefaultBrakingDecel = GetCharacterMovement()->BrakingDecelerationWalking;
	CurrentEyeHeight = StandingEyeHeight;
	FirstPersonCamera->SetFieldOfView(BaseFOV);

	Weapons->Initialize(FirstPersonCamera, WeaponMesh, WeaponStaticMesh);
	UpdateMoveSpeed();
}

void ANVPlayerCharacter::PawnClientRestart()
{
	Super::PawnClientRestart();

	if (const APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PC->GetLocalPlayer()))
		{
			if (DefaultMappingContext)
			{
				Subsystem->AddMappingContext(DefaultMappingContext, 0);
			}
		}
	}
}

void ANVPlayerCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	UEnhancedInputComponent* EIC = Cast<UEnhancedInputComponent>(PlayerInputComponent);
	if (!EIC)
	{
		UE_LOG(LogNeonVeil, Error, TEXT("NVPlayerCharacter needs the Enhanced Input component (check Project Settings > Input)."));
		return;
	}

	auto BindIf = [EIC](UInputAction* Action, ETriggerEvent Event, ANVPlayerCharacter* Self, void (ANVPlayerCharacter::*Func)())
	{
		if (Action)
		{
			EIC->BindAction(Action, Event, Self, Func);
		}
	};

	if (MoveAction)
	{
		EIC->BindAction(MoveAction, ETriggerEvent::Triggered, this, &ANVPlayerCharacter::Move);
		EIC->BindAction(MoveAction, ETriggerEvent::Completed, this, &ANVPlayerCharacter::Move);
	}
	if (LookAction)
	{
		EIC->BindAction(LookAction, ETriggerEvent::Triggered, this, &ANVPlayerCharacter::Look);
	}
	BindIf(JumpAction, ETriggerEvent::Started, this, &ANVPlayerCharacter::JumpPressed);
	BindIf(JumpAction, ETriggerEvent::Completed, this, &ANVPlayerCharacter::StopJumping);
	BindIf(SprintAction, ETriggerEvent::Started, this, &ANVPlayerCharacter::SprintPressed);
	BindIf(SprintAction, ETriggerEvent::Completed, this, &ANVPlayerCharacter::SprintReleased);
	BindIf(CrouchAction, ETriggerEvent::Started, this, &ANVPlayerCharacter::CrouchPressed);
	BindIf(CrouchAction, ETriggerEvent::Completed, this, &ANVPlayerCharacter::CrouchReleased);
	BindIf(FireAction, ETriggerEvent::Started, this, &ANVPlayerCharacter::FirePressed);
	BindIf(FireAction, ETriggerEvent::Completed, this, &ANVPlayerCharacter::FireReleased);
	BindIf(AimAction, ETriggerEvent::Started, this, &ANVPlayerCharacter::AimPressed);
	BindIf(AimAction, ETriggerEvent::Completed, this, &ANVPlayerCharacter::AimReleased);
	BindIf(ReloadAction, ETriggerEvent::Started, this, &ANVPlayerCharacter::ReloadPressed);
	BindIf(InteractAction, ETriggerEvent::Started, this, &ANVPlayerCharacter::InteractPressed);
	BindIf(InteractAction, ETriggerEvent::Completed, this, &ANVPlayerCharacter::InteractReleased);
	BindIf(NextWeaponAction, ETriggerEvent::Started, this, &ANVPlayerCharacter::NextWeapon);
	BindIf(PrevWeaponAction, ETriggerEvent::Started, this, &ANVPlayerCharacter::PrevWeapon);
}

// ---------------------------------------------------------------- input handlers

void ANVPlayerCharacter::Move(const FInputActionValue& Value)
{
	LastMoveInput = Value.Get<FVector2D>();
	if (bInputLocked || bVaulting)
	{
		return;
	}
	AddMovementInput(GetActorForwardVector(), LastMoveInput.Y);
	AddMovementInput(GetActorRightVector(), LastMoveInput.X);
}

void ANVPlayerCharacter::Look(const FInputActionValue& Value)
{
	if (bInputLocked && !bLookAllowedWhileLocked)
	{
		return;
	}
	FVector2D Axis = Value.Get<FVector2D>() * LookSensitivity;
	if (const UNVWeaponData* W = Weapons->GetCurrentWeapon())
	{
		Axis *= FMath::Lerp(1.f, W->AdsSensitivityScale, Weapons->GetAdsAlpha());
	}
	AddControllerYawInput(Axis.X);
	AddControllerPitchInput(bInvertY ? -Axis.Y : Axis.Y);
}

void ANVPlayerCharacter::JumpPressed()
{
	if (bInputLocked || bVaulting)
	{
		return;
	}
	// Jump into a waist-high obstacle vaults instead (Bible §7 vault band).
	if (!TryVault())
	{
		if (bIsCrouched)
		{
			UnCrouch();
		}
		Jump();
	}
}

void ANVPlayerCharacter::SprintPressed()
{
	if (bToggleSprintSetting)
	{
		bSprintHeld = !bSprintHeld;
	}
	else
	{
		bSprintHeld = true;
	}
}

void ANVPlayerCharacter::SprintReleased()
{
	if (!bToggleSprintSetting)
	{
		bSprintHeld = false;
	}
}

void ANVPlayerCharacter::CrouchPressed()
{
	if (bInputLocked)
	{
		return;
	}
	if (bSprinting && GetCharacterMovement()->IsMovingOnGround() && GetWorld()->GetTimeSeconds() - LastSlideEndTime > SlideCooldown)
	{
		StartSlide();
		return;
	}
	if (bToggleCrouchSetting && bIsCrouched)
	{
		UnCrouch();
	}
	else
	{
		Crouch();
	}
}

void ANVPlayerCharacter::CrouchReleased()
{
	if (!bToggleCrouchSetting && SlideTimeLeft <= 0.f)
	{
		UnCrouch();
	}
}

void ANVPlayerCharacter::FirePressed()
{
	if (bInputLocked)
	{
		return;
	}
	SetSprinting(false);
	Weapons->StartFire();
}

void ANVPlayerCharacter::FireReleased()
{
	Weapons->StopFire();
}

void ANVPlayerCharacter::AimPressed()
{
	if (bInputLocked)
	{
		return;
	}
	if (bToggleAimSetting)
	{
		bAimToggledOn = !bAimToggledOn;
		Weapons->SetAiming(bAimToggledOn);
	}
	else
	{
		Weapons->SetAiming(true);
	}
	SetSprinting(false);
}

void ANVPlayerCharacter::AimReleased()
{
	if (!bToggleAimSetting)
	{
		Weapons->SetAiming(false);
	}
}

void ANVPlayerCharacter::ReloadPressed()
{
	if (!bInputLocked)
	{
		Weapons->Reload();
	}
}

void ANVPlayerCharacter::InteractPressed()
{
	if (!bInputLocked)
	{
		Interaction->BeginUse();
	}
}

void ANVPlayerCharacter::InteractReleased()
{
	Interaction->EndUse();
}

void ANVPlayerCharacter::NextWeapon()
{
	if (!bInputLocked)
	{
		Weapons->CycleWeapon(1);
	}
}

void ANVPlayerCharacter::PrevWeapon()
{
	if (!bInputLocked)
	{
		Weapons->CycleWeapon(-1);
	}
}

// ---------------------------------------------------------------- settings / scripted control

void ANVPlayerCharacter::SetBaseFOV(float NewHorizontalFOV)
{
	BaseFOV = FMath::Clamp(NewHorizontalFOV, 80.f, 110.f);
}

void ANVPlayerCharacter::SetToggleSettings(bool bToggleSprint, bool bToggleCrouch, bool bToggleAim)
{
	bToggleSprintSetting = bToggleSprint;
	bToggleCrouchSetting = bToggleCrouch;
	bToggleAimSetting = bToggleAim;
}

void ANVPlayerCharacter::SetGameplayInputLocked(bool bLocked, bool bAllowLook)
{
	bInputLocked = bLocked;
	bLookAllowedWhileLocked = bAllowLook;
	if (bLocked)
	{
		Weapons->StopFire();
		Weapons->SetAiming(false);
		Interaction->EndUse();
		bSprintHeld = false;
		SetSprinting(false);
	}
}

// ---------------------------------------------------------------- movement

bool ANVPlayerCharacter::CanSprint() const
{
	const UCharacterMovementComponent* Move = GetCharacterMovement();
	return bSprintHeld && !bInputLocked && !bIsCrouched && !bVaulting
		&& Move->IsMovingOnGround()
		&& LastMoveInput.Y > 0.3f // forward only
		&& !Weapons->IsAiming();
}

void ANVPlayerCharacter::SetSprinting(bool bNewSprinting)
{
	if (bSprinting != bNewSprinting)
	{
		bSprinting = bNewSprinting;
		UpdateMoveSpeed();
		OnSprintChanged.Broadcast(bSprinting);
	}
}

void ANVPlayerCharacter::UpdateMoveSpeed()
{
	float Speed = bSprinting ? SprintSpeed : WalkSpeed;
	if (const UNVWeaponData* W = Weapons ? Weapons->GetCurrentWeapon() : nullptr)
	{
		Speed *= FMath::Lerp(1.f, W->AdsMoveSpeedScale, Weapons->GetAdsAlpha());
	}
	GetCharacterMovement()->MaxWalkSpeed = Speed;
}

void ANVPlayerCharacter::StartSlide()
{
	SetSprinting(false);
	Crouch();
	SlideTimeLeft = SlideDuration;
	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->GroundFriction = 0.6f;
	Move->BrakingDecelerationWalking = 350.f;
	// Keep current speed and add a short push in the travel direction.
	const FVector Dir = GetVelocity().GetSafeNormal2D().IsNearlyZero() ? GetActorForwardVector() : GetVelocity().GetSafeNormal2D();
	LaunchCharacter(Dir * SlideImpulse, false, false);
}

void ANVPlayerCharacter::TickSlide(float DeltaSeconds)
{
	if (SlideTimeLeft <= 0.f)
	{
		return;
	}
	SlideTimeLeft -= DeltaSeconds;
	const bool bTooSlow = GetVelocity().Size2D() < CrouchSpeed;
	if (SlideTimeLeft <= 0.f || bTooSlow || !GetCharacterMovement()->IsMovingOnGround())
	{
		SlideTimeLeft = 0.f;
		LastSlideEndTime = GetWorld()->GetTimeSeconds();
		UCharacterMovementComponent* Move = GetCharacterMovement();
		Move->GroundFriction = DefaultGroundFriction;
		Move->BrakingDecelerationWalking = DefaultBrakingDecel;
	}
}

bool ANVPlayerCharacter::TryVault()
{
	const UCharacterMovementComponent* Move = GetCharacterMovement();
	if (!Move->IsMovingOnGround() || bIsCrouched)
	{
		return false;
	}

	const UCapsuleComponent* Capsule = GetCapsuleComponent();
	const float HalfHeight = Capsule->GetScaledCapsuleHalfHeight();
	const float Radius = Capsule->GetScaledCapsuleRadius();
	const FVector Feet = GetActorLocation() - FVector(0.f, 0.f, HalfHeight);
	const FVector Fwd = GetActorForwardVector();

	FCollisionQueryParams Params(SCENE_QUERY_STAT(NVVault), false, this);

	// 1. Something solid in front at knee height?
	FHitResult WallHit;
	const FVector KneeStart = Feet + FVector(0.f, 0.f, VaultMinHeight * 0.5f + 10.f);
	if (!GetWorld()->LineTraceSingleByChannel(WallHit, KneeStart, KneeStart + Fwd * (Radius + VaultReach), ECC_Visibility, Params))
	{
		return false;
	}
	if (FMath::Abs(WallHit.ImpactNormal.Z) > 0.3f)
	{
		return false; // a slope, not a wall
	}

	// 2. Find the top surface just beyond the wall face.
	const FVector OverTop = WallHit.ImpactPoint + Fwd * 25.f;
	FHitResult TopHit;
	const FVector TopStart = FVector(OverTop.X, OverTop.Y, Feet.Z + VaultMaxHeight + 20.f);
	if (!GetWorld()->LineTraceSingleByChannel(TopHit, TopStart, FVector(OverTop.X, OverTop.Y, Feet.Z), ECC_Visibility, Params))
	{
		return false;
	}
	const float LedgeHeight = TopHit.ImpactPoint.Z - Feet.Z;
	if (LedgeHeight < VaultMinHeight || LedgeHeight > VaultMaxHeight || TopHit.ImpactNormal.Z < 0.7f)
	{
		return false;
	}

	// 3. Room for the capsule above the ledge, and a landing spot beyond it.
	const FVector Apex = FVector(TopHit.ImpactPoint.X, TopHit.ImpactPoint.Y, TopHit.ImpactPoint.Z + HalfHeight + 4.f);
	const FCollisionShape Shape = FCollisionShape::MakeCapsule(Radius, HalfHeight);
	if (GetWorld()->OverlapBlockingTestByChannel(Apex, FQuat::Identity, ECC_Pawn, Shape, Params))
	{
		return false;
	}

	FVector Land = Apex + Fwd * (Radius * 2.f + 30.f);
	FHitResult LandHit;
	// Drop the landing point down to the floor (up to 1.5 m) so we vault over thin rails as well as onto ledges.
	if (GetWorld()->SweepSingleByChannel(LandHit, Land, Land - FVector(0.f, 0.f, 150.f + LedgeHeight), FQuat::Identity, ECC_Pawn, Shape, Params))
	{
		Land = LandHit.Location + FVector(0.f, 0.f, 2.f);
	}
	if (GetWorld()->OverlapBlockingTestByChannel(Land, FQuat::Identity, ECC_Pawn, Shape, Params))
	{
		Land = Apex; // fall back to mantling onto the top
	}

	bVaulting = true;
	VaultElapsed = 0.f;
	VaultStart = GetActorLocation();
	VaultApex = Apex;
	VaultEnd = Land;
	SetSprinting(false);
	Weapons->StopFire();
	GetCharacterMovement()->SetMovementMode(MOVE_Flying);
	GetCharacterMovement()->StopMovementImmediately();
	return true;
}

void ANVPlayerCharacter::TickVault(float DeltaSeconds)
{
	if (!bVaulting)
	{
		return;
	}
	VaultElapsed += DeltaSeconds;
	const float T = FMath::Clamp(VaultElapsed / VaultDuration, 0.f, 1.f);
	// Quadratic Bezier start -> apex -> end, eased.
	const float E = FMath::InterpEaseInOut(0.f, 1.f, T, 2.f);
	const FVector A = FMath::Lerp(VaultStart, VaultApex, E);
	const FVector B = FMath::Lerp(VaultApex, VaultEnd, E);
	SetActorLocation(FMath::Lerp(A, B, E), false, nullptr, ETeleportType::None);

	if (T >= 1.f)
	{
		bVaulting = false;
		GetCharacterMovement()->SetMovementMode(MOVE_Falling);
		// Carry some momentum out of the vault.
		GetCharacterMovement()->Velocity = GetActorForwardVector() * WalkSpeed * 0.8f;
	}
}

void ANVPlayerCharacter::OnStartCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust)
{
	Super::OnStartCrouch(HalfHeightAdjust, ScaledHalfHeightAdjust);
	SetSprinting(false);
}

void ANVPlayerCharacter::OnEndCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust)
{
	Super::OnEndCrouch(HalfHeightAdjust, ScaledHalfHeightAdjust);
}

// ---------------------------------------------------------------- tick

void ANVPlayerCharacter::UpdateCamera(float DeltaSeconds)
{
	// Eye height relative to the feet, smoothed through crouch transitions.
	const float TargetEye = (bIsCrouched || IsSliding()) ? CrouchedEyeHeightCm : StandingEyeHeight;
	CurrentEyeHeight = FMath::FInterpTo(CurrentEyeHeight, TargetEye, DeltaSeconds, 12.f);
	const float HalfHeight = GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight();
	FirstPersonCamera->SetRelativeLocation(FVector(0.f, 0.f, CurrentEyeHeight - HalfHeight));

	float TargetFOV = BaseFOV + (bSprinting ? SprintFOVBoost : 0.f);
	if (const UNVWeaponData* W = Weapons->GetCurrentWeapon())
	{
		TargetFOV = FMath::Lerp(TargetFOV, W->AdsFOV, Weapons->GetAdsAlpha());
	}
	FirstPersonCamera->SetFieldOfView(FMath::FInterpTo(FirstPersonCamera->FieldOfView, TargetFOV, DeltaSeconds, 20.f));
}

void ANVPlayerCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	SetSprinting(CanSprint());
	TickSlide(DeltaSeconds);
	TickVault(DeltaSeconds);
	UpdateMoveSpeed();
	UpdateCamera(DeltaSeconds);
}
