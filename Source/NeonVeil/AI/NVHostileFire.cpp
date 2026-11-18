#include "AI/NVHostileFire.h"
#include "Abilities/NVAbilityComponent.h"
#include "Combat/NVHealthComponent.h"
#include "Core/NVGameplayTags.h"

#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "Kismet/GameplayStatics.h"
#include "NiagaraFunctionLibrary.h"
#include "UObject/ConstructorHelpers.h"

UNVHostileFire::UNVHostileFire()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = false;
}

void UNVHostileFire::BeginPlay()
{
	Super::BeginPlay();
	if (!DamageType.IsValid())
	{
		DamageType = NVTags::Damage_Ballistic;
	}
	UStaticMesh* Cyl = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	for (int32 i = 0; i < 4; ++i)
	{
		UStaticMeshComponent* T = NewObject<UStaticMeshComponent>(GetOwner());
		T->SetStaticMesh(Cyl);
		T->SetUsingAbsoluteLocation(true);
		T->SetUsingAbsoluteRotation(true);
		T->SetUsingAbsoluteScale(true);
		T->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		T->CastShadow = false;
		T->SetHiddenInGame(true);
		if (TracerMaterial)
		{
			T->SetMaterial(0, TracerMaterial);
		}
		T->SetupAttachment(this);
		T->RegisterComponent();
		Tracers.Add(T);
		TracerTime.Add(0.f);
	}
}

FVector UNVHostileFire::AimPointOn(const AActor* Target)
{
	if (!Target)
	{
		return FVector::ZeroVector;
	}
	FVector P = Target->GetActorLocation();
	if (const ACharacter* C = Cast<ACharacter>(Target))
	{
		P.Z += FMath::FRandRange(-0.4f, 0.8f) * C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	}
	return P;
}

bool UNVHostileFire::CanSee(const UWorld* World, const AActor* Self, const FVector& From, const AActor* Target)
{
	if (!World || !Target || UNVAbilityComponent::IsActorCloaked(Target))
	{
		return false;
	}
	FVector To = Target->GetActorLocation();
	if (const ACharacter* C = Cast<ACharacter>(Target))
	{
		To.Z += C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() * 0.7f;
	}
	FCollisionQueryParams Params(SCENE_QUERY_STAT(NVHostileSight), false, Self);
	FHitResult Hit;
	if (!World->LineTraceSingleByChannel(Hit, From, To, ECC_Visibility, Params))
	{
		return true;
	}
	return Hit.GetActor() == Target;
}

bool UNVHostileFire::Fire(AActor* Target, const FVector& AimPoint)
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return false;
	}
	// respawn protection: hold fire on a target that can't be hurt yet instead of burying it in tracers
	if (Target)
	{
		if (const UNVHealthComponent* TH = Target->FindComponentByClass<UNVHealthComponent>(); TH && TH->IsInvulnerable())
		{
			return false;
		}
	}
	const FVector Start = GetComponentLocation();
	const FVector Dir = FMath::VRandCone((AimPoint - Start).GetSafeNormal(), FMath::DegreesToRadians(SpreadDeg));
	const FVector End = Start + Dir * Range;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(NVHostileShot), false, GetOwner());
	FHitResult Hit;
	const bool bHit = World->LineTraceSingleByChannel(Hit, Start, End, ECC_Pawn, Params);
	const FVector Impact = bHit ? Hit.ImpactPoint : End;
	bool bLanded = false;
	if (bHit && Hit.GetActor())
	{
		// friendly fire between enemies is ignored; anything with health that is the target takes the hit
		if (Hit.GetActor() == Target)
		{
			if (UNVHealthComponent* H = Target->FindComponentByClass<UNVHealthComponent>())
			{
				H->ApplyDamage(Damage, GetOwner(), DamageType, false);
				bLanded = true;
			}
		}
		else if (ImpactFX)
		{
			UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, ImpactFX, Impact, Hit.ImpactNormal.Rotation(), FVector(0.4f));
		}
	}
	if (ShotSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, ShotSound, Start, ShotVolume, FMath::FRandRange(0.93f, 1.07f));
	}
	if (Tracers.Num() > 0)
	{
		UStaticMeshComponent* T = Tracers[NextTracer];
		const float Len = FVector::Dist(Start, Impact);
		T->SetWorldLocation((Start + Impact) * 0.5f);
		T->SetWorldRotation(FRotationMatrix::MakeFromZ(Impact - Start).Rotator());
		T->SetWorldScale3D(FVector(TracerThickness, TracerThickness, Len / 100.f));
		T->SetHiddenInGame(false);
		TracerTime[NextTracer] = TracerLife;
		NextTracer = (NextTracer + 1) % Tracers.Num();
		SetComponentTickEnabled(true);
	}
	return bLanded;
}

void UNVHostileFire::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	bool bAny = false;
	for (int32 i = 0; i < Tracers.Num(); ++i)
	{
		if (TracerTime[i] > 0.f)
		{
			TracerTime[i] -= DeltaTime;
			if (TracerTime[i] <= 0.f)
			{
				Tracers[i]->SetHiddenInGame(true);
			}
			else
			{
				bAny = true;
			}
		}
	}
	if (!bAny)
	{
		SetComponentTickEnabled(false);
	}
}
