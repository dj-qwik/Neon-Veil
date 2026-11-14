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
#include "ChaosClothAsset/ClothComponent.h"
#include "ChaosClothAsset/ClothAssetBase.h"
#include "Materials/MaterialInterface.h"

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

	for (int32 i = 0; i < MaxGarments; ++i)
	{
		UChaosClothComponent* G = CreateDefaultSubobject<UChaosClothComponent>(*FString::Printf(TEXT("Garment%d"), i));
		G->SetupAttachment(GetMesh());
		G->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		G->SetGenerateOverlapEvents(false);
		G->SetCanEverAffectNavigation(false);
		G->bUseBoundsFromLeaderPoseComponent = true;
		GarmentComponents.Add(G);
	}

	AIControllerClass = ANVEnemyController::StaticClass();
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;

	bUseControllerRotationYaw = false;
	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->bOrientRotationToMovement = true;
	Move->RotationRate = FRotator(0.f, 150.f, 0.f);
	Move->MaxWalkSpeed = WalkSpeed;
	Move->bUseControllerDesiredRotation = false;
	// Natural gait: ease into and out of walking and carve corners instead of snapping at path points.
	Move->GetNavMovementProperties()->bUseAccelerationForPaths = true;
	Move->MaxAcceleration = 380.f;
	Move->BrakingDecelerationWalking = 260.f;
	Move->GroundFriction = 6.f;
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
		Part->EmptyOverrideMaterials();
		if (PartMesh && OutfitMaterials.IsValidIndex(i) && OutfitMaterials[i])
		{
			for (int32 Slot = 0; Slot < Part->GetNumMaterials(); ++Slot)
			{
				Part->SetMaterial(Slot, OutfitMaterials[i]);
			}
		}
	}

	for (int32 i = 0; i < GarmentComponents.Num(); ++i)
	{
		UChaosClothComponent* G = GarmentComponents[i];
		UChaosClothAssetBase* A = Garments.IsValidIndex(i) ? Garments[i].Get() : nullptr;
		G->SetAsset(A);
		G->SetVisibility(A != nullptr);
		G->EmptyOverrideMaterials();
		if (A && GarmentMaterials.IsValidIndex(i) && GarmentMaterials[i])
		{
			for (int32 Slot = 0; Slot < G->GetNumMaterials(); ++Slot)
			{
				G->SetMaterial(Slot, GarmentMaterials[i]);
			}
		}
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
		ApplyGarments(Base);
		const bool bHide = bHideBodyUnderOutfit && OutfitParts.Num() > 0;
		Base->SetVisibility(!bHide, false);
		if (bHide)
		{
			Base->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
		}
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
	ApplyGarments(Body ? Body : Base);
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

void ANVGuardCharacter::ApplyGarments(USkeletalMeshComponent* Host)
{
	// Pose always comes from our animated base mesh (leader chains are not supported); placement from the host.
	USkeletalMeshComponent* Leader = GetMesh();
	for (UChaosClothComponent* G : GarmentComponents)
	{
		if (!G || !G->GetAsset())
		{
			continue;
		}
		// Ride on the visible body so garments match its shape and placement exactly.
		if (G->GetAttachParent() != Host)
		{
			G->AttachToComponent(Host, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
		}
		// Crowd garments are fitted to bodies with hidden-under-cloth faces; ours show the full body, so
		// loosen the fit a touch to stop skin poking through.
		G->SetRelativeTransform(FTransform(FQuat::Identity, FVector::ZeroVector, FVector(1.04f, 1.04f, 1.01f)));
		G->SetLeaderPoseComponent(Leader, true);
		G->SetEnableSimulation(bSimulateGarments);
		G->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
	}
}

void ANVGuardCharacter::BeginPlay()
{
	Super::BeginPlay();
	BindAppearance();
	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->MaxWalkSpeed = WalkSpeed;
	Move->GetNavMovementProperties()->bUseAccelerationForPaths = true;
	Move->MaxAcceleration = 380.f;
	Move->BrakingDecelerationWalking = 260.f;
	Move->RotationRate = FRotator(0.f, 150.f, 0.f);
}
