//------------------------------------------------------------------------------
// Author: Chang, Jia-Rung (jaredcjr.tw@gmail.com)
// Based on Eli's example. (eliben@gmail.com)
//------------------------------------------------------------------------------
#include <string>

#include "clang/AST/AST.h"
#include "clang/AST/ASTConsumer.h"
#include "clang/Basic/SourceManager.h"
#include "clang/Basic/SourceLocation.h"
#include "clang/ASTMatchers/ASTMatchFinder.h"
#include "clang/ASTMatchers/ASTMatchers.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Frontend/FrontendActions.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "clang/Tooling/CommonOptionsParser.h"
#include "clang/Tooling/Tooling.h"
#include "clang/AST/StmtCXX.h"
#include "llvm/Support/raw_ostream.h"
#include <iostream>

using namespace clang;
using namespace clang::ast_matchers;
using namespace clang::driver;
using namespace clang::tooling;
#define PassPeeper_pre  "PassPrediction::PassPeeper(__FILE__, __LINE__, "
#define PassPeeper_post ");\n"

static llvm::cl::OptionCategory MatcherSampleCategory("Pass Rewriter For Instrumentation");

namespace InsertHelpers {
  // Global var to count the index id (id != index)
  unsigned InsertIndexId = 0;
  // Insert API after the starting brace of the matched statement.
  // More specific, this api is for: for(...), while(...), etc.
  void InsertApiInCompStmt(const clang::Stmt *stmt, clang::Rewriter &Rewrite) {
    Stmt::const_child_iterator Istart = stmt->child_begin();
    Stmt::const_child_iterator Iend = stmt->child_end();
    if (Istart != Iend)
      if (*Istart){
        Rewrite.InsertTextBefore((*Istart)->getLocStart(), PassPeeper_post);
        Rewrite.InsertTextBefore((*Istart)->getLocStart(), std::to_string(InsertHelpers::InsertIndexId));
        Rewrite.InsertTextBefore((*Istart)->getLocStart(), PassPeeper_pre);
        if (Rewrite.getSourceMgr().isInMainFile((*Istart)->getLocStart())) {
          InsertIndexId++;
        }
      }
  }
  // This is for "case" and "break"
  void InsertApiInSingleStmt(const clang::SourceLocation SL, clang::Rewriter &Rewrite) {
    Rewrite.InsertTextAfter(SL, PassPeeper_pre);
    Rewrite.InsertTextAfter(SL, std::to_string(InsertHelpers::InsertIndexId));
    Rewrite.InsertTextAfter(SL, PassPeeper_post);
    if (Rewrite.getSourceMgr().isInMainFile(SL)) {
      InsertIndexId++;
    }
  }
  // Get the source file and line to record it.
  void RecordMatchedLoc(const clang::Stmt *stmt, clang::SourceManager &sm) {
    clang::SourceLocation Loc = stmt->getLocEnd();
    unsigned LineNum = sm.getSpellingLineNumber(Loc);
    StringRef FilePath = sm.getFilename(Loc);
    //FIXME: rewrite will make the line number wrong
    //llvm::errs() << "File:" << FilePath << " Line:" << LineNum << "\n";
  }
}


class IfStmtHandler : public MatchFinder::MatchCallback {
public:
  IfStmtHandler(Rewriter &Rewrite) : Rewrite(Rewrite) {}

  virtual void run(const MatchFinder::MatchResult &Result) {
    // The matched 'if' statement was bound to 'ifStmt'.
    if (const IfStmt *IfS = Result.Nodes.getNodeAs<clang::IfStmt>("ifStmt")) {
      const Stmt *Then = IfS->getThen();
      InsertHelpers::InsertApiInCompStmt(Then, Rewrite);
      //InsertHelpers::RecordMatchedLoc(Then, Rewrite.getSourceMgr());

      if (const Stmt *Else = IfS->getElse()) {
        InsertHelpers::InsertApiInCompStmt(Else, Rewrite);
      }
    }
  }

private:
  Rewriter &Rewrite;
};

class ForLoopHandler : public MatchFinder::MatchCallback {
public:
  ForLoopHandler(Rewriter &Rewrite) : Rewrite(Rewrite) {}

  virtual void run(const MatchFinder::MatchResult &Result) {
    if (const ForStmt *ForS = Result.Nodes.getNodeAs<clang::ForStmt>("forStmt")) {
      const Stmt *For = ForS->getBody();
      InsertHelpers::InsertApiInCompStmt(For, Rewrite);
    }
  }

private:
  Rewriter &Rewrite;
};

class ForRangeLoopHandler : public MatchFinder::MatchCallback {
public:
  ForRangeLoopHandler(Rewriter &Rewrite) : Rewrite(Rewrite) {}

  virtual void run(const MatchFinder::MatchResult &Result) {
    if (const CXXForRangeStmt *ForRangeS = 
        Result.Nodes.getNodeAs<clang::CXXForRangeStmt>("for-rangeStmt")) {
      const Stmt *ForRange = ForRangeS->getBody();
      InsertHelpers::InsertApiInCompStmt(ForRange, Rewrite);
    }
  }

private:
  Rewriter &Rewrite;
};

class WhileStmtHandler : public MatchFinder::MatchCallback {
public:
  WhileStmtHandler(Rewriter &Rewrite) : Rewrite(Rewrite) {}

  virtual void run(const MatchFinder::MatchResult &Result) {
    if (const WhileStmt *WhileS = Result.Nodes.getNodeAs<clang::WhileStmt>("whileStmt")) {
      const Stmt *While = WhileS->getBody();
      InsertHelpers::InsertApiInCompStmt(While, Rewrite);
    }
  }

private:
  Rewriter &Rewrite;
};

class DoWhileStmtHandler : public MatchFinder::MatchCallback {
public:
  DoWhileStmtHandler(Rewriter &Rewrite) : Rewrite(Rewrite) {}

  virtual void run(const MatchFinder::MatchResult &Result) {
    if (const DoStmt *DoWhileS = Result.Nodes.getNodeAs<clang::DoStmt>("do-whileStmt")) {
      const Stmt *DoWhile = DoWhileS->getBody();
      InsertHelpers::InsertApiInCompStmt(DoWhile, Rewrite);
    }
  }

private:
  Rewriter &Rewrite;
};

class BreakStmtHandler : public MatchFinder::MatchCallback {
public:
  BreakStmtHandler(Rewriter &Rewrite) : Rewrite(Rewrite) {}

  virtual void run(const MatchFinder::MatchResult &Result) {
    if (const BreakStmt *BreakS = 
        Result.Nodes.getNodeAs<clang::BreakStmt>("breakStmt")) {
      InsertHelpers::InsertApiInSingleStmt(BreakS->getLocStart(), Rewrite);
    }
  }

private:
  Rewriter &Rewrite;
};

class CaseStmtHandler : public MatchFinder::MatchCallback {
public:
  CaseStmtHandler(Rewriter &Rewrite) : Rewrite(Rewrite) {}

  virtual void run(const MatchFinder::MatchResult &Result) {
    if (const CaseStmt *CaseS = 
        Result.Nodes.getNodeAs<clang::CaseStmt>("caseStmt")) {
      InsertHelpers::InsertApiInSingleStmt(CaseS->getColonLoc(), Rewrite);
    }
  }

private:
  Rewriter &Rewrite;
};


// Implementation of the ASTConsumer interface for reading an AST produced
// by the Clang parser. It registers a couple of matchers and runs them on
// the AST.
class MyASTConsumer : public ASTConsumer {
public:
  MyASTConsumer(Rewriter &R) : HandlerForIf(R), HandlerForFor(R), 
                HandlerForForRange(R), HandlerForWhile(R),
                HandlerForDoWhile(R), HandlerForBreak(R),
                HandlerForCase(R) {
    // Add a simple matcher for finding 'if' statements.
    Matcher.addMatcher(ifStmt().bind("ifStmt"), &HandlerForIf);
    // Add a simple matcher for finding 'for' statements.
    Matcher.addMatcher(forStmt().bind("forStmt"), &HandlerForFor);
    // Add a simple matcher for finding 'CXX11 for-range' statements.
    Matcher.addMatcher(cxxForRangeStmt().bind("for-rangeStmt"), &HandlerForForRange);
    // Add a simple matcher for finding 'while' statements.
    Matcher.addMatcher(whileStmt().bind("whileStmt"), &HandlerForWhile);
    // Add a simple matcher for finding 'do-while' statements.
    Matcher.addMatcher(doStmt().bind("do-whileStmt"), &HandlerForDoWhile);
    // Add a simple matcher for finding 'break' statements.
    Matcher.addMatcher(breakStmt().bind("breakStmt"), &HandlerForBreak);
    // Add a simple matcher for finding 'case' statements.
    Matcher.addMatcher(caseStmt().bind("caseStmt"), &HandlerForCase);
  }


  void HandleTranslationUnit(ASTContext &Context) override {
    // Run the matchers when we have the whole TU parsed.
    Matcher.matchAST(Context);
  }

private:
  IfStmtHandler HandlerForIf;
  ForLoopHandler HandlerForFor;
  ForRangeLoopHandler HandlerForForRange;
  WhileStmtHandler HandlerForWhile;
  DoWhileStmtHandler HandlerForDoWhile;
  BreakStmtHandler HandlerForBreak;
  CaseStmtHandler HandlerForCase;
  MatchFinder Matcher;
};

// For each source file provided to the tool, a new FrontendAction is created.
class MyFrontendAction : public ASTFrontendAction {
public:
  MyFrontendAction() {}
  void EndSourceFileAction() override {
    TheRewriter.getEditBuffer(TheRewriter.getSourceMgr().getMainFileID())
        .write(llvm::outs());
  }

  std::unique_ptr<ASTConsumer> CreateASTConsumer(CompilerInstance &CI,
                                                 StringRef file) override {
    TheRewriter.setSourceMgr(CI.getSourceManager(), CI.getLangOpts());
    return llvm::make_unique<MyASTConsumer>(TheRewriter);
  }

private:
  Rewriter TheRewriter;
};

int main(int argc, const char **argv) {
  CommonOptionsParser op(argc, argv, MatcherSampleCategory);
  ClangTool Tool(op.getCompilations(), op.getSourcePathList());

  return Tool.run(newFrontendActionFactory<MyFrontendAction>().get());
}
