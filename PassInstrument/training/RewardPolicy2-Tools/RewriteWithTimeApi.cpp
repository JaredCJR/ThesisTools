//------------------------------------------------------------------------------
// Author: Chang, Jia-Rung (jaredcjr.tw@gmail.com)
// Based on Eli's example. (eliben@gmail.com)
// https://github.com/eliben/llvm-clang-samples
//
// This code is for inserting timing APIs for each function.
// We do not handle "C++ operator" overloading
//------------------------------------------------------------------------------
#include <sstream>
#include <string>
#include <iostream>

#include "clang/AST/AST.h"
#include "clang/AST/ASTConsumer.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Frontend/ASTConsumers.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Frontend/FrontendActions.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "clang/Tooling/CommonOptionsParser.h"
#include "clang/Tooling/Tooling.h"
#include "llvm/Support/raw_ostream.h"
#include "clang/ARCMigrate/ARCMT.h"
#include "Transforms.h"
#include "clang/Index/CodegenNameGenerator.h"

using namespace clang;
using namespace clang::driver;
using namespace clang::tooling;

#define FunctionEntryApi "\nunsigned long long __thesis_entry = __thesis_getUserTime();\n"
#define ReturnEntryApi_1    "__thesis_LogTiming(__thesis_entry, \""
#define ReturnEntryApi_2    "\");\n"

static llvm::cl::OptionCategory ToolingCategory("Tooling For Timing Measurement");

namespace {
  std::string ReturnEntry = std::string("{//return entry\n") + ReturnEntryApi_1;

  std::string getMangledFuncName(CompilerInstance &CI, FunctionDecl *f) {
    clang::index::CodegenNameGenerator CGNameGen(CI.getASTContext());
    return CGNameGen.getName(f);
  }

  void recursiveStmtVisitor(FunctionDecl *f, Stmt *stmt, Rewriter &TheRewriter,
      CompilerInstance &CI) {
    if (stmt) {
      if (isa<ReturnStmt>(stmt)) {
        TheRewriter.InsertText(stmt->getLocStart(),
            ReturnEntry + getMangledFuncName(CI, f) + ReturnEntryApi_2, true, true);
        SourceLocation semiPos =
          clang::arcmt::trans::findSemiAfterLocation(stmt->getLocEnd(),
              CI.getASTContext(), false);
        TheRewriter.InsertTextAfterToken(semiPos, "}//return exit\n");
      }
      for (auto iter:stmt->children()) {
        recursiveStmtVisitor(f, iter, TheRewriter, CI);
      }
    }
  }
}


// By implementing RecursiveASTVisitor, we can specify which AST nodes
// we're interested in by overriding relevant methods.
class MyASTVisitor : public RecursiveASTVisitor<MyASTVisitor> {
public:
  MyASTVisitor(Rewriter &R, CompilerInstance &CI) : TheRewriter(R), TheCompiler(CI) {}

  bool VisitFunctionDecl(FunctionDecl *f) {
    // Only function definitions (with bodies), not declarations.
    if (f->hasBody()) {
      Stmt *FuncBody = f->getBody();
      // Insert api in the begining of function
      TheRewriter.InsertText(FuncBody->getLocStart().getLocWithOffset(1),
          FunctionEntryApi, true, true);
      // Recursive inserting for "return"
      for (auto iter:FuncBody->children()) {
        recursiveStmtVisitor(f, iter, TheRewriter, TheCompiler);
      }
      // If the function return "void", insert before last brackets
      if (f->getReturnType().getAsString() == "void") {
        std::string api = std::string(ReturnEntryApi_1) +
          getMangledFuncName(TheCompiler, f) + std::string(ReturnEntryApi_2) +
          std::string("//Function End\n");
        TheRewriter.InsertText(FuncBody->getLocEnd(), api, false, true);
      }
    }

    return true;
  }

private:
  Rewriter &TheRewriter;
  CompilerInstance &TheCompiler;
};

// Implementation of the ASTConsumer interface for reading an AST produced
// by the Clang parser.
class MyASTConsumer : public ASTConsumer {
public:
  MyASTConsumer(Rewriter &R, CompilerInstance &CI) : Visitor(R, CI) {}

  // Override the method that gets called for each parsed top-level
  // declaration.
  bool HandleTopLevelDecl(DeclGroupRef DR) override {
    for (DeclGroupRef::iterator b = DR.begin(), e = DR.end(); b != e; ++b) {
      // Traverse the declaration using our AST visitor.
      Visitor.TraverseDecl(*b);
      //(*b)->dump(); // This will dump the AST tree
    }
    return true;
  }

private:
  MyASTVisitor Visitor;
};

// For each source file provided to the tool, a new FrontendAction is created.
class MyFrontendAction : public ASTFrontendAction {
public:
  MyFrontendAction() {}
  void EndSourceFileAction() override {
    //SourceManager &SM = TheRewriter.getSourceMgr();
    //llvm::errs() << "** EndSourceFileAction for: " << SM.getFileEntryForID(SM.getMainFileID())->getName() << "\n";
    // Now emit the rewritten buffer.
    //TheRewriter.getEditBuffer(SM.getMainFileID()).write(llvm::outs());
    SourceManager & sm = TheRewriter.getSourceMgr();
    FileID fileID = sm.getMainFileID();
    std::string path = sm.getFilename(sm.getLocForStartOfFile(fileID)).str();
    std::error_code ec;
    llvm::raw_fd_ostream *stream = new llvm::raw_fd_ostream(path, ec, llvm::sys::fs::OpenFlags::F_RW);
    // Write to original file.
    TheRewriter.getEditBuffer(fileID)
        .write(*stream);
    stream->close(); 
  }

  std::unique_ptr<ASTConsumer> CreateASTConsumer(CompilerInstance &CI,
                                                 StringRef file) override {
    //llvm::errs() << "** Creating AST consumer for: " << file << "\n";
    TheRewriter.setSourceMgr(CI.getSourceManager(), CI.getLangOpts());
    return llvm::make_unique<MyASTConsumer>(TheRewriter, CI);
  }

private:
  Rewriter TheRewriter;
};

int main(int argc, const char **argv) {
  CommonOptionsParser op(argc, argv, ToolingCategory);
  ClangTool Tool(op.getCompilations(), op.getSourcePathList());

  // ClangTool::run accepts a FrontendActionFactory, which is then used to
  // create new objects implementing the FrontendAction interface. Here we use
  // the helper newFrontendActionFactory to create a default factory that will
  // return a new MyFrontendAction object every time.
  // To further customize this, we could create our own factory class.
  return Tool.run(newFrontendActionFactory<MyFrontendAction>().get());
}
