CXX := gcc
CFLAGS_OBJ := -Wall -fPIC -c
CFLAGS_LIB := -shared -Wl,-soname,

OBJ := libfunctime
SRC := $(OBJ).c

.PHONY: all clean
all: BuildSharedLib

BuildSharedLib: $(SRC)
	$(CXX) $(CFLAGS_OBJ) $^
	$(CXX) $(CFLAGS_LIB)$(OBJ).so.1 -o $(OBJ).so.1.0 $(OBJ).o

clean:
	rm -f *.o *.so
