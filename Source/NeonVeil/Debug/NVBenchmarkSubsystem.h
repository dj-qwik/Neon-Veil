#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "NVBenchmarkSubsystem.generated.h"

/**
 * M8 performance benchmark. Inert unless the game is launched with -nvbench.
 * Rides the C00 tram, then tours a fixed viewpoint in every M00 room with a slow 360 pan,
 * marking each room as a CSV profiler event and logging per-room frame/GPU/VRAM stats,
 * then quits. Viewpoints are world coordinates so it works in packaged builds too.
 */
UCLASS()
class NEONVEIL_API UNVBenchmarkSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;
	virtual bool IsTickable() const override { return bActive; }

private:
	struct FStop
	{
		const TCHAR* Name;
		FVector Location;
		float Yaw;
		float Hold;
		bool bTeleport;
	};

	void BeginStop(int32 Index);
	void EndStop();
	void Finish();

	TArray<FStop> Stops;
	int32 Current = -1;
	double StopStart = 0.0;
	double LastTime = 0.0;
	bool bActive = false;

	// per-stop accumulators
	int32 Frames = 0;
	double SumFrameMs = 0.0, SumGpuMs = 0.0, MaxFrameMs = 0.0;
	TArray<float> FrameSamples;
	TArray<FString> Summary;
};
