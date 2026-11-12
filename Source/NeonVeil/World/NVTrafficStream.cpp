#include "World/NVTrafficStream.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"

ANVTrafficStream::ANVTrafficStream()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickGroup = TG_DuringPhysics;

	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	Forward = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Forward"));
	Forward->SetupAttachment(Root);
	Reverse = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Reverse"));
	Reverse->SetupAttachment(Root);
}

void ANVTrafficStream::SetupComponent(UInstancedStaticMeshComponent* C, UMaterialInterface* Mat)
{
	C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	C->SetCastShadow(false);
	C->SetAffectDistanceFieldLighting(false);
	C->SetAffectDynamicIndirectLighting(false);
	C->SetMobility(EComponentMobility::Movable);
	C->SetStaticMesh(VehicleMesh);
	if (Mat)
	{
		C->SetMaterial(0, Mat);
	}
}

void ANVTrafficStream::Build()
{
	FRandomStream R(Seed);
	auto Fill = [&](TArray<FLaneCar>& Cars, int32 Count)
	{
		Cars.Reset(Count);
		for (int32 i = 0; i < Count; ++i)
		{
			FLaneCar Car;
			Car.X = R.FRandRange(0.f, LaneLength);
			Car.Speed = R.FRandRange(SpeedRange.X, SpeedRange.Y);
			// cars cluster into a few sub-lanes rather than a uniform cloud
			const int32 SubLane = R.RandRange(0, 3);
			Car.Y = (SubLane - 1.5f) / 1.5f * LaneSpread.X + R.FRandRange(-0.08f, 0.08f) * LaneSpread.X;
			Car.Z = R.FRandRange(-1.f, 1.f) * LaneSpread.Y;
			Cars.Add(Car);
		}
	};
	Fill(ForwardCars, VehiclesPerDirection);
	Fill(ReverseCars, bTwoWay ? VehiclesPerDirection : 0);

	SetupComponent(Forward, ForwardMaterial);
	SetupComponent(Reverse, ReverseMaterial);
	Forward->ClearInstances();
	Reverse->ClearInstances();
	if (!VehicleMesh)
	{
		return;
	}
	TArray<FTransform> F, Rv;
	for (const FLaneCar& Car : ForwardCars)
	{
		F.Add(FTransform(FQuat::Identity, FVector(Car.X, Car.Y, Car.Z), VehicleScale));
	}
	for (const FLaneCar& Car : ReverseCars)
	{
		// reverse lanes sit offset across Y so the two directions read as separate ribbons
		Rv.Add(FTransform(FQuat::Identity, FVector(LaneLength - Car.X, Car.Y + LaneSpread.X * 2.6f, Car.Z), VehicleScale));
	}
	Forward->AddInstances(F, false);
	Reverse->AddInstances(Rv, false);
}

void ANVTrafficStream::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	Build();
}

void ANVTrafficStream::BeginPlay()
{
	Super::BeginPlay();
	Build();
}

void ANVTrafficStream::UpdateDirection(UInstancedStaticMeshComponent* C, TArray<FLaneCar>& Cars, float Sign, float DeltaSeconds)
{
	if (Cars.Num() == 0 || C->GetInstanceCount() != Cars.Num())
	{
		return;
	}
	TArray<FTransform> Xf;
	Xf.SetNumUninitialized(Cars.Num());
	const float YOffset = Sign > 0.f ? 0.f : LaneSpread.X * 2.6f;
	for (int32 i = 0; i < Cars.Num(); ++i)
	{
		FLaneCar& Car = Cars[i];
		Car.X = FMath::Fmod(Car.X + Car.Speed * DeltaSeconds, LaneLength);
		const float X = Sign > 0.f ? Car.X : LaneLength - Car.X;
		Xf[i] = FTransform(FQuat::Identity, FVector(X, Car.Y + YOffset, Car.Z), VehicleScale);
	}
	C->BatchUpdateInstancesTransforms(0, Xf, false, true, false);
}

void ANVTrafficStream::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	UpdateDirection(Forward, ForwardCars, 1.f, DeltaSeconds);
	UpdateDirection(Reverse, ReverseCars, -1.f, DeltaSeconds);
}
