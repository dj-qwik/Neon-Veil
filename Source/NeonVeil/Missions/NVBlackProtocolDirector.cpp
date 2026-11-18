#include "Missions/NVBlackProtocolDirector.h"
#include "AI/NVEnemyController.h"
#include "AI/NVGuardCharacter.h"
#include "AI/NVSecurityDrone.h"
#include "AI/NVSentryTurret.h"
#include "Abilities/NVAbilityComponent.h"
#include "Character/NVPlayerCharacter.h"
#include "Combat/NVHealthComponent.h"
#include "Combat/NVWeaponComponent.h"
#include "Core/NVGameplayTags.h"
#include "Interaction/NVInteractableActor.h"
#include "Objectives/NVObjectiveData.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "UI/NVHUD.h"
#include "World/NVObjectiveDoor.h"
#include "NeonVeil.h"

#include "Camera/PlayerCameraManager.h"
#include "Components/AudioComponent.h"
#include "Components/LightComponent.h"
#include "Engine/Light.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "NiagaraFunctionLibrary.h"
#include "TimerManager.h"

namespace
{
	const FName O01(TEXT("M01-O01"));

	ANVPlayerCharacter* GetPlayer(const UObject* Ctx)
	{
		return Cast<ANVPlayerCharacter>(UGameplayStatics::GetPlayerPawn(Ctx, 0));
	}
	ANVHUD* GetHUD(const UObject* Ctx)
	{
		const APlayerController* PC = UGameplayStatics::GetPlayerController(Ctx, 0);
		return PC ? Cast<ANVHUD>(PC->GetHUD()) : nullptr;
	}
}

ANVBlackProtocolDirector::ANVBlackProtocolDirector()
{
	PrimaryActorTick.bCanEverTick = true;
	SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));
}

bool ANVBlackProtocolDirector::IsM01Running() const
{
	const UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this);
	return Obj && Obj->GetCurrentMission() && Obj->GetCurrentMission()->MissionID == TEXT("M01");
}

bool ANVBlackProtocolDirector::IsDone(const TCHAR* ObjectiveID) const
{
	const UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this);
	return IsM01Running() && Obj->IsObjectiveComplete(FName(ObjectiveID));
}

void ANVBlackProtocolDirector::BeginPlay()
{
	Super::BeginPlay();
	for (ALight* L : LightsToAlarm)
	{
		if (L && L->GetLightComponent())
		{
			BaseIntensity.Add(L, L->GetLightComponent()->Intensity);
		}
	}
	for (ALight* L : EmergencyLights)
	{
		if (L && L->GetLightComponent())
		{
			BaseIntensity.Add(L, L->GetLightComponent()->Intensity);
			L->GetLightComponent()->SetVisibility(false);
		}
	}
	for (ALight* L : FlickerLights)
	{
		if (L && L->GetLightComponent())
		{
			BaseIntensity.Add(L, L->GetLightComponent()->Intensity);
		}
	}
	InitMovers(Shutters);
	InitMovers(SurgicalArms);
	InitMover(LiftGate);
	InitMover(EvacTube);
	InitMover(EvacPlatform);
	if (LiftCab)
	{
		LiftStart = LiftCab->GetActorLocation();
	}
	if (AgencyTag)
	{
		AgencyTag->SetEnabled(false);
	}
	if (UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this))
	{
		Obj->OnObjectiveActivated.AddDynamic(this, &ANVBlackProtocolDirector::HandleObjectiveActivated);
		Obj->OnObjectiveCompleted.AddDynamic(this, &ANVBlackProtocolDirector::HandleObjectiveCompleted);
		Obj->OnGameplayEvent.AddDynamic(this, &ANVBlackProtocolDirector::HandleGameplayEvent);
	}
	// a checkpoint inside M01: every other actor has begun play by the next tick
	if (IsM01Running())
	{
		GetWorldTimerManager().SetTimerForNextTick(this, &ANVBlackProtocolDirector::ApplyRestoredState);
	}
}

// ------------------------------------------------------------------------------------------------ helpers

void ANVBlackProtocolDirector::Say(const TArray<FNVSubtitleLine>& Lines)
{
	if (ANVHUD* HUD = GetHUD(this))
	{
		if (Lines.Num() > 0)
		{
			HUD->QueueSubtitles(Lines);
		}
	}
}

void ANVBlackProtocolDirector::GlitchHUD(float Seconds)
{
	// Bible: interference under 0.6 s, never during a firefight beat long enough to hide reticle or health
	Seconds = FMath::Min(Seconds, 0.55f);
	if (ANVHUD* HUD = GetHUD(this))
	{
		HUD->SetHUDVisible(false);
		TWeakObjectPtr<ANVHUD> W(HUD);
		GetWorldTimerManager().SetTimer(GlitchTimer, FTimerDelegate::CreateLambda([W]() { if (W.IsValid()) { W->SetHUDVisible(true); } }), Seconds, false);
	}
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
	{
		if (PC->PlayerCameraManager)
		{
			PC->PlayerCameraManager->StartCameraFade(0.45f, 0.f, Seconds, FLinearColor(0.6f, 0.f, 0.02f), false, false);
		}
	}
	if (GlitchSound)
	{
		UGameplayStatics::PlaySound2D(this, GlitchSound, 0.8f);
	}
}

void ANVBlackProtocolDirector::InitMover(FNVMover& M)
{
	if (M.Actor)
	{
		M.Start = M.Actor->GetActorTransform();
	}
}

void ANVBlackProtocolDirector::InitMovers(TArray<FNVMover>& Movers)
{
	for (FNVMover& M : Movers)
	{
		InitMover(M);
	}
}

void ANVBlackProtocolDirector::SetMover(FNVMover& M, float Target, float Speed, bool bInstant)
{
	M.Target = Target;
	M.Speed = FMath::Max(0.05f, Speed);
	if (bInstant)
	{
		M.Alpha = Target - 0.0001f;   // TickMover snaps it on the next frame
	}
}

void ANVBlackProtocolDirector::SetMovers(TArray<FNVMover>& Movers, float Target, float Speed, bool bInstant)
{
	for (FNVMover& M : Movers)
	{
		SetMover(M, Target, Speed, bInstant);
	}
}

void ANVBlackProtocolDirector::TickMover(FNVMover& M, float Dt)
{
	if (!M.Actor || FMath::IsNearlyEqual(M.Alpha, M.Target, 0.00001f))
	{
		return;
	}
	M.Alpha = FMath::FInterpConstantTo(M.Alpha, M.Target, Dt, M.Speed);
	if (FMath::Abs(M.Alpha - M.Target) < 0.001f)
	{
		M.Alpha = M.Target;
	}
	const float E = FMath::InterpEaseInOut(0.f, 1.f, M.Alpha, 2.f);
	const FVector L = M.Start.GetLocation() + M.Offset * E;
	const FQuat Q = M.Start.GetRotation() * FQuat(M.Rotation * E);
	M.Actor->SetActorLocationAndRotation(L, Q, false, nullptr, ETeleportType::None);
}

void ANVBlackProtocolDirector::TickMovers(TArray<FNVMover>& Movers, float Dt)
{
	for (FNVMover& M : Movers)
	{
		TickMover(M, Dt);
	}
}

// ------------------------------------------------------------------------------------------------ events

void ANVBlackProtocolDirector::HandleObjectiveActivated(FName ObjectiveID)
{
	if (ObjectiveID == O01 && !bLockdownStarted)
	{
		StartLockdown();
	}
}

void ANVBlackProtocolDirector::HandleObjectiveCompleted(FName ObjectiveID)
{
	if (ObjectiveID == O01 && ArteryTurret && ArteryTurret->GetMode() == ENVTurretMode::Off)
	{
		ArteryTurret->SetMode(ENVTurretMode::Hostile);
	}
	if (ObjectiveID == O01)
	{
		// reaching the emergency door saves the next checkpoint (CP_M01_Artery): the escape track ends here
		StopEscapeMusic(EscapeMusicFadeOut);
	}
}

void ANVBlackProtocolDirector::HandleGameplayEvent(FGameplayTag EventTag)
{
	if (EventTag == NVTags::Event_M01_DroneDown)
	{
		CheckDrones();
	}
	else if (EventTag == NVTags::Event_M01_LiftCalled)
	{
		StartLift();
	}
	else if (EventTag == NVTags::Event_M01_ReclamationStart)
	{
		StartReclamation();
	}
}

// ------------------------------------------------------------------------------------------------ A lockdown

void ANVBlackProtocolDirector::ApplyLockdownWorld(bool bInstant)
{
	for (ALight* L : LightsToAlarm)
	{
		if (L && L->GetLightComponent())
		{
			L->GetLightComponent()->SetLightColor(AlarmColor);
			L->GetLightComponent()->SetIntensity(BaseIntensity.FindRef(L) * AlarmIntensityScale);
		}
	}
	for (ALight* L : EmergencyLights)
	{
		if (L && L->GetLightComponent())
		{
			L->GetLightComponent()->SetVisibility(true);
		}
	}
	SetMovers(Shutters, 1.f, 0.8f, bInstant);
	for (ANVObjectiveDoor* D : DoorsToSeal)
	{
		if (D)
		{
			D->SetOpen(false, bInstant);
		}
	}
	if (EmergencyDoor && !bEmergencyOpen)
	{
		EmergencyDoor->SetOpen(false, true);
	}
	if (!bInstant && ShutterSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, ShutterSound, GetActorLocation());
	}
	if (AlarmSound && !Alarm)
	{
		Alarm = UGameplayStatics::SpawnSoundAtLocation(this, AlarmSound, GetActorLocation(), FRotator::ZeroRotator, 0.55f);
	}
}

void ANVBlackProtocolDirector::StartLockdown()
{
	bLockdownStarted = true;
	UE_LOG(LogNeonVeil, Log, TEXT("M01: Black Protocol lockdown"));
	Say(RevocationLines);
	const bool bDirectorBeat = TheDirector && !bDirectorGone;
	if (bDirectorBeat)
	{
		auto At = [this](float T, TFunction<void()> Fn)
		{
			FTimerHandle H;
			GetWorldTimerManager().SetTimer(H, FTimerDelegate::CreateWeakLambda(this, MoveTemp(Fn)), FMath::Max(0.01f, T), false);
		};
		At(DirTurnAt, [this]()
		{
			if (const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0))
			{
				DirectorTurnTo(P->GetActorLocation(), 1.4f);
			}
		});
		At(DirAppealAt, [this]() { Say(DirectorAppealLines); });
		At(DirSignTurnAt, [this]() { if (DirectorConsole) { DirectorTurnTo(DirectorConsole->GetActorLocation(), 0.9f); } });
		At(DirSignAt, [this]() { DirectorSign(); });
		At(DirApprovalAt, [this]()
		{
			Say(DirectorApprovalLines);
			if (const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0))
			{
				DirectorTurnTo(P->GetActorLocation(), 1.1f);
			}
			SetMover(EvacTube, 1.f, 0.7f, false);
		});
		At(DirEvacAt, [this]() { DirectorEvac(); });
		At(DirGoneAt, [this]() { DirectorGone(false); Say(AfterDirectorLines); StartEscapeMusic(1.5f); });
	}
	FTimerHandle H1, H2, H3;
	GetWorldTimerManager().SetTimer(H1, FTimerDelegate::CreateWeakLambda(this, [this]() { GlitchHUD(0.45f); }), 2.6f, false);
	GetWorldTimerManager().SetTimer(H2, FTimerDelegate::CreateWeakLambda(this, [this, bDirectorBeat]()
	{
		ApplyLockdownWorld(false);
		if (!bDirectorBeat)
		{
			StartEscapeMusic(1.f);
		}
	}), 3.0f, false);
	GetWorldTimerManager().SetTimer(H3, FTimerDelegate::CreateWeakLambda(this, [this]()
	{
		float Delay = 0.f;
		for (ANVSecurityDrone* D : LockdownDrones)
		{
			if (D && !D->IsDestroyed())
			{
				D->Activate(Delay);
				Delay += 1.2f;
			}
		}
	}), bDirectorBeat ? DronesAt : 4.5f, false);
	GetWorldTimerManager().SetTimer(DesignateTimer, FTimerDelegate::CreateWeakLambda(this, [this]() { Designate(false); }), DesignationDelay, false);
}

void ANVBlackProtocolDirector::StartEscapeMusic(float FadeSeconds)
{
	if (!CombatMusic || bEscapeMusicDone || (EscapeMusic && EscapeMusic->IsPlaying()))
	{
		return;
	}
	EscapeMusic = UGameplayStatics::SpawnSound2D(this, CombatMusic, CombatMusicVolume, 1.f, 0.f, nullptr, false, false);
	if (EscapeMusic)
	{
		EscapeMusic->FadeIn(FadeSeconds, CombatMusicVolume);
	}
}

void ANVBlackProtocolDirector::StopEscapeMusic(float FadeSeconds)
{
	bEscapeMusicDone = true;
	if (EscapeMusic && EscapeMusic->IsPlaying())
	{
		UE_LOG(LogNeonVeil, Log, TEXT("M01: escape music fading out (%.1f s)"), FadeSeconds);
		EscapeMusic->FadeOut(FadeSeconds, 0.f);
	}
	EscapeMusic = nullptr;
}

void ANVBlackProtocolDirector::DirectorTurnTo(const FVector& Target, float Seconds)
{
	if (!TheDirector)
	{
		return;
	}
	DirFrom = TheDirector->GetActorRotation();
	FVector D = Target - TheDirector->GetActorLocation();
	D.Z = 0.f;
	// BP_Director faces along its actor X (placed at yaw 0 looking into the glass)
	DirTo = FRotator(0.f, D.Rotation().Yaw, 0.f);
	DirTurnT = 0.f;
	DirTurnLen = FMath::Max(0.1f, Seconds);
}

void ANVBlackProtocolDirector::DirectorSign()
{
	UE_LOG(LogNeonVeil, Log, TEXT("M01: the Director signs the decommission order"));
	if (ConsoleLight && ConsoleLight->GetLightComponent())
	{
		ConsoleLight->GetLightComponent()->SetLightColor(AlarmColor);
		ConsoleLight->GetLightComponent()->SetIntensity(ConsoleLight->GetLightComponent()->Intensity * 2.5f);
	}
	if (SignSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, SignSound, DirectorConsole ? DirectorConsole->GetActorLocation() : GetActorLocation());
	}
	if (ANVHUD* HUD = GetHUD(this))
	{
		if (!SignedBody.IsEmpty())
		{
			HUD->ShowMessage(SignedSender, SignedBody, SignedChannel, true);
		}
	}
}

void ANVBlackProtocolDirector::DirectorEvac()
{
	if (EvacPlatform.Actor && TheDirector)
	{
		TheDirector->AttachToActor(EvacPlatform.Actor, FAttachmentTransformRules::KeepWorldTransform);
	}
	SetMover(EvacPlatform, 1.f, 0.28f, false);
	if (EvacSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, EvacSound, TheDirector ? TheDirector->GetActorLocation() : GetActorLocation());
	}
}

void ANVBlackProtocolDirector::DirectorGone(bool bInstant)
{
	bDirectorGone = true;
	DirTurnT = -1.f;
	for (AActor* A : { TheDirector.Get(), DirectorReflection.Get() })
	{
		if (A)
		{
			A->SetActorHiddenInGame(true);
			A->SetActorEnableCollision(false);
			A->SetActorTickEnabled(false);
		}
	}
	// the tube lifts back into the ceiling
	SetMover(EvacTube, 0.f, 0.5f, bInstant);
	SetMover(EvacPlatform, 1.f, 1.f, bInstant);
}

void ANVBlackProtocolDirector::SyncReflection()
{
	if (!TheDirector || !DirectorReflection || bDirectorGone)
	{
		return;
	}
	// mirror across the glass plane x = ReflectionPlaneX: x' = 2P - x, yaw' = -yaw (the double is scaled -1 in X)
	const FVector L = TheDirector->GetActorLocation();
	DirectorReflection->SetActorLocationAndRotation(FVector(2.f * ReflectionPlaneX - L.X, L.Y, L.Z),
		FRotator(0.f, -TheDirector->GetActorRotation().Yaw, 0.f));
}

void ANVBlackProtocolDirector::Designate(bool bInstant)
{
	if (bDesignated)
	{
		return;
	}
	bDesignated = true;
	if (!bInstant)
	{
		Say(DesignationLines);
		GlitchHUD(0.3f);
	}
	for (ANVGuardCharacter* G : GuardsToTurn)
	{
		if (G)
		{
			G->SetHostile(true);
		}
	}
	const bool bPastLockdown = IsDone(TEXT("M01-O01"));
	if (TrooperDoor && !bPastLockdown)
	{
		TrooperDoor->SetOpen(true, bInstant);
	}
	const ANVPlayerCharacter* P = GetPlayer(this);
	for (ANVGuardCharacter* G : LockdownTroopers)
	{
		if (!G)
		{
			continue;
		}
		if (bPastLockdown)
		{
			G->SetCorpse();
			continue;
		}
		G->SetHostile(true);
		if (ANVEnemyController* C = Cast<ANVEnemyController>(G->GetController()))
		{
			if (P)
			{
				C->AlertTo(P->GetActorLocation());
			}
		}
	}
}

void ANVBlackProtocolDirector::CheckDrones()
{
	if (bEmergencyOpen)
	{
		return;
	}
	for (const ANVSecurityDrone* D : LockdownDrones)
	{
		if (D && !D->IsDestroyed())
		{
			return;
		}
	}
	bEmergencyOpen = true;
	UE_LOG(LogNeonVeil, Log, TEXT("M01: lockdown drones down, emergency door open"));
	if (EmergencyDoor)
	{
		EmergencyDoor->SetOpen(true);
	}
	Say(DoorOpenLines);
	if (!bDesignated)
	{
		// both drones already gone: AION escalates right away
		GetWorldTimerManager().ClearTimer(DesignateTimer);
		GetWorldTimerManager().SetTimer(DesignateTimer, FTimerDelegate::CreateWeakLambda(this, [this]() { Designate(false); }), 2.5f, false);
	}
}

// ------------------------------------------------------------------------------------------------ restore

void ANVBlackProtocolDirector::ApplyRestoredState()
{
	if (!IsM01Running())
	{
		return;
	}
	UE_LOG(LogNeonVeil, Log, TEXT("M01: restoring world state from checkpoint"));
	DirectorGone(true);
	if (!IsDone(TEXT("M01-O01")))
	{
		// restored at the lockdown checkpoint: the escape track belongs to this fight only
		StartEscapeMusic(2.f);
		// died during the lockdown: the fight replays (no second revocation speech)
		bLockdownStarted = true;
		ApplyLockdownWorld(true);
		float Delay = 1.f;
		for (ANVSecurityDrone* D : LockdownDrones)
		{
			if (D)
			{
				D->Activate(Delay);
				Delay += 1.2f;
			}
		}
		GetWorldTimerManager().SetTimer(DesignateTimer, FTimerDelegate::CreateWeakLambda(this, [this]() { Designate(false); }), 8.f, false);
		return;
	}
	bLockdownStarted = true;
	bEmergencyOpen = true;
	for (ANVSecurityDrone* D : LockdownDrones)
	{
		if (D)
		{
			D->SetWrecked();
		}
	}
	ApplyLockdownWorld(true);
	if (EmergencyDoor)
	{
		EmergencyDoor->SetOpen(true, true);
	}
	Designate(true);
	if (ArteryTurret)
	{
		ArteryTurret->SetMode(IsDone(TEXT("M01-O02")) ? ENVTurretMode::Off : ENVTurretMode::Hostile);
	}
	if (IsDone(TEXT("M01-O03")) && LiftCab)
	{
		bLiftStarted = true;
		LiftPhase = 5;
		LiftCab->SetActorLocation(LiftStart - FVector(0.f, 0.f, LiftCruiseDrop + LiftPlungeDrop));
		if (LiftHatch)
		{
			LiftHatch->SetActorHiddenInGame(true);
			LiftHatch->SetActorEnableCollision(false);
		}
	}
	if (IsDone(TEXT("M01-O04")))
	{
		bReclaimStarted = true;
		SetMovers(SurgicalArms, 0.35f, 1.f, true);
		for (ALight* L : SuiteLights)
		{
			if (L && L->GetLightComponent())
			{
				L->GetLightComponent()->SetLightColor(AlarmColor);
			}
		}
		if (AgencyTag)
		{
			AgencyTag->SetEnabled(false);
			AgencyTag->SetActorHiddenInGame(true);
		}
	}
}

// ------------------------------------------------------------------------------------------------ C lift

void ANVBlackProtocolDirector::StartLift()
{
	if (bLiftStarted || !LiftCab)
	{
		return;
	}
	bLiftStarted = true;
	LiftPhase = 1;
	LiftTime = 0.f;
	LiftVel = 0.f;
	LiftTravelled = 0.f;
	SetMover(LiftGate, 1.f, 1.6f, false);
	Say(LiftLines);
	UE_LOG(LogNeonVeil, Log, TEXT("M01: service lift descending"));
}

// ------------------------------------------------------------------------------------------------ D reclamation

void ANVBlackProtocolDirector::StartReclamation()
{
	if (bReclaimStarted)
	{
		return;
	}
	bReclaimStarted = true;
	StripIndex = 0;
	UE_LOG(LogNeonVeil, Log, TEXT("M01: medical reclamation"));
	if (SuiteDoor)
	{
		SuiteDoor->SetOpen(false);
	}
	if (ANVPlayerCharacter* P = GetPlayer(this))
	{
		P->SetGameplayInputLocked(true, true);
		P->GetWeapons()->Holster();
	}
	for (ALight* L : SuiteLights)
	{
		if (L && L->GetLightComponent())
		{
			L->GetLightComponent()->SetLightColor(FLinearColor(0.75f, 0.9f, 1.f));
		}
	}
	// the rigs swing in around him (each arm's Offset/Rotation is authored toward the player's spot)
	SetMovers(SurgicalArms, 1.f, 0.45f, false);
	Say(ReclamationLines);
	GetWorldTimerManager().SetTimer(SeqTimer, this, &ANVBlackProtocolDirector::StripNext, FirstStripDelay, false);
}

void ANVBlackProtocolDirector::StripNext()
{
	ANVPlayerCharacter* P = GetPlayer(this);
	static const TArray<TPair<FGameplayTag, FText>> Systems = {
		{ NVTags::Ability_DroneUplink, NSLOCTEXT("NeonVeil", "OffDrone", "DRONE UPLINK  -  SEVERED") },
		{ NVTags::Ability_OpticalDisruption, NSLOCTEXT("NeonVeil", "OffOptic", "OPTICAL DISRUPTION  -  OFFLINE") },
		{ NVTags::Ability_KineticShield, NSLOCTEXT("NeonVeil", "OffShield", "KINETIC SHIELD  -  OFFLINE") },
		{ FGameplayTag(), NSLOCTEXT("NeonVeil", "OffMove", "ENHANCED MOVEMENT  -  OFFLINE") },
	};
	if (StripIndex >= Systems.Num())
	{
		FinishReclamation();
		return;
	}
	const auto& S = Systems[StripIndex++];
	if (P)
	{
		if (S.Key.IsValid())
		{
			P->GetAbilities()->SetAbilityDisabled(S.Key, true);
		}
		// each system costs a share of what's left above HealthAfter; never heals him if he came in lower
		const float Cur = P->GetHealth()->GetHealth();
		if (Cur > HealthAfter)
		{
			P->GetHealth()->SetHealthDirect(FMath::Lerp(Cur, HealthAfter, 1.f / FMath::Max(1, Systems.Num() - StripIndex + 1)));
		}
	}
	if (ANVHUD* HUD = GetHUD(this))
	{
		HUD->ShowThreat(S.Value, 2.2f);
	}
	if (ImplantSound)
	{
		UGameplayStatics::PlaySound2D(this, ImplantSound);
	}
	GlitchHUD(0.35f);
	GetWorldTimerManager().SetTimer(SeqTimer, this, &ANVBlackProtocolDirector::StripNext, StripInterval, false);
}

void ANVBlackProtocolDirector::FinishReclamation()
{
	UE_LOG(LogNeonVeil, Log, TEXT("M01: reclamation interrupted by power fault"));
	if (PowerFaultSound)
	{
		UGameplayStatics::PlaySound2D(this, PowerFaultSound);
	}
	for (ALight* L : SuiteLights)
	{
		if (L && L->GetLightComponent())
		{
			L->GetLightComponent()->SetLightColor(AlarmColor);
		}
	}
	if (SparksFX)
	{
		for (const FNVMover& M : SurgicalArms)
		{
			if (M.Actor)
			{
				UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SparksFX, M.Actor->GetActorLocation(), FRotator::ZeroRotator, FVector(1.f));
			}
		}
	}
	// rigs sag back, half-retracted, dead
	SetMovers(SurgicalArms, 0.35f, 0.8f, false);
	if (ANVPlayerCharacter* P = GetPlayer(this))
	{
		P->GetHealth()->SetHealthDirect(FMath::Min(P->GetHealth()->GetHealth(), HealthAfter));
		P->SetGameplayInputLocked(false);
	}
	CutAmmo();
	if (AgencyTag)
	{
		AgencyTag->SetEnabled(true);
	}
	Say(RecoveryLines);
}

void ANVBlackProtocolDirector::CutAmmo()
{
	ANVPlayerCharacter* P = GetPlayer(this);
	if (!P)
	{
		return;
	}
	TArray<FNVWeaponSlot> Slots = P->GetWeapons()->GetSlots();
	for (FNVWeaponSlot& S : Slots)
	{
		S.AmmoInMag = FMath::Min(S.AmmoInMag, ConduitMagAmmo);
		S.ReserveAmmo = FMath::Min(S.ReserveAmmo, ConduitReserveAmmo);
	}
	P->GetWeapons()->RestoreSlots(Slots, P->GetWeapons()->GetCurrentSlotIndex());
}

// ------------------------------------------------------------------------------------------------ tick

void ANVBlackProtocolDirector::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	TickMovers(Shutters, DeltaSeconds);
	TickMovers(SurgicalArms, DeltaSeconds);
	TickMover(LiftGate, DeltaSeconds);
	TickMover(EvacTube, DeltaSeconds);
	TickMover(EvacPlatform, DeltaSeconds);
	if (TheDirector && DirTurnT >= 0.f)
	{
		DirTurnT += DeltaSeconds;
		const float A = FMath::SmoothStep(0.f, 1.f, FMath::Clamp(DirTurnT / DirTurnLen, 0.f, 1.f));
		TheDirector->SetActorRotation(FMath::Lerp(DirFrom, DirTo, A));
		if (DirTurnT >= DirTurnLen)
		{
			DirTurnT = -1.f;
		}
	}
	if (bLockdownStarted)
	{
		SyncReflection();
	}
	const float Now = GetWorld()->GetTimeSeconds();

	// B: intermittent power once the lockdown is on
	if (bLockdownStarted && FlickerLights.Num() > 0 && Now >= NextFlicker)
	{
		NextFlicker = Now + FMath::FRandRange(0.06f, 0.5f);
		ALight* L = FlickerLights[FMath::RandRange(0, FlickerLights.Num() - 1)];
		if (L && L->GetLightComponent())
		{
			const float B = BaseIntensity.FindRef(L);
			L->GetLightComponent()->SetIntensity(FMath::RandBool() ? B * FMath::FRandRange(0.f, 0.25f) : B);
		}
	}

	// C: the lift — close gate, cruise, jolt, plunge, emergency brake
	if (LiftCab && LiftPhase > 0 && LiftPhase < 5)
	{
		LiftTime += DeltaSeconds;
		auto MoveCab = [this](float Dz)
		{
			LiftTravelled += Dz;
			LiftCab->SetActorLocation(LiftStart - FVector(0.f, 0.f, LiftTravelled));
		};
		if (LiftPhase == 1 && LiftTime > 1.2f)
		{
			LiftPhase = 2;
			LiftTime = 0.f;
		}
		else if (LiftPhase == 2)
		{
			LiftVel = FMath::Min(350.f, LiftVel + 300.f * DeltaSeconds);
			MoveCab(LiftVel * DeltaSeconds);
			if (LiftTravelled >= LiftCruiseDrop)
			{
				// beat 1: the cable lets go for a moment
				LiftPhase = 3;
				LiftTime = 0.f;
				if (LiftJoltSound)
				{
					UGameplayStatics::PlaySoundAtLocation(this, LiftJoltSound, LiftCab->GetActorLocation());
				}
				if (SparksFX)
				{
					UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SparksFX, LiftCab->GetActorLocation() + FVector(0.f, 0.f, 350.f), FRotator::ZeroRotator, FVector(2.f));
				}
				GlitchHUD(0.2f);
			}
		}
		else if (LiftPhase == 3)
		{
			// shudder in place
			LiftCab->SetActorLocation(LiftStart - FVector(0.f, 0.f, LiftTravelled) + FVector(0.f, 0.f, FMath::Sin(LiftTime * 60.f) * 3.f));
			if (LiftTime > 1.4f)
			{
				LiftPhase = 4;
				LiftTime = 0.f;
				LiftVel = 0.f;
			}
		}
		else if (LiftPhase == 4)
		{
			// beat 2: free fall (just under gravity so he stays on the floor), then the brake bites
			const float Remaining = LiftCruiseDrop + LiftPlungeDrop - LiftTravelled;
			LiftVel = Remaining > 500.f ? FMath::Min(1400.f, LiftVel + 900.f * DeltaSeconds) : FMath::Max(150.f, LiftVel - 2600.f * DeltaSeconds);
			MoveCab(FMath::Min(Remaining, LiftVel * DeltaSeconds));
			if (Remaining <= 1.f)
			{
				// beat 3: braked hard, jammed; the hatch blows out onto the maintenance ledge
				LiftPhase = 5;
				if (LiftBrakeSound)
				{
					UGameplayStatics::PlaySoundAtLocation(this, LiftBrakeSound, LiftCab->GetActorLocation());
				}
				if (SparksFX)
				{
					UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, SparksFX, LiftCab->GetActorLocation() + FVector(0.f, 0.f, 50.f), FRotator::ZeroRotator, FVector(3.f));
				}
				if (LiftHatch)
				{
					LiftHatch->SetActorHiddenInGame(true);
					LiftHatch->SetActorEnableCollision(false);
				}
				GlitchHUD(0.25f);
				UE_LOG(LogNeonVeil, Log, TEXT("M01: lift braked, hatch open"));
			}
		}
	}
}
