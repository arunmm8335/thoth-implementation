/*
 * Random Array Swap Benchmark for Thoth Secure Metadata System
 * Exchanges two arrays allocated contiguously with metadata updates
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

#define ARRAY_SIZE 50000
#define NUM_SWAPS 25000
#define METADATA_SIZE 8

typedef struct {
    uint64_t data;
    uint64_t metadata;  // 8B security metadata
} Element;

Element *array_a;
Element *array_b;

void write_metadata(volatile uint64_t *metadata_ptr, uint64_t value) {
    *metadata_ptr = value;
}

void swap_elements(int idx_a, int idx_b) {
    // Swap data
    uint64_t temp_data = array_a[idx_a].data;
    array_a[idx_a].data = array_b[idx_b].data;
    array_b[idx_b].data = temp_data;
    
    // Update metadata for both elements (two 8B partial writes)
    write_metadata(&array_a[idx_a].metadata, array_a[idx_a].data ^ 0xABCDEF01);
    write_metadata(&array_b[idx_b].metadata, array_b[idx_b].data ^ 0xABCDEF01);
}

int main() {
    printf("Starting Random Array Swap Benchmark...\n");
    
    // Allocate arrays contiguously
    void *memory = malloc(2 * ARRAY_SIZE * sizeof(Element));
    array_a = (Element *)memory;
    array_b = (Element *)((char *)memory + ARRAY_SIZE * sizeof(Element));
    
    // Initialize arrays
    for (int i = 0; i < ARRAY_SIZE; i++) {
        array_a[i].data = i;
        array_b[i].data = ARRAY_SIZE + i;
        write_metadata(&array_a[i].metadata, array_a[i].data ^ 0xABCDEF01);
        write_metadata(&array_b[i].metadata, array_b[i].data ^ 0xABCDEF01);
    }
    
    // Random swap phase
    for (int i = 0; i < NUM_SWAPS; i++) {
        int idx_a = rand() % ARRAY_SIZE;
        int idx_b = rand() % ARRAY_SIZE;
        swap_elements(idx_a, idx_b);
    }
    
    // Verify phase (read metadata)
    uint64_t checksum = 0;
    for (int i = 0; i < ARRAY_SIZE; i++) {
        volatile uint64_t meta_a = array_a[i].metadata;
        volatile uint64_t meta_b = array_b[i].metadata;
        checksum += meta_a + meta_b;
    }
    
    printf("Swap Benchmark Complete. Checksum: %lu\n", checksum);
    free(memory);
    return 0;
}
