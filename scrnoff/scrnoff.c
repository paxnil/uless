#include <windows.h>

void _start() {
    Sleep(500);
    SendMessage(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, 2);
    LockWorkStation();
    ExitProcess(0);
}
