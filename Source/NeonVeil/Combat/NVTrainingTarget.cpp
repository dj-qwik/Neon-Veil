#include "Combat/NVTrainingTarget.h"
#include "Combat/NVHealthComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimSequence.h"
#include "Kismet/GameplayStatics.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "Sound/SoundBase.h"
#include "NeonVeil.h"

ANVTrainingTarget::ANVTrainingTarget()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = false;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	Body = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));
	Body->SetupAttachment(Root);
	Body->SetCollisionProfileName(TEXT("BlockAllDynamic"));

	WeakPoint = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WeakPoint"));
	WeakPoint->SetupAttachment(Body);
	WeakPoint->ComponentTags.Add(TEXT("WeakPoint"));
	WeakPoint->SetCollisionProfileName(TEXT("BlockAllDynamic"));

	ShieldMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ShieldMesh"));
	ShieldMesh->SetupAttachment(Body);
	ShieldMesh->SetCollisionProfileName(TEXT("NoCollision")); // the shield is visual; damage rules live in Health
	ShieldMesh->CastShadow = false;

	Health = CreateDefaultSubobject<UNVHealthComponent>(TEXT("Health"));
	Health->MaxHealth = 60.f;
}

void ANVTrainingTarget::BeginPlay()
{
	Super::BeginPlay();
	StartLocation = GetActorLocation();
	StartRotation = GetActorRotation();
	Health->OnHealthChanged.AddDynamic(this, &ANVTrainingTarget::HandleHealthChanged);
	Health->OnShieldBroken.AddDynamic(this, &ANVTrainingTarget::HandleShieldBroken);
	Health->OnDeath.AddDynamic(this, &ANVTrainingTarget::HandleDeath);

	ShieldMesh->SetVisibility(Health->MaxShield > 0.f);
	SetupFigure();

	if (bStartActive)
	{
		Activate();
	}
	else
	{
		SetTargetVisible(false);
	}
}

void ANVTrainingTarget::Activate()
{
	bActive = true;
	bCleared = false;
	SetTargetVisible(true);
	ShieldMesh->SetVisibility(Health->MaxShield > 0.f);
	StaggerTimeLeft = 0.f;
	SetActorTickEnabled(NeedsTick());
	BP_OnActivated();
}

void ANVTrainingTarget::ResetTarget()
{
	Health->ResetHealth();
	SetActorLocation(StartLocation);
	SetActorRotation(StartRotation);
	PatrolAlpha = 0.f;
	PatrolDir = 1.f;
	PatrolPauseLeft = 0.f;
	Activate();
}

void ANVTrainingTarget::Deactivate()
{
	bActive = false;
	SetActorTickEnabled(false);
	SetTargetVisible(false);
}

void ANVTrainingTarget::SetTargetVisible(bool bVisible)
{
	SetActorHiddenInGame(!bVisible);
	SetActorEnableCollision(bVisible);
}

void ANVTrainingTarget::SetupFigure()
{
	TArray<USceneComponent*> Comps;
	GetComponents<USceneComponent>(Comps);
	for (USceneComponent* C : Comps)
	{
		if (C->GetFName() == TEXT("Figure")) { HoloFigure = Cast<USkeletalMeshComponent>(C); }
		else if (C->GetFName() == TEXT("FigureGun")) { HoloGun = C; }
	}
	if (!HoloFigure || !HoloFigure->GetSkeletalMeshAsset() || !HoloFigure->IsVisible())
	{
		HoloFigure = nullptr;
		return;
	}
	FigureFacingYaw = FigureYaw = HoloFigure->GetRelativeRotation().Yaw;
	if (FigureWalkAnim && FigureWalkAnimSpeed <= 0.f)
	{
		const float L = FigureWalkAnim->GetPlayLength();
		const float Measured = L > 0.f ? FigureWalkAnim->ExtractRootMotionFromRange(0.0, L, FAnimExtractContext()).GetTranslation().Size2D() / L : 0.f;
		FigureWalkAnimSpeed = Measured > 30.f ? Measured : 160.f;
	}
	HoloFigure->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	PlayFigureAnim(FigureIdleAnim, 1.f);
	if (HoloGun && FigureGunSocket != NAME_None)
	{
		if (FigureGunGrip.Equals(FTransform::Identity))
		{
			// The rifle was placed against the idle pose in the editor: evaluate that pose now and keep the rifle where it is,
			// riding the hand from here on (so it follows the walk cycle).
			HoloFigure->TickAnimation(0.f, false);
			HoloFigure->RefreshBoneTransforms();
			HoloGun->AttachToComponent(HoloFigure, FAttachmentTransformRules::KeepWorldTransform, FigureGunSocket);
		}
		else
		{
			HoloGun->AttachToComponent(HoloFigure, FAttachmentTransformRules::SnapToTargetNotIncludingScale, FigureGunSocket);
			HoloGun->SetRelativeTransform(FigureGunGrip);
		}
	}
}

void ANVTrainingTarget::PlayFigureAnim(UAnimSequence* Anim, float Rate)
{
	if (!HoloFigure || !Anim)
	{
		return;
	}
	if (FigureCurrentAnim != Anim)
	{
		FigureCurrentAnim = Anim;
		HoloFigure->PlayAnimation(Anim, true);
	}
	HoloFigure->SetPlayRate(Rate);
}

void ANVTrainingTarget::UpdateFigure(float DeltaSeconds, const FVector& Velocity)
{
	if (!HoloFigure)
	{
		return;
	}
	const bool bWalking = !Velocity.IsNearlyZero() && FigureWalkAnim;
	float TargetYaw = FigureFacingYaw;
	if (bWalking)
	{
		// Walk loops move along the mesh's own forward; turn that to the travel direction (relative to the actor).
		const float TravelYaw = Velocity.Rotation().Yaw - GetActorRotation().Yaw;
		TargetYaw = FigureMeshForwardYaw + TravelYaw;
		PlayFigureAnim(FigureWalkAnim, FMath::Clamp(Velocity.Size() / FMath::Max(FigureWalkAnimSpeed, 1.f), 0.5f, 2.f));
	}
	else
	{
		PlayFigureAnim(FigureIdleAnim, 1.f);
	}
	const float Diff = FMath::FindDeltaAngleDegrees(FigureYaw, TargetYaw);
	FigureYaw += FMath::Clamp(Diff, -FigureTurnRate * DeltaSeconds, FigureTurnRate * DeltaSeconds);
	HoloFigure->SetRelativeRotation(FRotator(0.f, FigureYaw, 0.f));
	if (WeakPoint)
	{
		WeakPoint->SetWorldLocation(HoloFigure->GetSocketLocation(FigureHeadBone) + FVector(0.f, 0.f, HeadCentreUp));
	}
}

bool ANVTrainingTarget::NeedsTick() const
{
	return !PatrolOffset.IsNearlyZero() || BobAmplitude > 0.f || StaggerTimeLeft > 0.f;
}

void ANVTrainingTarget::ApplyStagger(float Duration, AActor* StaggerInstigator)
{
	if (!bActive || bCleared)
	{
		return;
	}
	StaggerTimeLeft = Duration;
	// Readable reaction until real hit-reaction animation exists: knock the target back 14 degrees.
	SetActorRotation(StartRotation + FRotator(-14.f, 0.f, 0.f));
	SetActorTickEnabled(true);
	UE_LOG(LogNeonVeil, Log, TEXT("%s staggered for %.1f s"), *GetName(), Duration);
}

void ANVTrainingTarget::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!bActive || bCleared)
	{
		return;
	}
	Age += DeltaSeconds;
	if (StaggerTimeLeft > 0.f)
	{
		StaggerTimeLeft -= DeltaSeconds;
		if (StaggerTimeLeft <= 0.f)
		{
			StaggerTimeLeft = 0.f;
			SetActorRotation(StartRotation);
			SetActorTickEnabled(NeedsTick());
		}
		return; // a staggered target holds still
	}
	FVector Offset = FVector::ZeroVector;
	const float Length = PatrolOffset.Size();
	FVector Velocity = FVector::ZeroVector;
	if (HoloFigure && Length > KINDA_SMALL_NUMBER)
	{
		// Walking combatant: constant pace, stand and face the lane at each end, then turn back.
		const FVector LegWorld = GetActorTransform().TransformVectorNoScale(PatrolOffset);
		if (PatrolPauseLeft > 0.f)
		{
			PatrolPauseLeft -= DeltaSeconds;
		}
		else
		{
			PatrolAlpha += PatrolDir * (FigureWalkSpeed / Length) * DeltaSeconds;
			if (PatrolAlpha >= 1.f || PatrolAlpha <= 0.f)
			{
				PatrolAlpha = FMath::Clamp(PatrolAlpha, 0.f, 1.f);
				PatrolDir *= -1.f;
				PatrolPauseLeft = PatrolEndPause;
			}
			else
			{
				Velocity = LegWorld.GetSafeNormal() * PatrolDir * FigureWalkSpeed;
			}
		}
		Offset = LegWorld * PatrolAlpha;
		UpdateFigure(DeltaSeconds, Velocity);
	}
	else if (Length > KINDA_SMALL_NUMBER)
	{
		PatrolAlpha += PatrolDir * (PatrolSpeed / Length) * DeltaSeconds;
		if (PatrolAlpha >= 1.f || PatrolAlpha <= 0.f)
		{
			PatrolAlpha = FMath::Clamp(PatrolAlpha, 0.f, 1.f);
			PatrolDir *= -1.f;
		}
		// Smooth turnarounds so motion reads as a mechanical track, not a ping-pong.
		const float Eased = FMath::InterpEaseInOut(0.f, 1.f, PatrolAlpha, 1.6f);
		Offset = GetActorTransform().TransformVectorNoScale(PatrolOffset) * Eased;
	}
	if (BobAmplitude > 0.f)
	{
		Offset.Z += FMath::Sin(Age * BobSpeed) * BobAmplitude;
	}
	SetActorLocation(StartLocation + Offset);
}

void ANVTrainingTarget::HandleHealthChanged(UNVHealthComponent* HealthComp, float NewHealth, float Delta, AActor* InstigatorActor, FGameplayTag DamageType)
{
	if (Delta < 0.f)
	{
		BP_OnHit(false);
	}
}

void ANVTrainingTarget::HandleShieldBroken(UNVHealthComponent* HealthComp)
{
	ShieldMesh->SetVisibility(false);
	if (ShieldBreakSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, ShieldBreakSound, GetActorLocation());
	}
	if (ShieldBreakEffect)
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, ShieldBreakEffect, ShieldMesh->GetComponentLocation());
	}
	BP_OnShieldBroken();
}

void ANVTrainingTarget::HandleDeath(UNVHealthComponent* HealthComp, AActor* Killer)
{
	if (bCleared)
	{
		return;
	}
	bCleared = true;
	bActive = false;
	SetActorTickEnabled(false);
	if (ClearedSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, ClearedSound, GetActorLocation());
	}
	if (ClearedEffect)
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, ClearedEffect, Body->GetComponentLocation());
	}
	BP_OnCleared();
	SetTargetVisible(false);
	OnTargetCleared.Broadcast(this);
}
