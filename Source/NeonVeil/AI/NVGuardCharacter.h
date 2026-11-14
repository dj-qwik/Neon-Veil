#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "NVGuardCharacter.generated.h"

class UNVHealthComponent;
class USkeletalMesh;
class UAnimInstance;
class UStaticMesh;
class UStaticMeshComponent;
class USkeletalMeshComponent;
class UChildActorComponent;
class UChaosClothComponent;
class UChaosClothAssetBase;

/**
 * Agency guard (Bible §8). In M00 guards are non-hostile ambient security: they patrol, pause and
 * acknowledge Ghost-7. Combat behaviour (flank, suppress, retreat) arrives with M01 on the same
 * controller. Body: Waveforce mercenary restyled to the Directorate palette; the battery pack is the
 * Bible's "exposed battery pack" tell (weak point from M01).
 */
UCLASS(Blueprintable)
class NEONVEIL_API ANVGuardCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	ANVGuardCharacter(const FObjectInitializer& ObjectInitializer);

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void PostInitializeComponents() override;

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Guard")
	UNVHealthComponent* GetHealth() const { return Health; }

	/** Patrol route, relative to the actor's spawn point. Empty = stand post. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guard", meta = (MakeEditWidget = true))
	TArray<FVector> PatrolPoints;

	/** Seconds to pause at each point (random in range). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guard")
	FVector2D WaitTimeRange = FVector2D(2.f, 4.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guard")
	float WalkSpeed = 150.f;

	/** Turns to look at the player inside this radius (M00 acknowledgement). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guard")
	float GlanceRadius = 450.f;

	/** M00: never engages. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guard")
	bool bNonHostile = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guard|Body")
	TObjectPtr<USkeletalMesh> BodyMeshAsset;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guard|Body")
	TSubclassOf<UAnimInstance> BodyAnimClass;

	/**
	 * Optional assembled MetaHuman (BP_*) worn as the guard's look. The base mesh keeps animating (hidden) and the
	 * MetaHuman's "Body" follows it via leader pose; its face follows the body through its own post-process ABP.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guard|Body")
	TSubclassOf<AActor> AppearanceClass;

	/** Placement of the appearance actor relative to the capsule (feet at -half height). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guard|Body")
	FTransform AppearanceOffset = FTransform(FRotator::ZeroRotator, FVector(0.f, 0.f, -92.f));

	/** Extra skinned outfit pieces driven by the body's pose (leader pose). Up to MaxOutfitParts. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guard|Body")
	TArray<TObjectPtr<USkeletalMesh>> OutfitParts;

	/** Optional material per outfit piece (same index as OutfitParts), applied to every slot. Crowd-pack meshes ship without materials. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Appearance")
	TArray<TObjectPtr<UMaterialInterface>> OutfitMaterials;

	static constexpr int32 MaxOutfitParts = 6;

	/** Garments (Chaos cloth assets, e.g. the MetaHuman crowd wardrobe) skinned to the visible body via leader pose. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Appearance")
	TArray<TObjectPtr<UChaosClothAssetBase>> Garments;

	/** Run cloth simulation on the garments (off = skinned only; cheap for ambient crowds). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Appearance")
	bool bSimulateGarments = false;

	/** Optional tint material per garment (same index as Garments); empty = the asset's own materials. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Appearance")
	TArray<TObjectPtr<UMaterialInterface>> GarmentMaterials;

	static constexpr int32 MaxGarments = 4;

	/** Hide the base body (it keeps animating) when the outfit is a full suit that covers it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guard|Body")
	bool bHideBodyUnderOutfit = false;

	/** Rigid helmet on the head bone (Bible §8 tell: helmet optics). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guard|Body")
	TObjectPtr<UStaticMesh> HelmetMeshAsset;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guard|Body")
	FName HelmetSocket = TEXT("head");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guard|Body")
	FTransform HelmetOffset = FTransform::Identity;

	/** Exposed battery pack on the guard's back (Bible §8 tell). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guard|Body")
	TObjectPtr<UStaticMesh> BatteryMeshAsset;

	/** Body bone/socket the pack rides on; None = mesh root. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guard|Body")
	FName BatterySocket = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guard|Body")
	FTransform BatteryOffset = FTransform(FRotator::ZeroRotator, FVector(0.f, -24.f, 128.f), FVector(0.45f));

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Guard")
	UStaticMeshComponent* GetBatteryPack() const { return BatteryPack; }

	/** World-space route captured at BeginPlay. */
	const TArray<FVector>& GetWorldPatrol() const { return WorldPatrol; }

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UNVHealthComponent> Health;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> BatteryPack;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Helmet;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UChildActorComponent> Appearance;

	/** Leader-pose the appearance actor's body to our animated mesh. */
	void BindAppearance();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TArray<TObjectPtr<USkeletalMeshComponent>> OutfitComponents;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TArray<TObjectPtr<UChaosClothComponent>> GarmentComponents;

	void ApplyGarments(USkeletalMeshComponent* Host);

private:
	TArray<FVector> WorldPatrol;
};
