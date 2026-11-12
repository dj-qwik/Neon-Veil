#pragma once

#include "CoreMinimal.h"
#include "NVSubtitleLine.generated.h"

class USoundBase;

/** One line of dialogue or ambient text, shown as a subtitle with a speaker label. */
USTRUCT(BlueprintType)
struct FNVSubtitleLine
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subtitle")
	FText Speaker;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subtitle", meta = (MultiLine = true))
	FText Text;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subtitle", meta = (ClampMin = "0.5"))
	float Duration = 3.5f;

	/** Optional voice line. Subtitles-only for now (decided 11 Nov 2026). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subtitle")
	TObjectPtr<USoundBase> Voice;
};
