#include <stdio.h>

int add(int x, int y)
{
    int res;
    asm("mov %1, %%eax\n"    // %eax = x
        "mov %2, %%ecx\n"    // %ecx = y
        "add %%ecx, %%eax\n" // %eax += %ecx
        "mov %%eax, %0"      // res = %eax
        : "=r" (res)
        : "r" (x), "r" (y));
    return res;
}

int main()
{
    int a = add(1, 5);
    printf("%d\n", a);
    return 0;
}
