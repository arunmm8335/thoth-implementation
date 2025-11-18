/*
 * B-Tree Benchmark for Thoth Secure Metadata System
 * Simulates B-tree operations with 8B metadata writes
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

#define ORDER 5
#define NUM_OPERATIONS 50000
#define METADATA_SIZE 8

typedef struct BTreeNode {
    uint64_t keys[ORDER - 1];
    uint64_t metadata[ORDER - 1];  // 8B metadata per key
    struct BTreeNode *children[ORDER];
    int num_keys;
    int is_leaf;
} BTreeNode;

BTreeNode *root = NULL;

BTreeNode *create_node(int is_leaf) {
    BTreeNode *node = malloc(sizeof(BTreeNode));
    node->num_keys = 0;
    node->is_leaf = is_leaf;
    memset(node->children, 0, sizeof(node->children));
    memset(node->metadata, 0, sizeof(node->metadata));
    return node;
}

void write_metadata(volatile uint64_t *metadata_ptr, uint64_t value) {
    // Simulate 8B partial write to metadata
    *metadata_ptr = value;
}

void insert_non_full(BTreeNode *node, uint64_t key) {
    int i = node->num_keys - 1;
    
    if (node->is_leaf) {
        while (i >= 0 && key < node->keys[i]) {
            node->keys[i + 1] = node->keys[i];
            node->metadata[i + 1] = node->metadata[i];
            i--;
        }
        node->keys[i + 1] = key;
        // Write 8B metadata
        write_metadata(&node->metadata[i + 1], key ^ 0xDEADBEEF);
        node->num_keys++;
    }
}

void insert(uint64_t key) {
    if (root == NULL) {
        root = create_node(1);
        root->keys[0] = key;
        write_metadata(&root->metadata[0], key ^ 0xDEADBEEF);
        root->num_keys = 1;
    } else {
        if (root->num_keys < ORDER - 1) {
            insert_non_full(root, key);
        }
    }
}

int search(BTreeNode *node, uint64_t key) {
    if (node == NULL) return 0;
    
    int i = 0;
    while (i < node->num_keys && key > node->keys[i]) {
        i++;
    }
    
    if (i < node->num_keys && key == node->keys[i]) {
        // Verify metadata
        volatile uint64_t metadata = node->metadata[i];
        return 1;
    }
    
    if (node->is_leaf) return 0;
    return search(node->children[i], key);
}

int main() {
    printf("Starting B-Tree Benchmark...\n");
    
    // Insert phase
    for (int i = 0; i < NUM_OPERATIONS; i++) {
        insert(i);
    }
    
    // Search phase
    int found = 0;
    for (int i = 0; i < NUM_OPERATIONS / 2; i++) {
        if (search(root, i)) found++;
    }
    
    printf("B-Tree Benchmark Complete. Found: %d/%d\n", found, NUM_OPERATIONS / 2);
    return 0;
}
