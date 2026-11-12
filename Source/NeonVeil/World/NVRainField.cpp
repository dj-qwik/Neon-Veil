#include "World/NVRainField.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

ANVRainField::ANVRainField()
{
	PrimaryActorTick.bCanEverTick = false;
	Streaks = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Streaks"));
	RootComponent = Streaks;
	Streaks->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Streaks->SetCanEverAffectNavigation(false);
	Streaks->SetGenerateOverlapEvents(false);
	Streaks->CastShadow = false;
	Streaks->bAffectDistanceFieldLighting = false;
	Streaks->SetMobility(EComponentMobility::Static);
	Streaks->NumCustomDataFloats = 4;
	// Instances are displaced up to one box height by WPO; keep culling conservative.
	Streaks->SetBoundsScale(2.f);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Plane(TEXT("/Engine/BasicShapes/Plane.Plane"));
	if (Plane.Succeeded())
	{
		StreakMesh = Plane.Object;
	}
}

void ANVRainField::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	Build();
}

void ANVRainField::BeginPlay()
{
	Super::BeginPlay();
	Build(); // cheap (a few ms for thousands of instances); guarantees the instances match the current settings
}

void ANVRainField::Build()
{
	Streaks->ClearInstances();
	Streaks->SetStaticMesh(StreakMesh);
	if (Material)
	{
		Streaks->SetMaterial(0, Material);
	}
	Streaks->NumCustomDataFloats = 4;

	FRandomStream R(Seed);
	const float H = Extent.Z * 2.f;
	TArray<FTransform> Xf;
	Xf.Reserve(Count);
	TArray<float> Custom;
	Custom.Reserve(Count * 4);
	for (int32 i = 0; i < Count; ++i)
	{
		const float Phase = R.FRand();
		const float Speed = R.FRandRange(SpeedRange.X, SpeedRange.Y);
		const float Len = R.FRandRange(LengthRange.X, LengthRange.Y);
		const float Wid = R.FRandRange(WidthRange.X, WidthRange.Y);
		const float Bright = FMath::Lerp(BrightnessRange.X, BrightnessRange.Y, FMath::Square(R.FRand()));
		// Spawn spread through the column (top minus phase*H) so bounds are honest; WPO wraps it in time.
		const FVector Loc(R.FRandRange(-Extent.X, Extent.X), R.FRandRange(-Extent.Y, Extent.Y), Extent.Z - Phase * H);
		// Plane is XY (normal +Z): roll 90 stands it up facing ±Y with its length along Z.
		const FRotator Rot(Slant + R.FRandRange(-SlantJitter, SlantJitter), R.FRandRange(-YawJitter, YawJitter), 90.f);
		Xf.Add(FTransform(Rot, Loc, FVector(Wid / 100.f, Len / 100.f, 1.f)));
		Custom.Append({ Phase, Speed, Bright, H });
	}
	Streaks->AddInstances(Xf, false, false);
	for (int32 i = 0; i < Count; ++i)
	{
		Streaks->SetCustomData(i, TArrayView<const float>(Custom.GetData() + i * 4, 4), i == Count - 1);
	}
}
