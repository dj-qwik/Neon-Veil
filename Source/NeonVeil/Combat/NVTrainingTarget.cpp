#include "Combat/NVTrainingTarget.h"
#include "Combat/NVHealthComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Kismet/GameplayStatics.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "Sound/SoundBase.h"

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
	Health->OnHealthChanged.AddDynamic(this, &ANVTrainingTarget::HandleHealthChanged);
	Health->OnShieldBroken.AddDynamic(this, &ANVTrainingTarget::HandleShieldBroken);
	Health->OnDeath.AddDynamic(this, &ANVTrainingTarget::HandleDeath);

	ShieldMesh->SetVisibility(Health->MaxShield > 0.f);

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
	SetActorTickEnabled(!PatrolOffset.IsNearlyZero());
	BP_OnActivated();
}

void ANVTrainingTarget::ResetTarget()
{
	Health->ResetHealth();
	SetActorLocation(StartLocation);
	PatrolAlpha = 0.f;
	PatrolDir = 1.f;
	Activate();
}

void ANVTrainingTarget::SetTargetVisible(bool bVisible)
{
	SetActorHiddenInGame(!bVisible);
	SetActorEnableCollision(bVisible);
}

void ANVTrainingTarget::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!bActive || bCleared)
	{
		return;
	}
	const float Length = PatrolOffset.Size();
	if (Length <= KINDA_SMALL_NUMBER)
	{
		return;
	}
	PatrolAlpha += PatrolDir * (PatrolSpeed / Length) * DeltaSeconds;
	if (PatrolAlpha >= 1.f || PatrolAlpha <= 0.f)
	{
		PatrolAlpha = FMath::Clamp(PatrolAlpha, 0.f, 1.f);
		PatrolDir *= -1.f;
	}
	// Smooth turnarounds so motion reads as a mechanical track, not a ping-pong.
	const float Eased = FMath::InterpEaseInOut(0.f, 1.f, PatrolAlpha, 1.6f);
	const FVector WorldOffset = GetActorTransform().TransformVectorNoScale(PatrolOffset);
	SetActorLocation(StartLocation + WorldOffset * Eased);
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
