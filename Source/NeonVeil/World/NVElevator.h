#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameplayTagContainer.h"
#include "NVElevator.generated.h"

class UBoxComponent;
class USoundBase;
class UAudioComponent;

/**
 * One-way passenger lift (prologue: street lobby up to the Crown Line concourse).
 * The cab is a set of Movable actors (floor, walls, ceiling, lights) carried by this actor's Travel offset;
 * the rider stands on the Movable cab floor and is carried by CharacterMovement's based movement.
 * Flow: lower landing doors stand open -> player steps into the cab box -> after StartDelay the lower doors
 * close -> smooth ride -> upper doors open and ArrivedEventTag is sent. The cab box lives on this actor and
 * is placed in the cab at the lower landing.
 */
UCLASS()
class NEONVEIL_API ANVElevator : public AActor
{
	GENERATED_BODY()

public:
	ANVElevator();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	/** Cab actors (must be Movable). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lift")
	TArray<TObjectPtr<AActor>> CabParts;

	/** World-space offset from the lower landing to the upper landing. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lift")
	FVector Travel = FVector(0.f, 0.f, 2000.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lift", meta = (ClampMin = "1"))
	float RideTime = 9.f;

	/** Seconds the player must stand in the cab before the doors close. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lift", meta = (ClampMin = "0"))
	float StartDelay = 1.2f;

	/** Landing door leaves (Movable). Lower leaves start open, upper leaves start closed. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lift|Doors")
	TArray<TObjectPtr<AActor>> LowerDoors;

	/** World-space slide from closed to open, one per lower leaf. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lift|Doors")
	TArray<FVector> LowerDoorOpenOffsets;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lift|Doors")
	TArray<TObjectPtr<AActor>> UpperDoors;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lift|Doors")
	TArray<FVector> UpperDoorOpenOffsets;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lift|Doors", meta = (ClampMin = "0.1"))
	float DoorTime = 1.1f;

	/** Only rides while this objective is active (None = always). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lift")
	FName RequiredActiveObjective;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lift")
	FGameplayTag ArrivedEventTag;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lift|Audio")
	TObjectPtr<USoundBase> DoorSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lift|Audio")
	TObjectPtr<USoundBase> RideSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lift|Audio")
	TObjectPtr<USoundBase> ArriveSound;

	UFUNCTION(BlueprintPure, Category = "Lift")
	bool HasArrived() const { return Phase == EPhase::Done; }

protected:
	/** Rider detection inside the cab at the lower landing. */
	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UBoxComponent> CabVolume;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UAudioComponent> RideAudio;

private:
	enum class EPhase : uint8 { Waiting, Closing, Riding, Opening, Done };

	void SetCabAlpha(float Alpha);
	void SetDoors(const TArray<TObjectPtr<AActor>>& Doors, const TArray<FVector>& Closed, const TArray<FVector>& Offsets, float OpenAlpha, const FVector& Carry);
	bool PlayerInCab(APawn*& OutPawn) const;
	void PlayAt(USoundBase* Sound) const;

	TArray<FVector> CabHome;
	TArray<FVector> LowerClosed;
	TArray<FVector> UpperClosed;
	TWeakObjectPtr<APawn> Rider;
	EPhase Phase = EPhase::Waiting;
	float PhaseTime = 0.f;
	float InCabTime = 0.f;
	float CabAlpha = 0.f;
};
