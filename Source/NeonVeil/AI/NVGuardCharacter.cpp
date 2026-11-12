#include "AI/NVGuardCharacter.h"
#include "AI/NVEnemyController.h"
#include "Combat/NVHealthComponent.h"

#include "Animation/AnimInstance.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/CharacterMovementComponent.h"

ANVGuardCharacter::ANVGuardCharacter(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	PrimaryActorTick.bCanEverTick = false;
	GetCapsuleComponent()->InitCapsuleSize(34.f, 92.f);
	GetMesh()->SetRelativeLocation(FVector(0.f, 0.f, -92.f));
	GetMesh()->SetRelativeRotation(FRotator(0.f, -90.f, 0.f));

	Health = CreateDefaultSubobject<UNVHealthComponent>(TEXT("Health"));

	AIControllerClass = ANVEnemyController::StaticClass();
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;

	bUseControllerRotationYaw = false;
	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->bOrientRotationToMovement = true;
	Move->RotationRate = FRotator(0.f, 240.f, 0.f);
	Move->MaxWalkSpeed = WalkSpeed;
	Move->bUseControllerDesiredRotation = false;
}

void ANVGuardCharacter::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	if (BodyMeshAsset)
	{
		GetMesh()->SetSkeletalMesh(BodyMeshAsset);
	}
	if (BodyAnimClass)
	{
		GetMesh()->SetAnimInstanceClass(BodyAnimClass);
	}
}

void ANVGuardCharacter::PostInitializeComponents()
{
	// The AI controller is spawned and possesses inside Super, so the route must exist first.
	WorldPatrol.Reset();
	for (const FVector& P : PatrolPoints)
	{
		WorldPatrol.Add(GetActorTransform().TransformPosition(P));
	}
	Super::PostInitializeComponents();
}

void ANVGuardCharacter::BeginPlay()
{
	Super::BeginPlay();
	GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
}
