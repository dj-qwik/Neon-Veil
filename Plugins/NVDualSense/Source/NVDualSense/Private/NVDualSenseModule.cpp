// NV DualSense Input: reads a Sony DualSense / DualSense Edge over Windows HID (USB or Bluetooth)
// and feeds Unreal's standard gamepad keys, so Enhanced Input mappings written for an Xbox pad
// (Gamepad_FaceButton_Bottom, Gamepad_Left2D, Gamepad_RightTrigger, ...) work unchanged.
// Input only for now; rumble / adaptive triggers / lightbar are a later polish task.

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"
#include "IInputDeviceModule.h"
#include "IInputDevice.h"
#include "GenericPlatform/GenericApplicationMessageHandler.h"
#include "GenericPlatform/GenericPlatformInputDeviceMapper.h"
#include "HAL/Runnable.h"
#include "HAL/RunnableThread.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformProcess.h"
#include "Misc/ScopeLock.h"

DEFINE_LOG_CATEGORY_STATIC(LogNVDualSense, Log, All);

static TAutoConsoleVariable<int32> CVarNVDualSenseLogInput(
	TEXT("nv.DualSense.LogInput"), 1,
	TEXT("1 = log DualSense button presses (QA aid)."));

static TAutoConsoleVariable<float> CVarNVDualSenseDeadZone(
	TEXT("nv.DualSense.DeadZone"), 0.08f,
	TEXT("Radial stick dead zone, 0..0.5."));

namespace NVDS
{
	enum EButton : uint32
	{
		Cross, Circle, Square, Triangle, L1, R1, L3, R3, Create, Options,
		DUp, DDown, DLeft, DRight, L2Btn, R2Btn, Num
	};

	static const TArray<FGamepadKeyNames::Type>& Keys()
	{
		static const TArray<FGamepadKeyNames::Type> K = {
			FGamepadKeyNames::FaceButtonBottom, FGamepadKeyNames::FaceButtonRight,
			FGamepadKeyNames::FaceButtonLeft, FGamepadKeyNames::FaceButtonTop,
			FGamepadKeyNames::LeftShoulder, FGamepadKeyNames::RightShoulder,
			FGamepadKeyNames::LeftThumb, FGamepadKeyNames::RightThumb,
			FGamepadKeyNames::SpecialLeft, FGamepadKeyNames::SpecialRight,
			FGamepadKeyNames::DPadUp, FGamepadKeyNames::DPadDown,
			FGamepadKeyNames::DPadLeft, FGamepadKeyNames::DPadRight,
			FGamepadKeyNames::LeftTriggerThreshold, FGamepadKeyNames::RightTriggerThreshold };
		return K;
	}

	static const TCHAR* Names[] = { TEXT("Cross"), TEXT("Circle"), TEXT("Square"), TEXT("Triangle"),
		TEXT("L1"), TEXT("R1"), TEXT("L3"), TEXT("R3"), TEXT("Create"), TEXT("Options"),
		TEXT("DPadUp"), TEXT("DPadDown"), TEXT("DPadLeft"), TEXT("DPadRight"), TEXT("L2"), TEXT("R2") };

	struct FState
	{
		bool bConnected = false;
		float LX = 0.f, LY = 0.f, RX = 0.f, RY = 0.f, L2 = 0.f, R2 = 0.f;
		uint32 Buttons = 0;
	};

	static void ApplyRadialDeadZone(float& X, float& Y, float DZ)
	{
		const float Mag = FMath::Sqrt(X * X + Y * Y);
		if (Mag <= DZ)
		{
			X = Y = 0.f;
			return;
		}
		const float Scaled = FMath::Min(1.f, (Mag - DZ) / (1.f - DZ));
		X = X / Mag * Scaled;
		Y = Y / Mag * Scaled;
	}

	static float Stick(uint8 V) { return FMath::Clamp((float(V) - 127.5f) / 127.5f, -1.f, 1.f); }

	// Parses one input report. USB: id 0x01, full layout. Bluetooth: id 0x31 (extended, full layout)
	// or id 0x01 (simple layout, sent until the extended mode is requested).
	static bool Parse(const uint8* Buf, int32 Len, bool bBluetooth, uint32 PrevButtons, FState& Out)
	{
		if (Len < 11)
		{
			return false;
		}
		const uint8* D = nullptr;
		bool bFull = true;
		if (Buf[0] == 0x31)
		{
			D = Buf + 2;
		}
		else if (Buf[0] == 0x01)
		{
			D = Buf + 1;
			bFull = !bBluetooth;
		}
		else
		{
			return false;
		}

		uint8 L2, R2, B0, B1;
		if (bFull) { L2 = D[4]; R2 = D[5]; B0 = D[7]; B1 = D[8]; }
		else       { B0 = D[4]; B1 = D[5]; L2 = D[7]; R2 = D[8]; }

		Out.LX = Stick(D[0]);
		Out.LY = -Stick(D[1]); // HID: 0 = up; Unreal: +1 = up
		Out.RX = Stick(D[2]);
		Out.RY = -Stick(D[3]);
		Out.L2 = L2 / 255.f;
		Out.R2 = R2 / 255.f;

		uint32 B = 0;
		auto Set = [&B](EButton Btn, bool bOn) { if (bOn) { B |= (1u << Btn); } };
		Set(Square, B0 & 0x10); Set(Cross, B0 & 0x20); Set(Circle, B0 & 0x40); Set(Triangle, B0 & 0x80);
		const uint8 Hat = B0 & 0x0F; // 0 = N, clockwise, 8 = released
		Set(DUp, Hat == 0 || Hat == 1 || Hat == 7);
		Set(DRight, Hat == 1 || Hat == 2 || Hat == 3);
		Set(DDown, Hat == 3 || Hat == 4 || Hat == 5);
		Set(DLeft, Hat == 5 || Hat == 6 || Hat == 7);
		Set(L1, B1 & 0x01); Set(R1, B1 & 0x02);
		Set(Create, B1 & 0x10); Set(Options, B1 & 0x20);
		Set(L3, B1 & 0x40); Set(R3, B1 & 0x80);
		// Trigger "buttons" with hysteresis, matching XInput's ~30/255 threshold.
		const bool bL2Was = PrevButtons & (1u << L2Btn), bR2Was = PrevButtons & (1u << R2Btn);
		Set(L2Btn, bL2Was ? Out.L2 > 0.08f : Out.L2 > 0.12f);
		Set(R2Btn, bR2Was ? Out.R2 > 0.08f : Out.R2 > 0.12f);
		Out.Buttons = B;
		Out.bConnected = true;
		return true;
	}
}

#if PLATFORM_WINDOWS
#include "Windows/AllowWindowsPlatformTypes.h"
THIRD_PARTY_INCLUDES_START
#include <setupapi.h>
#include <hidsdi.h>
THIRD_PARTY_INCLUDES_END
#include "Windows/HideWindowsPlatformTypes.h"

/** Background reader: finds the controller, keeps the newest parsed state, reconnects on unplug. */
class FNVDualSenseReader : public FRunnable
{
public:
	virtual uint32 Run() override
	{
		HANDLE Event = CreateEventW(nullptr, 1, 0, nullptr);
		while (!bStop)
		{
			if (Device == INVALID_HANDLE_VALUE)
			{
				if (!TryOpen())
				{
					FPlatformProcess::Sleep(1.0f);
					continue;
				}
			}
			OVERLAPPED Ov = {};
			Ov.hEvent = Event;
			ResetEvent(Event);
			DWORD Read = 0;
			if (!ReadFile(Device, Buffer.GetData(), Buffer.Num(), nullptr, &Ov) && GetLastError() != ERROR_IO_PENDING)
			{
				CloseDevice(TEXT("read failed"));
				continue;
			}
			if (WaitForSingleObject(Event, 100) == WAIT_TIMEOUT)
			{
				CancelIo(Device);
				GetOverlappedResult(Device, &Ov, &Read, 1);
				continue;
			}
			if (!GetOverlappedResult(Device, &Ov, &Read, 0))
			{
				CloseDevice(TEXT("disconnected"));
				continue;
			}
			NVDS::FState S;
			uint32 Prev;
			{
				FScopeLock L(&Lock);
				Prev = Shared.Buttons;
			}
			if (NVDS::Parse(Buffer.GetData(), int32(Read), bBluetooth, Prev, S))
			{
				FScopeLock L(&Lock);
				Shared = S;
			}
		}
		CloseHandle(Event);
		if (Device != INVALID_HANDLE_VALUE)
		{
			CloseDevice(TEXT("shutdown"));
		}
		return 0;
	}

	virtual void Stop() override { bStop = true; }

	NVDS::FState GetState()
	{
		FScopeLock L(&Lock);
		return Shared;
	}

private:
	bool TryOpen()
	{
		GUID HidGuid;
		HidD_GetHidGuid(&HidGuid);
		HDEVINFO Info = SetupDiGetClassDevsW(&HidGuid, nullptr, nullptr, DIGCF_PRESENT | DIGCF_DEVICEINTERFACE);
		if (Info == INVALID_HANDLE_VALUE)
		{
			return false;
		}
		bool bFound = false;
		SP_DEVICE_INTERFACE_DATA IfData = {};
		IfData.cbSize = sizeof(IfData);
		for (DWORD i = 0; !bFound && SetupDiEnumDeviceInterfaces(Info, nullptr, &HidGuid, i, &IfData); ++i)
		{
			DWORD Need = 0;
			SetupDiGetDeviceInterfaceDetailW(Info, &IfData, nullptr, 0, &Need, nullptr);
			if (Need == 0)
			{
				continue;
			}
			TArray<uint8> DetailBuf;
			DetailBuf.SetNumZeroed(Need);
			SP_DEVICE_INTERFACE_DETAIL_DATA_W* Detail = reinterpret_cast<SP_DEVICE_INTERFACE_DETAIL_DATA_W*>(DetailBuf.GetData());
			Detail->cbSize = sizeof(SP_DEVICE_INTERFACE_DETAIL_DATA_W);
			if (!SetupDiGetDeviceInterfaceDetailW(Info, &IfData, Detail, Need, nullptr, nullptr))
			{
				continue;
			}
			HANDLE H = CreateFileW(Detail->DevicePath, GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE,
				nullptr, OPEN_EXISTING, FILE_FLAG_OVERLAPPED, nullptr);
			if (H == INVALID_HANDLE_VALUE)
			{
				H = CreateFileW(Detail->DevicePath, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE,
					nullptr, OPEN_EXISTING, FILE_FLAG_OVERLAPPED, nullptr);
			}
			if (H == INVALID_HANDLE_VALUE)
			{
				continue;
			}
			HIDD_ATTRIBUTES Attr = {};
			Attr.Size = sizeof(Attr);
			const bool bSony = HidD_GetAttributes(H, &Attr) && Attr.VendorID == 0x054C &&
				(Attr.ProductID == 0x0CE6 || Attr.ProductID == 0x0DF2);
			HIDP_CAPS Caps = {};
			if (bSony)
			{
				PHIDP_PREPARSED_DATA PD = nullptr;
				if (HidD_GetPreparsedData(H, &PD))
				{
					HidP_GetCaps(PD, &Caps);
					HidD_FreePreparsedData(PD);
				}
			}
			if (bSony && Caps.UsagePage == 0x01 && Caps.Usage == 0x05 && Caps.InputReportByteLength > 0)
			{
				Device = H;
				bBluetooth = Caps.InputReportByteLength > 64;
				Buffer.SetNumZeroed(Caps.InputReportByteLength);
				if (bBluetooth && Caps.FeatureReportByteLength > 0)
				{
					// Reading the calibration feature report switches BT to the extended 0x31 report.
					TArray<uint8> Feature;
					Feature.SetNumZeroed(Caps.FeatureReportByteLength);
					Feature[0] = 0x05;
					HidD_GetFeature(H, Feature.GetData(), Feature.Num());
				}
				UE_LOG(LogNVDualSense, Log, TEXT("DualSense%s connected over %s (PID 0x%04X, report %d bytes)"),
					Attr.ProductID == 0x0DF2 ? TEXT(" Edge") : TEXT(""), bBluetooth ? TEXT("Bluetooth") : TEXT("USB"),
					Attr.ProductID, int32(Caps.InputReportByteLength));
				bFound = true;
			}
			else
			{
				CloseHandle(H);
			}
		}
		SetupDiDestroyDeviceInfoList(Info);
		return bFound;
	}

	void CloseDevice(const TCHAR* Why)
	{
		CloseHandle(Device);
		Device = INVALID_HANDLE_VALUE;
		{
			FScopeLock L(&Lock);
			Shared = NVDS::FState();
		}
		UE_LOG(LogNVDualSense, Log, TEXT("DualSense closed (%s)"), Why);
	}

	TAtomic<bool> bStop { false };
	HANDLE Device = INVALID_HANDLE_VALUE;
	bool bBluetooth = false;
	TArray<uint8> Buffer;
	FCriticalSection Lock;
	NVDS::FState Shared;
};

class FNVDualSenseDevice : public IInputDevice
{
public:
	explicit FNVDualSenseDevice(const TSharedRef<FGenericApplicationMessageHandler>& InHandler)
		: Handler(InHandler)
	{
		Reader = new FNVDualSenseReader();
		Thread = FRunnableThread::Create(Reader, TEXT("NVDualSenseReader"), 0, TPri_AboveNormal);
		UE_LOG(LogNVDualSense, Log, TEXT("NV DualSense input device created"));
	}

	virtual ~FNVDualSenseDevice() override
	{
		if (Thread)
		{
			Reader->Stop();
			Thread->WaitForCompletion();
			delete Thread;
		}
		delete Reader;
	}

	virtual void Tick(float DeltaTime) override {}

	virtual void SendControllerEvents() override
	{
		NVDS::FState S = Reader->GetState();
		FPlatformUserId User = PLATFORMUSERID_NONE;
		FInputDeviceId Dev = INPUTDEVICEID_NONE;
		IPlatformInputDeviceMapper::Get().RemapControllerIdToPlatformUserAndDevice(0, User, Dev);
		const TArray<FGamepadKeyNames::Type>& K = NVDS::Keys();

		if (!S.bConnected)
		{
			if (Prev.bConnected)
			{
				for (int32 i = 0; i < NVDS::Num; ++i)
				{
					if (Prev.Buttons & (1u << i))
					{
						Handler->OnControllerButtonReleased(K[i], User, Dev, false);
					}
				}
				SendAnalog(NVDS::FState(), User, Dev);
			}
			Prev = NVDS::FState();
			return;
		}

		const float DZ = FMath::Clamp(CVarNVDualSenseDeadZone.GetValueOnGameThread(), 0.f, 0.5f);
		NVDS::ApplyRadialDeadZone(S.LX, S.LY, DZ);
		NVDS::ApplyRadialDeadZone(S.RX, S.RY, DZ);
		SendAnalog(S, User, Dev);

		const bool bLog = CVarNVDualSenseLogInput.GetValueOnGameThread() != 0;
		for (int32 i = 0; i < NVDS::Num; ++i)
		{
			const bool bNow = S.Buttons & (1u << i);
			const bool bWas = Prev.Buttons & (1u << i);
			if (bNow && !bWas)
			{
				Handler->OnControllerButtonPressed(K[i], User, Dev, false);
				if (bLog)
				{
					UE_LOG(LogNVDualSense, Log, TEXT("DualSense press %s"), NVDS::Names[i]);
				}
			}
			else if (!bNow && bWas)
			{
				Handler->OnControllerButtonReleased(K[i], User, Dev, false);
			}
		}
		Prev = S;
	}

	virtual void SetMessageHandler(const TSharedRef<FGenericApplicationMessageHandler>& InHandler) override { Handler = InHandler; }
	virtual bool Exec(UWorld* InWorld, const TCHAR* Cmd, FOutputDevice& Ar) override { return false; }
	virtual void SetChannelValue(int32 ControllerId, FForceFeedbackChannelType ChannelType, float Value) override {}
	virtual void SetChannelValues(int32 ControllerId, const FForceFeedbackValues& Values) override {}
	virtual bool SupportsForceFeedback(int32 ControllerId) override { return false; }
	virtual bool IsGamepadAttached() const override { return Prev.bConnected; }

private:
	void SendAnalog(const NVDS::FState& S, FPlatformUserId User, FInputDeviceId Dev)
	{
		Handler->OnControllerAnalog(FGamepadKeyNames::LeftAnalogX, User, Dev, S.LX);
		Handler->OnControllerAnalog(FGamepadKeyNames::LeftAnalogY, User, Dev, S.LY);
		Handler->OnControllerAnalog(FGamepadKeyNames::RightAnalogX, User, Dev, S.RX);
		Handler->OnControllerAnalog(FGamepadKeyNames::RightAnalogY, User, Dev, S.RY);
		Handler->OnControllerAnalog(FGamepadKeyNames::LeftTriggerAnalog, User, Dev, S.L2);
		Handler->OnControllerAnalog(FGamepadKeyNames::RightTriggerAnalog, User, Dev, S.R2);
	}

	TSharedRef<FGenericApplicationMessageHandler> Handler;
	FNVDualSenseReader* Reader = nullptr;
	FRunnableThread* Thread = nullptr;
	NVDS::FState Prev;
};
#endif // PLATFORM_WINDOWS

class FNVDualSenseModule : public IInputDeviceModule
{
public:
	virtual TSharedPtr<IInputDevice> CreateInputDevice(const TSharedRef<FGenericApplicationMessageHandler>& InMessageHandler) override
	{
#if PLATFORM_WINDOWS
		return MakeShared<FNVDualSenseDevice>(InMessageHandler);
#else
		return nullptr;
#endif
	}
};

IMPLEMENT_MODULE(FNVDualSenseModule, NVDualSense)
