/*
 * Chapter 2 Lab: Quicksort Performance Analysis
 * quicksort.c - starter quicksort implementation
 */

#include <stdio.h>

static void swap(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

/*
 * Partition the subarray arr[low..high] around a pivot chosen from the
 * current range.
 */
static int partition(int *arr, int low, int high) {
    int pivot = arr[low];
    int i = low + 1;
    int j = high;

    while (1) {
        while (i <= high && arr[i] < pivot) {
            i++;
        }

        while (j >= low + 1 && arr[j] > pivot) {
            j--;
        }

        if (i >= j) {
            break;
        }

        swap(&arr[i], &arr[j]);
        i++;
        j--;
    }

    swap(&arr[low], &arr[j]);
    return j;
}

void quicksort(int *arr, int low, int high) {
    if (low < high) {
        int pivot_idx = partition(arr, low, high);
        quicksort(arr, low, pivot_idx - 1);
        quicksort(arr, pivot_idx + 1, high);
    }
}
