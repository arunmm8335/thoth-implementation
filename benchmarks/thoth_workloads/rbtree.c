/*
 * Red-Black Tree Benchmark for Thoth Secure Metadata System
 * Simulates RB-tree operations with 8B metadata writes
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#define NUM_OPERATIONS 50000
#define RED 0
#define BLACK 1

typedef struct RBNode {
    uint64_t key;
    uint64_t metadata;  // 8B security metadata
    int color;
    struct RBNode *left;
    struct RBNode *right;
    struct RBNode *parent;
} RBNode;

RBNode *root = NULL;
RBNode *NIL;

void write_metadata(volatile uint64_t *metadata_ptr, uint64_t value) {
    *metadata_ptr = value;
}

RBNode *create_node(uint64_t key) {
    RBNode *node = malloc(sizeof(RBNode));
    node->key = key;
    node->color = RED;
    node->left = NIL;
    node->right = NIL;
    node->parent = NIL;
    // Write 8B metadata
    write_metadata(&node->metadata, key ^ 0xCAFEBABE);
    return node;
}

void left_rotate(RBNode **root, RBNode *x) {
    RBNode *y = x->right;
    x->right = y->left;
    if (y->left != NIL) y->left->parent = x;
    y->parent = x->parent;
    if (x->parent == NIL) *root = y;
    else if (x == x->parent->left) x->parent->left = y;
    else x->parent->right = y;
    y->left = x;
    x->parent = y;
}

void right_rotate(RBNode **root, RBNode *y) {
    RBNode *x = y->left;
    y->left = x->right;
    if (x->right != NIL) x->right->parent = y;
    x->parent = y->parent;
    if (y->parent == NIL) *root = x;
    else if (y == y->parent->right) y->parent->right = x;
    else y->parent->left = x;
    x->right = y;
    y->parent = x;
}

void insert_fixup(RBNode **root, RBNode *z) {
    while (z->parent->color == RED) {
        if (z->parent == z->parent->parent->left) {
            RBNode *y = z->parent->parent->right;
            if (y->color == RED) {
                z->parent->color = BLACK;
                y->color = BLACK;
                z->parent->parent->color = RED;
                z = z->parent->parent;
            } else {
                if (z == z->parent->right) {
                    z = z->parent;
                    left_rotate(root, z);
                }
                z->parent->color = BLACK;
                z->parent->parent->color = RED;
                right_rotate(root, z->parent->parent);
            }
        } else {
            RBNode *y = z->parent->parent->left;
            if (y->color == RED) {
                z->parent->color = BLACK;
                y->color = BLACK;
                z->parent->parent->color = RED;
                z = z->parent->parent;
            } else {
                if (z == z->parent->left) {
                    z = z->parent;
                    right_rotate(root, z);
                }
                z->parent->color = BLACK;
                z->parent->parent->color = RED;
                left_rotate(root, z->parent->parent);
            }
        }
    }
    (*root)->color = BLACK;
}

void insert(uint64_t key) {
    RBNode *z = create_node(key);
    RBNode *y = NIL;
    RBNode *x = root;
    
    while (x != NIL) {
        y = x;
        if (z->key < x->key) x = x->left;
        else x = x->right;
    }
    
    z->parent = y;
    if (y == NIL) root = z;
    else if (z->key < y->key) y->left = z;
    else y->right = z;
    
    if (z->parent == NIL) {
        z->color = BLACK;
        return;
    }
    
    if (z->parent->parent == NIL) return;
    
    insert_fixup(&root, z);
}

int search(RBNode *node, uint64_t key) {
    if (node == NIL) return 0;
    if (key == node->key) {
        volatile uint64_t metadata = node->metadata;
        return 1;
    }
    if (key < node->key) return search(node->left, key);
    return search(node->right, key);
}

int main() {
    printf("Starting Red-Black Tree Benchmark...\n");
    
    NIL = malloc(sizeof(RBNode));
    NIL->color = BLACK;
    NIL->left = NIL->right = NIL->parent = NIL;
    root = NIL;
    
    // Insert phase
    for (int i = 0; i < NUM_OPERATIONS; i++) {
        insert(i);
    }
    
    // Search phase
    int found = 0;
    for (int i = 0; i < NUM_OPERATIONS / 2; i++) {
        if (search(root, i)) found++;
    }
    
    printf("RB-Tree Benchmark Complete. Found: %d/%d\n", found, NUM_OPERATIONS / 2);
    return 0;
}
