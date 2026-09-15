/* radio_if.h -- the only file that knows what radio it is on.
 * Everything above this line (framing, codec, parity, commitment,
 * fetch, policy, journaling) is portable C and never includes
 * vendor headers. Porting to a new radio = reimplement this file.
 */
#pragma once
#include <stdint.h>
#include <stddef.h>

typedef void (*radio_rx_fn)(const uint8_t *data, size_t len, void *ctx);
typedef void (*radio_ev_fn)(int ev, uint32_t arg, void *ctx);

enum {
    RADIO_EV_CONNECTED = 1,
    RADIO_EV_DISCONNECTED = 2,
    RADIO_EV_CHAN_OPEN = 3,    /* arg = negotiated MTU */
    RADIO_EV_CHAN_CLOSED = 4,
    RADIO_EV_PARAMS = 5,       /* arg packs interval/latency (see impl) */
    RADIO_EV_PHY = 6,          /* arg packs tx_phy/rx_phy */
};

/* Bring up radio + advertise `name`. Events flow to ev/ctx. */
int radio_init(const char *name, radio_ev_fn ev, void *ctx);
/* Open a CoC-style channel to peer (central role) or accept (periph).
 * Returns channel id >= 0, or -1. */
int radio_chan_open(const uint8_t *peer_addr6, uint16_t psm,
                    uint16_t mtu);
/* Queue bytes; never blocks. Returns queued count, or -1 if the
 * channel is gone. Backpressure is reported, not absorbed. */
int radio_send(int ch, const uint8_t *data, size_t len);
/* Pending outbound bytes (credit/queue depth signal for policy). */
size_t radio_pending(int ch);
/* Register inbound SDU sink. */
void radio_on_rx(radio_rx_fn fn, void *ctx);
/* Fire-and-forget tuning request (PHY, interval, data length).
 * Completion (or silence) arrives via RADIO_EV_* — never assumed. */
int radio_request(int ch, uint8_t phy_mask, uint16_t itvl_min_125,
                  uint16_t itvl_max_125, uint16_t dle_octets);
/* Close channel / shut down. */
void radio_chan_close(int ch);
