#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameplayTagContainer.h"
#include "NVTramService.generated.h"

class UBoxComponent;
class USoundBase;
class UAudioComponent;
class UStaticMeshComponent;

/**
 * Crown Line platform service (prologue). Drives an existing tram actor (the Sci-Fi Tram Station BP_Tram):
 * it waits out in the tunnel, glides in when ArriveOnObjective becomes active, opens its doors, waits for the
 * player to step aboard, closes up and pulls back out into the tunnel. A little way into the departure it sends
 * BoardedEventTag, which completes the prologue so the game mode fades and opens the tower map (where C00's
 * arrival ride picks up). This actor sits where the tram docks; its +X is the arrival direction.
 * The tram BP's own door triggers are switched off; door leaves are its StaticMeshComponents with "Door" in
 * their name and slide along the tram's local X.
 */
UCLASS()
class NEONVEIL_API ANVTramService : public AActor
{
	GENERATED_BODY()

public:
	ANVTramService();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram")
	TObjectPtr<AActor> Tram;

	/** The tram arrives when this objective becomes active. None = at level start. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram")
	FName ArriveOnObjective;

	/** How far out (against +X) the tram waits before arriving. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram", meta = (ClampMin = "0"))
	float ArriveDistance = 7000.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram", meta = (ClampMin = "1"))
	float ArriveTime = 11.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram", meta = (ClampMin = "0"))
	float DepartDistance = 9000.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram", meta = (ClampMin = "1"))
	float DepartTime = 9.f;

	/** Seconds the player must be aboard (inside BoardVolume) before the doors close. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram", meta = (ClampMin = "0"))
	float BoardDelay = 2.f;

	/** Seconds into the departure when BoardedEventTag is sent (starts the fade to the tower). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram", meta = (ClampMin = "0"))
	float BoardedEventDelay = 3.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram")
	FGameplayTag BoardedEventTag;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram|Doors", meta = (ClampMin = "0"))
	float DoorSlide = 70.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram|Doors", meta = (ClampMin = "0.1"))
	float DoorTime = 1.2f;

	/** Flip if the leaves slide into each other instead of apart. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram|Doors")
	bool bFlipDoorDirection = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram|Audio")
	TObjectPtr<USoundBase> RunSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram|Audio")
	TObjectPtr<USoundBase> DockSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram|Audio")
	TObjectPtr<USoundBase> DoorSound;

	/** Platform announcement played as the tram pulls in (optional). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram|Audio")
	TObjectPtr<USoundBase> ArrivalAnnouncement;

protected:
	/** Cabin interior at the docked position. */
	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UBoxComponent> BoardVolume;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UAudioComponent> RunAudio;

private:
	enum class EPhase : uint8 { Away, Arriving, Opening, Boarding, Closing, Departing, Gone };

	void SetOffset(float Offset);
	void SetDoorAlpha(float Alpha);
	void PlayAtTram(USoundBase* Sound) const;

	struct FDoorLeaf
	{
		TWeakObjectPtr<UStaticMeshComponent> Comp;
		FVector ClosedRel;
		float Sign = 1.f;
	};
	TArray<FDoorLeaf> Leaves;
	FVector TramHome;
	TWeakObjectPtr<APawn> Rider;
	EPhase Phase = EPhase::Away;
	float PhaseTime = 0.f;
	float AboardTime = 0.f;
	float Offset = 0.f;
	bool bBoardedSent = false;
};
