/* esfnode: ESP-IDF node — PSRAM proof + NimBLE CoC bearer.
 * radio_if.h implementation against NimBLE comes next; this file
 * proves the radio path first (advertise -> CoC accept -> count).
 */
#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_nimble_hci.h"
#include "esp_nimble_hci.h"
#include "nimble/nimble_port.h"
#include "nimble/nimble_port_freertos.h"
#include "host/ble_hs.h"
#include "host/ble_gap.h"
#include "host/ble_l2cap.h"
#include "host/util/util.h"
#include "services/gap/ble_svc_gap.h"
#include "os/os_mbuf.h"

#define COC_PSM 0x81
#define COC_MTU 512

static volatile unsigned long rx_bytes, rx_sdus;
static volatile uint64_t rx_fnv = 0xcbf29ce484222325ULL;
static uint16_t conn_h = BLE_HS_CONN_HANDLE_NONE;

static void start_adv(void) {
    struct ble_hs_adv_fields f;
    memset(&f, 0, sizeof f);
    f.flags = BLE_HS_ADV_F_DISC_GEN | BLE_HS_ADV_F_BREDR_UNSUP;
    f.name = (uint8_t *)"ESFOC";
    f.name_len = 5;
    f.name_is_complete = 1;
    int rc = ble_gap_adv_set_fields(&f);
    printf("ADV fields rc=%d\n", rc);
    struct ble_gap_adv_params p;
    memset(&p, 0, sizeof p);
    p.conn_mode = BLE_GAP_CONN_MODE_UND;
    p.disc_mode = BLE_GAP_DISC_MODE_GEN;
    rc = ble_gap_adv_start(BLE_OWN_ADDR_PUBLIC, NULL, BLE_HS_FOREVER,
                           &p, NULL, NULL);
    printf("ADV start rc=%d\n", rc);
}

static int gap_ev(struct ble_gap_event *ev, void *arg) {
    (void)arg;
    if (ev->type == BLE_GAP_EVENT_CONNECT) {
        if (ev->connect.status == 0) {
            conn_h = ev->connect.conn_handle;
            printf("EVT connected h=%u\n", conn_h);
        } else {
            printf("EVT conn-fail %d\n", ev->connect.status);
            start_adv();
        }
    } else if (ev->type == BLE_GAP_EVENT_DISCONNECT) {
        printf("EVT disconnected reason=%d\n", ev->disconnect.reason);
        conn_h = BLE_HS_CONN_HANDLE_NONE;
        start_adv();
    } else if (ev->type == BLE_GAP_EVENT_ADV_COMPLETE) {
        start_adv();
    }
    return 0;
}

static void coc_arm(struct ble_l2cap_chan *chan) {
    /* No auto-buffers in raw NimBLE: the app must supply an SDU
     * buffer AND the credits that come with it, on accept and after
     * every SDU. Skip this and the sender stalls at zero credits. */
    struct os_mbuf *om = os_msys_get_pkthdr(COC_MTU, 0);
    if (!om) {
        printf("COC nombuf\n");
        return;
    }
    int rc = ble_l2cap_recv_ready(chan, om);
    if (rc != 0) {
        printf("COC arm rc=%d\n", rc);
        os_mbuf_free_chain(om);
    }
}
static int coc_ev(struct ble_l2cap_event *event, void *arg) {
    (void)arg;
    if (event->type == BLE_L2CAP_EVENT_COC_ACCEPT) {
        printf("COC accept\n");
        return 0;
    }
    if (event->type == BLE_L2CAP_EVENT_COC_CONNECTED) {
        printf("COC open status=%d\n", event->connect.status);
        if (event->connect.status == 0)
            coc_arm(event->connect.chan);
        return 0;
    }
    if (event->type == BLE_L2CAP_EVENT_COC_DATA_RECEIVED) {
        struct os_mbuf *om = event->receive.sdu_rx;
        struct ble_l2cap_chan *ch = event->receive.chan;
        uint16_t n = OS_MBUF_PKTLEN(om);
        struct os_mbuf *o = om;
        while (o) {
            for (int i = 0; i < o->om_len; i++) {
                rx_fnv ^= o->om_data[i];
                rx_fnv *= 0x100000001b3ULL;
            }
            o = SLIST_NEXT(o, om_next);
        }
        rx_bytes += n;
        rx_sdus++;
        os_mbuf_free_chain(om);
        coc_arm(ch);
        return 0;
    }
    if (event->type == BLE_L2CAP_EVENT_COC_DISCONNECTED) {
        printf("COC closed bytes=%lu sdus=%lu fnv=%08lx%08lx\n", rx_bytes,
               rx_sdus, (unsigned long)(rx_fnv >> 32),
               (unsigned long)(rx_fnv & 0xFFFFFFFFULL));
        rx_bytes = 0;
        rx_sdus = 0;
        return 0;
    }
    return 0;
}

static void on_sync(void) {
    printf("SYNC\n");
    int rc = ble_svc_gap_device_name_set("ESFOC");
    printf("NAME rc=%d\n", rc);
    rc = ble_l2cap_create_server(COC_PSM, COC_MTU, coc_ev, NULL);
    printf("COC-SRV rc=%d psm=129 mtu=512\n", rc);
    start_adv();
}

static void on_reset(int reason) {
    printf("RESET reason=%d\n", reason);
}

static void host_task(void *param) {
    nimble_port_run();
    nimble_port_freertos_deinit();
}

void app_main(void) {
    printf("BOOT-esfnode\n");
    printf("heap_free=%u psram_free=%u psram_size=%u\n",
           (unsigned)esp_get_free_heap_size(),
           (unsigned)heap_caps_get_free_size(MALLOC_CAP_SPIRAM),
           (unsigned)heap_caps_get_total_size(MALLOC_CAP_SPIRAM));
    int rc = esp_nimble_hci_init();
    printf("HCI-INIT rc=%d\n", rc);
    rc = nimble_port_init();
    printf("NIMBLE-INIT rc=%d\n", rc);
    ble_svc_gap_init();
    ble_hs_cfg.sync_cb = on_sync;
    ble_hs_cfg.reset_cb = on_reset;
    nimble_port_freertos_init(host_task);
    int n = 0;
    while (1) {
        if (++n % 5 == 0)
            printf("HB heap=%u rx=%lu\n",
                   (unsigned)esp_get_free_heap_size(), rx_bytes);
        else
            printf("HB\n");
        vTaskDelay(pdMS_TO_TICKS(2000));
    }
}
