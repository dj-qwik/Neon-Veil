#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "NVGuardCharacter.generated.h"

class UNVHealthComponent;
class USkeletalMesh;
class UAnimInstance;

/**
 * Agency guard (Bible §8). In M00 guards are non-hostile ambient security: they patrol, pause and
 * acknowledge Ghost-7. Combat behaviour (flank, suppress, retreat) arrives with M01 on the same
 * controller. Placeholder mannequin until the M5 character pass.
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

	/** World-space route captured at BeginPlay. */
	const TArray<FVector>& GetWorldPatrol() const { return WorldPatrol; }

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UNVHealthComponent> Health;

private:
	TArray<FVector> WorldPatrol;
};
