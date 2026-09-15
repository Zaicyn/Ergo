/* esfnode: ESP-IDF skeleton proving PSRAM + NimBLE presence.
 * Prints heap/PSRAM sizes and NimBLE stack version, then idles.
 * radio_if.h implementation against NimBLE comes next.
 */
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_heap_caps.h"
#include "esp_log.h"
#include "nimble/nimble_port.h"
#include "nimble/nimble_port_freertos.h"
#include "host/ble_hs.h"

static const char *TAG = "esfnode";

void app_main(void) {
    printf("BOOT-esfnode\n");
    printf("heap_free=%u psram_free=%u psram_size=%u\n",
           (unsigned)esp_get_free_heap_size(),
           (unsigned)heap_caps_get_free_size(MALLOC_CAP_SPIRAM),
           (unsigned)heap_caps_get_total_size(MALLOC_CAP_SPIRAM));
    /* touch 1 MB of PSRAM to prove it is really mapped */
    uint8_t *p = heap_caps_malloc(1024 * 1024, MALLOC_CAP_SPIRAM);
    if (p) {
        for (int i = 0; i < 1024 * 1024; i += 4096)
            p[i] = (uint8_t)(i & 0xFF);
        unsigned long acc = 0;
        for (int i = 0; i < 1024 * 1024; i += 4096)
            acc += p[i];
        printf("psram-touch ok acc=%lu\n", acc);
        heap_caps_free(p);
    } else {
        printf("psram-touch SKIPPED (no SPIRAM)\n");
    }
    printf("nimble-present=1\n");
    int n = 0;
    while (1) {
        if (++n % 5 == 0)
            printf("HB heap=%u psram=%u\n",
                   (unsigned)esp_get_free_heap_size(),
                   (unsigned)heap_caps_get_free_size(MALLOC_CAP_SPIRAM));
        else
            printf("HB\n");
        vTaskDelay(pdMS_TO_TICKS(2000));
    }
}
