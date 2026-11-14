#include "Character/NVBodyAnimInstance.h"
#include "Animation/AnimSequence.h"
#include "Animation/BlendSpace.h"
#include "Animation/AnimationPoseData.h"
#include "AnimationRuntime.h"
#include "BonePose.h"
#include "TwoBoneIK.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"

namespace NVBody
{
	static const TCHAR* Root = TEXT("/Game/Characters/Mannequins/Anims/");
	static const TCHAR* DirNames[8] = { TEXT("Fwd"), TEXT("Fwd_Right"), TEXT("Right"), TEXT("Bwd_Right"), TEXT("Bwd"), TEXT("Bwd_Left"), TEXT("Left"), TEXT("Fwd_Left") };

	template <typename T>
	static T* Load(const FString& Rel)
	{
		const FString Path = FString(Root) + Rel;
		const FString Name = FPaths::GetBaseFilename(Path);
		return LoadObject<T>(nullptr, *(Path + TEXT(".") + Name));
	}

	static float Len(const UAnimSequence* S) { return S ? FMath::Max(S->GetPlayLength(), 0.01f) : 1.f; }

	/** First L -> R -> L foot-plant cycle from the clip's sync markers (wrapping), or false if it has none. */
	static bool CycleFromMarkers(const UAnimSequence* S, FNVGaitCycle& Out)
	{
		if (!S)
		{
			return false;
		}
		const float L = Len(S);
		TArray<FAnimSyncMarker> M = S->AuthoredSyncMarkers;
		M.Sort([](const FAnimSyncMarker& A, const FAnimSyncMarker& B) { return A.Time < B.Time; });
		auto IsL = [](const FAnimSyncMarker& X) { return X.MarkerName.ToString().StartsWith(TEXT("L")); };
		auto IsR = [](const FAnimSyncMarker& X) { return X.MarkerName.ToString().StartsWith(TEXT("R")); };
		int32 IL = M.IndexOfByPredicate(IsL);
		if (IL == INDEX_NONE || M.Num() < 2)
		{
			return false;
		}
		// Walk forward (wrapping) from that L to the next R and the next L.
		const int32 N = M.Num();
		float T0 = M[IL].Time, TR = -1.f, T1 = -1.f;
		for (int32 k = 1; k <= N && T1 < 0.f; ++k)
		{
			const FAnimSyncMarker& X = M[(IL + k) % N];
			const float T = X.Time + ((IL + k) >= N ? L : 0.f);
			if (TR < 0.f && IsR(X)) { TR = T; }
			else if (TR >= 0.f && IsL(X)) { T1 = T; }
		}
		if (TR < 0.f)
		{
			return false;
		}
		if (T1 < 0.f)
		{
			T1 = T0 + L;   // a single stride pair in the clip
		}
		Out.L0 = T0; Out.R = TR; Out.L1 = T1; Out.Len = L;
		return true;
	}

	/** Root speed of a cycle in cm/s, or 0 if it is in place. */
	static float CycleSpeed(const UAnimSequence* S)
	{
		if (!S)
		{
			return 0.f;
		}
		const float L = Len(S);
		const FTransform Delta = S->ExtractRootMotionFromRange(0.0, L, FAnimExtractContext());
		return Delta.GetTranslation().Size2D() / L;
	}
}

UNVBodyAnimInstance::UNVBodyAnimInstance()
{
}

void UNVBodyAnimInstance::LoadDefaults()
{
	using namespace NVBody;
	auto Fill = [](FNVBodyAnimSet& S, const FString& Kind, const FString& Idle, const FString& Fall, const FString& Equip,
		const FString& Reload, const FString& Fire, const FString& Attack, const FString& AO)
	{
		if (!S.Idle) { S.Idle = Load<UAnimSequence>(Idle); }
		if (S.Jog.Num() != 8)
		{
			S.Jog.Reset();
			S.Walk.Reset();
			for (const TCHAR* D : DirNames)
			{
				S.Jog.Add(Load<UAnimSequence>(FString::Printf(TEXT("%s/Jog/MF_%s_Jog_%s"), *Kind, *Kind, D)));
				S.Walk.Add(Load<UAnimSequence>(FString::Printf(TEXT("%s/Walk/MF_%s_Walk_%s"), *Kind, *Kind, D)));
			}
		}
		if (!S.FallLoop && !Fall.IsEmpty()) { S.FallLoop = Load<UAnimSequence>(Fall); }
		if (!S.Equip && !Equip.IsEmpty()) { S.Equip = Load<UAnimSequence>(Equip); }
		if (!S.Reload && !Reload.IsEmpty()) { S.Reload = Load<UAnimSequence>(Reload); }
		if (!S.Fire && !Fire.IsEmpty()) { S.Fire = Load<UAnimSequence>(Fire); }
		if (!S.Attack && !Attack.IsEmpty()) { S.Attack = Load<UAnimSequence>(Attack); }
		if (!S.AimOffset && !AO.IsEmpty()) { S.AimOffset = Load<UBlendSpace>(AO); }

		for (int32 Pass = 0; Pass < 2; ++Pass)
		{
			TArray<TObjectPtr<UAnimSequence>>& Clips = Pass == 0 ? S.Jog : S.Walk;
			FNVGaitCycle* Cyc = Pass == 0 ? S.JogCycle : S.WalkCycle;
			bool bOk[8] = {};
			for (int32 i = 0; i < 8 && i < Clips.Num(); ++i)
			{
				bOk[i] = CycleFromMarkers(Clips[i], Cyc[i]);
			}
			for (int32 i = 0; i < 8 && i < Clips.Num(); ++i)
			{
				if (bOk[i] || !Clips[i])
				{
					continue;
				}
				// Unmarked diagonals are the neighbouring cardinal clip re-rooted: borrow its cycle when lengths match.
				const float Li = Len(Clips[i]);
				bool bDone = false;
				for (int32 Nb : { (i + 7) % 8, (i + 1) % 8 })
				{
					if (bOk[Nb] && Clips[Nb] && FMath::IsNearlyEqual(Len(Clips[Nb]), Li, 0.02f))
					{
						Cyc[i] = Cyc[Nb];
						bDone = true;
						break;
					}
				}
				if (!bDone)
				{
					Cyc[i].L0 = 0.f; Cyc[i].R = Li * 0.5f; Cyc[i].L1 = Li; Cyc[i].Len = Li;
				}
			}
		}

		const float J = CycleSpeed(S.Jog.IsValidIndex(0) ? S.Jog[0].Get() : nullptr);
		const float W = CycleSpeed(S.Walk.IsValidIndex(0) ? S.Walk[0].Get() : nullptr);
		S.JogSpeed = J > 60.f ? J : 380.f;
		S.WalkSpeed = W > 30.f ? W : 160.f;
		if (S.WalkSpeed >= S.JogSpeed - 20.f)
		{
			S.WalkSpeed = S.JogSpeed * 0.45f;
		}
	};

	Fill(Unarmed, TEXT("Unarmed"), TEXT("Unarmed/MM_Idle"), TEXT("Unarmed/Jump/MM_Fall_Loop"), FString(), FString(), FString(),
		TEXT("Unarmed/Attack/MM_Attack_01"), FString());
	Fill(Rifle, TEXT("Rifle"), TEXT("Rifle/MF_Rifle_Idle_ADS"), TEXT("Rifle/Jump/MM_Rifle_Jump_Fall_Loop"), TEXT("Rifle/MM_Rifle_Equip"),
		TEXT("Rifle/MM_Rifle_Reload"), TEXT("Rifle/MM_Rifle_Fire"), TEXT("Unarmed/Attack/MM_Attack_01"), TEXT("Rifle/AIM/AO_Rifle"));
	Fill(Pistol, TEXT("Pistol"), TEXT("Pistol/MF_Pistol_Idle_ADS"), TEXT("Pistol/Jump/MM_Pistol_Jump_Fall_Loop"), TEXT("Pistol/MM_Pistol_Equip"),
		TEXT("Pistol/MM_Pistol_Reload"), TEXT("Pistol/MM_Pistol_Fire"), TEXT("Unarmed/Attack/MM_Attack_01"), TEXT("Pistol/Aim/AO_Pistol"));
}

FString UNVBodyAnimInstance::DescribeSets() const
{
	auto D = [](const TCHAR* N, const FNVBodyAnimSet& S)
	{
		int32 Jogs = 0, Walks = 0;
		for (const auto& A : S.Jog) { Jogs += A ? 1 : 0; }
		for (const auto& A : S.Walk) { Walks += A ? 1 : 0; }
		return FString::Printf(TEXT("%s: idle=%s jog=%d/8 (%.0f cm/s, %.2fs) walk=%d/8 (%.0f cm/s) fall=%d equip=%d reload=%d fire=%d ao=%s"),
			N, S.Idle ? *S.Idle->GetName() : TEXT("-"), Jogs, S.JogSpeed, (S.Jog.Num() && S.Jog[0]) ? S.Jog[0]->GetPlayLength() : 0.f,
			Walks, S.WalkSpeed, S.FallLoop != nullptr, S.Equip != nullptr, S.Reload != nullptr, S.Fire != nullptr,
			S.AimOffset ? *S.AimOffset->GetName() : TEXT("-"));
	};
	return D(TEXT("Unarmed"), Unarmed) + TEXT("\n") + D(TEXT("Rifle"), Rifle) + TEXT("\n") + D(TEXT("Pistol"), Pistol)
		+ FString::Printf(TEXT("\narmed=%d hold=%d actions: calls=%d rejected=%d active=%d kind=%d seq=%s t=%.2f rate=%.2f w=%.2f | eval w=%.2f upperBones=%d | move=%.2f gait=%.2f fall=%.2f left=%.2f"),
			bArmed, (int32)HoldType, DebugActionCalls, DebugActionRejected, bActionActive, (int32)ActionKind, ActionSeq ? *ActionSeq->GetName() : TEXT("-"),
			ActionTime, ActionRate, ActionWeight, DebugEvalActionWeight, DebugUpperBones, MoveWeight, GaitAlpha, FallWeight, LeftHandWeight);
}

void UNVBodyAnimInstance::NativeInitializeAnimation()
{
	Super::NativeInitializeAnimation();
	LoadDefaults();
}

const FNVBodyAnimSet& UNVBodyAnimInstance::CurrentSet() const
{
	if (!bArmed)
	{
		return Unarmed;
	}
	return HoldType == ENVWeaponHold::Pistol ? Pistol : Rifle;
}

void UNVBodyAnimInstance::SetHold(bool bInArmed, ENVWeaponHold InHold)
{
	if (bInArmed == bArmed && (!bArmed || InHold == HoldType))
	{
		return;
	}
	bArmed = bInArmed;
	HoldType = InHold;
	CarryOver = 1.f;
	// A one-shot from the old set no longer matches the hands.
	bActionActive = false;
	ActionWeight = 0.f;
	ActionSeq = nullptr;
}

void UNVBodyAnimInstance::SetWeaponGrip(const FTransform& InGrip, const FVector& InLeftHandLocal)
{
	GripTransform = InGrip;
	LeftHandLocal = InLeftHandLocal;
}

void UNVBodyAnimInstance::PlayAction(EAction Action, float Duration)
{
	const FNVBodyAnimSet& S = CurrentSet();
	UAnimSequence* Seq = nullptr;
	switch (Action)
	{
	case EAction::Fire: Seq = S.Fire; break;
	case EAction::Reload: Seq = S.Reload; break;
	case EAction::Equip: Seq = S.Equip; break;
	case EAction::Attack: Seq = S.Attack; break;
	default: break;
	}
	++DebugActionCalls;
	if (!Seq)
	{
		++DebugActionRejected;
		return;
	}
	// Firing must not cut a reload or draw short.
	if (Action == EAction::Fire && bActionActive && (ActionKind == EAction::Reload || ActionKind == EAction::Equip))
	{
		return;
	}
	const float L = NVBody::Len(Seq);
	const bool bRestartFire = Action == EAction::Fire && bActionActive && ActionKind == EAction::Fire;
	ActionSeq = Seq;
	ActionKind = Action;
	ActionRate = Duration > 0.f ? L / Duration : (Action == EAction::Equip ? 1.35f : 1.f);
	// Back-to-back shots restart a little in so the kick reads without snapping back to the start pose.
	ActionTime = bRestartFire ? FMath::Min(0.04f, L * 0.2f) : 0.f;
	bActionActive = true;
}

void UNVBodyAnimInstance::NativeUpdateAnimation(float DeltaSeconds)
{
	Super::NativeUpdateAnimation(DeltaSeconds);
	BuildFrame(DeltaSeconds);
}

void UNVBodyAnimInstance::BuildFrame(float Dt)
{
	using namespace NVBody;
	FNVBodyPoseFrame F;
	const FNVBodyAnimSet& S = CurrentSet();

	float Speed = 0.f, DirDeg = 0.f, AimPitch = 0.f;
	bool bFalling = false;
	if (const ACharacter* C = Cast<ACharacter>(TryGetPawnOwner()))
	{
		FVector V = C->GetVelocity();
		V.Z = 0.f;
		Speed = V.Size();
		const FVector Local = C->GetActorRotation().UnrotateVector(V);
		DirDeg = FMath::RadiansToDegrees(FMath::Atan2(Local.Y, Local.X));
		bFalling = C->GetCharacterMovement() && C->GetCharacterMovement()->IsFalling();
		AimPitch = FRotator::NormalizeAxis(C->GetBaseAimRotation().Pitch);
	}

	// --- Locomotion weights
	const float MoveTarget = bFalling ? MoveWeight : FMath::Clamp((Speed - 15.f) / 110.f, 0.f, 1.f);
	MoveWeight = FMath::FInterpTo(MoveWeight, MoveTarget, Dt, 9.f);
	const bool bHasWalk = S.Walk.Num() == 8 && S.Walk[0] != nullptr;
	const float GaitTarget = bHasWalk ? FMath::Clamp((Speed - S.WalkSpeed) / FMath::Max(S.JogSpeed - S.WalkSpeed, 1.f), 0.f, 1.f) : 1.f;
	GaitAlpha = FMath::FInterpTo(GaitAlpha, GaitTarget, Dt, 6.f);

	IdleTime += Dt;
	if (S.Idle)
	{
		IdleTime = FMath::Fmod(IdleTime, Len(S.Idle));
	}
	F.Loco[F.NumLoco++] = { S.Idle.Get(), IdleTime, 1.f - MoveWeight };

	if (MoveWeight > 0.001f)
	{
		const float Idx = (DirDeg < 0.f ? DirDeg + 360.f : DirDeg) / 45.f;
		const int32 I0 = FMath::FloorToInt(Idx) % 8;
		const int32 I1 = (I0 + 1) % 8;
		const float Fr = Idx - FMath::FloorToFloat(Idx);

		// Gait phase is one left-right stride pair, shared by every clip through its foot-plant markers, and advanced
		// so the planted foot keeps pace with the ground: cycles per second = speed / (clip speed * cycle duration).
		float RateSum = 0.f, WSum = 0.f;
		auto Accum = [&](const FNVGaitCycle* Cyc, const TArray<TObjectPtr<UAnimSequence>>& Set, float ClipSpeed, float GaitW)
		{
			if (Set.Num() != 8 || GaitW <= 0.001f)
			{
				return;
			}
			for (const TPair<int32, float>& T : { TPair<int32, float>(I0, 1.f - Fr), TPair<int32, float>(I1, Fr) })
			{
				if (Set[T.Key] && T.Value > 0.001f)
				{
					const float W = GaitW * T.Value;
					RateSum += W * Speed / (FMath::Max(ClipSpeed, 1.f) * Cyc[T.Key].Duration());
					WSum += W;
				}
			}
		};
		const float JogW = bHasWalk ? GaitAlpha : 1.f;
		Accum(S.JogCycle, S.Jog, S.JogSpeed, JogW);
		if (bHasWalk)
		{
			Accum(S.WalkCycle, S.Walk, S.WalkSpeed, 1.f - JogW);
		}
		if (WSum > 0.f)
		{
			Phase = FMath::Fmod(Phase + Dt * RateSum / WSum, 1.f);
		}

		auto AddDir = [&](const FNVGaitCycle* Cyc, const TArray<TObjectPtr<UAnimSequence>>& Set, float GaitW)
		{
			if (Set.Num() != 8 || GaitW <= 0.001f)
			{
				return;
			}
			const UAnimSequence* A = Set[I0];
			const UAnimSequence* B = Set[I1];
			if (A) { F.Loco[F.NumLoco++] = { A, Cyc[I0].TimeAt(Phase), MoveWeight * GaitW * (1.f - Fr) }; }
			if (B) { F.Loco[F.NumLoco++] = { B, Cyc[I1].TimeAt(Phase), MoveWeight * GaitW * Fr }; }
		};
		AddDir(S.JogCycle, S.Jog, JogW);
		if (bHasWalk)
		{
			AddDir(S.WalkCycle, S.Walk, 1.f - JogW);
		}
	}

	// --- Falling
	FallWeight = FMath::FInterpConstantTo(FallWeight, bFalling ? 1.f : 0.f, Dt, 6.f);
	FallTime = bFalling ? FallTime + Dt : 0.f;
	if (S.FallLoop && FallWeight > 0.001f)
	{
		F.Fall = { S.FallLoop.Get(), FMath::Fmod(FallTime, Len(S.FallLoop)), FallWeight };
	}

	// --- Upper-body one-shot
	if (bActionActive && ActionSeq)
	{
		ActionTime += Dt * ActionRate;
		const float L = Len(ActionSeq);
		if (ActionTime >= L)
		{
			bActionActive = false;
		}
		else
		{
			const float In = ActionKind == EAction::Fire ? 1.f : FMath::Clamp(ActionTime / (ActionBlendIn * ActionRate), 0.f, 1.f);
			const float Out = FMath::Clamp((L - ActionTime) / (ActionBlendOut * ActionRate), 0.f, 1.f);
			ActionWeight = FMath::Min(In, Out);
			F.Action = { ActionSeq.Get(), ActionTime, ActionWeight };
		}
	}
	if (!bActionActive)
	{
		ActionWeight = 0.f;
	}

	// --- Aim offset (armed only; eased off while the hands are busy reloading/drawing)
	SmoothedPitch = FMath::FInterpTo(SmoothedPitch, FMath::Clamp(AimPitch, -75.f, 75.f), Dt, 14.f);
	const bool bBusy = bActionActive && (ActionKind == EAction::Reload || ActionKind == EAction::Equip || ActionKind == EAction::Attack);
	F.AimOffset = bArmed ? S.AimOffset.Get() : nullptr;
	F.AimPitch = SmoothedPitch / 90.f;   // the template aim offsets take a normalized -1..1 pitch
	F.AimWeight = bArmed ? (1.f - 0.75f * (bBusy ? ActionWeight : 0.f)) : 0.f;

	// --- Left hand on the weapon
	const bool bWantLeft = bArmed && !LeftHandLocal.IsNearlyZero() && !bBusy;
	LeftHandWeight = FMath::FInterpConstantTo(LeftHandWeight, bWantLeft ? 1.f : 0.f, Dt, 6.f);
	F.LeftHandWeight = LeftHandWeight;
	F.Grip = GripTransform;
	F.LeftHandLocal = LeftHandLocal;

	// --- Set switch carry-over
	CarryOver = FMath::Max(0.f, CarryOver - Dt / FMath::Max(SwitchBlendTime, 0.01f));
	F.CarryOver = FMath::Square(CarryOver);

	PendingFrame = F;
}

// ------------------------------------------------------------------ proxy (worker thread)

void FNVBodyAnimProxy::PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds)
{
	FAnimInstanceProxy::PreUpdate(InAnimInstance, DeltaSeconds);
	if (UNVBodyAnimInstance* I = Cast<UNVBodyAnimInstance>(InAnimInstance))
	{
		Frame = I->PendingFrame;
		Owner = I;
	}
}

bool FNVBodyAnimProxy::EvalSeq(const UAnimSequence* Seq, float Time, FPoseContext& Out) const
{
	if (!Seq || !Seq->GetSkeleton())
	{
		Out.ResetToRefPose();
		return false;
	}
	FAnimationPoseData PD(Out);
	Seq->GetAnimationPose(PD, FAnimExtractContext(static_cast<double>(Time), false, FDeltaTimeRecord(), true));
	return true;
}

bool FNVBodyAnimProxy::Evaluate(FPoseContext& Output)
{
	const FBoneContainer& Bones = Output.Pose.GetBoneContainer();
	const int32 NumBones = Output.Pose.GetNumBones();

	auto BlendInto = [&](FPoseContext& Other, float WeightOfOutput)
	{
		FPoseContext R(Output);
		const FAnimationPoseData A(Output);
		const FAnimationPoseData B(Other);
		FAnimationPoseData RD(R);
		FAnimationRuntime::BlendTwoPosesTogether(A, B, WeightOfOutput, RD);
		Output = R;
	};

	// 1) Locomotion: idle + directional walk/jog cycles, accumulated as a normalized weighted blend.
	float Acc = 0.f;
	for (int32 i = 0; i < Frame.NumLoco; ++i)
	{
		const FNVBodyPoseFrame::FTerm& T = Frame.Loco[i];
		if (!T.Seq || T.Weight <= 0.001f)
		{
			continue;
		}
		if (Acc <= 0.f)
		{
			EvalSeq(T.Seq, T.Time, Output);
			Acc = T.Weight;
			continue;
		}
		FPoseContext P(Output);
		EvalSeq(T.Seq, T.Time, P);
		BlendInto(P, Acc / (Acc + T.Weight));
		Acc += T.Weight;
	}
	if (Acc <= 0.f)
	{
		Output.ResetToRefPose();
	}

	// 2) Falling (full body).
	if (Frame.Fall.Seq && Frame.Fall.Weight > 0.001f)
	{
		FPoseContext P(Output);
		EvalSeq(Frame.Fall.Seq, Frame.Fall.Time, P);
		BlendInto(P, 1.f - Frame.Fall.Weight);
	}

	// 3) Upper-body one-shot. Additive clips (the template fire kicks are mesh-space rotation offsets) are added on
	//    top; full-pose clips (reload, draw, melee) are layered from the spine.
	if (Frame.Action.Seq && Frame.Action.Weight > 0.001f)
	{
		const EAdditiveAnimationType AddType = Frame.Action.Seq->GetAdditiveAnimType();
		if (AddType != AAT_None)
		{
			FPoseContext Add(Output, true);
			EvalSeq(Frame.Action.Seq, Frame.Action.Time, Add);
			FAnimationPoseData Base(Output);
			const FAnimationPoseData AddData(Add);
			if (AddType == AAT_RotationOffsetMeshSpace)
			{
				FAnimationRuntime::AccumulateMeshSpaceRotationAdditiveToLocalPose(Base, AddData, Frame.Action.Weight);
			}
			else
			{
				FAnimationRuntime::AccumulateAdditivePose(Base, AddData, Frame.Action.Weight, AddType);
			}
			Output.Pose.NormalizeRotations();
		}
		else
		{
		if (UpperWeightsBoneCount != NumBones)
		{
			UpperWeights.SetNumZeroed(NumBones);
			const int32 SpineMesh = Bones.GetPoseBoneIndexForBoneName(UpperBodyRoot);
			const FCompactPoseBoneIndex Spine = SpineMesh != INDEX_NONE ? Bones.MakeCompactPoseIndex(FMeshPoseBoneIndex(SpineMesh)) : FCompactPoseBoneIndex(INDEX_NONE);
			for (FCompactPoseBoneIndex B : Output.Pose.ForEachBoneIndex())
			{
				float W = 0.f;
				if (B == Spine)
				{
					W = 1.f;
				}
				else
				{
					const FCompactPoseBoneIndex Parent = Bones.GetParentBoneIndex(B);
					W = Parent.IsValid() ? UpperWeights[Parent.GetInt()] : 0.f;
				}
				UpperWeights[B.GetInt()] = W;
			}
			UpperWeightsBoneCount = NumBones;
		}
		if (Owner)
		{
			int32 N = 0;
			for (float X : UpperWeights) { N += X > 0.f ? 1 : 0; }
			Owner->DebugUpperBones = N;
			Owner->DebugEvalActionWeight = Frame.Action.Weight;
		}
		TArray<float> W = UpperWeights;
		for (float& X : W)
		{
			X *= Frame.Action.Weight;
		}
		FPoseContext P(Output);
		EvalSeq(Frame.Action.Seq, Frame.Action.Time, P);
		FPoseContext R(Output);
		const FAnimationPoseData A(Output);
		const FAnimationPoseData Bd(P);
		FAnimationPoseData RD(R);
		FAnimationRuntime::BlendTwoPosesTogetherPerBone(A, Bd, W, RD);
		Output = R;
		}
	}

	// 4) Pitch aim offset (mesh-space rotation additive).
	if (Frame.AimOffset && Frame.AimWeight > 0.001f)
	{
		// Template AOs: X = yaw, Y = pitch, both normalized -1..1.
		const FVector Input(0.f, FMath::Clamp(Frame.AimPitch, -1.f, 1.f), 0.f);
		TArray<FBlendSampleData> Samples;
		int32 Tri = INDEX_NONE;
		if (Frame.AimOffset->GetSamplesFromBlendInput(Input, Samples, Tri, true) && Samples.Num() > 0)
		{
			FPoseContext Add(Output, true);
			FAnimationPoseData AddData(Add);
			Frame.AimOffset->GetAnimationPose(Samples, FAnimExtractContext(), AddData);
			FAnimationPoseData Base(Output);
			FAnimationRuntime::AccumulateMeshSpaceRotationAdditiveToLocalPose(Base, AddData, Frame.AimWeight);
			Output.Pose.NormalizeRotations();
		}
	}

	// 5) Keep the root where the capsule puts it (cycles are played in place).
	if (NumBones > 0)
	{
		const FCompactPoseBoneIndex RootIdx(0);
		Output.Pose[RootIdx] = Bones.GetRefPoseTransform(RootIdx);
	}

	// 6) Left hand onto the weapon (two-bone IK in component space).
	if (Frame.LeftHandWeight > 0.001f)
	{
		auto Find = [&](const TCHAR* Name)
		{
			const int32 M = Bones.GetPoseBoneIndexForBoneName(FName(Name));
			return M != INDEX_NONE ? Bones.MakeCompactPoseIndex(FMeshPoseBoneIndex(M)) : FCompactPoseBoneIndex(INDEX_NONE);
		};
		const FCompactPoseBoneIndex HandR = Find(TEXT("hand_r"));
		const FCompactPoseBoneIndex UpperL = Find(TEXT("upperarm_l"));
		const FCompactPoseBoneIndex LowerL = Find(TEXT("lowerarm_l"));
		const FCompactPoseBoneIndex HandL = Find(TEXT("hand_l"));
		if (HandR.IsValid() && UpperL.IsValid() && LowerL.IsValid() && HandL.IsValid())
		{
			FCSPose<FCompactPose> CS;
			CS.InitPose(Output.Pose);
			const FTransform HandRCS = CS.GetComponentSpaceTransform(HandR);
			const FVector Target = (Frame.Grip * HandRCS).TransformPosition(Frame.LeftHandLocal);
			FTransform RootT = CS.GetComponentSpaceTransform(UpperL);
			FTransform JointT = CS.GetComponentSpaceTransform(LowerL);
			FTransform EndT = CS.GetComponentSpaceTransform(HandL);
			const FVector Effector = FMath::Lerp(EndT.GetLocation(), Target, Frame.LeftHandWeight);
			// Pole: keep the elbow bending the way the animation bends it, pushed slightly down/out.
			const FVector Pole = JointT.GetLocation() + (JointT.GetLocation() - FMath::Lerp(RootT.GetLocation(), EndT.GetLocation(), 0.5f)).GetSafeNormal() * 30.f;
			AnimationCore::SolveTwoBoneIK(RootT, JointT, EndT, Pole, Effector, false, 1.0, 1.0);
			TArray<FBoneTransform> Out;
			Out.Add(FBoneTransform(UpperL, RootT));
			Out.Add(FBoneTransform(LowerL, JointT));
			Out.Add(FBoneTransform(HandL, EndT));
			CS.SafeSetCSBoneTransforms(Out);
			FCSPose<FCompactPose>::ConvertComponentPosesToLocalPoses(MoveTemp(CS), Output.Pose);
		}
	}

	// 7) Carry over from the last pose after a set switch (cheap inertial smoothing).
	if (Frame.CarryOver > 0.001f && LastPose.Num() == NumBones)
	{
		for (FCompactPoseBoneIndex B : Output.Pose.ForEachBoneIndex())
		{
			FTransform T;
			T.Blend(Output.Pose[B], LastPose[B.GetInt()], Frame.CarryOver);
			Output.Pose[B] = T;
		}
		Output.Pose.NormalizeRotations();
	}
	LastPose.SetNum(NumBones);
	for (FCompactPoseBoneIndex B : Output.Pose.ForEachBoneIndex())
	{
		LastPose[B.GetInt()] = Output.Pose[B];
	}
	return true;
}
