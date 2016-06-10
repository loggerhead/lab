#include <stdio.h>

// GCC Assembler Syntax: https://www.ibiblio.org/gferg/ldp/GCC-Inline-Assembly-HOWTO.html#s3
int add(int x, int y)
{
    int res;
    /*
     * +---+--------------------+
     * | r |    Register(s)     |
     * +---+--------------------+
     * | a |   %eax, %ax, %al   |
     * | b |   %ebx, %bx, %bl   |
     * | c |   %ecx, %cx, %cl   |
     * | d |   %edx, %dx, %dl   |
     * | S |   %esi, %si        |
     * | D |   %edi, %di        |
     * +---+--------------------+
     */
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
