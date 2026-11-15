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

void ANVTrafficStream::SetupComponent(UInstancedStaticMeshComponent* C, UStaticMesh* Mesh, UMaterialInterface* Mat, UMaterialInterface* Accent)
{
	C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	C->SetCastShadow(false);
	C->SetAffectDistanceFieldLighting(false);
	C->SetAffectDynamicIndirectLighting(false);
	C->SetMobility(EComponentMobility::Movable);
	C->SetStaticMesh(Mesh);
	C->EmptyOverrideMaterials();
	if (Mat)
	{
		C->SetMaterial(0, Mat);
	}
	if (Accent && Mesh && AccentSlot < Mesh->GetStaticMaterials().Num())
	{
		C->SetMaterial(AccentSlot, Accent);
	}
}

FTransform ANVTrafficStream::CarTransform(const FLaneCar& Car, float Sign) const
{
	// reverse lanes sit offset across Y so the two directions read as separate ribbons
	if (Sign > 0.f)
	{
		return FTransform(FQuat::Identity, FVector(Car.X, Car.Y, Car.Z), VehicleScale);
	}
	const FQuat Q = bTurnReverseCars ? FQuat(FVector::UpVector, PI) : FQuat::Identity;
	return FTransform(Q, FVector(LaneLength - Car.X, Car.Y + LaneSpread.X * 2.6f, Car.Z), VehicleScale);
}

void ANVTrafficStream::Build()
{
	// drop every runtime-made lane component (including any copied over by PIE duplication)
	TArray<UInstancedStaticMeshComponent*> Existing;
	GetComponents(Existing);
	for (UInstancedStaticMeshComponent* C : Existing)
	{
		if (C && C != Forward && C != Reverse)
		{
			C->DestroyComponent();
		}
	}
	ExtraComps.Reset();
	Lanes.Reset();

	TArray<UStaticMesh*> Meshes;
	Meshes.Add(VehicleMesh);
	for (UStaticMesh* M : ExtraMeshes)
	{
		if (M)
		{
			Meshes.Add(M);
		}
	}
	TArray<UMaterialInterface*> Accents;
	for (UMaterialInterface* M : AccentMaterials)
	{
		if (M)
		{
			Accents.Add(M);
		}
	}
	if (Accents.Num() == 0)
	{
		Accents.Add(nullptr);
	}
	const int32 Kinds = Meshes.Num() * Accents.Num();

	// kind 0 uses the saved Forward/Reverse components, the rest are made here
	for (int32 Dir = 0; Dir < 2; ++Dir)
	{
		const float Sign = Dir == 0 ? 1.f : -1.f;
		for (int32 K = 0; K < Kinds; ++K)
		{
			UInstancedStaticMeshComponent* C = nullptr;
			if (K == 0)
			{
				C = Dir == 0 ? Forward.Get() : Reverse.Get();
			}
			else
			{
				C = NewObject<UInstancedStaticMeshComponent>(this, NAME_None, RF_Transient | RF_TextExportTransient);
				C->SetupAttachment(GetRootComponent());
				C->CreationMethod = EComponentCreationMethod::Instance;
				C->RegisterComponent();
				ExtraComps.Add(C);
			}
			SetupComponent(C, Meshes[K / Accents.Num()], Dir == 0 ? ForwardMaterial.Get() : ReverseMaterial.Get(), Accents[K % Accents.Num()]);
			C->ClearInstances();
			FKindLane Lane;
			Lane.Comp = C;
			Lane.Sign = Sign;
			Lanes.Add(MoveTemp(Lane));
		}
	}

	FRandomStream R(Seed);
	auto Fill = [&](int32 Dir, int32 Count)
	{
		for (int32 i = 0; i < Count; ++i)
		{
			FLaneCar Car;
			Car.X = R.FRandRange(0.f, LaneLength);
			Car.Speed = R.FRandRange(SpeedRange.X, SpeedRange.Y);
			// cars cluster into a few sub-lanes rather than a uniform cloud
			const int32 SubLane = R.RandRange(0, 3);
			Car.Y = (SubLane - 1.5f) / 1.5f * LaneSpread.X + R.FRandRange(-0.08f, 0.08f) * LaneSpread.X;
			Car.Z = R.FRandRange(-1.f, 1.f) * LaneSpread.Y;
			const int32 K = Kinds > 1 ? R.RandRange(0, Kinds - 1) : 0;
			Lanes[Dir * Kinds + K].Cars.Add(Car);
		}
	};
	Fill(0, VehiclesPerDirection);
	Fill(1, bTwoWay ? VehiclesPerDirection : 0);

	if (!VehicleMesh)
	{
		return;
	}
	for (FKindLane& Lane : Lanes)
	{
		UInstancedStaticMeshComponent* C = Lane.Comp.Get();
		if (!C || Lane.Cars.Num() == 0)
		{
			continue;
		}
		TArray<FTransform> Xf;
		Xf.Reserve(Lane.Cars.Num());
		for (const FLaneCar& Car : Lane.Cars)
		{
			Xf.Add(CarTransform(Car, Lane.Sign));
		}
		C->AddInstances(Xf, false);
	}
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

void ANVTrafficStream::UpdateLane(FKindLane& Lane, float DeltaSeconds)
{
	UInstancedStaticMeshComponent* C = Lane.Comp.Get();
	if (!C || Lane.Cars.Num() == 0 || C->GetInstanceCount() != Lane.Cars.Num())
	{
		return;
	}
	TArray<FTransform> Xf;
	Xf.SetNumUninitialized(Lane.Cars.Num());
	for (int32 i = 0; i < Lane.Cars.Num(); ++i)
	{
		FLaneCar& Car = Lane.Cars[i];
		Car.X = FMath::Fmod(Car.X + Car.Speed * DeltaSeconds, LaneLength);
		Xf[i] = CarTransform(Car, Lane.Sign);
	}
	C->BatchUpdateInstancesTransforms(0, Xf, false, true, false);
}

void ANVTrafficStream::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	for (FKindLane& Lane : Lanes)
	{
		UpdateLane(Lane, DeltaSeconds);
	}
}
