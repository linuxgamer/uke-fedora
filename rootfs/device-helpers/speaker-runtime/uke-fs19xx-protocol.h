/* SPDX-License-Identifier: GPL-2.0-only */
/* Runtime-only FourSemi provisioning. No device calibration in source/files. */
#ifndef UKE_FS19XX_PROTOCOL_H
#define UKE_FS19XX_PROTOCOL_H
#ifdef __KERNEL__
#include <linux/types.h>
#include <linux/errno.h>
#include <linux/string.h>
typedef u8 uke_u8;
typedef u32 uke_u32;
#else
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <errno.h>
#include <string.h>
typedef uint8_t uke_u8;
typedef uint32_t uke_u32;
#endif

#define UKE_FS19XX_ABI 1
#define UKE_FS19XX_FRAME_BYTES 512
#define UKE_FS19XX_DATA_BYTES 480
#define UKE_FS19XX_RX_IID 0x4040
#define UKE_FS19XX_TX_IID 0x49fd
#define UKE_FS19XX_RX_MODULE 0x10001111
#define UKE_FS19XX_TX_MODULE 0x10001110
#define UKE_FS19XX_RE25_PARAM 0x10001fa7
#define UKE_FS19XX_RE25_BYTES 96
#define UKE_FS19XX_CONTROL "FS19xx Runtime Provisioning"
#define UKE_FS19XX_STATUS "FS19xx Protection State"

enum uke_fs19xx_operation {
	UKE_FS_BEGIN = 1, UKE_FS_PARAMETER, UKE_FS_CALIBRATION,
	UKE_FS_COMMIT, UKE_FS_CLEAR,
};
enum uke_fs19xx_status {
	UKE_FS_EMPTY, UKE_FS_STAGING, UKE_FS_READY, UKE_FS_PREPARED,
	UKE_FS_RUNNING, UKE_FS_FAULT,
};
struct uke_fs19xx_parameter {
	uke_u32 instance, id, bytes;
	const char *sha256;
};
static const struct uke_fs19xx_parameter uke_fs19xx_parameters[5] = {
	{0x4040, 0x10001fb0, 5360, "ae2fb662cefab77744a31a1b89b753e247a41c3a8bd231483c1240bd22b6de5a"},
	{0x4040, 0x10001fc2, 8, "af5570f5a1810b7af78caf4bc70a660f0df51e42baf91d4de5b2328de0e83dfc"},
	{0x49fd, 0x10001fc2, 8, "af5570f5a1810b7af78caf4bc70a660f0df51e42baf91d4de5b2328de0e83dfc"},
	{0x4040, 0x11111611, 4, "67abdd721024f0ff4e0b3f4c2fc13bc5bad42d0b7851d456d88d203d15aaa450"},
	{0x49fd, 0x11111601, 4, "67abdd721024f0ff4e0b3f4c2fc13bc5bad42d0b7851d456d88d203d15aaa450"},
};
struct uke_fs19xx_state {
	uke_u8 tuning[5360], opaque[2][8], enable[2][4];
	uke_u8 re25[UKE_FS19XX_RE25_BYTES];
	uke_u32 positions[4], received[5], transaction;
	enum uke_fs19xx_status status;
	bool calibrated;
};

static inline uke_u32 uke_fs19xx_word(const uke_u8 *p)
{
	return (uke_u32)p[0] | (uke_u32)p[1] << 8 |
	       (uke_u32)p[2] << 16 | (uke_u32)p[3] << 24;
}
static inline void uke_fs19xx_put_word(uke_u8 *p, uke_u32 value)
{
	p[0] = value; p[1] = value >> 8; p[2] = value >> 16; p[3] = value >> 24;
}
static inline uke_u8 *uke_fs19xx_parameter_data(struct uke_fs19xx_state *state,
					      unsigned int slot)
{
	if (!slot) return state->tuning;
	if (slot < 3) return state->opaque[slot - 1];
	if (slot < 5) return state->enable[slot - 3];
	return NULL;
}
static inline void uke_fs19xx_erase(struct uke_fs19xx_state *state)
{
	volatile uke_u8 *p = (volatile uke_u8 *)state;
	size_t i;
	for (i = 0; i < sizeof(*state); i++) p[i] = 0;
}

typedef bool (*uke_fs19xx_verify)(void *, unsigned int, const uke_u8 *, size_t);
typedef int (*uke_fs19xx_send)(void *, uke_u32, uke_u32, const uke_u8 *, size_t);

/* Caller holds its state mutex. No buffer or parameter values may be logged. */
static inline int uke_fs19xx_provision(struct uke_fs19xx_state *state,
		const uke_u8 *frame, size_t bytes, bool busy,
		uke_fs19xx_verify verify, void *context)
{
	uke_u32 operation, transaction, slot, total, offset, length;
	unsigned int i;
	const uke_u8 *data;
	if (busy) return -EBUSY;
	if (bytes != UKE_FS19XX_FRAME_BYTES || !frame) return -EINVAL;
	operation = uke_fs19xx_word(frame + 4);
	transaction = uke_fs19xx_word(frame + 8);
	slot = uke_fs19xx_word(frame + 12);
	total = uke_fs19xx_word(frame + 16);
	offset = uke_fs19xx_word(frame + 20);
	length = uke_fs19xx_word(frame + 24);
	data = frame + 32;
	if (uke_fs19xx_word(frame) != UKE_FS19XX_ABI ||
	    uke_fs19xx_word(frame + 28) || length > UKE_FS19XX_DATA_BYTES)
		goto invalid;
	for (i = length; i < UKE_FS19XX_DATA_BYTES; i++)
		if (data[i]) goto invalid;
	if (operation == UKE_FS_CLEAR) {
		if (slot || total || offset || length) goto invalid;
		uke_fs19xx_erase(state);
		return 0;
	}
	if (!transaction) goto invalid;
	if (operation == UKE_FS_BEGIN) {
		if (slot || total || offset || length) goto invalid;
		uke_fs19xx_erase(state);
		state->transaction = transaction;
		state->status = UKE_FS_STAGING;
		return 0;
	}
	if (state->status != UKE_FS_STAGING || state->transaction != transaction)
		goto invalid;
	if (operation == UKE_FS_PARAMETER) {
		if (slot >= 5 || total != uke_fs19xx_parameters[slot].bytes || !length ||
		    offset != state->received[slot] || offset > total || length > total - offset)
			goto invalid;
		memcpy(uke_fs19xx_parameter_data(state, slot) + offset, data, length);
		state->received[slot] += length;
		return 0;
	}
	if (operation == UKE_FS_CALIBRATION) {
		uke_u32 mask = 0;
		if (slot || offset || total != 112 || length != 112 || state->calibrated)
			goto invalid;
		for (i = 0; i < 4; i++) {
			uke_u32 position = uke_fs19xx_word(data + 4 * i);
			uke_u32 resistance = uke_fs19xx_word(data + 16 + 24 * i);
			unsigned int j;
			if (!position || position > 8 || (position & (position - 1)) ||
			    (mask & position) || !resistance || resistance > 0x7fffffff)
				goto invalid;
			mask |= position;
			state->positions[i] = position;
			for (j = 4; j < 24; j++)
				if (data[16 + 24 * i + j]) goto invalid;
		}
		if (mask != 15) goto invalid;
		memcpy(state->re25, data + 16, UKE_FS19XX_RE25_BYTES);
		state->calibrated = true;
		return 0;
	}
	if (operation == UKE_FS_COMMIT) {
		if (slot || total || offset || length || !state->calibrated || !verify)
			goto invalid;
		for (i = 0; i < 5; i++)
			if (state->received[i] != uke_fs19xx_parameters[i].bytes ||
			    !verify(context, i, uke_fs19xx_parameter_data(state, i), state->received[i]))
				goto invalid;
		state->status = UKE_FS_READY;
		return 0;
	}
invalid:
	uke_fs19xx_erase(state);
	state->status = UKE_FS_FAULT;
	return -EINVAL;
}

static inline int uke_fs19xx_prepare(struct uke_fs19xx_state *state,
		uke_fs19xx_send send, void *context)
{
	static const unsigned int order[] = {0, 1, 2};
	uke_u8 disable[4] = {0};
	unsigned int i;
	int ret;
	if (state->status != UKE_FS_READY || !state->calibrated || !send)
		return -ENODATA;
	for (i = 0; i < 3; i++) {
		unsigned int slot = order[i];
		ret = send(context, uke_fs19xx_parameters[slot].instance,
			uke_fs19xx_parameters[slot].id, uke_fs19xx_parameter_data(state, slot),
			uke_fs19xx_parameters[slot].bytes);
		if (ret) goto failed;
	}
	ret = send(context, UKE_FS19XX_RX_IID, UKE_FS19XX_RE25_PARAM,
		   state->re25, UKE_FS19XX_RE25_BYTES);
	if (ret) goto failed;
	for (i = 0; i < 2; i++) {
		unsigned int slot = 4 - i; /* VI TX enabled before playback RX. */
		ret = send(context, uke_fs19xx_parameters[slot].instance,
			uke_fs19xx_parameters[slot].id, uke_fs19xx_parameter_data(state, slot), 4);
		if (ret) goto failed;
	}
	state->status = UKE_FS_PREPARED;
	return 0;
failed:
	/* Best-effort disabling cannot replace the caller's physical mute gate. */
	send(context, UKE_FS19XX_RX_IID, 0x11111611, disable, 4);
	send(context, UKE_FS19XX_TX_IID, 0x11111601, disable, 4);
	uke_fs19xx_erase(state);
	state->status = UKE_FS_FAULT;
	return ret;
}
#endif
