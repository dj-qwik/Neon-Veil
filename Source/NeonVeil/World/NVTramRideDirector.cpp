#include "World/NVTramRideDirector.h"

#include "NeonVeil.h"
#include "World/NVTramRide.h"
#include "UI/NVHUD.h"
#include "Components/AudioComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "Sound/SoundAttenuation.h"
#include "Sound/SoundBase.h"

namespace
{
	// Pursuit timings, seconds after ChaseStart.
	constexpr float SpotFrom = 4.6f;
	constexpr float SpotTo = 8.8f;
	constexpr float FightFrom = 10.f;
	constexpr float HitAt = 15.6f;
	constexpr float CrashTime = 2.8f;     // hit -> impact
	constexpr float SuspectGone = 20.f;
}

ANVTramRideDirector::ANVTramRideDirector()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickGroup = TG_PostPhysics;   // after the tram has been placed for the frame
	SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));
}

UStaticMeshComponent* ANVTramRideDirector::MakeCar(const TCHAR* Name, UStaticMesh* Mesh, UMaterialInterface* Paint, FLinearColor Glow)
{
	UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this, Name);
	C->SetMobility(EComponentMobility::Movable);
	C->SetStaticMesh(Mesh);
	if (Paint && Mesh && PaintSlot < Mesh->GetStaticMaterials().Num())
	{
		C->SetMaterial(PaintSlot, Paint);
	}
	C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	C->SetWorldScale3D(CarScale);
	C->SetVisibility(false);
	C->RegisterComponent();
	// underglow so the car reads against the night city
	UPointLightComponent* G = NewObject<UPointLightComponent>(this);
	G->SetupAttachment(C);
	G->SetRelativeLocation(FVector(0.f, 0.f, -45.f));
	G->SetIntensityUnits(ELightUnits::Lumens);
	G->SetIntensity(6000.f);
	G->SetAttenuationRadius(900.f);
	G->SetLightColor(Glow);
	G->SetCastShadows(false);
	G->RegisterComponent();
	return C;
}

void ANVTramRideDirector::BeginPlay()
{
	Super::BeginPlay();

	// Tram-space choreography (cm): X ahead of the tram, Y toward the action side (flipped below), Z up.
	SuspectKeys = {
		{0.f, {-9000, -1500, 400}}, {2.5f, {-1500, -1300, 300}}, {4.f, {1800, -1400, 350}}, {6.f, {2400, -1500, 450}},
		{8.f, {2700, -1700, 330}}, {10.f, {2900, -1500, 520}}, {12.f, {3100, -1800, 380}}, {14.f, {3300, -1600, 560}},
		{15.6f, {3500, -1800, 450}}, {18.f, {11000, -2500, 2200}}, {20.f, {24000, -2000, 5500}} };
	PoliceKeys = {
		{0.f, {-12000, -1600, 400}}, {1.2f, {-9000, -1500, 380}}, {3.6f, {-1200, -1050, 240}}, {SpotFrom, {250, -900, 190}},
		{6.7f, {350, -880, 210}}, {SpotTo, {450, -920, 200}}, {9.8f, {1100, -1050, 300}}, {11.2f, {1500, -1150, 380}},
		{13.2f, {1700, -1250, 300}}, {HitAt, {1900, -1150, 470}}, {HitAt + 1.f, {2500, -1300, 420}} };
	for (FKey& K : SuspectKeys) { K.P.Y *= Side; }
	for (FKey& K : PoliceKeys) { K.P.Y *= Side; }

	if (SuspectMesh)
	{
		Suspect = MakeCar(TEXT("Suspect"), SuspectMesh, SuspectPaint, FLinearColor(1.f, 0.15f, 0.35f));
	}
	if (PoliceMesh)
	{
		Police = MakeCar(TEXT("Police"), PoliceMesh, PolicePaint, FLinearColor(0.55f, 0.75f, 1.f));
		UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
		auto MakeBar = [&](const TCHAR* N, UMaterialInterface* M, float Y) {
			UStaticMeshComponent* B = NewObject<UStaticMeshComponent>(this, N);
			B->SetStaticMesh(Cube);
			B->SetMaterial(0, M);
			B->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			B->SetCastShadow(false);
			B->SetupAttachment(Police);
			B->SetRelativeLocation(FVector(-4.f, Y, 42.f));
			B->SetRelativeScale3D(FVector(0.32f / CarScale.X, 0.16f / CarScale.Y, 0.09f / CarScale.Z));
			B->RegisterComponent();
			return B;
		};
		BarRed = MakeBar(TEXT("BarRed"), LightBarRed, -12.f);
		BarBlue = MakeBar(TEXT("BarBlue"), LightBarBlue, 12.f);
		auto MakeFlash = [&](const TCHAR* N, FLinearColor C, float Y) {
			UPointLightComponent* L = NewObject<UPointLightComponent>(this, N);
			L->SetupAttachment(Police);
			L->SetRelativeLocation(FVector(-4.f, Y, 60.f));
			L->SetIntensityUnits(ELightUnits::Lumens);
			L->SetIntensity(0.f);
			L->SetAttenuationRadius(2600.f);
			L->SetLightColor(C);
			L->SetCastShadows(false);
			L->RegisterComponent();
			return L;
		};
		FlashRed = MakeFlash(TEXT("FlashRed"), FLinearColor(1.f, 0.05f, 0.05f), -12.f);
		FlashBlue = MakeFlash(TEXT("FlashBlue"), FLinearColor(0.1f, 0.3f, 1.f), 12.f);
		Spot = NewObject<USpotLightComponent>(this, TEXT("Spot"));
		Spot->SetupAttachment(Police);
		Spot->SetRelativeLocation(FVector(48.f, 0.f, 10.f));
		Spot->SetIntensityUnits(ELightUnits::Lumens);
		Spot->SetIntensity(0.f);
		Spot->SetAttenuationRadius(5000.f);
		Spot->SetInnerConeAngle(5.f);
		Spot->SetOuterConeAngle(11.f);
		Spot->SetLightColor(FLinearColor(0.85f, 0.92f, 1.f));
		Spot->SetCastShadows(true);
		Spot->SetVolumetricScatteringIntensity(0.3f);
		Spot->RegisterComponent();
		Siren = NewObject<UAudioComponent>(this, TEXT("Siren"));
		Siren->SetupAttachment(Police);
		Siren->bAutoActivate = false;
		Siren->SetSound(SirenSound);
		Siren->AttenuationSettings = Attenuation;
		Siren->RegisterComponent();
	}
	if (Suspect)
	{
		SuspectEngine = NewObject<UAudioComponent>(this, TEXT("SuspectEngine"));
		SuspectEngine->SetupAttachment(Suspect);
		SuspectEngine->bAutoActivate = false;
		SuspectEngine->SetSound(EngineSound);
		SuspectEngine->AttenuationSettings = Attenuation;
		SuspectEngine->RegisterComponent();
	}
	BlastLight = NewObject<UPointLightComponent>(this, TEXT("BlastLight"));
	BlastLight->SetMobility(EComponentMobility::Movable);
	BlastLight->SetIntensityUnits(ELightUnits::Lumens);
	BlastLight->SetIntensity(0.f);
	BlastLight->SetAttenuationRadius(9000.f);
	BlastLight->SetLightColor(FLinearColor(1.f, 0.55f, 0.2f));
	BlastLight->SetCastShadows(false);
	BlastLight->RegisterComponent();
	for (int32 i = 0; i < 12; ++i)
	{
		UStaticMeshComponent* T = NewObject<UStaticMeshComponent>(this);
		T->SetMobility(EComponentMobility::Movable);
		T->SetStaticMesh(TracerMesh);
		T->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		T->SetCastShadow(false);
		T->SetVisibility(false);
		T->RegisterComponent();
		Tracers.Add(T);
		TracerLife.Add(0.f);
	}
}

FVector ANVTramRideDirector::TramLocal(const FVector& L) const
{
	return TramLoc + Fwd * L.X + Right * L.Y + FVector::UpVector * L.Z;
}

FVector ANVTramRideDirector::Sample(const TArray<FKey>& Keys, float T)
{
	if (Keys.Num() == 0) { return FVector::ZeroVector; }
	if (T <= Keys[0].T) { return Keys[0].P; }
	for (int32 i = 0; i + 1 < Keys.Num(); ++i)
	{
		if (T <= Keys[i + 1].T)
		{
			const FVector P0 = Keys[FMath::Max(i - 1, 0)].P, P1 = Keys[i].P, P2 = Keys[i + 1].P, P3 = Keys[FMath::Min(i + 2, Keys.Num() - 1)].P;
			const float U = (T - Keys[i].T) / FMath::Max(Keys[i + 1].T - Keys[i].T, 0.01f);
			// Catmull-Rom through the keys
			const float U2 = U * U, U3 = U2 * U;
			return 0.5f * ((2.f * P1) + (-P0 + P2) * U + (2.f * P0 - 5.f * P1 + 4.f * P2 - P3) * U2 + (-P0 + 3.f * P1 - 3.f * P2 + P3) * U3);
		}
	}
	return Keys.Last().P;
}

void ANVTramRideDirector::UpdateFrame(float Dt)
{
	AActor* Tram = Ride ? Ride->Tram.Get() : nullptr;
	if (!Tram) { return; }
	TramLoc = Tram->GetActorLocation();
	const FVector Move = (TramLoc - PrevTramLoc) * FVector(1, 1, 0);
	if (PrevTramLoc.IsZero())
	{
		Fwd = Tram->GetActorRotation().Vector().RotateAngleAxis(-Ride->TramYawOffset, FVector::UpVector).GetSafeNormal2D();
	}
	else if (Move.Size() > 1.f)
	{
		Fwd = FMath::Lerp(Fwd, Move.GetSafeNormal(), FMath::Clamp(Dt * 4.f, 0.f, 1.f)).GetSafeNormal();
	}
	PrevTramLoc = TramLoc;
	Right = FVector::CrossProduct(FVector::UpVector, Fwd).GetSafeNormal();
}

void ANVTramRideDirector::PlaceCar(UStaticMeshComponent* Car, const FVector& World, float Dt, FVector& PrevWorld, float Roll)
{
	if (!Car) { return; }
	const FVector V = PrevWorld.IsZero() ? Fwd : (World - PrevWorld) / FMath::Max(Dt, 0.001f);
	FRotator R = V.Size() > 50.f ? V.Rotation() : Car->GetComponentRotation();
	R.Pitch = FMath::Clamp(R.Pitch, -25.f, 25.f);
	// bank into turns: lateral component of the change in heading
	const float Turn = PrevWorld.IsZero() ? 0.f : FMath::FindDeltaAngleDegrees(Car->GetComponentRotation().Yaw, R.Yaw) / FMath::Max(Dt, 0.001f);
	R.Roll = FMath::Clamp(Turn * 0.35f, -35.f, 35.f) + Roll;
	Car->SetWorldLocationAndRotation(World, FMath::RInterpTo(Car->GetComponentRotation(), R, Dt, 8.f));
	if (Roll != 0.f)
	{
		Car->SetWorldRotation(R);
	}
	PrevWorld = World;
	Car->SetVisibility(true, true);
}

void ANVTramRideDirector::FireShot(const FVector& From, const FVector& To, bool bPolice)
{
	const FVector Aim = To + FMath::VRand() * FMath::FRandRange(60.f, 260.f);
	const FVector D = Aim - From;
	for (int32 i = 0; i < Tracers.Num(); ++i)
	{
		if (TracerLife[i] <= 0.f && Tracers[i])
		{
			UStaticMeshComponent* T = Tracers[i];
			T->SetMaterial(0, bPolice ? PoliceTracer : SuspectTracer);
			T->SetWorldLocation(From + D * 0.5f);
			T->SetWorldRotation(FRotationMatrix::MakeFromZ(D.GetSafeNormal()).Rotator());
			T->SetWorldScale3D(FVector(0.12f, 0.12f, D.Size() / 100.f));
			T->SetVisibility(true);
			TracerLife[i] = 0.1f;
			break;
		}
	}
	if (ShotSounds.Num() > 0)
	{
		if (USoundBase* S = ShotSounds[FMath::RandRange(0, ShotSounds.Num() - 1)])
		{
			UGameplayStatics::PlaySoundAtLocation(this, S, From, FMath::FRandRange(0.7f, 0.95f), FMath::FRandRange(0.9f, 1.1f), 0.f, Attenuation);
		}
	}
}

void ANVTramRideDirector::Explode(const FVector& At)
{
	bExploded = true;
	if (Police) { Police->SetVisibility(false, true); }
	if (Siren) { Siren->FadeOut(0.3f, 0.f); }
	if (SmokeTrail) { SmokeTrail->Deactivate(); }
	if (ExplosionFX) { UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, ExplosionFX, At, FRotator::ZeroRotator, FVector(ExplosionScale)); }
	if (FireFX) { UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, FireFX, At, FRotator::ZeroRotator, FVector(ExplosionScale * 0.8f), false); }
	if (SmokeFX) { UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SmokeFX, At + FVector(0, 0, 200), FRotator::ZeroRotator, FVector(ExplosionScale), false); }
	if (ExplosionSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, ExplosionSound, At, 1.f, 0.8f, 0.f, Attenuation);
		UGameplayStatics::PlaySound2D(this, ExplosionSound, 0.35f, 0.6f);   // the low thump through the cabin
	}
	BlastLight->SetWorldLocation(At);
	BlastAge = 0.f;
	UE_LOG(LogNeonVeil, Log, TEXT("%s: patrol car down at %s"), *GetName(), *At.ToString());
}

void ANVTramRideDirector::SayLine(const FNVSubtitleLine& Line)
{
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
	{
		if (ANVHUD* Hud = Cast<ANVHUD>(PC->GetHUD()))
		{
			Hud->QueueSubtitles({ Line });
		}
	}
}

void ANVTramRideDirector::Tick(float Dt)
{
	Super::Tick(Dt);
	if (!Ride) { return; }
	const float T = Ride->GetRideTime();
	if (T < 0.f) { return; }

	while (NextLine < Lines.Num() && Lines[NextLine].Time <= T)
	{
		SayLine(Lines[NextLine].Line);
		++NextLine;
	}

	for (int32 i = 0; i < Tracers.Num(); ++i)
	{
		if (TracerLife[i] > 0.f && (TracerLife[i] -= Dt) <= 0.f && Tracers[i]) { Tracers[i]->SetVisibility(false); }
	}
	if (BlastAge >= 0.f)
	{
		BlastAge += Dt;
		const float A = BlastAge < 0.08f ? BlastAge / 0.08f : FMath::Exp(-(BlastAge - 0.08f) * 1.6f);
		BlastLight->SetIntensity(600000.f * A);
		if (BlastAge > 6.f) { BlastLight->SetIntensity(0.f); BlastAge = -1.f; }
	}

	const float C = T - ChaseStart;
	if (C < 0.f || C > 40.f) { return; }
	UpdateFrame(Dt);
	if (!bStarted)
	{
		bStarted = true;
		if (Siren && SirenSound) { Siren->FadeIn(1.5f, 1.f); }
		if (SuspectEngine && EngineSound) { SuspectEngine->Play(); }
		UE_LOG(LogNeonVeil, Log, TEXT("%s: pursuit begins at ride %.1f s"), *GetName(), T);
	}

	// suspect
	if (Suspect)
	{
		if (C < SuspectGone)
		{
			PlaceCar(Suspect, TramLocal(Sample(SuspectKeys, C)), Dt, SuspectPrev, 0.f);
		}
		else if (Suspect->IsVisible())
		{
			Suspect->SetVisibility(false, true);
			if (SuspectEngine) { SuspectEngine->FadeOut(0.5f, 0.f); }
		}
	}

	// police
	if (Police && !bExploded)
	{
		const bool bFlashA = FMath::Fmod(C, 0.24f) < 0.12f;
		BarRed->SetVisibility(bFlashA);
		BarBlue->SetVisibility(!bFlashA);
		FlashRed->SetIntensity(bFlashA ? 9000.f : 0.f);
		FlashBlue->SetIntensity(bFlashA ? 0.f : 12000.f);
		if (!bHit)
		{
			PlaceCar(Police, TramLocal(Sample(PoliceKeys, C)), Dt, PolicePrev, 0.f);
			const bool bSpot = C >= SpotFrom && C <= SpotTo;
			Spot->SetIntensity(bSpot ? 16000.f : 0.f);
			if (bSpot)
			{
				// sweep the beam slowly along the cabin
				const float Sweep = FMath::Sin((C - SpotFrom) * 1.4f) * 350.f;
				const FVector Target = TramLocal(FVector(Sweep, 0.f, 140.f));
				Spot->SetWorldRotation((Target - Spot->GetComponentLocation()).Rotation());
			}
		}
		if (!bHit && C >= HitAt)
		{
			bHit = true;
			Spot->SetIntensity(0.f);
			CrashFrom = Police->GetComponentLocation();
			// down and away into the nearest facade, but close enough to fill the windows
			const FVector Aim = CrashFrom + Fwd * 2200.f - Right * Side * 1800.f + FVector(0, 0, -900.f);
			FHitResult Hit;
			FCollisionQueryParams Q(SCENE_QUERY_STAT(NVChaseCrash), false, this);
			Q.AddIgnoredActor(Ride->Tram.Get());
			const bool bWall = GetWorld()->LineTraceSingleByChannel(Hit, CrashFrom, CrashFrom + (Aim - CrashFrom) * 2.f, ECC_Visibility, Q);
			CrashTo = (bWall && Hit.Distance < 5000.f) ? Hit.ImpactPoint : Aim;
			if (SparksFX) { UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SparksFX, CrashFrom, FRotator::ZeroRotator, FVector(3.f)); }
			if (SmokeFX) { SmokeTrail = UNiagaraFunctionLibrary::SpawnSystemAttached(SmokeFX, Police, NAME_None, FVector::ZeroVector, FRotator::ZeroRotator, EAttachLocation::SnapToTarget, false); }
			UE_LOG(LogNeonVeil, Log, TEXT("%s: patrol car hit, going down toward %s"), *GetName(), *CrashTo.ToString());
		}
		if (bHit)
		{
			const float A = FMath::Clamp((C - HitAt) / CrashTime, 0.f, 1.f);
			const FVector P = FMath::Lerp(CrashFrom, CrashTo, A * A) + FVector(0, 0, FMath::Sin(A * PI) * 250.f);
			PlaceCar(Police, P, Dt, PolicePrev, 540.f * A * A);
			if (A >= 1.f) { Explode(CrashTo); }
		}
	}

	// firefight
	if (Suspect && Police && !bHit && C >= FightFrom)
	{
		const FVector S = Suspect->GetComponentLocation(), P = Police->GetComponentLocation();
		if (C >= NextSuspectShot)
		{
			FireShot(S - (S - P).GetSafeNormal() * 300.f, P, false);
			NextSuspectShot = C + FMath::FRandRange(0.3f, 0.55f);
		}
		if (C >= NextPoliceShot)
		{
			FireShot(P + (S - P).GetSafeNormal() * 300.f, S, true);
			NextPoliceShot = C + (++PoliceBurst % 3 == 0 ? FMath::FRandRange(0.5f, 0.8f) : 0.1f);
		}
	}
}
