#pragma once

#include "CoreMinimal.h"
#include "NVCommsMessage.generated.h"

class USoundBase;

/** An incoming transmission shown as a GHOST-OS comms card (top left) and kept in the menu's COMMS log. */
USTRUCT(BlueprintType)
struct FNVCommsMessage
{
	GENERATED_BODY()

	/** Who is talking, e.g. "Handler", "Unknown". */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Comms")
	FText Sender;

	/** Channel tag, e.g. "Secure", "Station PA", "Encrypted". Empty = "Direct". */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Comms")
	FText Channel;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Comms", meta = (MultiLine = true))
	FText Body;

	/** Seconds on screen. 0 = long enough to read it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Comms", meta = (ClampMin = "0"))
	float Duration = 0.f;

	/** Amber card for urgent traffic. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Comms")
	bool bPriority = false;

	/** Optional voice line, played when the card opens. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Comms")
	TObjectPtr<USoundBase> Voice;
};

/** A logged transmission (menu COMMS tab). */
USTRUCT(BlueprintType)
struct FNVCommsLogEntry
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Comms")
	FNVCommsMessage Message;

	/** Game seconds since the level started. */
	UPROPERTY(BlueprintReadOnly, Category = "Comms")
	float Time = 0.f;
};
