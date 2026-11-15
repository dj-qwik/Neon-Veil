#include "UI/NVHoloRig.h"

#include "Animation/AnimSequence.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Misc/App.h"

namespace
{
	const TCHAR* HoloMaterialPath = TEXT("/Game/NeonVeil/UI/Holo/M_NV_Hologram2.M_NV_Hologram2");
	const TCHAR* PresenterPath = TEXT("/Game/NeonVeil/UI/Holo/M_NV_HoloUI.M_NV_HoloUI");
	const TCHAR* IdlePath = TEXT("/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle.MM_Idle");
	const FVector RigLocation(0.f, 0.f, -250000.f);
	constexpr int32 TargetW = 920;   // 2x the widget box
	constexpr int32 TargetH = 1080;
}

ANVHoloRig::ANVHoloRig()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bTickEvenWhenPaused = true;
	SetTickableWhenPaused(true);
	SetActorEnableCollision(false);

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
	Turntable = CreateDefaultSubobject<USceneComponent>(TEXT("Turntable"));
	Turntable->SetupAttachment(Root);

	Body = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Body"));
	Body->SetupAttachment(Turntable);
	Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Body->SetCastShadow(false);
	Body->bAffectDynamicIndirectLighting = false;
	Body->SetTickableWhenPaused(true);
	Body->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
	Body->SetRelativeRotation(FRotator(0.f, -90.f, 0.f));      // mesh forward (+Y) -> actor +X, facing the capture

	Capture = CreateDefaultSubobject<USceneCaptureComponent2D>(TEXT("Capture"));
	Capture->SetupAttachment(Root);
	Capture->ProjectionType = ECameraProjectionMode::Orthographic;
	Capture->PrimitiveRenderMode = ESceneCapturePrimitiveRenderMode::PRM_UseShowOnlyList;
	Capture->CaptureSource = ESceneCaptureSource::SCS_FinalColorLDR;
	Capture->bCaptureEveryFrame = false;
	Capture->bCaptureOnMovement = false;
	Capture->bAlwaysPersistRenderingState = true;
	Capture->SetRelativeRotation(FRotator(0.f, 180.f, 0.f));   // looking back along -X at the body's front
	Capture->ShowFlags.SetFog(false);
	Capture->ShowFlags.SetAtmosphere(false);
	Capture->ShowFlags.SetVolumetricFog(false);
	Capture->ShowFlags.SetEyeAdaptation(false);
	Capture->ShowFlags.SetMotionBlur(false);
	Capture->ShowFlags.SetGrain(false);
	Capture->ShowFlags.SetLensFlares(false);
	Capture->ShowFlags.SetBloom(true);
	Capture->PostProcessSettings.bOverride_AutoExposureMethod = true;
	Capture->PostProcessSettings.AutoExposureMethod = EAutoExposureMethod::AEM_Manual;
	Capture->PostProcessSettings.bOverride_AutoExposureBias = true;
	Capture->PostProcessSettings.AutoExposureBias = 0.f;
	Capture->PostProcessSettings.bOverride_BloomIntensity = true;
	Capture->PostProcessSettings.BloomIntensity = 0.9f;
	Capture->PostProcessSettings.bOverride_VignetteIntensity = true;
	Capture->PostProcessSettings.VignetteIntensity = 0.f;
}

ANVHoloRig* ANVHoloRig::Get(UWorld* World, USkeletalMesh* InBody)
{
	if (!World)
	{
		return nullptr;
	}
	ANVHoloRig* Rig = nullptr;
	for (TActorIterator<ANVHoloRig> It(World); It; ++It)
	{
		Rig = *It;
		break;
	}
	if (!Rig)
	{
		FActorSpawnParameters P;
		P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		P.ObjectFlags |= RF_Transient;
		Rig = World->SpawnActor<ANVHoloRig>(ANVHoloRig::StaticClass(), FTransform(RigLocation), P);
	}
	if (Rig && InBody && Rig->Body->GetSkeletalMeshAsset() != InBody)
	{
		Rig->SetBody(InBody);
	}
	return Rig;
}

void ANVHoloRig::BeginPlay()
{
	Super::BeginPlay();
	Target = NewObject<UTextureRenderTarget2D>(this);
	Target->RenderTargetFormat = ETextureRenderTargetFormat::RTF_RGBA8;
	Target->ClearColor = FLinearColor::Black;
	Target->InitAutoFormat(TargetW, TargetH);
	Target->UpdateResourceImmediate(true);
	Capture->TextureTarget = Target;
	Capture->ShowOnlyComponents.Add(Body);
	if (UMaterialInterface* P = LoadObject<UMaterialInterface>(nullptr, PresenterPath))
	{
		Presenter = UMaterialInstanceDynamic::Create(P, this);
		Presenter->SetTextureParameterValue(TEXT("Capture"), Target);
	}
}

void ANVHoloRig::SetBody(USkeletalMesh* InBody)
{
	Body->SetSkeletalMeshAsset(InBody);
	if (UMaterialInterface* Holo = LoadObject<UMaterialInterface>(nullptr, HoloMaterialPath))
	{
		for (int32 i = 0; i < Body->GetNumMaterials(); ++i)
		{
			Body->SetMaterial(i, Holo);
		}
	}
	if (UAnimSequence* Idle = LoadObject<UAnimSequence>(nullptr, IdlePath))
	{
		Body->SetAnimationMode(EAnimationMode::AnimationSingleNode);
		Body->PlayAnimation(Idle, true);
	}
	Frame();
}

void ANVHoloRig::Frame()
{
	// Reference-pose bounds: feet at the component origin, head top at the mesh's height.
	const USkeletalMesh* Mesh = Body->GetSkeletalMeshAsset();
	const float Height = Mesh ? FMath::Max(150.f, static_cast<float>(Mesh->GetImportedBounds().GetBox().Max.Z)) : 185.f;
	// Widget units: Y = 5 at the head top, Y = 470 at the soles; the box spans Y -20..520 and X -230..230.
	CmPerUnit = Height / 465.f;
	Capture->OrthoWidth = BoxW * CmPerUnit;
	CentreZ = Height - (250.f - 5.f) * CmPerUnit;
	Capture->SetRelativeLocation(FVector(600.f, 0.f, CentreZ));
}

bool ANVHoloRig::ProjectBone(FName Bone, const FVector& Offset, FVector2f& OutUnits) const
{
	if (!Body->GetSkeletalMeshAsset() || Body->GetBoneIndex(Bone) == INDEX_NONE)
	{
		return false;
	}
	// The capture looks down -X with +Y to the left of the frame (camera right = world -Y).
	const FVector Rel = Body->GetSocketLocation(Bone) + Offset - GetActorLocation();
	OutUnits = FVector2f(static_cast<float>(-Rel.Y) / CmPerUnit, 250.f - static_cast<float>(Rel.Z - CentreZ) / CmPerUnit);
	return true;
}

void ANVHoloRig::Touch()
{
	LastTouch = FPlatformTime::Seconds();
}

void ANVHoloRig::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const bool bLive = FPlatformTime::Seconds() - LastTouch < 0.5;
	Body->SetComponentTickEnabled(bLive);
	if (!bLive)
	{
		return;
	}
	// Real time (the menu usually pauses the game): slow sway so the rim light moves over the body.
	const float Dt = FMath::Min(FApp::GetDeltaTime(), 0.1f);
	Age += Dt;
	Turntable->SetRelativeRotation(FRotator(0.f, FMath::Sin(Age * 0.35f) * 16.f, 0.f));
	Capture->CaptureScene();
}
