/* esfnode: ESP-IDF node — PSRAM proof + NimBLE CoC bearer.
 * radio_if.h implementation against NimBLE comes next; this file
 * proves the radio path first (advertise -> CoC accept -> count).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
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

#include "radio_if.h"

#define COC_PSM 0x81
#define COC_MTU 512

/* RX-only test build: skip PHY/DLE/interval tune + auto-TX flood at
 * CoC open, so inbound-SDU delivery is measured without LL reconfig
 * racing it or mbuf-pool pressure from ATX. 0 = full behavior. */
#define RX_ONLY_TEST 0

static volatile unsigned long rx_bytes, rx_sdus;
static volatile uint64_t rx_fnv = 0xcbf29ce484222325ULL;
/* Auto-TX: fire N known-pattern frames once per CoC open, paced by
 * credits. Lets the host verify the TX path with no serial input. */
static volatile int auto_tx = 0;
static int auto_n = 0;
static uint16_t conn_h = BLE_HS_CONN_HANDLE_NONE;
static int gap_ev(struct ble_gap_event *ev, void *arg);
/* The LE hardware gate (bit8 @0x60031000) is NOT touched by the blob's
 * ADV path (shared-memory + task messages only). Natural ADV (boot init)
 * dies at the first TOG-clear/adv-stop; only TOG-set/REKICK re-arms it.
 * So every host-side (re)start sets the gate itself -- else disconnect
 * recovery silently leaves the modem deaf. */
static void gate_set(void) {
    volatile uint32_t *r = (volatile uint32_t *)0x60031000;
    __asm__ volatile ("memw");
    *r = *r | 0x100U;
    __asm__ volatile ("memw");
}
static void start_adv(void) {
    gate_set();
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
                           &p, gap_ev, NULL);
    printf("ADV start rc=%d\n", rc);
}

static int gap_ev(struct ble_gap_event *ev, void *arg) {
    (void)arg;
    if (ev->type == BLE_GAP_EVENT_CONNECT) {
        if (ev->connect.status == 0) {
            conn_h = ev->connect.conn_handle;
            printf("EVT connected h=%u\n", conn_h);
            radio_gap_notify(RADIO_EV_CONNECTED, 0);
        } else {
            printf("EVT conn-fail %d\n", ev->connect.status);
            start_adv();
        }
    } else if (ev->type == BLE_GAP_EVENT_DISCONNECT) {
        printf("EVT disconnected reason=%d\n", ev->disconnect.reason);
        conn_h = BLE_HS_CONN_HANDLE_NONE;
        radio_gap_notify(RADIO_EV_DISCONNECTED, 0);
        start_adv();
    } else if (ev->type == BLE_GAP_EVENT_ADV_COMPLETE) {
        start_adv();
    } else if (ev->type == BLE_GAP_EVENT_CONN_UPDATE) {
        struct ble_gap_conn_desc d;
        uint32_t v;
        if (ble_gap_conn_find(ev->conn_update.conn_handle, &d) == 0) {
            v = ((uint32_t)d.conn_itvl << 16) | (d.conn_latency & 0xffff);
            printf("EVT params itvl=%d lat=%d\n", d.conn_itvl, d.conn_latency);
        } else {
            v = 0;
            printf("EVT params status=%d\n", ev->conn_update.status);
        }
        radio_gap_notify(RADIO_EV_PARAMS, v);
    } else if (ev->type == BLE_GAP_EVENT_PHY_UPDATE_COMPLETE) {
        /* LE PHY Update Complete → packs tx/rx phy */
        uint32_t v = ((uint32_t)ev->phy_updated.tx_phy << 8) |
                     (ev->phy_updated.rx_phy & 0xff);
        printf("EVT phy tx=%d rx=%d\n", ev->phy_updated.tx_phy,
               ev->phy_updated.rx_phy);
        radio_gap_notify(RADIO_EV_PHY, v);
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
        printf("COC accept peer_sdu=%u\n",
               event->accept.peer_sdu_size);
        return 0;
    }
    /* NOTE: accept carries no chan pointer in this stack version;
     * attach happens at CONNECT with event->connect.chan. */
    if (event->type == BLE_L2CAP_EVENT_COC_CONNECTED) {
        printf("COC open status=%d\n", event->connect.status);
        if (event->connect.status == 0) {
            struct ble_l2cap_chan_info ci;
            memset(&ci, 0, sizeof ci);
            int cir = ble_l2cap_get_chan_info(event->connect.chan, &ci);
            printf("COC info rc=%d scid=%u dcid=%u psm=%u our_mtu=%u peer_mtu=%u our_coc=%u peer_coc=%u\n",
                   cir, ci.scid, ci.dcid, ci.psm, ci.our_l2cap_mtu,
                   ci.peer_l2cap_mtu, ci.our_coc_mtu, ci.peer_coc_mtu);
            int slot = radio_chan_attach(event->connect.chan,
                                         event->connect.conn_handle);
            printf("COC slot=%d\n", slot);
#if !RX_ONLY_TEST
            if (slot >= 0)
                radio_request(slot, BLE_GAP_LE_PHY_2M_MASK,
                              6, 12, 251);
            auto_tx = 8;
#endif
            coc_arm(event->connect.chan);
        }
        return 0;
    }
    if (event->type == BLE_L2CAP_EVENT_COC_DATA_RECEIVED) {
        struct os_mbuf *om = event->receive.sdu_rx;
        struct ble_l2cap_chan *ch = event->receive.chan;
        uint16_t n = OS_MBUF_PKTLEN(om);
        printf("RX sdu len=%u\n", n);
        static uint8_t flat[2048];
        if (n <= sizeof flat) {
            size_t o = 0;
            struct os_mbuf *q = om;
            while (q && o < sizeof flat) {
                size_t k = q->om_len;
                if (o + k > sizeof flat)
                    k = sizeof flat - o;
                memcpy(flat + o, q->om_data, k);
                o += k;
                q = SLIST_NEXT(q, om_next);
            }
            radio_chan_rx(ch, flat, o);
        }
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
    if (event->type == BLE_L2CAP_EVENT_COC_TX_UNSTALLED) {
        printf("COC unstalled status=%d\n", event->tx_unstalled.status);
        return 0;
    }
    if (event->type == BLE_L2CAP_EVENT_COC_DISCONNECTED) {        radio_chan_detach(event->disconnect.chan);
        printf("COC closed bytes=%lu sdus=%lu fnv=%08lx%08lx\n", rx_bytes,
               rx_sdus, (unsigned long)(rx_fnv >> 32),
               (unsigned long)(rx_fnv & 0xFFFFFFFFULL));
        rx_bytes = 0;
        rx_sdus = 0;
        rx_fnv = 0xcbf29ce484222325ULL;
        return 0;
    }
    return 0;
}

/* Direct-register probe, phase A: SAFE-SUBSET dump + bit8 toggle.
 * Whitelist = config/trim/timing/status regs touched by le_init or
 * plain config writers. EXCLUDED (read side-effects suspected):
 * ISR/ack/FIFO/command regs 0x6003100c,10,18,24,48,50, 0x60011084,
 * 0x6001108c,0x60011090, 0x60011868, 0x60031304,0x60031360,0x60031364.
 * 0x6003101c/28 are the riskiest inclusions: bisect targets if ADV
 * is stillborn again. */
static const uint32_t probe_addrs[] = {
    0x60031000, 0x6003101c, 0x60031028, 0x60031070, 0x60031074,
    0x60031078, 0x60031080, 0x60031084, 0x60031088, 0x6003108c,
    0x60031090, 0x60031094, 0x60031098, 0x6003109c, 0x600310e0,
    0x600310f8, 0x60011004, 0x60011050, 0x600110b8, 0x600110d4,
    0x60011800, 0x6001186c, 0x600118fc,
};
static void reg_dump(void) {
    for (unsigned i = 0; i < sizeof probe_addrs / sizeof probe_addrs[0];
         i++) {
        uint32_t a = probe_addrs[i];
        printf("REG %08lx=%08lx\n", (unsigned long)a,
               (unsigned long)*(volatile uint32_t *)a);
    }
}
static void poke(uint32_t a, uint32_t and_m, uint32_t or_b) {
    volatile uint32_t *r = (volatile uint32_t *)a;
    __asm__ volatile ("memw");
    uint32_t v = *r;
    v = (v & and_m) | or_b;
    __asm__ volatile ("memw");
    *r = v;
    __asm__ volatile ("memw");
}
/* Phase C: software re-kick. Bit8 must be set first (hardware gate),
 * then re-issue ADV start through the blob's own API to resync its
 * software state machine with the hardware underneath. */
static void rekick(void) {
    volatile uint32_t *r = (volatile uint32_t *)0x60031000;
    __asm__ volatile ("memw");
    uint32_t v = *r;
    __asm__ volatile ("memw");
    *r = v | 0x100U;
    __asm__ volatile ("memw");
    printf("REKICK bit8=1, adv restart:\n");
    int rs = ble_gap_adv_stop();
    printf("REKICK stop rc=%d\n", rs);
    start_adv();
}
/* Phase B: replay the static part of r_rf_rw_v9_le_init (see
 * tools/out/poke_tables.txt) on a wedged controller, then set bit8.
 * Dynamic/calibration calls from the original are skipped. */
static void resume_pokes(void) {
    poke(0x60031074, 0xffffdfff, 0x00000000);
    poke(0x60031080, 0xffffff00, 0x00000064);
    poke(0x60031080, 0xff00ffff, 0x00640000);
    poke(0x60031084, 0xffffff00, 0x00000064);
    poke(0x60031084, 0xff00ffff, 0x00640000);
    poke(0x60031088, 0xffffff00, 0x00000064);
    poke(0x60031088, 0xff00ffff, 0x00640000);
    poke(0x6003108c, 0xffffff00, 0x00000064);
    poke(0x6003108c, 0xff00ffff, 0x00640000);
    poke(0x60031090, 0xffffff80, 0x0000000d);
    poke(0x60031094, 0xffffff80, 0x0000000d);
    poke(0x60031098, 0xffffff80, 0x0000000d);
    poke(0x6003109c, 0xffffff80, 0x0000000d);
    poke(0x60031000, 0xffffffff, 0x0000000f);
    poke(0x600310e0, 0xfc00ffff, 0x01be0000);
    poke(0x600310e0, 0xfffffe00, 0x000000fa);
    poke(0x60031070, 0x00000000, 0x00000000);
    poke(0x60031074, 0xffffffff, 0x00001020);
    poke(0x60031078, 0xffffffff, 0x0cc00100);
    poke(0x60031078, 0xffffffff, 0x00010000);
    poke(0x60031094, 0xffffffff, 0x00020202);
    poke(0x60031098, 0xffffffff, 0x0f020202);
    poke(0x6003109c, 0xffffffff, 0x0f020202);
    poke(0x60011050, 0xfffff800, 0x00000320);
    poke(0x60011868, 0xffffc7df, 0x00000000);
    poke(0x600310f8, 0xfffff7ff, 0x00000000);
    poke(0x60031098, 0xff00ffff, 0x00020000);
    poke(0x6003109c, 0xff80ffff, 0x00020000);
    /* finally set LE enable bit8 */
    poke(0x60031000, 0xffffffff, 0x00000100);
    printf("RES done reg=%08lx\n", (unsigned long)*(volatile uint32_t *)0x60031000);
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

/* Auto-cycle gate: the TOG/RES/REKICK 4-phase probe loop was for TX
 * mapping (done). RX/connection work needs a stable rig, so the cycle
 * now DEFAULTS OFF (serial input is dead, so no runtime toggle):
 * cycle_en = 0 freezes it; set 1 to resume probing. */
static int cycle_en = 0;

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
    /* Serial input via IDF usb_serial_jtag_read_bytes HANGS the app loop
     * (Arduino owns the USB peripheral; PC pins inside
     * usb_serial_jtag_read_bytes, console goes silent). Reverted to the
     * legacy stdin path (input effectively dead, output fine); RX state
     * is monitored passively via HB rx= lines. */
    fcntl(STDIN_FILENO, F_SETFL, O_NONBLOCK);
    static char cmd[32];
    static int cmdlen = 0;
    static uint8_t txb[480];
    while (1) {
        char c;
        if (read(STDIN_FILENO, &c, 1) == 1) {
            if (c == '\n' || cmdlen >= (int)sizeof cmd - 1) {
                cmd[cmdlen] = 0;
                cmdlen = 0;
                if (!strncmp(cmd, "TX ", 3)) {
                    int cnt = atoi(cmd + 3), ok = 0;
                    for (int i = 0; i < cnt; i++) {
                        for (int j = 0; j < 480; j++)
                            txb[j] = (uint8_t)((i * 480 + j) & 0xFF);
                        /* Credit-paced: peer grants arrive over time;
                         * retry instead of dropping on a dry window. */
                        for (int att = 0; att < 400; att++) {
                            if (radio_send(0, txb, 480) == 480) {
                                ok++;
                                break;
                            }
                            vTaskDelay(pdMS_TO_TICKS(10));
                        }
                        vTaskDelay(pdMS_TO_TICKS(5));
                    }
                    printf("TX done %d/%d\n", ok, cnt);
                } else if (!strcmp(cmd, "STAT")) {
                    printf("STAT rx=%lu sdus=%lu\n", rx_bytes,
                           rx_sdus);
                } else if (!strcmp(cmd, "CYCLE 0")) {
                    cycle_en = 0;
                    printf("CYCLE off\n");
                } else if (!strcmp(cmd, "CYCLE 1")) {
                    cycle_en = 1;
                    printf("CYCLE on\n");
                }
            } else if (c != '\r') {
                cmd[cmdlen++] = c;
            }
        }
        if (++n % 5 == 0)
            printf("HB-FLASH4 heap=%u rx=%lu sdus=%lu\n",
                   (unsigned)esp_get_free_heap_size(), rx_bytes, rx_sdus);
        else
            printf("HB\n");
        if (n == 5 || (n >= 45 && (n % 40) == 5))
            reg_dump();
        if (cycle_en && n >= 37 && (n % 8) == 5) {
            /* 4-phase cycle: set -> clear -> RESUME(init replay) ->
             * REKICK(bit8 + adv_start through the blob API). */
            static int phase = 0;
            if (phase == 2) {
                resume_pokes();
            } else if (phase == 3) {
                rekick();
            } else {
                int want = (phase == 1) ? 0 : 1;
                volatile uint32_t *r = (volatile uint32_t *)0x60031000;
                __asm__ volatile ("memw");
                uint32_t v = *r;
                v = (want == 0) ? (v & ~0x100U) : (v | 0x100U);
                __asm__ volatile ("memw");
                *r = v;
                __asm__ volatile ("memw");
                printf("TOG bit8=%d reg=%08lx\n", want,
                       (unsigned long)*r);
            }
            phase = (phase + 1) % 4;
        }
        if (auto_tx > 0) {
            for (int j = 0; j < 480; j++)
                txb[j] = (uint8_t)((auto_n * 480 + j) & 0xFF);
            if (radio_send(0, txb, 480) == 480) {
                printf("ATX %d ok\n", auto_n);
                auto_n++;
                auto_tx--;
            }
        }
        vTaskDelay(pdMS_TO_TICKS(2000));
    }
}
