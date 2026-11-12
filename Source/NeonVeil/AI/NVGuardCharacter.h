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

	/** Extra skinned outfit pieces driven by the body's pose (leader pose). Up to MaxOutfitParts. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Guard|Body")
	TArray<TObjectPtr<USkeletalMesh>> OutfitParts;

	static constexpr int32 MaxOutfitParts = 6;

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
	TArray<TObjectPtr<USkeletalMeshComponent>> OutfitComponents;

private:
	TArray<FVector> WorldPatrol;
};
