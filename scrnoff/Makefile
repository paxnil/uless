CC = i686-w64-mingw32-gcc
CFLAGS = -O3 -Wall -c -municode -mwindows
LD = i686-w64-mingw32-ld
LDFLAGS = -luser32 -lkernel32 -lmsvcrt -s --subsystem windows

all: scrnoff.exe

%.o: %.c
	$(CC) $(CFLAGS) $< -o $@

scrnoff.exe: scrnoff.o
	$(LD) $< $(LDFLAGS) -o $@

.PHONY: clean
clean:
	rm -f *.o *.exe
