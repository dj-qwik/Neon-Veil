#include "World/NVBlastShake.h"

#include "Camera/PlayerCameraManager.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

void UNVBlastShake::Kick(const UObject* WorldContext, float InTrauma, float Decay)
{
	APlayerController* PC = UGameplayStatics::GetPlayerController(WorldContext, 0);
	APlayerCameraManager* Cam = PC ? PC->PlayerCameraManager.Get() : nullptr;
	if (!Cam)
	{
		return;
	}
	UNVBlastShake* S = Cast<UNVBlastShake>(Cam->FindCameraModifierByClass(UNVBlastShake::StaticClass()));
	if (!S)
	{
		S = Cast<UNVBlastShake>(Cam->AddNewCameraModifier(UNVBlastShake::StaticClass()));
	}
	if (S)
	{
		S->Trauma = FMath::Min(S->Trauma + InTrauma, 1.6f);
		S->DecayRate = Decay;
	}
}

bool UNVBlastShake::ModifyCamera(float DeltaTime, FMinimalViewInfo& InOutPOV)
{
	if (Trauma <= 0.f)
	{
		return false;
	}
	Clock += DeltaTime;
	const float S = FMath::Square(FMath::Min(Trauma, 1.f)) * FMath::Max(Trauma, 1.f);   // squared: big kicks, quick settle
	const float F = Clock * Frequency;
	auto N = [F](float Seed) { return FMath::PerlinNoise1D(F + Seed); };
	InOutPOV.Rotation += FRotator(N(11.3f) * MaxPitchYaw, N(37.9f) * MaxPitchYaw, N(73.1f) * MaxRoll) * S;
	InOutPOV.Location += InOutPOV.Rotation.RotateVector(FVector(N(5.7f), N(19.2f), N(51.4f)) * MaxOffset * S);
	InOutPOV.FOV += N(91.6f) * 2.5f * S;
	Trauma = FMath::Max(0.f, Trauma - DecayRate * DeltaTime);
	return false;
}
