#include <string.h>
#include <windows.h>

int WINAPI
wWinMain (HINSTANCE hInstance, HINSTANCE hPrevInstance, LPWSTR lpCmdLine, int nShowCmd) {
    if (wcsstr(GetCommandLine(), L"-lock")) {
        LockWorkStation();
    }
    Sleep(5000);
    PostMessage(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, 2);
    ExitProcess(0);
}
