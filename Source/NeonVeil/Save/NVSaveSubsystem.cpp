#include "Save/NVSaveSubsystem.h"
#include "Abilities/NVAbilityComponent.h"
#include "Save/NVSaveGame.h"
#include "World/NVCheckpoint.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "Character/NVPlayerCharacter.h"
#include "Combat/NVHealthComponent.h"
#include "Combat/NVWeaponComponent.h"
#include "UI/NVHUD.h"
#include "NeonVeil.h"

#include "EngineUtils.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "HAL/PlatformTime.h"

const FString UNVSaveSubsystem::SlotName = TEXT("NV_Checkpoint");

UNVSaveSubsystem* UNVSaveSubsystem::Get(const UObject* WorldContext)
{
	const UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	const UGameInstance* GI = World ? World->GetGameInstance() : nullptr;
	return GI ? GI->GetSubsystem<UNVSaveSubsystem>() : nullptr;
}

void UNVSaveSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	if (UNVObjectiveSubsystem* Obj = Collection.InitializeDependency<UNVObjectiveSubsystem>())
	{
		Obj->OnCheckpointRequested.AddDynamic(this, &UNVSaveSubsystem::HandleCheckpointRequested);
	}
}

bool UNVSaveSubsystem::HasCheckpoint() const
{
	return UGameplayStatics::DoesSaveGameExist(SlotName, 0);
}

void UNVSaveSubsystem::HandleCheckpointRequested(FName ReasonObjectiveID)
{
	UWorld* World = GetGameInstance()->GetWorld();
	if (!World)
	{
		return;
	}
	for (TActorIterator<ANVCheckpoint> It(World); It; ++It)
	{
		if (It->ObjectiveID == ReasonObjectiveID)
		{
			SaveCheckpoint(It->CheckpointID);
			return;
		}
	}
	UE_LOG(LogNeonVeil, Warning, TEXT("Checkpoint requested by %s but no ANVCheckpoint is tagged with it"), *ReasonObjectiveID.ToString());
}

bool UNVSaveSubsystem::SaveCheckpoint(FName CheckpointID)
{
	UWorld* World = GetGameInstance()->GetWorld();
	const UNVObjectiveSubsystem* Obj = GetGameInstance()->GetSubsystem<UNVObjectiveSubsystem>();
	APlayerController* PC = World ? World->GetFirstPlayerController() : nullptr;
	const ANVPlayerCharacter* Player = PC ? Cast<ANVPlayerCharacter>(PC->GetPawn()) : nullptr;
	if (!World || !Obj || !Player || !Obj->GetCurrentMission())
	{
		UE_LOG(LogNeonVeil, Warning, TEXT("SaveCheckpoint(%s) skipped: no world/player/mission"), *CheckpointID.ToString());
		return false;
	}

	UNVSaveGame* Save = Cast<UNVSaveGame>(UGameplayStatics::CreateSaveGameObject(UNVSaveGame::StaticClass()));
	Save->MapPackage = World->GetOutermost()->GetName();
	// PIE prefixes the package name; strip it so the save reloads the real map.
	Save->MapPackage = UWorld::RemovePIEPrefix(Save->MapPackage);
	Save->MissionID = Obj->GetCurrentMission()->MissionID;
	Save->CompletedObjectives = Obj->GetCompletedSet().Array();
	Save->CheckpointID = CheckpointID;
	Save->Health = Player->GetHealth()->GetHealth();
	Save->WeaponSlots = Player->GetWeapons()->GetSlots();
	Save->DisabledAbilities = Player->GetAbilities()->GetDisabledTags();
	Save->CurrentWeaponSlot = Player->GetWeapons()->GetCurrentSlotIndex();
	Save->SavedAt = FDateTime::Now();

	const bool bOk = UGameplayStatics::SaveGameToSlot(Save, SlotName, 0);
	UE_LOG(LogNeonVeil, Log, TEXT("Checkpoint %s %s (map %s, %d objectives done, health %.0f)"),
		*CheckpointID.ToString(), bOk ? TEXT("saved") : TEXT("FAILED"), *Save->MapPackage, Save->CompletedObjectives.Num(), Save->Health);
	if (bOk)
	{
		if (ANVHUD* HUD = Cast<ANVHUD>(PC->GetHUD()))
		{
			HUD->ShowNotice(NSLOCTEXT("NeonVeil", "CheckpointSaved", "Checkpoint saved"), 2.f);
		}
		OnCheckpointSaved.Broadcast(CheckpointID);
	}
	return bOk;
}

bool UNVSaveSubsystem::LoadCheckpoint()
{
	UNVSaveGame* Save = Cast<UNVSaveGame>(UGameplayStatics::LoadGameFromSlot(SlotName, 0));
	if (!Save || Save->Version != UNVSaveGame::CurrentVersion)
	{
		UE_LOG(LogNeonVeil, Warning, TEXT("LoadCheckpoint: no compatible save"));
		return false;
	}
	PendingRestore = Save;
	LoadRequestTime = FPlatformTime::Seconds();
	UE_LOG(LogNeonVeil, Log, TEXT("Loading checkpoint %s on %s"), *Save->CheckpointID.ToString(), *Save->MapPackage);
	UGameplayStatics::OpenLevel(GetGameInstance()->GetWorld(), FName(*Save->MapPackage));
	return true;
}

void UNVSaveSubsystem::FinishRestore()
{
	if (PendingRestore)
	{
		UE_LOG(LogNeonVeil, Log, TEXT("Checkpoint %s restored in %.2f s (load request to control)"),
			*PendingRestore->CheckpointID.ToString(), FPlatformTime::Seconds() - LoadRequestTime);
	}
	PendingRestore = nullptr;
}

void UNVSaveSubsystem::NewGame(const FString& MapPackage)
{
	UGameplayStatics::DeleteGameInSlot(SlotName, 0);
	PendingRestore = nullptr;
	UE_LOG(LogNeonVeil, Log, TEXT("New game on %s"), *MapPackage);
	UGameplayStatics::OpenLevel(GetGameInstance()->GetWorld(), FName(*MapPackage));
}
