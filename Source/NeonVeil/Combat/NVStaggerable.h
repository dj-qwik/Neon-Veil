#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "NVStaggerable.generated.h"

UINTERFACE(MinimalAPI, meta = (CannotImplementInterfaceInBlueprint))
class UNVStaggerable : public UInterface
{
	GENERATED_BODY()
};

/**
 * Anything the shock baton can stagger (Bible §7: "emergency stagger and takedown").
 * A strike on a staggered target that allows it is a takedown. Bosses return false from
 * CanBeTakenDown ("no instant boss kill").
 */
class NEONVEIL_API INVStaggerable
{
	GENERATED_BODY()

public:
	virtual void ApplyStagger(float Duration, AActor* StaggerInstigator) = 0;
	virtual bool IsStaggered() const = 0;
	virtual bool CanBeTakenDown() const { return true; }
};
