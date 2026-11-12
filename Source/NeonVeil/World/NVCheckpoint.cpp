#include "World/NVCheckpoint.h"

ANVCheckpoint::ANVCheckpoint(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	// Never used as an ordinary spawn: the game mode only picks these during a checkpoint load.
	PlayerStartTag = TEXT("NVCheckpoint");
}
