/*
 * Hashmap Benchmark for Thoth Secure Metadata System
 * Simulates hash table operations with 8B metadata writes
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#define HASH_SIZE 10000
#define NUM_OPERATIONS 100000
#define METADATA_SIZE 8  // 8B partial writes

typedef struct {
    uint64_t key;
    uint64_t value;
    uint64_t metadata;  // 8B security metadata (MAC/counter)
} HashEntry;

HashEntry *hash_table[HASH_SIZE];

uint64_t hash_function(uint64_t key) {
    return key % HASH_SIZE;
}

void insert(uint64_t key, uint64_t value) {
    uint64_t index = hash_function(key);
    HashEntry *entry = malloc(sizeof(HashEntry));
    entry->key = key;
    entry->value = value;
    entry->metadata = (key ^ value) & 0xFFFFFFFFFFFFFFFF;  // Simulate MAC
    
    // Write metadata (8B partial write)
    volatile uint64_t *metadata_ptr = &(entry->metadata);
    *metadata_ptr = entry->metadata;
    
    hash_table[index] = entry;
}

uint64_t lookup(uint64_t key) {
    uint64_t index = hash_function(key);
    HashEntry *entry = hash_table[index];
    if (entry && entry->key == key) {
        // Read and verify metadata
        volatile uint64_t metadata = entry->metadata;
        return entry->value;
    }
    return 0;
}

void update(uint64_t key, uint64_t new_value) {
    uint64_t index = hash_function(key);
    HashEntry *entry = hash_table[index];
    if (entry && entry->key == key) {
        entry->value = new_value;
        // Update metadata (8B partial write)
        volatile uint64_t *metadata_ptr = &(entry->metadata);
        *metadata_ptr = (key ^ new_value) & 0xFFFFFFFFFFFFFFFF;
    }
}

int main() {
    printf("Starting Hashmap Benchmark...\n");
    
    memset(hash_table, 0, sizeof(hash_table));
    
    // Insert phase
    for (int i = 0; i < NUM_OPERATIONS / 2; i++) {
        insert(i, i * 100);
    }
    
    // Update phase (generates 8B metadata writes)
    for (int i = 0; i < NUM_OPERATIONS / 4; i++) {
        update(i, i * 200);
    }
    
    // Lookup phase
    uint64_t sum = 0;
    for (int i = 0; i < NUM_OPERATIONS / 4; i++) {
        sum += lookup(i);
    }
    
    printf("Hashmap Benchmark Complete. Checksum: %lu\n", sum);
    return 0;
}
