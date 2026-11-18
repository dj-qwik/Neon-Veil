#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NVNameTag.generated.h"

/**
 * Identifies a story character on the HUD: when the player looks at this point from close enough, GHOST-OS prints the
 * name and role above it (e.g. the Director in the antechamber). Attach it to the character so it follows them.
 */
UCLASS()
class NEONVEIL_API ANVNameTag : public AActor
{
	GENERATED_BODY()

public:
	ANVNameTag();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil|NameTag")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil|NameTag")
	FText RoleText;

	/** Shown only within this distance (cm) and when the view is within LookAngle degrees of the tag. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil|NameTag")
	float MaxDistance = 1600.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil|NameTag")
	float LookAngle = 16.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil|NameTag")
	bool bEnabled = true;

	/** Fade state, driven by the HUD. */
	float Visibility = 0.f;

	static const TArray<TWeakObjectPtr<ANVNameTag>>& All();

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;
};
