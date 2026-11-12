#include "Debug/NVBenchmarkSubsystem.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "HAL/PlatformTime.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "NeonVeil.h"
#include "ProfilingDebugging/CsvProfiler.h"
#include "RHI.h"

bool UNVBenchmarkSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	return FParse::Param(FCommandLine::Get(), TEXT("nvbench")) && Super::ShouldCreateSubsystem(Outer);
}

TStatId UNVBenchmarkSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UNVBenchmarkSubsystem, STATGROUP_Tickables);
}

void UNVBenchmarkSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);
	if (!InWorld.IsGameWorld())
	{
		return;
	}
	// Name, viewpoint (cm), start yaw, hold seconds, teleport
	Stops = {
		{ TEXT("Load"),            FVector::ZeroVector,              0.f, 6.f,  false },
		{ TEXT("A_TramArrival"),   FVector::ZeroVector,              0.f, 22.f, false },
		{ TEXT("A_Skybridge"),     FVector(1700.f, 0.f, 100.f),      0.f, 12.f, true },
		{ TEXT("B_Atrium"),        FVector(4100.f, -600.f, 100.f),  30.f, 16.f, true },
		{ TEXT("C_SimSuite"),      FVector(6900.f, 0.f, 100.f),      0.f, 16.f, true },
		{ TEXT("D_Gallery"),       FVector(11900.f, 0.f, 100.f),     0.f, 14.f, true },
		{ TEXT("E_Antechamber"),   FVector(15100.f, 0.f, 100.f),     0.f, 12.f, true },
	};
	bActive = true;
	LastTime = FPlatformTime::Seconds();
	GEngine->Exec(&InWorld, TEXT("csvprofile start"));
	UE_LOG(LogNeonVeil, Log, TEXT("NVBench: started (%d stops)"), Stops.Num());
	BeginStop(0);
}

void UNVBenchmarkSubsystem::BeginStop(int32 Index)
{
	Current = Index;
	StopStart = FPlatformTime::Seconds();
	Frames = 0; SumFrameMs = SumGpuMs = MaxFrameMs = 0.0;
	FrameSamples.Reset();
	const FStop& S = Stops[Index];
	CSV_EVENT_GLOBAL(TEXT("NV_%s"), S.Name);
	if (S.bTeleport)
	{
		if (ACharacter* P = Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(GetWorld(), 0)))
		{
			P->TeleportTo(S.Location, FRotator(0.f, S.Yaw, 0.f));
		}
	}
	UE_LOG(LogNeonVeil, Log, TEXT("NVBench: stop %s"), S.Name);
}

void UNVBenchmarkSubsystem::Tick(float DeltaTime)
{
	if (!bActive || !Stops.IsValidIndex(Current))
	{
		return;
	}
	const double Now = FPlatformTime::Seconds();
	const double FrameMs = (Now - LastTime) * 1000.0;
	LastTime = Now;
	const FStop& S = Stops[Current];
	const double T = Now - StopStart;

	// Slow full pan across the hold so every wall of the room is rendered; skip the first 1.5 s (streaming settle).
	if (S.bTeleport)
	{
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0))
		{
			PC->SetControlRotation(FRotator(-4.f, S.Yaw + 360.f * FMath::Clamp(T / S.Hold, 0.0, 1.0), 0.f));
		}
	}
	if (T > 1.5)
	{
		++Frames;
		SumFrameMs += FrameMs;
		MaxFrameMs = FMath::Max(MaxFrameMs, FrameMs);
		FrameSamples.Add(static_cast<float>(FrameMs));
		SumGpuMs += FPlatformTime::ToMilliseconds(RHIGetGPUFrameCycles(0));
	}
	if (T >= S.Hold)
	{
		EndStop();
		if (Current + 1 < Stops.Num())
		{
			BeginStop(Current + 1);
		}
		else
		{
			Finish();
		}
	}
}

void UNVBenchmarkSubsystem::EndStop()
{
	const FStop& S = Stops[Current];
	FrameSamples.Sort();
	const float P95 = FrameSamples.Num() ? FrameSamples[FMath::Min(FrameSamples.Num() - 1, FMath::FloorToInt(FrameSamples.Num() * 0.95f))] : 0.f;
	const FString Line = FString::Printf(TEXT("%-15s frames %5d  avg %6.2f ms (%5.1f fps)  p95 %6.2f ms  max %7.1f ms  gpu %6.2f ms"),
		S.Name, Frames, Frames ? SumFrameMs / Frames : 0.0, Frames ? 1000.0 / (SumFrameMs / Frames) : 0.0, P95, MaxFrameMs, Frames ? SumGpuMs / Frames : 0.0);
	Summary.Add(Line);
	UE_LOG(LogNeonVeil, Log, TEXT("NVBench: %s"), *Line);
}

void UNVBenchmarkSubsystem::Finish()
{
	bActive = false;
	GEngine->Exec(GetWorld(), TEXT("csvprofile stop"));
	const FString Path = FPaths::ProjectSavedDir() / TEXT("NV_Benchmark.txt");
	FFileHelper::SaveStringToFile(FString::Join(Summary, TEXT("\n")), *Path);
	UE_LOG(LogNeonVeil, Log, TEXT("NVBench: done -> %s"), *Path);
	UKismetSystemLibrary::QuitGame(GetWorld(), UGameplayStatics::GetPlayerController(GetWorld(), 0), EQuitPreference::Quit, false);
}
