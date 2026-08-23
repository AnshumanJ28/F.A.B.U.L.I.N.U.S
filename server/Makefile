ORT_DIR := third_party/onnxruntime
CXX := g++
CXXFLAGS := -std=c++17 -O2 -Wall -Wextra -pthread -I. -I$(ORT_DIR)/include

ifeq ($(OS),Windows_NT)
    CXXFLAGS += -D_WIN32_WINNT=0x0A00 -D_stdcall=__stdcall
    LDFLAGS := -L$(ORT_DIR)/lib -lonnxruntime -lws2_32
    BIN := vsa-server.exe
else
    LDFLAGS := -L$(ORT_DIR)/lib -lonnxruntime -Wl,-rpath,'$$ORIGIN/$(ORT_DIR)/lib'
    BIN := vsa-server
endif

.PHONY: all clean run

all: $(BIN)

$(BIN): main.cpp
	$(CXX) $(CXXFLAGS) main.cpp -o $(BIN) $(LDFLAGS)

run: all
	./$(BIN)

clean:
	rm -f $(BIN)
