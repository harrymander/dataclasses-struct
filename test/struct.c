#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#ifdef _MSC_VER
#define _CRT_SECURE_NO_WARNINGS
#endif

#ifndef TEST_NATIVE_INTS
// If using std sizes, then structs do not have native alignment (i.e. they are
// packed)
#define TEST_PACKED
#endif

#ifdef TEST_PACKED
#pragma pack(push, 1)
#endif // TEST_PACKED
struct test {
    // Types that work on both native and std sizes
    bool test_bool;
    float test_float;
    double test_double;
    char test_char;
    char test_char_array[10];

#ifdef TEST_NATIVE_INTS
    signed char test_signed_char;
    unsigned char test_unsigned_char;
    signed short test_signed_short;
    unsigned short test_unsigned_short;
    signed int test_signed_int;
    unsigned int test_unsigned_int;
    signed long test_signed_long;
    unsigned long test_unsigned_long;
    signed long long test_signed_long_long;
    unsigned long long test_unsigned_long_long;
    size_t test_size; // ssize_t is POSIX-only
    void *test_pointer;
#else
    uint8_t test_uint8;
    int8_t test_int8;
    uint16_t test_uint16;
    int16_t test_int16;
    uint32_t test_uint32;
    int32_t test_int32;
    uint64_t test_uint64;
    int64_t test_int64;
#endif // TEST_NATIVE_INS
};

struct container {
    struct test t1;
    struct test t2;
};
#ifdef TEST_PACKED
#pragma pack(pop)
#endif // TEST_PACKED

int main(const int argc, const char *argv[])
{
    if (argc < 2) {
        fprintf(stderr, "usage: %s [outfile]\n", argv[0]);
        return 1;
    }

    const struct test test = {
        .test_bool = true,
        .test_float = 1.5,
        .test_double = 2.5,
        .test_char = '!',
        .test_char_array = "123456789",

#ifdef TEST_NATIVE_INTS
        .test_signed_char = -10,
        .test_unsigned_char = 10,
        .test_signed_short = -500,
        .test_unsigned_short = 500,
        .test_signed_int = -5000,
        .test_unsigned_int = 5000,
        .test_signed_long = -6000,
        .test_unsigned_long = 6000,
        .test_signed_long_long = -7000,
        .test_unsigned_long_long = 7000,
        .test_size = 8000,
        .test_pointer = (void *)0,
#else
        .test_uint8 = UINT8_MAX,
        .test_int8 = INT8_MIN,
        .test_uint16 = UINT16_MAX,
        .test_int16 = INT16_MIN,
        .test_uint32 = UINT32_MAX,
        .test_int32 = INT32_MIN,
        .test_uint64 = UINT64_MAX,
        .test_int64 = INT64_MIN,
#endif // TEST_NATIVE_INTS
    };

    const struct container container = {test, test};

    FILE *fp = fopen(argv[1], "wb");
    if (!fp) {
        fprintf(stderr, "cannot open file: %s\n", strerror(errno));
        return 1;
    }

    int ret = fwrite(&container, sizeof(container), 1, fp) != 1;
    if (ret) {
        fprintf(stderr, "write error\n");
    }
    fclose(fp);
    return ret != 0;
}
