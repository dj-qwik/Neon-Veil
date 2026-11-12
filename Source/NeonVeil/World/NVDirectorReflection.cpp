#include "World/NVDirectorReflection.h"
#include "NeonVeil.h"

#include "Components/BoxComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

ANVDirectorReflection::ANVDirectorReflection()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.f;
	Volume = CreateDefaultSubobject<UBoxComponent>(TEXT("Volume"));
	RootComponent = Volume;
	Volume->SetBoxExtent(FVector(700.f, 700.f, 300.f));
	Volume->SetCollisionProfileName(TEXT("NoCollision"));
}

USkeletalMeshComponent* ANVDirectorReflection::FindBody(AActor* Actor)
{
	if (!Actor)
	{
		return nullptr;
	}
	TArray<USkeletalMeshComponent*> Comps;
	Actor->GetComponents(Comps);
	USkeletalMeshComponent* Best = nullptr;
	for (USkeletalMeshComponent* C : Comps)
	{
		if (C->GetName().Contains(TEXT("Body")))
		{
			return C;
		}
		if (!Best || (C->GetSkeletalMeshAsset() && Best->GetSkeletalMeshAsset()
			&& C->GetNumBones() > Best->GetNumBones()))
		{
			Best = C;
		}
	}
	return Best;
}

void ANVDirectorReflection::BeginPlay()
{
	Super::BeginPlay();
	if (IdleAnim)
	{
		for (AActor* A : { Real.Get(), Mirror.Get() })
		{
			if (USkeletalMeshComponent* Body = FindBody(A))
			{
				Body->PlayAnimation(IdleAnim, true);
			}
		}
	}
	UE_LOG(LogNeonVeil, Log, TEXT("%s: reflection armed (real %s, mirror %s)"), *GetName(),
		Real ? *Real->GetName() : TEXT("none"), Mirror ? *Mirror->GetName() : TEXT("none"));
}

void ANVDirectorReflection::SetMirrorRate(float Rate)
{
	if (USkeletalMeshComponent* Body = FindBody(Mirror))
	{
		Body->GlobalAnimRateScale = Rate;
	}
}

void ANVDirectorReflection::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (Phase >= 3 || !Mirror)
	{
		SetActorTickEnabled(Phase < 3);
		return;
	}
	StateTime += DeltaSeconds;
	if (Phase == 0)
	{
		APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
		APawn* Pawn = PC ? PC->GetPawn() : nullptr;
		if (!Pawn || !Volume->Bounds.GetBox().IsInside(Pawn->GetActorLocation()))
		{
			Looked = 0.f;
			return;
		}
		FVector Eye;
		FRotator ViewRot;
		PC->GetPlayerViewPoint(Eye, ViewRot);
		const FVector Target = Mirror->GetActorLocation() + FVector(0.f, 0.f, 150.f);
		const float Dot = FVector::DotProduct(ViewRot.Vector(), (Target - Eye).GetSafeNormal());
		Looked = Dot >= LookDot ? Looked + DeltaSeconds : 0.f;
		if (Looked >= LookTime)
		{
			Phase = 1;
			StateTime = 0.f;
			SetMirrorRate(0.f);
			UE_LOG(LogNeonVeil, Log, TEXT("%s: reflection desync (%.2f s)"), *GetName(), LagTime);
		}
	}
	else if (Phase == 1 && StateTime >= LagTime)
	{
		// Behind by LagTime; run slightly fast for CatchUp seconds to drift back into step (works with any anim setup).
		Phase = 2;
		StateTime = 0.f;
		SetMirrorRate(1.f + LagTime / FMath::Max(CatchUp, 0.1f));
	}
	else if (Phase == 2 && StateTime >= CatchUp)
	{
		SetMirrorRate(1.f);
		Phase = 3;
		UE_LOG(LogNeonVeil, Log, TEXT("%s: reflection back in sync"), *GetName());
	}
}
