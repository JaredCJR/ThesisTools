#ifndef __THESIS_API_H
#define __THESIS_API_H

unsigned long long __thesis_getUserTime();
void __thesis_LogTiming(unsigned long long entryTime, const char *FuncName);

#endif
