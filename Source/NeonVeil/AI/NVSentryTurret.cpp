#include "AI/NVSentryTurret.h"
#include "AI/NVHostileFire.h"
#include "AI/NVSecurityDrone.h"
#include "AI/NVGuardCharacter.h"
#include "Combat/NVHealthComponent.h"
#include "Combat/NVFriendly.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "NeonVeil.h"

#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/ConstructorHelpers.h"

ANVSentryTurret::ANVSentryTurret()
{
	PrimaryActorTick.bCanEverTick = true;
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cyl(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));

	Base = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Base"));
	Base->SetupAttachment(Root);
	Base->SetRelativeScale3D(FVector(0.8f, 0.8f, 0.6f));
	Base->SetRelativeLocation(FVector(0.f, 0.f, 30.f));
	Head = CreateDefaultSubobject<USceneComponent>(TEXT("Head"));
	Head->SetupAttachment(Root);
	Head->SetRelativeLocation(FVector(0.f, 0.f, 95.f));
	HeadMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("HeadMesh"));
	HeadMesh->SetupAttachment(Head);
	HeadMesh->SetRelativeScale3D(FVector(0.75f, 0.6f, 0.45f));
	Barrel = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Barrel"));
	Barrel->SetupAttachment(Head);
	Barrel->SetRelativeLocation(FVector(70.f, 0.f, 0.f));
	Barrel->SetRelativeRotation(FRotator(-90.f, 0.f, 0.f));
	Barrel->SetRelativeScale3D(FVector(0.12f, 0.12f, 0.8f));
	Barrel->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Laser = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Laser"));
	Laser->SetupAttachment(Head);
	Laser->SetUsingAbsoluteScale(true);
	Laser->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Laser->CastShadow = false;
	StatusLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("StatusLight"));
	StatusLight->SetupAttachment(Head);
	StatusLight->SetRelativeLocation(FVector(40.f, 0.f, 30.f));
	StatusLight->SetAttenuationRadius(500.f);
	StatusLight->SetCastShadows(false);
	if (Cube.Succeeded())
	{
		Base->SetStaticMesh(Cube.Object);
		HeadMesh->SetStaticMesh(Cube.Object);
	}
	if (Cyl.Succeeded())
	{
		Barrel->SetStaticMesh(Cyl.Object);
		Laser->SetStaticMesh(Cyl.Object);
	}
	Gun = CreateDefaultSubobject<UNVHostileFire>(TEXT("Gun"));
	Gun->SetupAttachment(Head);
	Gun->SetRelativeLocation(FVector(115.f, 0.f, 0.f));
	Gun->Damage = 9.f;
	Gun->SpreadDeg = 1.6f;
	Gun->Range = 4500.f;
}

void ANVSentryTurret::BeginPlay()
{
	Super::BeginPlay();
	if (UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this))
	{
		Obj->OnGameplayEvent.AddDynamic(this, &ANVSentryTurret::HandleGameplayEvent);
	}
	// make SetMode apply the start mode's visuals
	Mode = StartMode == ENVTurretMode::Off ? ENVTurretMode::Hostile : ENVTurretMode::Off;
	SetMode(StartMode);
}

void ANVSentryTurret::HandleGameplayEvent(FGameplayTag EventTag)
{
	if (RerouteEventTag.IsValid() && EventTag == RerouteEventTag && Mode != ENVTurretMode::Rerouted)
	{
		SetMode(ENVTurretMode::Rerouted);
	}
}

void ANVSentryTurret::SetMode(ENVTurretMode NewMode)
{
	if (NewMode == Mode)
	{
		return;
	}
	Mode = NewMode;
	Current.Reset();
	LockTimer = FireTimer = 0.f;
	ShotsLeft = 0;
	const bool bOn = Mode != ENVTurretMode::Off;
	Laser->SetVisibility(bOn);
	Laser->SetMaterial(0, Mode == ENVTurretMode::Rerouted ? LaserFriendly : LaserHostile);
	StatusLight->SetLightColor(Mode == ENVTurretMode::Rerouted ? FLinearColor(0.2f, 1.f, 0.4f) : FLinearColor(1.f, 0.15f, 0.1f));
	StatusLight->SetIntensity(bOn ? 2500.f : 0.f);
	SetActorTickEnabled(bOn);
	UE_LOG(LogNeonVeil, Log, TEXT("%s mode -> %s"), *GetName(), *UEnum::GetValueAsString(Mode));
	if (Mode == ENVTurretMode::Rerouted)
	{
		if (RerouteSound)
		{
			UGameplayStatics::PlaySoundAtLocation(this, RerouteSound, GetActorLocation());
		}
		if (!bSentReroute && ObjectiveEventOnReroute.IsValid())
		{
			bSentReroute = true;
			if (UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this))
			{
				Obj->SendEvent(ObjectiveEventOnReroute);
			}
		}
	}
}

bool ANVSentryTurret::InArc(const FVector& P) const
{
	const FVector To = P - Head->GetComponentLocation();
	if (To.Size() > Range)
	{
		return false;
	}
	const FVector Fwd = GetActorForwardVector();
	const float Cos = FVector::DotProduct(Fwd.GetSafeNormal2D(), To.GetSafeNormal2D());
	return Cos >= FMath::Cos(FMath::DegreesToRadians(FieldOfFireDeg));
}

AActor* ANVSentryTurret::PickTarget() const
{
	const FVector From = Gun->GetComponentLocation();
	if (Mode == ENVTurretMode::Hostile)
	{
		AActor* P = UGameplayStatics::GetPlayerPawn(this, 0);
		return (P && InArc(P->GetActorLocation()) && UNVHostileFire::CanSee(GetWorld(), this, From, P)) ? P : nullptr;
	}
	// rerouted: nearest live Directorate unit in the arc
	AActor* Best = nullptr;
	float BestD = TNumericLimits<float>::Max();
	auto Consider = [&](AActor* A)
	{
		const UNVHealthComponent* H = A->FindComponentByClass<UNVHealthComponent>();
		if (!H || H->IsDead() || !InArc(A->GetActorLocation()) || !UNVHostileFire::CanSee(GetWorld(), this, From, A))
		{
			return;
		}
		const float D = FVector::DistSquared(From, A->GetActorLocation());
		if (D < BestD)
		{
			BestD = D;
			Best = A;
		}
	};
	for (TActorIterator<ANVSecurityDrone> It(GetWorld()); It; ++It)
	{
		if (!It->IsDestroyed() && !It->IsHidden())
		{
			Consider(*It);
		}
	}
	for (TActorIterator<ANVGuardCharacter> It(GetWorld()); It; ++It)
	{
		if (!NVFriendly::IsFriendly(*It))
		{
			Consider(*It);
		}
	}
	return Best;
}

void ANVSentryTurret::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	AActor* T = Current.Get();
	const FVector From = Gun->GetComponentLocation();
	if (!T || !InArc(T->GetActorLocation()) || !UNVHostileFire::CanSee(GetWorld(), this, From, T)
		|| (T->FindComponentByClass<UNVHealthComponent>() && T->FindComponentByClass<UNVHealthComponent>()->IsDead()))
	{
		AActor* NewT = PickTarget();
		if (NewT != T)
		{
			Current = NewT;
			T = NewT;
			LockTimer = LockTime;
			ShotsLeft = 0;
			if (T && LockSound)
			{
				UGameplayStatics::PlaySoundAtLocation(this, LockSound, GetActorLocation(), 0.8f);
			}
		}
	}
	// aim: track the target, or sweep the arc slowly
	FRotator Want;
	if (T)
	{
		Want = (T->GetActorLocation() - Head->GetComponentLocation()).Rotation();
	}
	else
	{
		SweepTime += DeltaSeconds;
		Want = GetActorRotation() + FRotator(-4.f, FieldOfFireDeg * 0.8f * FMath::Sin(SweepTime * 0.5f), 0.f);
	}
	const FRotator Cur = Head->GetComponentRotation();
	const FRotator Next = FMath::RInterpConstantTo(Cur, Want, DeltaSeconds, TurnRateDeg);
	Head->SetWorldRotation(Next);

	// laser to the first thing it hits
	{
		const FVector S = Head->GetComponentLocation() + Head->GetForwardVector() * 60.f;
		const FVector E = S + Head->GetForwardVector() * Range;
		FHitResult Hit;
		FCollisionQueryParams Params(SCENE_QUERY_STAT(NVTurretLaser), false, this);
		const FVector End = GetWorld()->LineTraceSingleByChannel(Hit, S, E, ECC_Visibility, Params) ? Hit.ImpactPoint : E;
		const float Len = FVector::Dist(S, End);
		Laser->SetWorldLocation((S + End) * 0.5f);
		Laser->SetWorldRotation(FRotationMatrix::MakeFromZ(End - S).Rotator());
		Laser->SetWorldScale3D(FVector(0.012f, 0.012f, Len / 100.f));
	}
	if (!T)
	{
		return;
	}
	const bool bOnTarget = FVector::DotProduct(Head->GetForwardVector(), (T->GetActorLocation() - Head->GetComponentLocation()).GetSafeNormal()) > 0.985f;
	if (LockTimer > 0.f)
	{
		LockTimer -= DeltaSeconds;
		StatusLight->SetIntensity(FMath::Fmod(GetWorld()->GetTimeSeconds() * 12.f, 1.f) < 0.5f ? 9000.f : 1500.f);
		return;
	}
	StatusLight->SetIntensity(2500.f);
	FireTimer -= DeltaSeconds;
	if (FireTimer > 0.f || !bOnTarget)
	{
		return;
	}
	if (ShotsLeft <= 0)
	{
		ShotsLeft = BurstShots;
	}
	Gun->Fire(T, UNVHostileFire::AimPointOn(T));
	--ShotsLeft;
	FireTimer = ShotsLeft > 0 ? ShotInterval : BurstPause;
}
