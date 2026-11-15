#include "Character/NVPlayerCharacter.h"
#include "Character/NVBodyAnimInstance.h"
#include "Materials/MaterialInterface.h"
#include "Animation/AnimSequenceBase.h"
#include "Engine/SkeletalMesh.h"
#include "Combat/NVHealthComponent.h"
#include "Combat/NVWeaponComponent.h"
#include "Combat/NVWeaponData.h"
#include "Interaction/NVInteractionComponent.h"
#include "Abilities/NVAbilityComponent.h"
#include "Combat/NVMeleeComponent.h"
#include "NeonVeil.h"

#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "InputMappingContext.h"
#include "InputAction.h"
#include "InputTriggers.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"
#include "UI/NVNavArrow.h"

#include "GameFramework/SpringArmComponent.h"

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

	ViewmodelRoot = CreateDefaultSubobject<USceneComponent>(TEXT("ViewmodelRoot"));
	ViewmodelRoot->SetupAttachment(FirstPersonCamera);

	// Arms ride the viewmodel root so they share its sway, bob, kick and ADS offset with the weapon.
	FirstPersonMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("FirstPersonMesh"));
	FirstPersonMesh->SetupAttachment(ViewmodelRoot);
	FirstPersonMesh->SetOnlyOwnerSee(true);
	FirstPersonMesh->FirstPersonPrimitiveType = EFirstPersonPrimitiveType::FirstPerson;
	FirstPersonMesh->CastShadow = false;
	FirstPersonMesh->SetCollisionProfileName(TEXT("NoCollision"));
	FirstPersonMesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	FirstPersonMesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;

	WeaponMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("WeaponMesh"));
	WeaponMesh->SetupAttachment(ViewmodelRoot);
	WeaponMesh->SetOnlyOwnerSee(true);
	WeaponMesh->FirstPersonPrimitiveType = EFirstPersonPrimitiveType::FirstPerson;
	WeaponMesh->CastShadow = false;
	WeaponMesh->SetCollisionProfileName(TEXT("NoCollision"));

	WeaponStaticMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WeaponStaticMesh"));
	WeaponStaticMesh->SetupAttachment(ViewmodelRoot);
	WeaponStaticMesh->SetOnlyOwnerSee(true);
	WeaponStaticMesh->FirstPersonPrimitiveType = EFirstPersonPrimitiveType::FirstPerson;
	WeaponStaticMesh->CastShadow = false;
	WeaponStaticMesh->SetCollisionProfileName(TEXT("NoCollision"));

	BatonMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BatonMesh"));
	BatonMesh->SetupAttachment(FirstPersonCamera);
	BatonMesh->SetOnlyOwnerSee(true);
	BatonMesh->FirstPersonPrimitiveType = EFirstPersonPrimitiveType::FirstPerson;
	BatonMesh->CastShadow = false;
	BatonMesh->SetCollisionProfileName(TEXT("NoCollision"));
	BatonMesh->SetHiddenInGame(true);
	BatonMesh->SetRelativeScale3D(FVector(0.035f, 0.035f, 0.5f));
	{
		static ConstructorHelpers::FObjectFinder<UStaticMesh> Cyl(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
		if (Cyl.Succeeded())
		{
			BatonMesh->SetStaticMesh(Cyl.Object);
		}
	}

	// Full-body mesh: hidden from the owner, still casts a shadow (Bible §13: full-body shadow mesh).
	GetMesh()->SetOwnerNoSee(true);
	GetMesh()->FirstPersonPrimitiveType = EFirstPersonPrimitiveType::WorldSpaceRepresentation;
	GetMesh()->bCastHiddenShadow = true;
	GetMesh()->SetRelativeLocation(FVector(0.f, 0.f, -96.f));
	GetMesh()->SetRelativeRotation(FRotator(0.f, -90.f, 0.f));

	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(GetCapsuleComponent());
	CameraBoom->SetRelativeLocation(FVector(0.f, 0.f, 55.f));
	CameraBoom->TargetArmLength = 230.f;
	CameraBoom->SocketOffset = FVector(0.f, 55.f, 15.f);       // over the right shoulder
	CameraBoom->bUsePawnControlRotation = true;
	CameraBoom->bDoCollisionTest = true;
	CameraBoom->ProbeSize = 14.f;
	CameraBoom->bEnableCameraLag = true;
	CameraBoom->CameraLagSpeed = 18.f;

	ThirdPersonCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("ThirdPersonCamera"));
	ThirdPersonCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	ThirdPersonCamera->bUsePawnControlRotation = false;
	ThirdPersonCamera->SetFieldOfView(BaseFOV);
	ThirdPersonCamera->SetAutoActivate(false);

	ThirdPersonWeapon = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("ThirdPersonWeapon"));
	ThirdPersonWeapon->SetupAttachment(GetMesh(), ThirdPersonWeaponSocket);
	ThirdPersonWeapon->SetCollisionProfileName(TEXT("NoCollision"));
	ThirdPersonWeapon->SetVisibility(false);
	ThirdPersonWeaponStatic = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ThirdPersonWeaponStatic"));
	ThirdPersonWeaponStatic->SetupAttachment(GetMesh(), ThirdPersonWeaponSocket);
	ThirdPersonWeaponStatic->SetCollisionProfileName(TEXT("NoCollision"));
	ThirdPersonWeaponStatic->SetVisibility(false);

	Health = CreateDefaultSubobject<UNVHealthComponent>(TEXT("Health"));
	Weapons = CreateDefaultSubobject<UNVWeaponComponent>(TEXT("Weapons"));
	Interaction = CreateDefaultSubobject<UNVInteractionComponent>(TEXT("Interaction"));
	Abilities = CreateDefaultSubobject<UNVAbilityComponent>(TEXT("Abilities"));
	Melee = CreateDefaultSubobject<UNVMeleeComponent>(TEXT("Melee"));

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
	Weapons->OnWeaponFired.AddDynamic(this, &ANVPlayerCharacter::HandleWeaponFired);
	if (!ArmsMeshAsset)
	{
		// Default arms: the KINEMATION gloves (local-only pack content; stays null if the pack is absent).
		ArmsMeshAsset = LoadObject<USkeletalMesh>(nullptr, TEXT("/Game/KINEMATION/Sci-fi_FPS_Pack/Gloves/Meshes/SKM_SciFi_Arms.SKM_SciFi_Arms"));
	}
	Weapons->OnWeaponEquipped.AddDynamic(this, &ANVPlayerCharacter::HandleWeaponEquipped);
	Weapons->OnReloadStateChanged.AddDynamic(this, &ANVPlayerCharacter::HandleReloadState);
	Melee->OnSwing.AddDynamic(this, &ANVPlayerCharacter::HandleMeleeSwing);
	ApplyBodyAnimClass();
	HandleWeaponEquipped(Weapons->GetCurrentWeapon());
	UpdateMoveSpeed();
	ThirdPersonCamera->Deactivate();
	SetThirdPerson(bStartThirdPerson);
}

void ANVPlayerCharacter::SetThirdPerson(bool bNewThirdPerson)
{
	bThirdPerson = bNewThirdPerson;
	FirstPersonCamera->SetActive(!bThirdPerson);
	ThirdPersonCamera->SetActive(bThirdPerson);
	// the full body: hidden from the owner in first person (shadow only), drawn in third person
	GetMesh()->SetOwnerNoSee(!bThirdPerson);
	GetMesh()->FirstPersonPrimitiveType = bThirdPerson ? EFirstPersonPrimitiveType::None : EFirstPersonPrimitiveType::WorldSpaceRepresentation;
	GetMesh()->MarkRenderStateDirty();
	// aim and safety traces come from whichever camera is drawing
	Weapons->Initialize(bThirdPerson ? ThirdPersonCamera : FirstPersonCamera, WeaponMesh, WeaponStaticMesh);
	ApplyViewmodelVisibility(bScopedIn);
	RefreshThirdPersonWeapon();
	if (APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		PC->SetViewTarget(this);
	}
}

void ANVPlayerCharacter::ToggleViewPressed()
{
	if (!bInputLocked)
	{
		SetThirdPerson(!bThirdPerson);
	}
}

void ANVPlayerCharacter::HolsterPressed()
{
	if (!bInputLocked && !bVaulting)
	{
		Weapons->ToggleHolster();
	}
}

void ANVPlayerCharacter::NavGuidePressed()
{
	if (bInputLocked)
	{
		return;
	}
	if (!NavArrow)
	{
		FActorSpawnParameters P;
		P.Owner = this;
		P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		NavArrow = GetWorld()->SpawnActor<ANVNavArrow>(ANVNavArrow::StaticClass(), GetActorTransform(), P);
	}
	if (NavArrow)
	{
		NavArrow->Show(this);
	}
}


void ANVPlayerCharacter::ApplyViewmodelVisibility(bool bScoped)
{
	const bool bHide = bScoped || bThirdPerson;
	bViewmodelHidden = bHide;
	WeaponMesh->SetHiddenInGame(bHide);
	WeaponStaticMesh->SetHiddenInGame(bHide);
	UpdateArmsVisibility();
}

void ANVPlayerCharacter::UpdateArmsVisibility()
{
	FirstPersonMesh->SetHiddenInGame(bViewmodelHidden || bArmsAdsHidden);
}

void ANVPlayerCharacter::RefreshThirdPersonWeapon()
{
	const UNVWeaponData* W = Weapons ? Weapons->GetCurrentWeapon() : nullptr;
	USkeletalMesh* Skel = W ? W->WeaponMesh.LoadSynchronous() : nullptr;
	UStaticMesh* Stat = (W && !Skel) ? W->WeaponStaticMesh.LoadSynchronous() : nullptr;
	ThirdPersonWeapon->SetSkeletalMesh(Skel);
	ThirdPersonWeaponStatic->SetStaticMesh(Stat);
	FTransform Grip = (W && !W->ThirdPersonGrip.Equals(FTransform::Identity)) ? W->ThirdPersonGrip : ThirdPersonWeaponOffset;
	if (DebugGripOverride.IsSet())
	{
		Grip = DebugGripOverride.GetValue();
	}
	for (USceneComponent* C : { static_cast<USceneComponent*>(ThirdPersonWeapon), static_cast<USceneComponent*>(ThirdPersonWeaponStatic) })
	{
		C->AttachToComponent(GetMesh(), FAttachmentTransformRules::KeepRelativeTransform, ThirdPersonWeaponSocket);
		C->SetRelativeTransform(Grip);
	}
	ThirdPersonWeapon->SetVisibility(bThirdPerson && Skel != nullptr);
	ThirdPersonWeaponStatic->SetVisibility(bThirdPerson && Stat != nullptr);

	if (UNVBodyAnimInstance* Body = GetBodyAnim())
	{
		Body->SetHold(W != nullptr, W ? W->HoldType : ENVWeaponHold::Rifle);
		FVector Left = W ? W->ThirdPersonLeftHand : FVector::ZeroVector;
		if (W && Left.IsNearlyZero() && W->HoldType == ENVWeaponHold::Rifle)
		{
			// Estimate a foregrip: along the longest axis of the mesh, ahead of the grip.
			FBox Box(ForceInit);
			if (Skel) { Box = Skel->GetBounds().GetBox(); }
			else if (Stat) { Box = Stat->GetBoundingBox(); }
			if (Box.IsValid)
			{
				const FVector Ext = Box.GetExtent();
				const FVector Ctr = Box.GetCenter();
				const int32 Axis = (Ext.X >= Ext.Y && Ext.X >= Ext.Z) ? 0 : (Ext.Y >= Ext.Z ? 1 : 2);
				FVector P = Ctr;
				// Muzzle end: the side of the long axis away from the grip (the mesh origin sits at/near the grip).
				const float Sign = (Ctr[Axis] >= 0.f) ? 1.f : -1.f;
				P[Axis] = Ctr[Axis] + Sign * Ext[Axis] * (DefaultForegripFraction * 2.f - 1.f);
				Left = P;
			}
		}
		if (DebugLeftOverride.IsSet())
		{
			Left = DebugLeftOverride.GetValue();
		}
		Body->SetWeaponGrip(Grip, Left);
	}
}

void ANVPlayerCharacter::HandleWeaponEquipped(UNVWeaponData* Weapon)
{
	GetWorldTimerManager().ClearTimer(ArmsReturnTimer);
	RefreshThirdPersonWeapon();
	if (UNVBodyAnimInstance* Body = GetBodyAnim(); Body && Weapon)
	{
		Body->PlayAction(UNVBodyAnimInstance::EAction::Equip);
	}
	UAnimationAsset* Idle = (ArmsMeshAsset && Weapon) ? Weapon->ArmsIdleAnim.LoadSynchronous() : nullptr;
	bFistArms = false;
	if (!Idle)
	{
		ArmsWeapon = nullptr;
		FirstPersonMesh->SetVisibility(false);
		WeaponMesh->AttachToComponent(ViewmodelRoot, FAttachmentTransformRules::KeepRelativeTransform);
		WeaponMesh->SetRelativeTransform(FTransform::Identity);
		WeaponStaticMesh->AttachToComponent(ViewmodelRoot, FAttachmentTransformRules::KeepRelativeTransform);
		WeaponStaticMesh->SetRelativeTransform(FTransform::Identity);
		return;
	}
	ArmsWeapon = Weapon;
	if (FirstPersonMesh->GetSkeletalMeshAsset() != ArmsMeshAsset)
	{
		FirstPersonMesh->SetSkeletalMesh(ArmsMeshAsset);
	}
	FirstPersonMesh->SetRelativeTransform(ArmsOffset);
	FirstPersonMesh->SetVisibility(true);
	WeaponMesh->AttachToComponent(FirstPersonMesh, FAttachmentTransformRules::KeepRelativeTransform, Weapon->ArmsWeaponBone);
	WeaponMesh->SetRelativeTransform(Weapon->ArmsWeaponOffset);
	WeaponStaticMesh->AttachToComponent(FirstPersonMesh, FAttachmentTransformRules::KeepRelativeTransform, Weapon->ArmsWeaponBone);
	WeaponStaticMesh->SetRelativeTransform(Weapon->ArmsWeaponOffset);
	if (UAnimationAsset* Draw = Weapon->ArmsDrawAnim.LoadSynchronous())
	{
		PlayArms(Draw, false);
	}
	else
	{
		PlayArms(Idle, true);
	}
}

void ANVPlayerCharacter::HandleReloadState(bool bReloading)
{
	if (UNVBodyAnimInstance* Body = GetBodyAnim(); Body && bReloading)
	{
		const UNVWeaponData* W = Weapons->GetCurrentWeapon();
		Body->PlayAction(UNVBodyAnimInstance::EAction::Reload, W ? W->ReloadTime : 0.f);
	}
	if (!ArmsWeapon)
	{
		return;
	}
	if (bReloading)
	{
		if (UAnimationAsset* Reload = ArmsWeapon->ArmsReloadAnim.LoadSynchronous())
		{
			const UAnimSequenceBase* Seq = Cast<UAnimSequenceBase>(Reload);
			const float Len = Seq ? Seq->GetPlayLength() : 0.f;
			const float Rate = (Len > 0.f && ArmsWeapon->ReloadTime > 0.f) ? Len / ArmsWeapon->ReloadTime : 1.f;
			PlayArms(Reload, false, Rate);
		}
	}
	else
	{
		ReturnArmsToIdle();
	}
}

void ANVPlayerCharacter::PlayArms(UAnimationAsset* Anim, bool bLoop, float Rate)
{
	if (!Anim)
	{
		return;
	}
	GetWorldTimerManager().ClearTimer(ArmsReturnTimer);
	FirstPersonMesh->PlayAnimation(Anim, bLoop);
	FirstPersonMesh->SetPlayRate(Rate);
	if (!bLoop)
	{
		const UAnimSequenceBase* Seq = Cast<UAnimSequenceBase>(Anim);
		const float Len = Seq ? Seq->GetPlayLength() / FMath::Max(Rate, 0.01f) : 0.f;
		if (Len > 0.f)
		{
			GetWorldTimerManager().SetTimer(ArmsReturnTimer, this, &ANVPlayerCharacter::ReturnArmsToIdle, Len, false);
		}
	}
}

void ANVPlayerCharacter::ReturnArmsToIdle()
{
	if (bFistArms && !ArmsWeapon)
	{
		bFistArms = false;
		FirstPersonMesh->SetVisibility(false);
		return;
	}
	if (ArmsWeapon && !Weapons->IsReloading())
	{
		PlayArms(ArmsWeapon->ArmsIdleAnim.LoadSynchronous(), true);
	}
}

void ANVPlayerCharacter::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	if (BodyMeshAsset)
	{
		GetMesh()->SetSkeletalMesh(BodyMeshAsset);
	}
	ApplyBodyAnimClass();
}

void ANVPlayerCharacter::ApplyBodyAnimClass()
{
	if (!BodyMaterial)
	{
		BodyMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/NeonVeil/Characters/Ghost7/MI_NV_Ghost7.MI_NV_Ghost7"));
	}
	if (BodyMaterial && GetMesh()->GetSkeletalMeshAsset())
	{
		for (int32 i = 0; i < GetMesh()->GetNumMaterials(); ++i)
		{
			GetMesh()->SetMaterial(i, BodyMaterial);
		}
	}
	UClass* Want = bNativeBodyAnim ? UNVBodyAnimInstance::StaticClass() : BodyAnimClass.Get();
	if (Want && GetMesh()->GetAnimClass() != Want)
	{
		GetMesh()->SetAnimInstanceClass(Want);
	}
}

UNVBodyAnimInstance* ANVPlayerCharacter::GetBodyAnim() const
{
	return GetMesh() ? Cast<UNVBodyAnimInstance>(GetMesh()->GetAnimInstance()) : nullptr;
}

void ANVPlayerCharacter::HandleMeleeSwing()
{
	if (UNVBodyAnimInstance* Body = GetBodyAnim())
	{
		Body->PlayAction(UNVBodyAnimInstance::EAction::Attack);
	}
	if (Melee->GetSwingStyle() == ENVMeleeStyle::Fist)
	{
		ShowFistArms();
	}
}

void ANVPlayerCharacter::ShowFistArms()
{
	// Unarmed: bring the arms in just for the punch, then put them away again.
	UAnimationAsset* Punch = ArmsMeshAsset ? FistPunchAnim.LoadSynchronous() : nullptr;
	if (!Punch || ArmsWeapon)
	{
		return;
	}
	if (FirstPersonMesh->GetSkeletalMeshAsset() != ArmsMeshAsset)
	{
		FirstPersonMesh->SetSkeletalMesh(ArmsMeshAsset);
	}
	FirstPersonMesh->SetRelativeTransform(ArmsOffset);
	ViewmodelRoot->SetRelativeLocation(FistViewmodelOffset);
	ViewmodelRoot->SetRelativeRotation(FRotator::ZeroRotator);
	ViewmodelRoot->SetRelativeScale3D(FVector::OneVector);
	bFistArms = true;
	FirstPersonMesh->SetVisibility(true);
	UpdateArmsVisibility();
	PlayArms(Punch, false, FistPunchRate);
}

void ANVPlayerCharacter::DebugSetGrip(const FTransform& Grip, const FVector& LeftHand)
{
	DebugGripOverride = Grip;
	DebugLeftOverride = LeftHand;
	RefreshThirdPersonWeapon();
}

FString ANVPlayerCharacter::DebugDescribeBody() const
{
	FString Out;
	if (const UNVBodyAnimInstance* Body = GetBodyAnim())
	{
		Out += Body->DescribeSets();
	}
	else
	{
		Out += FString::Printf(TEXT("body anim: %s"), GetMesh()->GetAnimInstance() ? *GetMesh()->GetAnimInstance()->GetClass()->GetName() : TEXT("none"));
	}
	const USceneComponent* Wc = ThirdPersonWeapon->GetSkeletalMeshAsset() ? static_cast<const USceneComponent*>(ThirdPersonWeapon) : static_cast<const USceneComponent*>(ThirdPersonWeaponStatic);
	Out += FString::Printf(TEXT("\ngrip rel: %s"), *Wc->GetRelativeTransform().ToString());
	const FTransform HandR = GetMesh()->GetSocketTransform(TEXT("hand_r"));
	const FTransform HandL = GetMesh()->GetSocketTransform(TEXT("hand_l"));
	Out += FString::Printf(TEXT("\nhand_r %s  hand_l %s  dist %.1f"), *HandR.GetLocation().ToString(), *HandL.GetLocation().ToString(), FVector::Dist(HandR.GetLocation(), HandL.GetLocation()));
	// First-person arms reference: how the KINEMATION rig holds this weapon (same Manny hand bones).
	if (FirstPersonMesh && FirstPersonMesh->GetSkeletalMeshAsset() && ArmsWeapon)
	{
		const USceneComponent* Fw = WeaponMesh->GetSkeletalMeshAsset() ? static_cast<const USceneComponent*>(WeaponMesh) : static_cast<const USceneComponent*>(WeaponStaticMesh);
		const FTransform W = Fw->GetComponentTransform();
		const FTransform R = FirstPersonMesh->GetSocketTransform(TEXT("hand_r"));
		const FTransform L = FirstPersonMesh->GetSocketTransform(TEXT("hand_l"));
		FTransform Rel = W.GetRelativeTransform(R);
		Out += FString::Printf(TEXT("\nFP %s: grip loc %s rot %s scale %s | left (weapon space) %s | weapon scale %s"),
			*ArmsWeapon->GetName(), *Rel.GetLocation().ToString(), *Rel.Rotator().ToString(), *Rel.GetScale3D().ToString(),
			*W.InverseTransformPosition(L.GetLocation()).ToString(), *W.GetScale3D().ToString());
	}
	return Out;
}

void ANVPlayerCharacter::HandleWeaponFired()
{
	Abilities->NotifyAttacked();
	if (UNVBodyAnimInstance* Body = GetBodyAnim())
	{
		Body->PlayAction(UNVBodyAnimInstance::EAction::Fire);
	}
	if (const UNVWeaponData* W = Weapons->GetCurrentWeapon())
	{
		ViewmodelKick = W->ViewmodelKickBack * FMath::Lerp(1.f, 0.5f, Weapons->GetAdsAlpha());
	}
	if (ArmsWeapon && !Weapons->IsReloading())
	{
		PlayArms(ArmsWeapon->ArmsFireAnim.LoadSynchronous(), false);
	}
}

void ANVPlayerCharacter::EnsureViewInput()
{
	// Fallbacks: the Blueprint defaults have lost these before, and the IMC asset may not carry their keys.
	if (!HolsterAction)
	{
		HolsterAction = LoadObject<UInputAction>(nullptr, TEXT("/Game/NeonVeil/Input/Actions/IA_NV_Holster.IA_NV_Holster"));
	}
	if (!ToggleViewAction)
	{
		ToggleViewAction = LoadObject<UInputAction>(nullptr, TEXT("/Game/NeonVeil/Input/Actions/IA_NV_ToggleView.IA_NV_ToggleView"));
	}
	if (!RuntimeViewContext)
	{
		RuntimeViewContext = NewObject<UInputMappingContext>(this, TEXT("IMC_NV_ViewRuntime"));
		if (HolsterAction)
		{
			RuntimeViewContext->MapKey(HolsterAction, EKeys::H);
		}
		if (ToggleViewAction)
		{
			RuntimeViewContext->MapKey(ToggleViewAction, EKeys::B);
			RuntimeViewContext->MapKey(ToggleViewAction, EKeys::Gamepad_Special_Left);
		}
	}
	// Wayfinding arrow: N on the keyboard, a tap on D-pad Down on the pad. Holding D-pad Down holsters instead.
	// (L3 stays sprint only.)
	if (!NavGuideAction)
	{
		NavGuideAction = NewObject<UInputAction>(this, TEXT("IA_NV_NavGuideRuntime"));
		NavGuideAction->ValueType = EInputActionValueType::Boolean;
		NavGuidePadAction = NewObject<UInputAction>(this, TEXT("IA_NV_NavGuidePadRuntime"));
		NavGuidePadAction->ValueType = EInputActionValueType::Boolean;
		HolsterPadAction = NewObject<UInputAction>(this, TEXT("IA_NV_HolsterPadRuntime"));
		HolsterPadAction->ValueType = EInputActionValueType::Boolean;
		if (RuntimeViewContext)
		{
			RuntimeViewContext->MapKey(NavGuideAction, EKeys::N);
			FEnhancedActionKeyMapping& Tap = RuntimeViewContext->MapKey(NavGuidePadAction, EKeys::Gamepad_DPad_Down);
			UInputTriggerTap* TapTrigger = NewObject<UInputTriggerTap>(RuntimeViewContext);
			TapTrigger->TapReleaseTimeThreshold = 0.35f;
			Tap.Triggers.Add(TapTrigger);
			FEnhancedActionKeyMapping& Hold = RuntimeViewContext->MapKey(HolsterPadAction, EKeys::Gamepad_DPad_Down);
			UInputTriggerHold* HoldTrigger = NewObject<UInputTriggerHold>(RuntimeViewContext);
			HoldTrigger->HoldTimeThreshold = 0.4f;
			HoldTrigger->bIsOneShot = true;
			Hold.Triggers.Add(HoldTrigger);
		}
	}
}

void ANVPlayerCharacter::PawnClientRestart()
{
	Super::PawnClientRestart();
	EnsureViewInput();

	if (const APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PC->GetLocalPlayer()))
		{
			int32 Priority = MappingContexts.Num();
			for (UInputMappingContext* Context : MappingContexts)
			{
				if (Context)
				{
					Subsystem->AddMappingContext(Context, Priority--);
				}
			}
			if (RuntimeViewContext)
			{
				Subsystem->AddMappingContext(RuntimeViewContext, MappingContexts.Num() + 1);
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
	if (MouseLookAction)
	{
		EIC->BindAction(MouseLookAction, ETriggerEvent::Triggered, this, &ANVPlayerCharacter::MouseLook);
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
	BindIf(MeleeAction, ETriggerEvent::Started, this, &ANVPlayerCharacter::MeleePressed);
	EnsureViewInput();
	BindIf(HolsterAction, ETriggerEvent::Started, this, &ANVPlayerCharacter::HolsterPressed);
	BindIf(ToggleViewAction, ETriggerEvent::Started, this, &ANVPlayerCharacter::ToggleViewPressed);
	BindIf(NavGuideAction, ETriggerEvent::Started, this, &ANVPlayerCharacter::NavGuidePressed);
	BindIf(NavGuidePadAction, ETriggerEvent::Triggered, this, &ANVPlayerCharacter::NavGuidePressed);
	BindIf(HolsterPadAction, ETriggerEvent::Triggered, this, &ANVPlayerCharacter::HolsterPressed);
	BindIf(Ability1Action, ETriggerEvent::Started, this, &ANVPlayerCharacter::Ability1Pressed);
	BindIf(Ability2Action, ETriggerEvent::Started, this, &ANVPlayerCharacter::Ability2Pressed);
	BindIf(Ability3Action, ETriggerEvent::Started, this, &ANVPlayerCharacter::Ability3Pressed);
}

void ANVPlayerCharacter::MeleePressed()
{
	if (bInputLocked || bVaulting)
	{
		return;
	}
	SetSprinting(false);
	Weapons->StopFire();
	const UNVWeaponData* W = Weapons->GetCurrentWeapon();
	Melee->Strike(!W ? ENVMeleeStyle::Fist : (W->bMelee ? ENVMeleeStyle::Baton : ENVMeleeStyle::GunBash));
}

void ANVPlayerCharacter::Ability1Pressed() { DebugAbility(0); }
void ANVPlayerCharacter::Ability2Pressed() { DebugAbility(1); }
void ANVPlayerCharacter::Ability3Pressed() { DebugAbility(2); }

void ANVPlayerCharacter::DebugAbility(int32 Slot)
{
	if (bInputLocked)
	{
		return;
	}
	Abilities->TryActivateSlot(Slot);
}

// ---------------------------------------------------------------- input handlers

void ANVPlayerCharacter::Move(const FInputActionValue& Value)
{
	LastMoveInput = Value.Get<FVector2D>();
	if (bInputLocked || bVaulting)
	{
		return;
	}
	if (IsSliding())
	{
		return; // committed slide: momentum only
	}
	AddMovementInput(GetActorForwardVector(), LastMoveInput.Y);
	AddMovementInput(GetActorRightVector(), LastMoveInput.X);
}

void ANVPlayerCharacter::Look(const FInputActionValue& Value)
{
	// Gamepad stick: rate-based, frame-rate independent, with a radial response curve so small deflections
	// give fine aim and full deflection still turns quickly. The IMC dead zone has already been applied.
	FVector2D Stick = Value.Get<FVector2D>();
	const float Mag = FMath::Min(Stick.Size(), 1.f);
	if (Mag <= KINDA_SMALL_NUMBER)
	{
		return;
	}
	Stick = Stick / Stick.Size() * FMath::Pow(Mag, GamepadLookExponent);
	Stick.Y *= GamepadPitchScale;
	float Rate = GamepadLookRate;
	if (Weapons && Weapons->GetCurrentWeapon())
	{
		Rate *= FMath::Lerp(1.f, GamepadAdsScale, Weapons->GetAdsAlpha());
	}
	ApplyLook(Stick * Rate * GetWorld()->GetDeltaSeconds());
}

void ANVPlayerCharacter::MouseLook(const FInputActionValue& Value)
{
	ApplyLook(Value.Get<FVector2D>());
}

void ANVPlayerCharacter::ApplyLook(FVector2D Axis)
{
	if (bInputLocked && !bLookAllowedWhileLocked)
	{
		return;
	}
	LookDeltaThisFrame += Axis;
	Axis *= LookSensitivity;
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
	UE_LOG(LogNeonVeil, Log, TEXT("Slide start at %.0f cm/s"), GetVelocity().Size2D());
	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->GroundFriction = 0.6f;
	Move->BrakingDecelerationWalking = 200.f;
	// Let the slide exceed the crouch speed cap; restored when the slide ends.
	Move->MaxWalkSpeedCrouched = SprintSpeed + SlideImpulse;
	// Keep current speed and add a short push in the travel direction. Velocity is set
	// directly (not LaunchCharacter) so the character stays grounded.
	const FVector Dir = GetVelocity().GetSafeNormal2D().IsNearlyZero() ? GetActorForwardVector() : GetVelocity().GetSafeNormal2D();
	Move->Velocity += Dir * SlideImpulse * 0.5f;
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
		Move->MaxWalkSpeedCrouched = CrouchSpeed;
		UE_LOG(LogNeonVeil, Log, TEXT("Slide end (%s)"), bTooSlow ? TEXT("slowed to crouch speed") : TEXT("timed out or left ground"));
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
		UE_LOG(LogNeonVeil, Log, TEXT("Vault: no obstacle within %.0f cm"), Radius + VaultReach);
		return false;
	}
	if (FMath::Abs(WallHit.ImpactNormal.Z) > 0.3f)
	{
		UE_LOG(LogNeonVeil, Log, TEXT("Vault: surface is a slope"));
		return false; // a slope, not a wall
	}

	// 2. Find the top surface just beyond the wall face.
	const FVector OverTop = WallHit.ImpactPoint + Fwd * 25.f;
	FHitResult TopHit;
	const FVector TopStart = FVector(OverTop.X, OverTop.Y, Feet.Z + VaultMaxHeight + 20.f);
	if (!GetWorld()->LineTraceSingleByChannel(TopHit, TopStart, FVector(OverTop.X, OverTop.Y, Feet.Z), ECC_Visibility, Params))
	{
		UE_LOG(LogNeonVeil, Log, TEXT("Vault: no top surface found"));
		return false;
	}
	const float LedgeHeight = TopHit.ImpactPoint.Z - Feet.Z;
	if (LedgeHeight < VaultMinHeight || LedgeHeight > VaultMaxHeight || TopHit.ImpactNormal.Z < 0.7f)
	{
		UE_LOG(LogNeonVeil, Log, TEXT("Vault: ledge %.0f cm outside %.0f-%.0f band"), LedgeHeight, VaultMinHeight, VaultMaxHeight);
		return false;
	}

	// 3. Room for the capsule above the ledge, and a landing spot beyond it.
	const FVector Apex = FVector(TopHit.ImpactPoint.X, TopHit.ImpactPoint.Y, TopHit.ImpactPoint.Z + HalfHeight + 4.f);
	const FCollisionShape Shape = FCollisionShape::MakeCapsule(Radius, HalfHeight);
	if (GetWorld()->OverlapBlockingTestByChannel(Apex, FQuat::Identity, ECC_Pawn, Shape, Params))
	{
		UE_LOG(LogNeonVeil, Log, TEXT("Vault: no headroom above ledge"));
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

	UE_LOG(LogNeonVeil, Log, TEXT("Vault: ledge %.0f cm, %s"), LedgeHeight, Land.Equals(Apex) ? TEXT("mantle onto top") : TEXT("vault over"));
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

	// Sprint widening is smoothed; ADS follows the weapon's own blend exactly so the
	// transition takes AdsTime (Bible §7: 0.15-0.25 s, no camera snap).
	SmoothedSprintFOV = FMath::FInterpTo(SmoothedSprintFOV, bSprinting ? SprintFOVBoost : 0.f, DeltaSeconds, 8.f);
	float FOV = BaseFOV + SmoothedSprintFOV;
	if (const UNVWeaponData* W = Weapons->GetCurrentWeapon())
	{
		const float A = Weapons->GetAdsAlpha();
		FOV = FMath::Lerp(FOV, W->AdsFOV, A * A * (3.f - 2.f * A)); // smoothstep: eases in and out
	}
	FirstPersonCamera->SetFieldOfView(FOV);
	ThirdPersonCamera->SetFieldOfView(FOV);
}

void ANVPlayerCharacter::SetDebugMoveInput(FVector2D Input, bool bSprint)
{
	DebugMoveInput = Input;
	bSprintHeld = bSprint;
	LastMoveInput = Input;
}

void ANVPlayerCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (!DebugMoveInput.IsNearlyZero() && !bVaulting && !IsSliding())
	{
		LastMoveInput = DebugMoveInput;
		AddMovementInput(GetActorForwardVector(), DebugMoveInput.Y);
		AddMovementInput(GetActorRightVector(), DebugMoveInput.X);
	}

	SetSprinting(CanSprint());
	TickSlide(DeltaSeconds);
	TickVault(DeltaSeconds);
	UpdateMoveSpeed();
	UpdateCamera(DeltaSeconds);
	UpdateViewmodel(DeltaSeconds);
}

void ANVPlayerCharacter::UpdateViewmodel(float DeltaSeconds)
{
	const UNVWeaponData* W = Weapons->GetCurrentWeapon();
	if (!W)
	{
		LookDeltaThisFrame = FVector2D::ZeroVector;
		if (bArmsAdsHidden)
		{
			bArmsAdsHidden = false;
			UpdateArmsVisibility();
		}
		if (bFistArms)
		{
			// a small forward lunge of the whole arms rig on top of the punch animation
			const float Swing = Melee->GetSwingAlpha();
			const float Lunge = FMath::Sin(FMath::Clamp(Swing * 2.2f, 0.f, 1.f) * PI);
			ViewmodelRoot->SetRelativeLocation(FistViewmodelOffset + FVector(4.f * Lunge, 0.f, 0.f));
		}
		return;
	}
	const float Ads = Weapons->GetAdsAlpha();
	FVector Offset = FMath::Lerp(W->ViewmodelHipOffset, W->ViewmodelAdsOffset, Ads);

	// Sway: viewmodel lags slightly behind look input; much less when aiming.
	const FVector2D TargetSway = LookDeltaThisFrame * ViewmodelSwayAmount * (1.f - 0.85f * Ads);
	SmoothedSway = FMath::Vector2DInterpTo(SmoothedSway, TargetSway, DeltaSeconds, 10.f);
	LookDeltaThisFrame = FVector2D::ZeroVector;
	Offset.Y -= FMath::Clamp(SmoothedSway.X, -2.5f, 2.5f);
	Offset.Z += FMath::Clamp(SmoothedSway.Y, -2.5f, 2.5f);

	// Gentle walk bob on the viewmodel only (camera stays steady; Bible §3).
	const float Speed = GetVelocity().Size2D();
	if (GetCharacterMovement()->IsMovingOnGround() && Speed > 10.f)
	{
		BobPhase += DeltaSeconds * Speed * 0.022f;
		const float Bob = ViewmodelBobAmount * (1.f - 0.8f * Ads) * FMath::Min(Speed / WalkSpeed, 1.5f);
		Offset.Z += FMath::Sin(BobPhase * 2.f) * Bob;
		Offset.Y += FMath::Cos(BobPhase) * Bob;
	}

	// Fire kick, recovering quickly.
	Offset.X -= ViewmodelKick;
	ViewmodelKick = FMath::FInterpTo(ViewmodelKick, 0.f, DeltaSeconds, 14.f);

	// Lower the weapon while sprinting or reloading. For arms-held weapons ViewmodelRotation is the hip convergence
	// (barrel toward the crosshair); it fades out as the sights come up so ADS is dead straight.
	FRotator Rot = ArmsWeapon ? W->ViewmodelRotation * (1.f - Ads) : W->ViewmodelRotation;
	if (bSprinting)
	{
		Rot.Pitch -= 12.f;
		Rot.Yaw += 10.f;
		Offset.Z -= 3.f;
	}
	if (Weapons->IsReloading() && !(ArmsWeapon && !ArmsWeapon->ArmsReloadAnim.IsNull()))
	{
		Rot.Roll -= 25.f;
		Offset.Z -= 4.f;
	}

	// Melee motion on the whole viewmodel (arms and weapon together).
	BatonMesh->SetHiddenInGame(true);
	FVector MeleeOff = FVector::ZeroVector;
	FRotator MeleeRot = FRotator::ZeroRotator;
	const float Swing = Melee->GetSwingAlpha();
	if (Swing > 0.f)
	{
		const ENVMeleeStyle Style = Melee->GetSwingStyle();
		if (Style == ENVMeleeStyle::Baton)
		{
			// Wind up (0-0.18), chop down and across (0.18-0.45), recover (0.45-1).
			const float Up = FMath::SmoothStep(0.f, 0.18f, Swing) * (1.f - FMath::SmoothStep(0.18f, 0.32f, Swing));
			const float Chop = FMath::SmoothStep(0.18f, 0.45f, Swing) * (1.f - FMath::SmoothStep(0.55f, 1.f, Swing));
			MeleeRot = BatonWindUpRot * Up + BatonChopRot * Chop;
			MeleeOff = BatonWindUpOffset * Up + BatonChopOffset * Chop;
		}
		else
		{
			// Butt-stroke / pistol-whip (and the baton's own Melee button press uses the chop above): draw back
			// (0-0.2), drive forward and across turning the gun on its side (0.2-0.4), then return.
			const float Back = FMath::SmoothStep(0.f, 0.2f, Swing) * (1.f - FMath::SmoothStep(0.2f, 0.3f, Swing));
			const float Drive = FMath::SmoothStep(0.2f, 0.4f, Swing) * (1.f - FMath::SmoothStep(0.5f, 1.f, Swing));
			MeleeRot = BashRot * Drive;
			MeleeOff = BashBackOffset * Back + BashOffset * Drive;
		}
	}

	// Near-plane clearance: aimed down the sights, the stock can come closer to the eye than the near clip plane and get
	// cut open. Measure the weapon's rearmost point in camera space (as rendered, after the first-person scale) and
	// push the viewmodel straight forward until it clears; moving along the view axis keeps the sights lined up.
	{
		const UPrimitiveComponent* Gun = nullptr;
		if (WeaponMesh && WeaponMesh->GetSkeletalMeshAsset() && WeaponMesh->IsVisible())
		{
			Gun = WeaponMesh;
		}
		else if (WeaponStaticMesh && WeaponStaticMesh->GetStaticMesh() && WeaponStaticMesh->IsVisible())
		{
			Gun = WeaponStaticMesh;
		}
		float Target = 0.f;
		if (Gun && !bThirdPerson)
		{
			const FBox Local = Gun->CalcBounds(FTransform::Identity).GetBox();
			const FTransform GunT = Gun->GetComponentTransform();
			const FTransform CamT = FirstPersonCamera->GetComponentTransform();
			float MinDepth = TNumericLimits<float>::Max();
			for (int32 i = 0; i < 8; ++i)
			{
				const FVector Corner((i & 1) ? Local.Max.X : Local.Min.X, (i & 2) ? Local.Max.Y : Local.Min.Y, (i & 4) ? Local.Max.Z : Local.Min.Z);
				MinDepth = FMath::Min(MinDepth, static_cast<float>(CamT.InverseTransformPosition(GunT.TransformPosition(Corner)).X));
			}
			const float FPScale = FirstPersonCamera->bEnableFirstPersonScale ? FMath::Max(FirstPersonCamera->FirstPersonScale, 0.05f) : 1.f;
			const float Desired = ViewmodelNearClearance / FPScale;
			// MinDepth already includes the current push, so this converges on exactly the push needed.
			Target = FMath::Clamp(NearClearPush + (Desired - MinDepth), 0.f, 40.f) * Ads;
		}
		NearClearPush = FMath::FInterpTo(NearClearPush, Target, DeltaSeconds, 18.f);
		Offset.X += NearClearPush;
	}

	// Aimed in, the rifle poses swing the upper arm/sleeve across the eye. Hide the arms while that's the case
	// (measured on the arm bones, with a little hysteresis); the weapon carries the sight picture on its own.
	{
		bool bHideArms = false;
		if (ArmsWeapon && !bThirdPerson && Ads > 0.35f && FirstPersonMesh->GetSkeletalMeshAsset())
		{
			const FTransform CamT = FirstPersonCamera->GetComponentTransform();
			float Nearest = TNumericLimits<float>::Max();
			for (const FName Bone : { FName(TEXT("upperarm_r")), FName(TEXT("upperarm_l")), FName(TEXT("lowerarm_r")) })
			{
				if (FirstPersonMesh->GetBoneIndex(Bone) != INDEX_NONE)
				{
					const FVector L = CamT.InverseTransformPosition(FirstPersonMesh->GetSocketLocation(Bone));
					Nearest = FMath::Min(Nearest, static_cast<float>(L.X));
				}
			}
			bHideArms = Nearest < (bArmsAdsHidden ? ArmsAdsHideDepth + 4.f : ArmsAdsHideDepth);
		}
		if (bHideArms != bArmsAdsHidden)
		{
			bArmsAdsHidden = bHideArms;
			UpdateArmsVisibility();
		}
	}

	// Melee motion goes on top of the smoothing so the strike keeps its snap.
	SmoothedViewmodelLoc = FMath::VInterpTo(SmoothedViewmodelLoc, Offset, DeltaSeconds, 25.f);
	SmoothedViewmodelRot = FMath::RInterpTo(SmoothedViewmodelRot, Rot, DeltaSeconds, 12.f);
	ViewmodelRoot->SetRelativeLocation(SmoothedViewmodelLoc + MeleeOff);
	ViewmodelRoot->SetRelativeRotation(SmoothedViewmodelRot + MeleeRot);
	ViewmodelRoot->SetRelativeScale3D(W->ViewmodelScale);

	// Scope: once the sights are up, hand over to the HUD's scope view.
	const bool bScoped = W->bScopeOverlay && Ads > 0.92f && !Weapons->IsReloading();
	if (bScoped != bScopedIn)
	{
		bScopedIn = bScoped;
		ApplyViewmodelVisibility(bScoped);
	}
}
