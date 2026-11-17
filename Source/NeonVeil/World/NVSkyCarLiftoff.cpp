#include "World/NVSkyCarLiftoff.h"

#include "NeonVeil.h"
#include "UI/NVHUD.h"
#include "World/NVBlastShake.h"
#include "Components/AudioComponent.h"
#include "Components/BoxComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "AIController.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "NiagaraFunctionLibrary.h"
#include "Sound/SoundAttenuation.h"
#include "Sound/SoundBase.h"

namespace
{
	FVector Bezier(const FVector& A, const FVector& B, const FVector& C, const FVector& D, float T)
	{
		const float U = 1.f - T;
		return U * U * U * A + 3.f * U * U * T * B + 3.f * U * T * T * C + T * T * T * D;
	}
	UPointLightComponent* MakePoint(AActor* Owner, USceneComponent* Parent, const TCHAR* Name, const FVector& At, const FLinearColor& Col, float Lm, float Radius)
	{
		UPointLightComponent* L = Owner->CreateDefaultSubobject<UPointLightComponent>(Name);
		L->SetupAttachment(Parent);
		L->SetRelativeLocation(At);
		L->SetIntensityUnits(ELightUnits::Lumens);
		L->SetIntensity(Lm);
		L->SetAttenuationRadius(Radius);
		L->SetLightColor(Col);
		L->SetCastShadows(false);
		L->SetMobility(EComponentMobility::Movable);
		return L;
	}
	USpotLightComponent* MakeHead(AActor* Owner, USceneComponent* Parent, const TCHAR* Name, const FVector& At)
	{
		USpotLightComponent* L = Owner->CreateDefaultSubobject<USpotLightComponent>(Name);
		L->SetupAttachment(Parent);
		L->SetRelativeLocation(At);
		L->SetRelativeRotation(FRotator(-6.f, 0.f, 0.f));
		L->SetIntensityUnits(ELightUnits::Lumens);
		L->SetIntensity(9000.f);
		L->SetAttenuationRadius(4200.f);
		L->SetInnerConeAngle(10.f);
		L->SetOuterConeAngle(26.f);
		L->SetLightColor(FLinearColor(0.82f, 0.9f, 1.f));
		L->SetCastShadows(false);
		L->SetVolumetricScatteringIntensity(1.2f);
		L->SetMobility(EComponentMobility::Movable);
		return L;
	}
}

ANVSkyCarLiftoff::ANVSkyCarLiftoff()
{
	PrimaryActorTick.bCanEverTick = true;
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
	CarRoot = CreateDefaultSubobject<USceneComponent>(TEXT("CarRoot"));
	CarRoot->SetupAttachment(Root);
	CarRoot->SetMobility(EComponentMobility::Movable);

	Body = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));
	Body->SetupAttachment(CarRoot);
	Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Body->SetMobility(EComponentMobility::Movable);
	Canopy = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Canopy"));
	Canopy->SetupAttachment(CarRoot);
	Canopy->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Canopy->SetMobility(EComponentMobility::Movable);
	Canopy->SetRelativeLocation(FVector(95.f, 0.f, 101.8f));

	HeadL = MakeHead(this, CarRoot, TEXT("HeadL"), FVector(262.f, -62.f, 58.f));
	HeadR = MakeHead(this, CarRoot, TEXT("HeadR"), FVector(262.f, 62.f, 58.f));
	TailL = MakePoint(this, CarRoot, TEXT("TailL"), FVector(-268.f, -70.f, 80.f), FLinearColor(1.f, 0.08f, 0.12f), 900.f, 380.f);
	TailR = MakePoint(this, CarRoot, TEXT("TailR"), FVector(-268.f, 70.f, 80.f), FLinearColor(1.f, 0.08f, 0.12f), 900.f, 380.f);
	UnderF = MakePoint(this, CarRoot, TEXT("UnderF"), FVector(110.f, 0.f, -15.f), FLinearColor(0.2f, 0.85f, 1.f), 5000.f, 650.f);
	UnderR = MakePoint(this, CarRoot, TEXT("UnderR"), FVector(-150.f, 0.f, -15.f), FLinearColor(0.2f, 0.85f, 1.f), 5000.f, 650.f);
	Cabin = MakePoint(this, CarRoot, TEXT("Cabin"), FVector(20.f, 0.f, 95.f), FLinearColor(0.3f, 0.75f, 1.f), 220.f, 160.f);

	Hum = CreateDefaultSubobject<UAudioComponent>(TEXT("Hum"));
	Hum->SetupAttachment(CarRoot);
	Hum->bAutoActivate = false;

	ParkFill = CreateDefaultSubobject<USpotLightComponent>(TEXT("ParkFill"));
	ParkFill->SetupAttachment(Root);
	ParkFill->SetRelativeLocation(FVector(0.f, 0.f, 650.f));
	ParkFill->SetRelativeRotation(FRotator(-90.f, 0.f, 0.f));
	ParkFill->SetIntensityUnits(ELightUnits::Lumens);
	ParkFill->SetIntensity(2600.f);
	ParkFill->SetAttenuationRadius(1100.f);
	ParkFill->SetInnerConeAngle(20.f);
	ParkFill->SetOuterConeAngle(48.f);
	ParkFill->SetLightColor(FLinearColor(0.7f, 0.8f, 1.f));
	ParkFill->SetCastShadows(false);
	ParkFill->SetMobility(EComponentMobility::Movable);

	Blocker = CreateDefaultSubobject<UBoxComponent>(TEXT("Blocker"));
	Blocker->SetupAttachment(Root);
	Blocker->SetCollisionProfileName(TEXT("BlockAll"));
	Blocker->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Blocker->SetCanEverAffectNavigation(false);
	Blocker->SetHiddenInGame(true);
}

void ANVSkyCarLiftoff::BeginPlay()
{
	Super::BeginPlay();
	ParkPos = CarRoot->GetComponentLocation();
	ParkRot = CarRoot->GetComponentRotation();
	CurRot = ParkRot;
	PrevPos = ParkPos;
	PrevYaw = ParkRot.Yaw;
	Blocker->SetBoxExtent(BlockerExtent);
	Blocker->SetRelativeLocation(FVector(0.f, 0.f, BlockerExtent.Z - 20.f));

	for (UStaticMeshComponent* M : { Body.Get(), Canopy.Get() })
	{
		for (int32 i = 0; i < M->GetNumMaterials(); ++i)
		{
			UMaterialInterface* Mat = M->GetMaterial(i);
			float Dummy = 0.f;
			if (Mat && Mat->GetScalarParameterValue(FHashedMaterialParameterInfo(GlowParam), Dummy))
			{
				GlowMIDs.Add(M->CreateDynamicMaterialInstance(i, Mat));
			}
		}
	}
	HeadBase = HeadL->Intensity; TailBase = TailL->Intensity; UnderBase = UnderF->Intensity; CabinBase = Cabin->Intensity;
	for (ULightComponent* L : { (ULightComponent*)HeadL, (ULightComponent*)HeadR, (ULightComponent*)TailL, (ULightComponent*)TailR,
		(ULightComponent*)UnderF, (ULightComponent*)UnderR, (ULightComponent*)Cabin })
	{
		L->SetIntensity(0.f);
	}
	SetGlow(ParkedGlow);
	if (HumSound)
	{
		Hum->SetSound(HumSound);
		Hum->AttenuationSettings = Attenuation;
	}

	if (Driver)
	{
		Canopy->SetRelativeRotation(CanopyOpen);
		// take the driver off its AI: this actor walks them to the cockpit
		if (AController* C = Driver->GetController())
		{
			if (AAIController* AI = Cast<AAIController>(C)) { AI->StopMovement(); }
			C->UnPossess();
		}
		if (UCharacterMovementComponent* CM = Driver->GetCharacterMovement()) { CM->DisableMovement(); }
		SetPhase(EPhase::WaitDriver);
	}
	else
	{
		Blocker->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
		SetPhase(EPhase::Parked);
	}
	UE_LOG(LogNeonVeil, Log, TEXT("%s: sky car ready (%d glow materials, driver %s)"), *GetName(), GlowMIDs.Num(), Driver ? *Driver->GetName() : TEXT("none"));
}

void ANVSkyCarLiftoff::SetGlow(float G)
{
	for (UMaterialInstanceDynamic* M : GlowMIDs)
	{
		if (M) { M->SetScalarParameterValue(GlowParam, G); }
	}
}

void ANVSkyCarLiftoff::Say(const TArray<FNVSubtitleLine>& Lines)
{
	if (Lines.Num() == 0) { return; }
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
	{
		if (ANVHUD* Hud = Cast<ANVHUD>(PC->GetHUD())) { Hud->QueueSubtitles(Lines); }
	}
}

bool ANVSkyCarLiftoff::PlayerPast(const FVector& Plane) const
{
	const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0);
	return P && FVector::DotProduct(P->GetActorLocation() - Plane, ProgressDirection.GetSafeNormal()) > 0.f;
}

float ANVSkyCarLiftoff::PlayerDistance() const
{
	const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0);
	return P ? FVector::Dist(P->GetActorLocation(), ParkPos) : BIG_NUMBER;
}

void ANVSkyCarLiftoff::PlaceCar(const FVector& Pos, const FRotator& Rot)
{
	CarRoot->SetWorldLocationAndRotation(Pos, Rot);
}

void ANVSkyCarLiftoff::Tick(float Dt)
{
	Super::Tick(Dt);
	PhaseTime += Dt;
	const FTransform Park(ParkRot, ParkPos, CarRoot->GetComponentScale());

	switch (Phase)
	{
	case EPhase::WaitDriver:
	{
		const FVector Board = Park.TransformPosition(BoardPoint);
		if (!Driver)
		{
			SetPhase(EPhase::Closing);
			break;
		}
		UCharacterMovementComponent* CM = Driver->GetCharacterMovement();
		const FVector Here = Driver->GetActorLocation();
		const FVector To = FVector(Board.X - Here.X, Board.Y - Here.Y, 0.f);
		if (PhaseTime > DriverStartDelay && To.Size() > BoardRadius)
		{
			const FVector Dir = To.GetSafeNormal();
			const float Step = FMath::Min(DriverWalkSpeed * Dt, To.Size());
			Driver->SetActorLocation(Here + Dir * Step, false);
			const float Yaw = FMath::FixedTurn(Driver->GetActorRotation().Yaw, Dir.Rotation().Yaw, 240.f * Dt);
			Driver->SetActorRotation(FRotator(0.f, Yaw, 0.f));
			if (CM) { CM->Velocity = Dir * DriverWalkSpeed; CM->UpdateComponentVelocity(); }
		}
		else if (CM)
		{
			CM->Velocity = FVector::ZeroVector; CM->UpdateComponentVelocity();
		}
		if ((PhaseTime > DriverStartDelay && To.Size() <= BoardRadius) || PhaseTime > 60.f)
		{
			if (CM) { CM->Velocity = FVector::ZeroVector; CM->UpdateComponentVelocity(); }
			Driver->SetActorEnableCollision(false);
			ClimbFrom = Driver->GetActorLocation();
			SetPhase(EPhase::Climb);
		}
		break;
	}
	case EPhase::Climb:
	{
		const float A = FMath::Clamp(PhaseTime / FMath::Max(ClimbTime, 0.1f), 0.f, 1.f);
		const FVector Seat = Park.TransformPosition(SeatPoint) + FVector(0.f, 0.f, 90.f);   // capsule centre
		FVector P = FMath::Lerp(ClimbFrom, Seat, FMath::InterpEaseInOut(0.f, 1.f, A, 2.f));
		P.Z += FMath::Sin(A * PI) * 45.f;                                                    // step up and over the sill
		Driver->SetActorLocationAndRotation(P, FRotator(0.f, FMath::Lerp(Driver->GetActorRotation().Yaw, ParkRot.Yaw, A), 0.f));
		if (A >= 1.f)
		{
			Driver->SetActorHiddenInGame(true);
			if (CanopySound) { UGameplayStatics::PlaySoundAtLocation(this, CanopySound, Canopy->GetComponentLocation(), 1.f, 1.f, 0.f, Attenuation); }
			SetPhase(EPhase::Closing);
		}
		break;
	}
	case EPhase::Closing:
	{
		const float A = FMath::Clamp(PhaseTime / FMath::Max(CanopyCloseTime, 0.1f), 0.f, 1.f);
		Canopy->SetRelativeRotation(FMath::Lerp(CanopyOpen, FRotator::ZeroRotator, FMath::InterpEaseInOut(0.f, 1.f, A, 2.f)));
		Cabin->SetIntensity(CabinBase * (1.f - A));
		if (A >= 1.f)
		{
			Blocker->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
			if (Driver) { Driver->Destroy(); Driver = nullptr; }
			SetPhase(EPhase::Parked);
		}
		else if (PhaseTime < Dt * 1.5f && Driver)
		{
			Cabin->SetIntensity(CabinBase);
		}
		break;
	}
	case EPhase::Parked:
		if (LightsOnPlane.IsNearlyZero() ? PlayerDistance() < LightsOnDistance : PlayerPast(LightsOnPlane))
		{
			if (PowerUpSound) { UGameplayStatics::PlaySoundAtLocation(this, PowerUpSound, ParkPos, 1.2f, 1.f, 0.f, Attenuation); }
			if (Hum && HumSound) { Hum->FadeIn(2.5f, 0.55f); }
			Say(LinesOnLightsOn);
			SetPhase(EPhase::Lit);
		}
		break;
	case EPhase::Lit:
	{
		// headlights blink twice then hold; strips, tail and underglow fade up
		const float T = PhaseTime;
		const bool bHead = (T > 0.f && T < 0.12f) || (T > 0.28f && T < 0.38f) || T > 0.55f;
		HeadL->SetIntensity(bHead ? HeadBase : 0.f);
		HeadR->SetIntensity(bHead ? HeadBase : 0.f);
		const float F = FMath::Clamp(T / 1.5f, 0.f, 1.f);
		TailL->SetIntensity(TailBase * F); TailR->SetIntensity(TailBase * F);
		UnderF->SetIntensity(UnderBase * 0.35f * F); UnderR->SetIntensity(UnderBase * 0.35f * F);
		Cabin->SetIntensity(CabinBase * F);
		SetGlow(FMath::Lerp(ParkedGlow, GlowOn, F));
		const float PD = PlayerDistance();
		const bool bGo = LiftoffPlane.IsNearlyZero() ? PD < LiftoffDistance : (PlayerPast(LiftoffPlane) || PD < LiftoffDistance);
		if (T > MinIdleBeforeLiftoff && (bGo || (T > LingerTime && PD < LingerDistance)))
		{
			if (LiftoffSound) { UGameplayStatics::SpawnSoundAttached(LiftoffSound, CarRoot, NAME_None, FVector::ZeroVector, EAttachLocation::KeepRelativeOffset, false, LiftoffVolume, 1.f, 0.f, Attenuation); }
			SetPhase(EPhase::Spool);
		}
		break;
	}
	case EPhase::Spool:
	{
		const float A = FMath::Clamp(PhaseTime / FMath::Max(SpoolTime, 0.1f), 0.f, 1.f);
		const float U = FMath::Lerp(0.35f, 1.f, A);
		UnderF->SetIntensity(UnderBase * U * (1.f + 0.08f * FMath::Sin(PhaseTime * 37.f)));
		UnderR->SetIntensity(UnderBase * U * (1.f + 0.08f * FMath::Sin(PhaseTime * 41.f)));
		SetGlow(FMath::Lerp(GlowOn, GlowThrust, A));
		if (Hum) { Hum->SetPitchMultiplier(1.f + 0.25f * A); Hum->SetVolumeMultiplier(0.55f + 0.35f * A); }
		// settles on its pads, then lifts a hand's width and hangs there trembling
		const float Lift = A < 0.4f ? -4.f * FMath::Sin(A / 0.4f * PI) : 18.f * FMath::InterpEaseOut(0.f, 1.f, (A - 0.4f) / 0.6f, 2.f);
		PlaceCar(ParkPos + FVector(0.f, 0.f, Lift + FMath::Sin(PhaseTime * 23.f) * 0.8f * A), ParkRot);
		if (A >= 1.f)
		{
			if (LiftDustFX) { UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, LiftDustFX, ParkPos, FRotator::ZeroRotator, FVector(LiftDustScale)); }
			if (PlayerDistance() < 1800.f) { UNVBlastShake::Kick(this, 0.22f, 0.5f); }
			SetPhase(EPhase::Rise);
		}
		break;
	}
	case EPhase::Rise:
	{
		const float A = FMath::Clamp(PhaseTime / FMath::Max(RiseTime, 0.1f), 0.f, 1.f);
		const float H = 18.f + (HoverHeight - 18.f) * FMath::InterpEaseInOut(0.f, 1.f, A, 2.2f);
		const FRotator R(3.5f * FMath::Sin(A * PI), ParkRot.Yaw + 2.f * FMath::Sin(A * PI * 1.3f), 1.8f * FMath::Sin(PhaseTime * 1.7f));
		PlaceCar(ParkPos + FVector(0.f, 0.f, H), R);
		UnderF->SetIntensity(UnderBase * (1.f - 0.4f * A)); UnderR->SetIntensity(UnderBase * (1.f - 0.4f * A));
		ParkFill->SetIntensity(2600.f * (1.f - A));
		if (!bLiftLineSaid && PhaseTime > LiftoffLineDelay - SpoolTime) { bLiftLineSaid = true; Say(LinesOnLiftoff); }
		if (A >= 1.f)
		{
			// curve: from the hover point, forward and up along the car's heading, turning into the lane
			P1 = CarRoot->GetComponentLocation();
			const FVector Fwd = ParkRot.Vector();
			P3 = JoinPoint.IsNearlyZero() ? P1 + Fwd * 12000.f + FVector(0.f, 0.f, 4000.f) : JoinPoint;
			const FVector Dir = JoinDirection.GetSafeNormal2D().IsNearlyZero() ? Fwd : JoinDirection.GetSafeNormal();
			const float Span = FVector::Dist(P1, P3);
			C1 = P1 + Fwd * Span * 0.35f + FVector(0.f, 0.f, Span * 0.15f);
			C2 = P3 - Dir * Span * 0.45f;
			PrevPos = P1;
			PrevYaw = CarRoot->GetComponentRotation().Yaw;
			CurRot = CarRoot->GetComponentRotation();
			SetPhase(EPhase::Depart);
		}
		break;
	}
	case EPhase::Depart:
	case EPhase::Cruise:
	{
		FVector Pos;
		if (Phase == EPhase::Depart)
		{
			const float A = FMath::Clamp(PhaseTime / FMath::Max(DepartTime, 0.1f), 0.f, 1.f);
			// accelerate away: slow, majestic first metres, then committed
			const float S = FMath::Pow(A, 1.8f);
			Pos = Bezier(P1, C1, C2, P3, S);
			if (!bLiftLineSaid && PhaseTime > 0.5f) { bLiftLineSaid = true; Say(LinesOnLiftoff); }
			if (A >= 1.f) { SetPhase(EPhase::Cruise); }
		}
		else
		{
			const FVector Dir = JoinDirection.GetSafeNormal().IsNearlyZero() ? CurRot.Vector() : JoinDirection.GetSafeNormal();
			Pos = P3 + Dir * CruiseSpeed * PhaseTime;
			if (PhaseTime > CruiseTime)
			{
				SetActorHiddenInGame(true);
				if (Hum) { Hum->Stop(); }
				SetPhase(EPhase::Gone);
				SetActorTickEnabled(false);
				break;
			}
		}
		const FVector Vel = (Pos - PrevPos) / FMath::Max(Dt, 1e-3f);
		if (Vel.SizeSquared() > 25.f)
		{
			const FRotator Want = Vel.Rotation();
			const float YawRate = FMath::FindDeltaAngleDegrees(PrevYaw, Want.Yaw) / FMath::Max(Dt, 1e-3f);
			Bank = FMath::FInterpTo(Bank, FMath::Clamp(YawRate * 0.6f, -MaxBank, MaxBank), Dt, 2.5f);
			CurRot.Yaw = FMath::FInterpTo(CurRot.Yaw, CurRot.Yaw + FMath::FindDeltaAngleDegrees(CurRot.Yaw, Want.Yaw), Dt, 2.2f);
			CurRot.Pitch = FMath::FInterpTo(CurRot.Pitch, FMath::Clamp(Want.Pitch * 0.6f, -10.f, 14.f), Dt, 2.f);
			CurRot.Roll = Bank;
			PrevYaw = Want.Yaw;
		}
		PlaceCar(Pos, CurRot);
		PrevPos = Pos;
		break;
	}
	default:
		break;
	}
}
