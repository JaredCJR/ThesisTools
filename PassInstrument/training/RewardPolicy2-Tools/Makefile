CXX := g++-7
CXXFLAGS := -fno-rtti -O0

# User specific variable
# The LLVM 5.0 build must using the following Cmake cmd
# $ cmake -DCMAKE_BUILD_TYPE=Release \
#         -DLLVM_ENABLE_ASSERTIONS=ON \
#         -DCMAKE_C_FLAGS=-DLLVM_ENABLE_DUMP \
#         -DCMAKE_CXX_FLAGS=-DLLVM_ENABLE_DUMP \
#         -DLLVM_TARGETS_TO_BUILD="X86" \
#         -G "Unix Makefiles"
LLVM_SRC_PATH := $$HOME/workspace/llvm-official
LLVM_BUILD_PATH := $(LLVM_SRC_PATH)/build-release-dump-gcc7
LLVM_BIN_PATH   := $(LLVM_BUILD_PATH)/bin


LLVM_CXXFLAGS := `$(LLVM_BIN_PATH)/llvm-config --cxxflags`
LLVM_LDFLAGS := `$(LLVM_BIN_PATH)/llvm-config --ldflags --libs --system-libs`
CLANG_INCLUDES := \
    -I$(LLVM_SRC_PATH)/tools/clang/include \
    -I$(LLVM_BUILD_PATH)/tools/clang/include \
    -I$(LLVM_SRC_PATH)/tools/clang/lib/ARCMigrate

# List of Clang libraries to link. The proper -L will be provided by the
# call to llvm-config
# Note that I'm using -Wl,--{start|end}-group around the Clang libs; this is
# because there are circular dependencies that make the correct order difficult
# to specify and maintain. The linker group options make the linking somewhat
# slower, but IMHO they're still perfectly fine for tools that link with Clang.
CLANG_LIBS := \
    -Wl,--start-group \
    -lclangAST \
    -lclangASTMatchers \
    -lclangAnalysis \
    -lclangBasic \
    -lclangDriver \
    -lclangEdit \
    -lclangFrontend \
    -lclangFrontendTool \
    -lclangLex \
    -lclangParse \
    -lclangSema \
    -lclangEdit \
    -lclangRewrite \
    -lclangRewriteFrontend \
    -lclangStaticAnalyzerFrontend \
    -lclangStaticAnalyzerCheckers \
    -lclangStaticAnalyzerCore \
    -lclangSerialization \
    -lclangToolingCore \
    -lclangTooling \
    -lclangFormat \
    -lclangARCMigrate \
		-lclangIndex \
    -Wl,--end-group


SRC := RewriteWithTimeApi.cpp

.PHONY: all clean
all: RewriteWithTimeApi

RewriteWithTimeApi: $(SRC)
	$(CXX) $(CXXFLAGS) $(LLVM_CXXFLAGS) $(CLANG_INCLUDES) $^ \
        $(CLANG_LIBS) $(LLVM_LDFLAGS) -o $@

rewrite-sample: PassRewriter
	# copy the original file to prepare for rewrite
	cp ~/workspace/llvm-thesis/lib/Transforms/Scalar/DCE.cpp ./
	# Make sure all braces are located properly
	clang-tidy -fix -config="{Checks: 'readability-braces-around-statements'}" \
  		./DCE.cpp \
  		-- -I/home/jrchang/workspace/llvm-thesis/include/llvm \
  		-std=c++11
	# clang-tidy will make the code looks dirty, format it!
	clang-format -style=LLVM DCE.cpp > DCE-tidy-format.cpp
	# Instrument the fully-braced file
	./PassRewriter DCE-tidy-format.cpp  -- -std=c++11 -I/usr/lib/gcc/x86_64-linux-gnu/7/include -I/usr/local/include -I/usr/lib/gcc/x86_64-linux-gnu/7/include-fixed -I/usr/include/x86_64-linux-gnu -I/usr/include -I/home/jrchang/workspace/llvm-thesis/include/llvm > DCE-rewritten.cpp

clean:
	rm -f RewriteWithTimeApi
