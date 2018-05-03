#ifndef __THESIS_API_H

extern "C" unsigned long long __thesis_getUserTime();
extern "C" void __thesis_LogTiming(unsigned long long entryTime, char *FuncName);

#endif
