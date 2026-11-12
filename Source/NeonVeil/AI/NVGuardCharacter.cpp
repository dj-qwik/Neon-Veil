#include "AI/NVGuardCharacter.h"
#include "Combat/NVFriendly.h"
#include "AI/NVEnemyController.h"
#include "Combat/NVHealthComponent.h"

#include "Animation/AnimInstance.h"
#include "Components/CapsuleComponent.h"
#include "Components/ChildActorComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
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

	BatteryPack = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BatteryPack"));
	BatteryPack->SetupAttachment(GetMesh());
	BatteryPack->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	BatteryPack->SetGenerateOverlapEvents(false);
	BatteryPack->SetCanEverAffectNavigation(false);

	Appearance = CreateDefaultSubobject<UChildActorComponent>(TEXT("Appearance"));
	Appearance->SetupAttachment(GetCapsuleComponent());

	Helmet = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Helmet"));
	Helmet->SetupAttachment(GetMesh(), HelmetSocket);
	Helmet->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Helmet->SetGenerateOverlapEvents(false);
	Helmet->SetCanEverAffectNavigation(false);

	for (int32 i = 0; i < MaxOutfitParts; ++i)
	{
		USkeletalMeshComponent* Part = CreateDefaultSubobject<USkeletalMeshComponent>(*FString::Printf(TEXT("OutfitPart%d"), i));
		Part->SetupAttachment(GetMesh());
		Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Part->SetGenerateOverlapEvents(false);
		Part->SetCanEverAffectNavigation(false);
		Part->bUseBoundsFromLeaderPoseComponent = true;
		OutfitComponents.Add(Part);
	}

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
	for (int32 i = 0; i < OutfitComponents.Num(); ++i)
	{
		USkeletalMeshComponent* Part = OutfitComponents[i];
		USkeletalMesh* PartMesh = OutfitParts.IsValidIndex(i) ? OutfitParts[i].Get() : nullptr;
		Part->SetSkeletalMeshAsset(PartMesh);
		Part->SetVisibility(PartMesh != nullptr);
		Part->SetLeaderPoseComponent(PartMesh ? GetMesh() : nullptr);
	}

	if (Appearance->GetChildActorClass() != AppearanceClass)
	{
		Appearance->SetChildActorClass(AppearanceClass);
	}
	Appearance->SetRelativeTransform(AppearanceOffset);
	BindAppearance();

	Helmet->SetStaticMesh(HelmetMeshAsset);
	Helmet->SetVisibility(HelmetMeshAsset != nullptr);
	Helmet->AttachToComponent(GetMesh(), FAttachmentTransformRules::KeepRelativeTransform, HelmetSocket);
	Helmet->SetRelativeTransform(HelmetOffset);

	BatteryPack->SetStaticMesh(BatteryMeshAsset);
	BatteryPack->SetVisibility(BatteryMeshAsset != nullptr);
	BatteryPack->AttachToComponent(GetMesh(), FAttachmentTransformRules::KeepRelativeTransform, BatterySocket);
	BatteryPack->SetRelativeTransform(BatteryOffset);
}

void ANVGuardCharacter::PostInitializeComponents()
{
	// The AI controller is spawned and possesses inside Super, so the route must exist first.
	WorldPatrol.Reset();
	for (const FVector& P : PatrolPoints)
	{
		WorldPatrol.Add(GetActorTransform().TransformPosition(P));
	}
	if (bNonHostile)
	{
		Tags.AddUnique(NVFriendly::Tag);
	}
	Super::PostInitializeComponents();
}

void ANVGuardCharacter::BindAppearance()
{
	AActor* Look = Appearance ? Appearance->GetChildActor() : nullptr;
	USkeletalMeshComponent* Base = GetMesh();
	if (!Look)
	{
		Base->SetVisibility(true, false);
		return;
	}
	// The base mesh still drives locomotion; keep its pose updating while hidden.
	Base->SetVisibility(false, false);
	Base->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;

	TArray<USkeletalMeshComponent*> Skins;
	Look->GetComponents<USkeletalMeshComponent>(Skins);
	USkeletalMeshComponent* Body = nullptr;
	for (USkeletalMeshComponent* S : Skins)
	{
		if (S->GetFName() == TEXT("Body"))
		{
			Body = S;
		}
	}
	if (Body)
	{
		Body->SetLeaderPoseComponent(Base, true);
		Body->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
	}
	for (USkeletalMeshComponent* S : Skins)
	{
		S->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		// Clothing pieces (anything not the face) follow the body's pose too.
		if (S != Body && Body && S->GetFName() != TEXT("Face") && !S->LeaderPoseComponent.IsValid())
		{
			S->SetLeaderPoseComponent(Body, true);
		}
	}
}

void ANVGuardCharacter::BeginPlay()
{
	Super::BeginPlay();
	BindAppearance();
	GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
}
