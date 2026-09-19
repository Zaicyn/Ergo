/* radio_if.c -- NimBLE implementation of radio_if.h + internal glue.
 * Channel table (4 slots); send path allocates an mbuf chain per SDU.
 * Never blocks: send fails cleanly when mbufs or credits run out.
 */
#include <string.h>
#include "radio_if.h"
#include "host/ble_l2cap.h"
#include "host/ble_gap.h"
#include "os/os_mbuf.h"

#define NCHAN 4

typedef struct {
    int open;
    struct ble_l2cap_chan *chan;
    uint16_t conn;
} chslot_t;

static chslot_t slots[NCHAN];
static radio_ev_fn app_ev;
static void *app_ev_ctx;
static radio_rx_fn app_rx;
static void *app_rx_ctx;

int radio_init(const char *name, radio_ev_fn ev, void *ctx) {
    (void)name; /* app owns NimBLE init + advertising in this build */
    app_ev = ev;
    app_ev_ctx = ctx;
    memset(slots, 0, sizeof slots);
    return 0;
}

/* ---- internal glue (app + stack call these; see radio_if.h) ---- */
int radio_chan_attach(struct ble_l2cap_chan *chan, uint16_t conn) {
    for (int i = 0; i < NCHAN; i++) {
        if (!slots[i].open) {
            slots[i].open = 1;
            slots[i].chan = chan;
            slots[i].conn = conn;
            return i;
        }
    }
    return -1;
}
void radio_chan_detach(struct ble_l2cap_chan *chan) {
    for (int i = 0; i < NCHAN; i++) {
        if (slots[i].open && slots[i].chan == chan) {
            slots[i].open = 0;
            slots[i].chan = NULL;
        }
    }
}
void radio_chan_rx(struct ble_l2cap_chan *chan, const uint8_t *data,
                   size_t len) {
    (void)chan;
    if (app_rx)
        app_rx(data, len, app_rx_ctx);
}

int radio_chan_open(const uint8_t *peer_addr6, uint16_t psm,
                    uint16_t mtu) {
    (void)peer_addr6;
    (void)psm;
    (void)mtu;
    /* peripheral role: channels arrive via CoC accept, not here */
    for (int i = 0; i < NCHAN; i++)
        if (slots[i].open)
            return i;
    return -1;
}

int radio_send(int ch, const uint8_t *data, size_t len) {
    if (ch < 0 || ch >= NCHAN || !slots[ch].open || !len)
        return -1;
    /* Header-only pkthdr + append (stack practice): get_pkthdr(len)
     * preallocates uninitialized data space whose interplay with a
     * following append produced stale TX payloads under back-to-back
     * load (frame N+1 carrying frame N's bytes on air). */
    struct os_mbuf *om = os_msys_get_pkthdr(0, 0);
    if (!om)
        return -1;
    if (os_mbuf_append(om, data, (uint16_t)len) != 0) {
        os_mbuf_free_chain(om);
        return -1;
    }
    if (ble_l2cap_send(slots[ch].chan, om) != 0) {
        os_mbuf_free_chain(om);
        return -1;
    }
    return (int)len;
}

size_t radio_pending(int ch) {
    (void)ch;
    /* No cheap outstanding-bytes query in this stack version;
     * callers pace by MTU count instead. Honest zero. */
    return 0;
}

void radio_on_rx(radio_rx_fn fn, void *ctx) {
    app_rx = fn;
    app_rx_ctx = ctx;
}

void radio_gap_notify(int ev, uint32_t arg) {
    if (app_ev)
        app_ev(ev, arg, app_ev_ctx);
}

void radio_chan_close(int ch) {
    if (ch >= 0 && ch < NCHAN) {
        slots[ch].open = 0;
        slots[ch].chan = NULL;
    }
}

int radio_request(int ch, uint8_t phy_mask, uint16_t itvl_min_125,
                  uint16_t itvl_max_125, uint16_t dle_octets) {
    uint16_t h = 0xFFFF;
    if (ch >= 0 && ch < NCHAN && slots[ch].open)
        h = slots[ch].conn;
    if (h == 0xFFFF)
        return -1;
    int rc = 0;
    if (phy_mask)
        rc |= ble_gap_set_prefered_le_phy(h, phy_mask, phy_mask, 0);
    if (itvl_min_125 && itvl_max_125) {
        struct ble_gap_upd_params p = {
            itvl_min_125, itvl_max_125, 0, 420, 0, 0,
        };
        rc |= ble_gap_update_params(h, &p);
    }
    if (dle_octets)
        rc |= ble_gap_set_data_len(h, dle_octets, 2120);
    return rc ? -1 : 0;
}
