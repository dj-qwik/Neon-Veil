#include "UI/NVNavArrow.h"

#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "GameFramework/Character.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "NavigationPath.h"
#include "NavigationSystem.h"
#include "Interaction/NVInteractableActor.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "UObject/ConstructorHelpers.h"
#include "TimerManager.h"
#include "Camera/PlayerCameraManager.h"
#include "CanvasItem.h"
#include "Engine/Texture2D.h"
#include "TextureResource.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "World/NVElevator.h"
#include "World/NVObjectiveTrigger.h"
#include "World/NVTramService.h"

namespace
{
	/** The arrow's size; where it settles is worked out from the camera so it lands in the lower part of the view. */
	constexpr float ArrowScale = 1.0f;
	TAutoConsoleVariable<float> CVarNavArrowScreenMargin(TEXT("nv.NavArrow.Margin"), 0.22f,
		TEXT("Where the wayfinding arrow settles: this fraction of the screen height above the bottom edge."));
}

ANVNavArrow::ANVNavArrow()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = true;  // always ticks; idles cheaply while hidden
	PrimaryActorTick.TickGroup = TG_PostUpdateWork; // after the pawn moved this frame: stays glued to the feet
	SetActorEnableCollision(false);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
	static ConstructorHelpers::FObjectFinder<UTexture2D> White(TEXT("/Engine/EngineResources/WhiteSquareTexture.WhiteSquareTexture"));
	WhiteTex = White.Object;
	// green chevron with a dark rim (SM_/MI_ assets from nv_nav_chevron.py); masked + dithered, not translucent
	static ConstructorHelpers::FObjectFinder<UStaticMesh> FillMesh(TEXT("/Game/NeonVeil/UI/Nav/SM_NV_NavChevron.SM_NV_NavChevron"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> RimMesh(TEXT("/Game/NeonVeil/UI/Nav/SM_NV_NavChevronOutline.SM_NV_NavChevronOutline"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> FillMat(TEXT("/Game/NeonVeil/UI/Nav/MI_NV_NavArrow_Fill.MI_NV_NavArrow_Fill"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> RimMat(TEXT("/Game/NeonVeil/UI/Nav/MI_NV_NavArrow_Outline.MI_NV_NavArrow_Outline"));

	SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));
	Pivot = CreateDefaultSubobject<USceneComponent>(TEXT("Pivot"));
	Pivot->SetupAttachment(GetRootComponent());

	auto Part = [&](FName Name, UStaticMesh* Mesh, UMaterialInterface* Mat)
	{
		UStaticMeshComponent* C = CreateDefaultSubobject<UStaticMeshComponent>(Name);
		C->SetupAttachment(Pivot);
		C->SetStaticMesh(Mesh ? Mesh : Cube.Object.Get());
		if (Mat)
		{
			C->SetMaterial(0, Mat);
		}
		C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		C->SetGenerateOverlapEvents(false);
		C->SetCastShadow(false);
		C->SetCanEverAffectNavigation(false);
		C->SetAffectDistanceFieldLighting(false);
		C->SetAffectDynamicIndirectLighting(false);
		C->bReceivesDecals = false;
		C->SetVisibility(false);
		// a little extra room for occlusion tests on a paper-thin mesh
		C->SetBoundsScale(4.f);
		return C;
	};
	// Shaft = the dark rim, Head = the green fill (names kept from the first version)
	Shaft = Part(TEXT("Shaft"), RimMesh.Object, RimMat.Object);
	Head = Part(TEXT("Head"), FillMesh.Object, FillMat.Object);
}

bool ANVNavArrow::FindObjectiveGoal(const UObject* WorldContext, const FVector& From, FVector& OutGoal)
{
	const UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(WorldContext);
	UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	if (!Obj || !World)
	{
		return false;
	}
	const TArray<FNVObjectiveDef> ActiveList = Obj->GetActiveObjectives();
	for (const FNVObjectiveDef& Def : ActiveList)
	{
		const FName ID = Def.ObjectiveID;
		const FGameplayTag& Tag = Def.CompletionEventTag;
		const FName GoalTag(*FString::Printf(TEXT("NVGoal:%s"), *ID.ToString()));
		TArray<FVector> Explicit, Found;
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			AActor* A = *It;
			if (A->ActorHasTag(GoalTag))
			{
				Explicit.Add(A->GetActorLocation());
				continue;
			}
			if (const ANVInteractableActor* I = Cast<ANVInteractableActor>(A))
			{
				if ((!I->GetRequiredActiveObjective().IsNone() && I->GetRequiredActiveObjective() == ID) ||
					(Tag.IsValid() && I->GetCompletionEventTag() == Tag))
				{
					Found.Add(I->GetComponentsBoundingBox(true).GetCenter());
				}
			}
			else if (const ANVObjectiveTrigger* T = Cast<ANVObjectiveTrigger>(A))
			{
				if (Tag.IsValid() && T->EventTag == Tag)
				{
					Found.Add(T->GetActorLocation());
				}
			}
			else if (const ANVElevator* E = Cast<ANVElevator>(A))
			{
				if (E->RequiredActiveObjective == ID || (Tag.IsValid() && E->ArrivedEventTag == Tag))
				{
					Found.Add(E->GetActorLocation());
				}
			}
			else if (const ANVTramService* S = Cast<ANVTramService>(A))
			{
				if (Tag.IsValid() && S->BoardedEventTag == Tag)
				{
					Found.Add(S->Tram ? S->Tram->GetActorLocation() : S->GetActorLocation());
				}
			}
		}
		const TArray<FVector>& Pool = Explicit.Num() > 0 ? Explicit : Found;
		if (Pool.Num() > 0)
		{
			float Best = TNumericLimits<float>::Max();
			for (const FVector& P : Pool)
			{
				const float D = FVector::DistSquared(P, From);
				if (D < Best)
				{
					Best = D;
					OutGoal = P;
				}
			}
			return true;
		}
	}
	return false;
}

bool ANVNavArrow::Show(APawn* ForPawn)
{
	if (!ForPawn || !FindObjectiveGoal(this, ForPawn->GetActorLocation(), Goal))
	{
		UE_LOG(LogTemp, Log, TEXT("NavArrow: no goal for the current objective"));
		return false;
	}
	UE_LOG(LogTemp, Log, TEXT("NavArrow: goal %s"), *Goal.ToString());
	Pawn = ForPawn;
	if (!MID)
	{
		MID = Head->CreateDynamicMaterialInstance(0);
		MIDRim = Shaft->CreateDynamicMaterialInstance(0);
	}
	const float Now = GetWorld()->GetTimeSeconds();
	const bool bWasShowing = bShowing && (Now - ShowTime) < Duration;
	ShowTime = bWasShowing ? Now - FMath::Min(Now - ShowTime, 0.3f) : Now;
	bShowing = true;
	bLoggedMid = false;
	bLoggedDraw = false;
	LastOpacity = -1.f;
	Age = Now - ShowTime;
	RepathTimer = 0.f;
	UpdateDirection();
	if (!bWasShowing)
	{
		Yaw = TargetYaw;
	}
	Shaft->SetVisibility(true);
	Head->SetVisibility(true);
	Place(0.f);
	return true;
}

void ANVNavArrow::UpdateDirection()
{
	const APawn* P = Pawn.Get();
	if (!P)
	{
		return;
	}
	const FVector From = P->GetActorLocation();
	FVector Toward = Goal;
	// follow the walkable route when the nav mesh connects us to the goal; otherwise point straight at it
	if (UNavigationSystemV1* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld()))
	{
		if (UNavigationPath* Path = Nav->FindPathToLocationSynchronously(GetWorld(), From, Goal, const_cast<APawn*>(P)))
		{
			if (Path->IsValid() && !Path->IsPartial() && Path->PathPoints.Num() >= 2)
			{
				for (int32 i = 1; i < Path->PathPoints.Num(); ++i)
				{
					if (FVector::Dist2D(Path->PathPoints[i], From) > 120.f)
					{
						Toward = Path->PathPoints[i];
						break;
					}
				}
			}
		}
	}
	const FVector D = (Toward - From).GetSafeNormal2D();
	if (!D.IsNearlyZero())
	{
		TargetYaw = D.Rotation().Yaw;
	}
}

void ANVNavArrow::Place(float DeltaSeconds)
{
	const APawn* P = Pawn.Get();
	if (!P)
	{
		return;
	}
	FVector Feet = P->GetActorLocation();
	if (const ACharacter* C = Cast<ACharacter>(P))
	{
		Feet.Z -= C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	}
	Feet.Z += 4.f;
	// it slides out from under the feet to a spot on the floor in front of the view (where a first-person
	// camera can actually see it) and turns there toward the goal like a compass needle
	FVector ViewFwd = P->GetActorForwardVector();
	float AheadDistance = 300.f;
	const APlayerController* PC = Cast<APlayerController>(P->GetController());
	if (PC && PC->PlayerCameraManager)
	{
		const FRotator CamRot = PC->PlayerCameraManager->GetCameraRotation().GetNormalized();
		const FVector CamLoc = PC->PlayerCameraManager->GetCameraLocation();
		ViewFwd = CamRot.Vector();
		// where the floor shows at ~70% down the screen (straight below the crosshair): the ray through that
		// pixel, met with the floor plane
		int32 VX = 0, VY = 0;
		PC->GetViewportSize(VX, VY);
		FVector RayO, RayD;
		const float ScreenFrac = 1.f - CVarNavArrowScreenMargin.GetValueOnGameThread();   // 0.78 by default
		if (VX > 0 && VY > 0 && PC->DeprojectScreenPositionToWorld(VX * 0.5f, VY * ScreenFrac, RayO, RayD) && RayD.Z < -0.03f)
		{
			const float T = (Feet.Z - RayO.Z) / RayD.Z;
			AheadDistance = FVector::Dist2D(RayO + RayD * T, Feet);
		}
		else
		{
			AheadDistance = 700.f;
		}
		(void)CamLoc;
		AheadDistance = FMath::Clamp(AheadDistance, 140.f, 700.f);
	}
	ViewFwd = ViewFwd.GetSafeNormal2D();
	// facing a wall: keep the arrow on this side of it
	{
		FHitResult WallHit;
		FCollisionQueryParams WQ(SCENE_QUERY_STAT(NVNavArrowWall), false, P);
		WQ.AddIgnoredActor(this);
		const FVector WStart = Feet + FVector(0.f, 0.f, 40.f);
		// static geometry only: a pedestrian crossing in front must not yank the arrow back under your feet
		if (GetWorld()->LineTraceSingleByObjectType(WallHit, WStart, WStart + ViewFwd * (AheadDistance + 100.f), FCollisionObjectQueryParams(ECC_WorldStatic), WQ))
		{
			AheadDistance = FMath::Max(90.f, WallHit.Distance - 100.f);
		}
	}
	const float Out = FMath::InterpEaseOut(0.f, 1.f, FMath::Clamp(Age / 0.4f, 0.f, 1.f), 2.f);
	FVector Anchor = Feet + ViewFwd * FMath::Lerp(0.f, AheadDistance, Out);
	// hover a little above the floor: the wet street's rendered surface (rain ripples / displacement) rises well
	// above its collision and swallowed an arrow lying lower. Follows the floor height (slopes, steps, platforms).
	{
		FHitResult Hit;
		FCollisionQueryParams Q(SCENE_QUERY_STAT(NVNavArrowFloor), false, P);
		Q.AddIgnoredActor(this);
		const FVector Start(Anchor.X, Anchor.Y, Feet.Z + 80.f);
		const FVector End(Anchor.X, Anchor.Y, Feet.Z - 200.f);
		const float FloorZ = GetWorld()->LineTraceSingleByObjectType(Hit, Start, End, FCollisionObjectQueryParams(ECC_WorldStatic), Q) ? Hit.ImpactPoint.Z : Feet.Z - 4.f;
		Anchor.Z = FloorZ + 14.f;
	}
	Yaw = FMath::FixedTurn(Yaw, TargetYaw, 360.f * DeltaSeconds);
	// only push changes (no point re-sending an identical transform/material every frame)
	const FRotator Rot(0.f, Yaw, 0.f);
	if (!GetActorLocation().Equals(Anchor, 0.5f) || !GetActorRotation().Equals(Rot, 0.5f))
	{
		SetActorLocationAndRotation(Anchor, Rot);
	}
	const float S = FMath::Lerp(0.4f, 1.f, Out) * ArrowScale;
	const FVector PivotLoc(0.f, 0.f, 0.f);
	if (!Pivot->GetRelativeLocation().Equals(PivotLoc, 0.1f))
	{
		Pivot->SetRelativeLocation(PivotLoc);
	}
	if (!FMath::IsNearlyEqual(Pivot->GetRelativeScale3D().X, S, 0.005f))
	{
		Pivot->SetRelativeScale3D(FVector(S, S, 1.f));
	}
	CurrentScale = S;
	const float FadeIn = FMath::Clamp(Age / 0.2f, 0.f, 1.f);
	const float FadeOut = FMath::Clamp((Duration - Age) / 1.f, 0.f, 1.f);
	const float Opacity = MaxOpacity * FadeIn * FadeOut;
	CurrentOpacity = Opacity;
	if (MID && FMath::Abs(Opacity - LastOpacity) > 0.01f)
	{
		LastOpacity = Opacity;
		MID->SetScalarParameterValue(TEXT("Opacity"), Opacity);
		if (MIDRim)
		{
			MIDRim->SetScalarParameterValue(TEXT("Opacity"), Opacity * 0.9f);
		}
	}
}

void ANVNavArrow::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!bShowing)
	{
		return;
	}
	Age = GetWorld()->GetTimeSeconds() - ShowTime;
	if (Age >= Duration || !Pawn.IsValid())
	{
		bShowing = false;
		Shaft->SetVisibility(false);
		Head->SetVisibility(false);
		UE_LOG(LogTemp, Log, TEXT("NavArrow: hidden after %.2f s"), Age);
		return;
	}
	if (!bLoggedMid && Age > 2.f)
	{
		bLoggedMid = true;
		UE_LOG(LogTemp, Log, TEXT("NavArrow: at %s yaw %.0f (target %.0f), dt %.3f"), *GetActorLocation().ToString(), Yaw, TargetYaw, DeltaSeconds);
	}
	RepathTimer -= DeltaSeconds;
	if (RepathTimer <= 0.f)
	{
		RepathTimer = 0.25f;
		UpdateDirection();
	}
	Place(DeltaSeconds);
}

void ANVNavArrow::DrawOnCanvas(UCanvas* Canvas, APlayerController* PC) const
{
	if (!bShowing || !Canvas || !PC || CurrentOpacity <= 0.01f)
	{
		return;
	}
	// Optional screen-overlay rendering of the same arrow (not used by default; the mesh draws it).
	const FTransform Xf = GetActorTransform();
	const float S = CurrentScale;
	auto W = [&](float X, float Y)
	{
		return Xf.TransformPosition(FVector(-60.f * S + X * S, Y * S, 0.f));
	};
	const FVector Pts[7] = {
		W(0.f, -7.f), W(70.f, -7.f), W(70.f, 7.f), W(0.f, 7.f),   // shaft
		W(64.f, -24.f), W(116.f, 0.f), W(64.f, 24.f)                // head
	};
	FVector2D Scr[7];
	for (int32 i = 0; i < 7; ++i)
	{
		if (!PC->ProjectWorldLocationToScreen(Pts[i], Scr[i], true))
		{
			UE_LOG(LogTemp, Verbose, TEXT("NavArrow: point %d off screen"), i);
			return;
		}
	}
	const FLinearColor Col(Color.R, Color.G, Color.B, CurrentOpacity);
	TArray<FCanvasUVTri> Tris;
	auto Tri = [&](int32 A, int32 B, int32 C)
	{
		FCanvasUVTri T;
		T.V0_Pos = Scr[A]; T.V1_Pos = Scr[B]; T.V2_Pos = Scr[C];
		T.V0_Color = Col; T.V1_Color = Col; T.V2_Color = Col;
		Tris.Add(T);
	};
	Tri(0, 1, 2);
	Tri(0, 2, 3);
	Tri(4, 5, 6);
	const FTexture* White = WhiteTex ? WhiteTex->GetResource() : nullptr;
	FCanvasTriangleItem Item(Tris, White);
	Item.BlendMode = SE_BLEND_Translucent;
	Canvas->DrawItem(Item);
	if (!bLoggedDraw)
	{
		bLoggedDraw = true;
		UE_LOG(LogTemp, Log, TEXT("NavArrow: drawn at %s / %s (opacity %.2f, tex %d)"), *Scr[0].ToString(), *Scr[5].ToString(), CurrentOpacity, White != nullptr);
	}
}
