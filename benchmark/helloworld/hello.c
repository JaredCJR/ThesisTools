#include <stdio.h>

void function_2() {
    printf("function 2\n");
}
void function_3() {
    for(int i = 0;i < 10;i++) {
        printf("function 3, %d\n", 1024*4+i);
        if(i > 5) {
            function_2();
        }
        if(i < 7) {
            printf("good\n");
        }
    }
}


void function_1() {
    printf("function 1\n");
}

int main() {
  printf("hello world\n");
  function_1();
  function_2();
  function_3();
  return 0;
}
