#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimInstanceProxy.h"
#include "Combat/NVWeaponData.h"
#include "NVBodyAnimInstance.generated.h"

class UAnimSequence;
class UBlendSpace;

/** Directions in the 8-way sets, clockwise from forward. */
enum class ENVBodyDir : uint8 { Fwd, FwdRight, Right, BwdRight, Bwd, BwdLeft, Left, FwdLeft, Num };

/** One gait cycle of a locomotion clip, from its L/R foot sync markers: left plant, right plant, next left plant. */
struct FNVGaitCycle
{
	float L0 = 0.f, R = 0.5f, L1 = 1.f, Len = 1.f;
	float Duration() const { return FMath::Max(L1 - L0, 0.05f); }
	/** Clip time for a gait phase (0 = left foot plant, 0.5 = right foot plant). */
	float TimeAt(float G) const
	{
		const float T = G < 0.5f ? L0 + (G / 0.5f) * (R - L0) : R + ((G - 0.5f) / 0.5f) * (L1 - R);
		return FMath::Fmod(T, Len);
	}
};

/** One animation set for the third-person body: unarmed, rifle or pistol. */
USTRUCT(BlueprintType)
struct FNVBodyAnimSet
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, Category = "Body")
	TObjectPtr<UAnimSequence> Idle;

	/** 8-way jog, clockwise from forward (Fwd, FwdRight, Right, BwdRight, Bwd, BwdLeft, Left, FwdLeft). */
	UPROPERTY(EditAnywhere, Category = "Body")
	TArray<TObjectPtr<UAnimSequence>> Jog;

	UPROPERTY(EditAnywhere, Category = "Body")
	TArray<TObjectPtr<UAnimSequence>> Walk;

	UPROPERTY(EditAnywhere, Category = "Body")
	TObjectPtr<UAnimSequence> FallLoop;

	UPROPERTY(EditAnywhere, Category = "Body")
	TObjectPtr<UAnimSequence> Equip;

	UPROPERTY(EditAnywhere, Category = "Body")
	TObjectPtr<UAnimSequence> Reload;

	UPROPERTY(EditAnywhere, Category = "Body")
	TObjectPtr<UAnimSequence> Fire;

	UPROPERTY(EditAnywhere, Category = "Body")
	TObjectPtr<UAnimSequence> Attack;

	/** Pitch aim offset (mesh-space additive). */
	UPROPERTY(EditAnywhere, Category = "Body")
	TObjectPtr<UBlendSpace> AimOffset;

	/** Root speed the jog/walk cycles were authored at (cm/s); measured from root motion when present. */
	float JogSpeed = 380.f;
	float WalkSpeed = 160.f;

	/** Foot-synced cycles for Jog[i] / Walk[i] (directional clips hold 1-3 strides each, so they are synced by
	 *  foot plants, not by normalized clip time). */
	FNVGaitCycle JogCycle[8];
	FNVGaitCycle WalkCycle[8];
};

/** Everything the worker thread needs to build one frame's pose (raw pointers kept alive by the instance). */
struct FNVBodyPoseFrame
{
	struct FTerm
	{
		const UAnimSequence* Seq = nullptr;
		float Time = 0.f;
		float Weight = 0.f;
	};

	FTerm Loco[5];       // idle + up to 4 directional cycle terms
	int32 NumLoco = 0;
	FTerm Fall;
	FTerm Action;        // upper body one-shot (fire / reload / equip / melee)
	const UBlendSpace* AimOffset = nullptr;
	float AimPitch = 0.f;
	float AimWeight = 0.f;
	/** Blend from the previous output pose (state switches); 0 = none. */
	float CarryOver = 0.f;

	/** Left hand onto the weapon: weapon transform relative to hand_r, and the hold point in weapon space. */
	float LeftHandWeight = 0.f;
	FTransform Grip = FTransform::Identity;
	FVector LeftHandLocal = FVector::ZeroVector;
};

struct FNVBodyAnimProxy : public FAnimInstanceProxy
{
	FNVBodyAnimProxy() = default;
	explicit FNVBodyAnimProxy(UAnimInstance* Instance) : FAnimInstanceProxy(Instance) {}

	virtual void PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds) override;
	virtual bool Evaluate(FPoseContext& Output) override;

	FNVBodyPoseFrame Frame;
	FName UpperBodyRoot = TEXT("spine_01");
	class UNVBodyAnimInstance* Owner = nullptr;

private:
	bool EvalSeq(const UAnimSequence* Seq, float Time, FPoseContext& Out) const;
	TArray<float> UpperWeights;
	int32 UpperWeightsBoneCount = -1;
	TArray<FTransform> LastPose;
};

/**
 * Ghost-7's third-person body, built natively (no anim graph): 8-way strafing locomotion with walk/jog blend and
 * phase sync, falling, per-weapon idle/aim pose, a pitch aim offset, and upper-body one-shots layered from the spine
 * (fire, reload, equip, melee). Sets come from the template Mannequin animations already in the project.
 */
UCLASS()
class NEONVEIL_API UNVBodyAnimInstance : public UAnimInstance
{
	GENERATED_BODY()

public:
	UNVBodyAnimInstance();

	enum class EAction : uint8 { None, Fire, Reload, Equip, Attack };

	/** Start an upper-body one-shot from the current set. Duration > 0 time-fits the clip (e.g. to ReloadTime). */
	void PlayAction(EAction Action, float Duration = 0.f);

	/** Which set the body uses; switching blends from the last pose. */
	void SetHold(bool bArmed, ENVWeaponHold Hold);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Body")
	FNVBodyAnimSet Unarmed;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Body")
	FNVBodyAnimSet Rifle;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Body")
	FNVBodyAnimSet Pistol;

	/** Seconds to blend between sets / into actions. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Body")
	float SwitchBlendTime = 0.22f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Body")
	float ActionBlendIn = 0.08f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Body")
	float ActionBlendOut = 0.18f;

	/** Weapon placement for the left-hand IK: weapon relative to hand_r, and where the left hand holds it (weapon
	 *  space). Zero LeftHandLocal turns the IK off (pistols already hold two-handed around the right hand). */
	void SetWeaponGrip(const FTransform& InGrip, const FVector& InLeftHandLocal);

	/** Report of the measured cycle speeds (for tuning). */
	FString DescribeSets() const;

protected:
	virtual void NativeInitializeAnimation() override;
	virtual void NativeUpdateAnimation(float DeltaSeconds) override;
	virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override { return new FNVBodyAnimProxy(this); }
	virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy) override { delete InProxy; }

private:
	friend struct FNVBodyAnimProxy;

	void LoadDefaults();
	const FNVBodyAnimSet& CurrentSet() const;
	void BuildFrame(float DeltaSeconds);

	FTransform GripTransform = FTransform::Identity;
	FVector LeftHandLocal = FVector::ZeroVector;
	float LeftHandWeight = 0.f;
	EAction ActionKind = EAction::None;

	bool bArmed = false;
	ENVWeaponHold HoldType = ENVWeaponHold::Rifle;

	float Phase = 0.f;          // normalized locomotion cycle phase
	float IdleTime = 0.f;
	float MoveWeight = 0.f;
	float GaitAlpha = 1.f;
	float FallWeight = 0.f;
	float FallTime = 0.f;
	float SmoothedPitch = 0.f;
	float CarryOver = 0.f;

	UPROPERTY(Transient)
	TObjectPtr<UAnimSequence> ActionSeq;
	float ActionTime = 0.f;
	float ActionRate = 1.f;
	float ActionWeight = 0.f;
	bool bActionActive = false;

	FNVBodyPoseFrame PendingFrame;

public:
	// Debug counters (NVBodyInfo).
	int32 DebugActionCalls = 0;
	int32 DebugActionRejected = 0;
	mutable int32 DebugUpperBones = -1;
	mutable float DebugEvalActionWeight = 0.f;
};
