#include "World/NVTutorialZone.h"

#include "Character/NVPlayerCharacter.h"
#include "Components/BoxComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "UI/NVHUD.h"
#include "NeonVeil.h"

ANVTutorialZone::ANVTutorialZone()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.f;
	Volume = CreateDefaultSubobject<UBoxComponent>(TEXT("Volume"));
	SetRootComponent(Volume);
	Volume->SetBoxExtent(FVector(300.f, 300.f, 200.f));
	Volume->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	Volume->SetGenerateOverlapEvents(true);
}

void ANVTutorialZone::SetHint(bool bShow)
{
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
	{
		if (ANVHUD* HUD = Cast<ANVHUD>(PC->GetHUD()))
		{
			HUD->SetInstruction(bShow ? Instruction : FText::GetEmpty());
		}
	}
}

void ANVTutorialZone::Complete()
{
	bDone = true;
	SetHint(false);
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
	{
		if (ANVHUD* HUD = Cast<ANVHUD>(PC->GetHUD()))
		{
			if (!CompleteNotice.IsEmpty())
			{
				HUD->ShowNotice(CompleteNotice, 2.f);
			}
		}
	}
	if (CompleteEventTag.IsValid())
	{
		if (UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this))
		{
			Obj->SendEvent(CompleteEventTag);
		}
	}
	UE_LOG(LogNeonVeil, Log, TEXT("%s: tutorial step done"), *GetName());
	SetActorTickEnabled(false);
}

void ANVTutorialZone::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (bDone)
	{
		return;
	}
	ANVPlayerCharacter* P = Cast<ANVPlayerCharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
	if (!P)
	{
		return;
	}
	const UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this);
	const bool bArmed = RequiredActiveObjective.IsNone() || (Obj && Obj->IsObjectiveActive(RequiredActiveObjective));
	const bool bNowInside = bArmed && Volume->IsOverlappingActor(P);
	if (bNowInside != bInside)
	{
		bInside = bNowInside;
		SetHint(bInside && Action != ENVTutorialAction::None);
		if (!bInside && Action == ENVTutorialAction::None)
		{
			Complete();
			return;
		}
	}
	if (!bInside)
	{
		bWasGrounded = P->GetCharacterMovement()->IsMovingOnGround();
		return;
	}
	const UCharacterMovementComponent* Move = P->GetCharacterMovement();
	const bool bGrounded = Move->IsMovingOnGround();
	bool bDid = false;
	switch (Action)
	{
	case ENVTutorialAction::Sprint:
		SprintAccum += P->IsSprinting() && P->GetVelocity().Size2D() > 400.f ? DeltaSeconds : 0.f;
		bDid = SprintAccum >= SprintSeconds;
		break;
	case ENVTutorialAction::Jump:
		bDid = bWasGrounded && !bGrounded && P->GetVelocity().Z > 150.f;
		break;
	case ENVTutorialAction::Crouch:
		bDid = P->bIsCrouched && !P->IsSliding();
		break;
	case ENVTutorialAction::Slide:
		bDid = P->IsSliding();
		break;
	case ENVTutorialAction::Vault:
		bDid = P->IsVaulting();
		break;
	default:
		break;
	}
	bWasGrounded = bGrounded;
	if (bDid)
	{
		Complete();
	}
}
