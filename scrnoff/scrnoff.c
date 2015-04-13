#include <windows.h>

int main(int argc, char *argv[]) {
    Sleep(500);
    SendMessage(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, 2);
    LockWorkStation();
    return 0;
}
