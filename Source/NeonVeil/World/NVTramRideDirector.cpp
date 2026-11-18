#include "World/NVTramRideDirector.h"

#include "NeonVeil.h"
#include "World/NVTramRide.h"
#include "World/NVBlastShake.h"
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
	BlastLight->SetAttenuationRadius(20000.f);
	BlastLight->SetLightColor(FLinearColor(1.f, 0.55f, 0.2f));
	BlastLight->SetCastShadows(false);
	BlastLight->RegisterComponent();
	for (int32 m = 0; m < 2; ++m)
	{
		UPointLightComponent* L = NewObject<UPointLightComponent>(this);
		L->SetMobility(EComponentMobility::Movable);
		L->SetIntensityUnits(ELightUnits::Lumens);
		L->SetIntensity(0.f);
		L->SetAttenuationRadius(1400.f);
		L->SetLightColor(m == 0 ? FLinearColor(1.f, 0.35f, 0.1f) : FLinearColor(0.35f, 0.6f, 1.f));
		L->SetCastShadows(false);
		L->RegisterComponent();
		(m == 0 ? MuzzleSuspect : MuzzlePolice) = L;
	}
	for (int32 i = 0; i < 16; ++i)
	{
		UStaticMeshComponent* T = NewObject<UStaticMeshComponent>(this);
		T->SetMobility(EComponentMobility::Movable);
		T->SetStaticMesh(TracerMesh);
		T->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		T->SetCastShadow(false);
		T->SetVisibility(false);
		T->RegisterComponent();
		Tracers.Add(T);
		TracerBusy.Add(false);
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

FVector ANVTramRideDirector::Muzzle(const UStaticMeshComponent* Shooter, const FVector& Dir) const
{
	// the hull surface facing the target: project the bounds box onto the firing direction
	const FVector E = Shooter->Bounds.BoxExtent;
	const float Reach = FMath::Abs(Dir.X) * E.X + FMath::Abs(Dir.Y) * E.Y + FMath::Abs(Dir.Z) * E.Z;
	return Shooter->Bounds.Origin + Dir * Reach * 0.85f;
}

void ANVTramRideDirector::FireShot(bool bPolice)
{
	const UStaticMeshComponent* From = bPolice ? Police.Get() : Suspect.Get();
	const UStaticMeshComponent* To = bPolice ? Suspect.Get() : Police.Get();
	if (!From || !To) { return; }
	int32 Free = INDEX_NONE;
	for (int32 i = 0; i < Tracers.Num(); ++i) { if (!TracerBusy[i] && Tracers[i]) { Free = i; break; } }
	if (Free == INDEX_NONE) { return; }

	FBolt B;
	B.bPolice = bPolice;
	// the last shots before the patrol car is hit always land, so the hit reads as caused by the gunfire
	const float C = Ride ? Ride->GetRideTime() - ChaseStart : 0.f;
	B.bHit = (!bPolice && C > HitAt - 0.7f) || FMath::FRand() < (bPolice ? PoliceAccuracy : SuspectAccuracy);
	// aim point in tram axes (X fwd, Y right, Z up) relative to the target's centre: on the hull for hits,
	// a near miss just past it otherwise
	const FVector E = To->Bounds.BoxExtent;
	if (B.bHit)
	{
		B.AimOfs = FVector(FMath::FRandRange(-0.45f, 0.45f) * E.X, FMath::FRandRange(-0.3f, 0.3f) * E.Y, FMath::FRandRange(-0.3f, 0.35f) * E.Z);
	}
	else
	{
		const float Ang = FMath::FRandRange(0.f, 2.f * PI);
		B.AimOfs = FVector(FMath::FRandRange(-0.5f, 0.5f) * E.X, FMath::Cos(Ang) * (E.Y + 160.f), FMath::Sin(Ang) * (E.Z + 120.f));
	}
	const FVector D = (To->Bounds.Origin - From->Bounds.Origin);
	B.Flight = FMath::Clamp(D.Size() / FMath::Max(BoltSpeed, 1000.f), 0.05f, 0.3f);
	B.Tracer = Free;
	TracerBusy[Free] = true;
	UStaticMeshComponent* T = Tracers[Free];
	T->SetMaterial(0, bPolice ? PoliceTracer : SuspectTracer);
	Bolts.Add(B);

	// muzzle flash at the gun side of the hull
	const FVector M = Muzzle(From, D.GetSafeNormal());
	UPointLightComponent* L = bPolice ? MuzzlePolice : MuzzleSuspect;
	if (L) { L->SetWorldLocation(M); }
	MuzzleAge[bPolice ? 1 : 0] = 0.f;
	if (ShotSounds.Num() > 0)
	{
		if (USoundBase* S = ShotSounds[FMath::RandRange(0, ShotSounds.Num() - 1)])
		{
			UGameplayStatics::PlaySoundAtLocation(this, S, M, FMath::FRandRange(0.7f, 0.95f), FMath::FRandRange(0.9f, 1.1f), 0.f, Attenuation);
		}
	}
}

void ANVTramRideDirector::UpdateBolts(float Dt)
{
	for (int32 m = 0; m < 2; ++m)
	{
		MuzzleAge[m] += Dt;
		UPointLightComponent* L = m == 0 ? MuzzleSuspect : MuzzlePolice;
		if (L) { L->SetIntensity(MuzzleAge[m] < 0.05f ? 60000.f : 0.f); }
	}
	for (int32 i = Bolts.Num() - 1; i >= 0; --i)
	{
		FBolt& B = Bolts[i];
		const UStaticMeshComponent* From = B.bPolice ? Police.Get() : Suspect.Get();
		const UStaticMeshComponent* To = B.bPolice ? Suspect.Get() : Police.Get();
		UStaticMeshComponent* T = Tracers.IsValidIndex(B.Tracer) ? Tracers[B.Tracer].Get() : nullptr;
		B.Age += Dt;
		const bool bGone = !From || !To || !T || !To->IsVisible() || bExploded;
		// a near miss carries on past the target for a little longer before it fades
		const float End = B.bHit ? 1.f : 1.8f;
		const float A = B.Age / B.Flight;
		if (bGone || A >= End)
		{
			if (!bGone && B.bHit)
			{
				const FVector Hit = To->Bounds.Origin + Fwd * B.AimOfs.X + Right * B.AimOfs.Y + FVector::UpVector * B.AimOfs.Z;
				if (SparksFX && FMath::FRand() < 0.7f)
				{
					UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SparksFX, Hit, FRotator::ZeroRotator, FVector(B.bPolice ? 1.2f : 1.6f));
				}
			}
			if (T) { T->SetVisibility(false); }
			if (TracerBusy.IsValidIndex(B.Tracer)) { TracerBusy[B.Tracer] = false; }
			Bolts.RemoveAt(i);
			continue;
		}
		// muzzle and aim follow both cars this frame
		const FVector Aim = To->Bounds.Origin + Fwd * B.AimOfs.X + Right * B.AimOfs.Y + FVector::UpVector * B.AimOfs.Z;
		const FVector Dir = (Aim - From->Bounds.Origin).GetSafeNormal();
		const FVector M0 = Muzzle(From, Dir);
		const FVector Head = M0 + (Aim - M0) * A;
		const float Len = FMath::Min(BoltLength, FVector::Dist(M0, Head));
		if (Len < 5.f) { T->SetVisibility(false); continue; }
		const FVector Tail = Head - Dir * Len;
		T->SetWorldLocation((Head + Tail) * 0.5f);
		T->SetWorldRotation(FRotationMatrix::MakeFromZ(Dir).Rotator());
		T->SetWorldScale3D(FVector(BoltThickness, BoltThickness, Len / 100.f));
		T->SetVisibility(true);
	}
}

void ANVTramRideDirector::Explode(const FVector& At)
{
	bExploded = true;
	if (Police) { Police->SetVisibility(false, true); }
	if (Siren) { Siren->Stop(); }
	if (SirenDying) { SirenDying->Stop(); }
	if (SmokeTrail) { SmokeTrail->Deactivate(); }
	const float S = ExplosionScale;
	if (ExplosionFX)
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, ExplosionFX, At, FRotator::ZeroRotator, FVector(S * 2.2f));
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, ExplosionFX, At + FVector(0, 0, 350), FRotator(0, 90, 0), FVector(S * 1.6f));
	}
	if (SparksFX)
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SparksFX, At, FRotator::ZeroRotator, FVector(S * 2.f));
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SparksFX, At + FVector(0, 0, 300), FRotator(180, 0, 0), FVector(S * 1.5f));
	}
	if (FireFX)
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, FireFX, At, FRotator::ZeroRotator, FVector(S * 1.4f), false);
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, FireFX, At + Fwd * 500.f + FVector(0, 0, -150), FRotator::ZeroRotator, FVector(S * 0.9f), false);
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, FireFX, At - Fwd * 450.f + FVector(0, 0, 200), FRotator::ZeroRotator, FVector(S * 0.8f), false);
	}
	if (SmokeFX)
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SmokeFX, At + FVector(0, 0, 300), FRotator::ZeroRotator, FVector(S * 1.8f), false);
	}
	// the blast itself: located explosion + full-weight 2D layers so it hits you in the cabin
	if (ExplosionSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, ExplosionSound, At, 1.5f, 0.75f, 0.f, Attenuation);
		UGameplayStatics::PlaySound2D(this, ExplosionSound, 0.9f, 0.55f);
	}
	if (BigExplosionSound) { UGameplayStatics::PlaySound2D(this, BigExplosionSound, 1.6f); }
	if (BassHitSound) { UGameplayStatics::PlaySound2D(this, BassHitSound, BassHitVolume); }
	UNVBlastShake::Kick(this, BlastShake, 0.55f);
	// cook-offs: a chain of follow-up blasts around the wreck
	PendingBlasts = {
		{ 0.45f, At + Fwd * 420.f + FVector(0, 0, 260), 0.9f, true },
		{ 0.95f, At - Fwd * 380.f + FVector(0, 0, -120), 0.7f, false },
		{ 1.6f, At + FVector(0, 0, 520), 1.1f, true },
		{ 2.4f, At + Fwd * 700.f + FVector(0, 0, -300), 0.6f, false },
		{ 3.3f, At - Fwd * 200.f + FVector(0, 0, 150), 0.8f, true } };
	BlastLight->SetWorldLocation(At);
	BlastAge = 0.f;
	UE_LOG(LogNeonVeil, Log, TEXT("%s: patrol car down at %s"), *GetName(), *At.ToString());
}

void ANVTramRideDirector::SecondaryBlast(const FVector& At, float Scale, bool bLoud)
{
	const float S = ExplosionScale * Scale;
	if (ExplosionFX) { UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, ExplosionFX, At, FRotator(0, FMath::FRandRange(0.f, 360.f), 0), FVector(S * 1.3f)); }
	if (SparksFX) { UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SparksFX, At, FRotator::ZeroRotator, FVector(S)); }
	if (ExplosionSound) { UGameplayStatics::PlaySoundAtLocation(this, ExplosionSound, At, bLoud ? 1.3f : 0.9f, FMath::FRandRange(0.7f, 0.95f), 0.f, Attenuation); }
	if (bLoud && SecondaryExplosionSound && !bCookOffsPlaying)
	{
		// one long chain of cook-off blasts under all the follow-ups
		bCookOffsPlaying = true;
		UGameplayStatics::PlaySound2D(this, SecondaryExplosionSound, 1.1f);
	}
	if (bLoud && BassHitSound) { UGameplayStatics::PlaySound2D(this, BassHitSound, BassHitVolume * 0.45f, 1.15f); }
	UNVBlastShake::Kick(this, bLoud ? 0.45f : 0.25f, 0.9f);
	// re-flare the blast light
	BlastLight->SetWorldLocation(At);
	BlastAge = BlastAge < 0.f ? 0.f : FMath::Min(BlastAge, 0.3f);
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

	if (BlastAge >= 0.f)
	{
		BlastAge += Dt;
		const float A = BlastAge < 0.06f ? BlastAge / 0.06f : FMath::Exp(-(BlastAge - 0.06f) * 1.3f);
		// flicker like a fireball, settling into the burning wreck's glow
		BlastLight->SetIntensity(2500000.f * A * FMath::FRandRange(0.8f, 1.1f) + (bExploded ? 60000.f : 0.f));
		if (BlastAge > 12.f) { BlastLight->SetIntensity(0.f); BlastAge = -1.f; }
	}
	if (bExploded && PendingBlasts.Num() > 0)
	{
		ExplodeClock += Dt;
		while (PendingBlasts.Num() > 0 && PendingBlasts[0].Due <= ExplodeClock)
		{
			const FPendingBlast B = PendingBlasts[0];
			PendingBlasts.RemoveAt(0);
			SecondaryBlast(B.At, B.Scale, B.bLoud);
		}
	}

	const float C = T - ChaseStart;
	if (C < 0.f || C > 40.f) { return; }
	UpdateFrame(Dt);
	if (!bStarted)
	{
		bStarted = true;
		if (Siren && SirenSound) { Siren->FadeIn(1.5f, SirenVolume); }
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
		if (!bHit)
		{
			const bool bFlashA = FMath::Fmod(C, 0.24f) < 0.12f;
			BarRed->SetVisibility(bFlashA);
			BarBlue->SetVisibility(!bFlashA);
			FlashRed->SetIntensity(bFlashA ? 9000.f : 0.f);
			FlashBlue->SetIntensity(bFlashA ? 0.f : 12000.f);
		}
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
			if (SparksFX) { UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SparksFX, CrashFrom, FRotator::ZeroRotator, FVector(5.f)); }
			if (ExplosionFX) { UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, ExplosionFX, CrashFrom, FRotator::ZeroRotator, FVector(ExplosionScale * 0.35f)); }
			if (ExplosionSound) { UGameplayStatics::PlaySoundAtLocation(this, ExplosionSound, CrashFrom, 0.8f, 1.3f, 0.f, Attenuation); }
			UNVBlastShake::Kick(this, 0.3f, 1.2f);
			if (SirenDyingSound && Siren)
			{
				Siren->FadeOut(0.05f, 0.f);
				SirenDying = UGameplayStatics::SpawnSoundAttached(SirenDyingSound, Police, NAME_None, FVector::ZeroVector,
					EAttachLocation::KeepRelativeOffset, false, SirenVolume * 1.1f, 1.f, 0.f, Attenuation);
			}
			NextSparkBurst = C + 0.25f;
			if (SmokeFX) { SmokeTrail = UNiagaraFunctionLibrary::SpawnSystemAttached(SmokeFX, Police, NAME_None, FVector::ZeroVector, FRotator::ZeroRotator, EAttachLocation::SnapToTarget, false); }
			UE_LOG(LogNeonVeil, Log, TEXT("%s: patrol car hit, going down toward %s"), *GetName(), *CrashTo.ToString());
		}
		if (bHit)
		{
			const float A = FMath::Clamp((C - HitAt) / CrashTime, 0.f, 1.f);
			const FVector P = FMath::Lerp(CrashFrom, CrashTo, A * A) + FVector(0, 0, FMath::Sin(A * PI) * 250.f);
			PlaceCar(Police, P, Dt, PolicePrev, 540.f * A * A);
			// the siren winds down and detunes as the car tumbles: pitch sags toward SirenDyingPitch with a
			// growing warble, like the motor losing power
			if (Siren && !SirenDying)
			{
				const float Sag = FMath::InterpEaseIn(1.f, SirenDyingPitch, A, 1.6f);
				const float Warble = 1.f + FMath::Sin((C - HitAt) * 21.f) * 0.05f * A + FMath::Sin((C - HitAt) * 7.3f) * 0.03f * A;
				Siren->SetPitchMultiplier(FMath::Max(0.2f, Sag * Warble));
				Siren->SetVolumeMultiplier(SirenVolume * (1.f - 0.25f * A));
			}
			// light bar stutters as the car breaks up
			const bool bOn = FMath::FRand() > 0.35f + 0.4f * A;
			BarRed->SetVisibility(bOn && FMath::FRand() > 0.5f);
			BarBlue->SetVisibility(bOn && !BarRed->IsVisible());
			FlashRed->SetIntensity(BarRed->IsVisible() ? 12000.f : 0.f);
			FlashBlue->SetIntensity(BarBlue->IsVisible() ? 15000.f : 0.f);
			if (SparksFX && C >= NextSparkBurst)
			{
				UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SparksFX, Police->GetComponentLocation(), FRotator::ZeroRotator, FVector(2.5f));
				NextSparkBurst = C + FMath::FRandRange(0.18f, 0.35f);
			}
			if (A >= 1.f) { Explode(CrashTo); }
		}
	}

	// firefight: short controlled bursts from both cars, the suspect's bursts getting longer toward the hit
	if (Suspect && Police && !bHit && C >= FightFrom)
	{
		if (C >= NextSuspectShot)
		{
			FireShot(false);
			const int32 Len = C > HitAt - 2.5f ? 5 : 3;
			NextSuspectShot = C + (++SuspectBurst % Len == 0 ? FMath::FRandRange(0.35f, 0.6f) : 0.09f);
		}
		if (C >= NextPoliceShot)
		{
			FireShot(true);
			NextPoliceShot = C + (++PoliceBurst % 3 == 0 ? FMath::FRandRange(0.55f, 0.85f) : 0.1f);
		}
	}
	UpdateBolts(Dt);
}
