// SPDX-License-Identifier: GPL-2.0-only
/*
 * Novatek NT36532 touchscreen (Xiaomi Pad 7 / uke).
 *
 * ЧЕРНОВИК mainline-порта. Протокол, регистровая модель и firmware update
 * перенесены из downstream `nt36xxx`
 * (Xiaomi-Pad-7-Pro-Resources/android_kernel_xiaomi_sm8635-modules).
 *
 * Реализовано:
 *  - SPI (mode 0, read/write с маской 0x80/0x7F и dummy-байтом);
 *  - регистровый доступ (set_page/write_addr), чтение fw info, reset-state, статуса;
 *  - reset/boot MCU, firmware download (header parse + SRAM write + checksum);
 *  - threaded IRQ, разбор пакета (6 байт/палец, checksum 65), report MT-B.
 * TODO: ESD/WDT-recovery, стилус, MP-тест. Требует проверки на железе.
 */

#include <linux/delay.h>
#include <linux/firmware.h>
#include <linux/gpio/consumer.h>
#include <linux/input.h>
#include <linux/input/mt.h>
#include <linux/input/touchscreen.h>
#include <linux/interrupt.h>
#include <linux/module.h>
#include <linux/mutex.h>
#include <linux/of.h>
#include <linux/regulator/consumer.h>
#include <linux/spi/spi.h>

#define NT36532_MAX_TOUCHES		10
#define NT36532_POINT_DATA_LEN		65
#define NT36532_CHECKSUM_LEN		65
#define NT36532_FORCE_MAX		1000
#define NT36532_XBUF_LEN		(63 * 1024 + 1 + 1)
#define NT36532_DEFAULT_X		3200
#define NT36532_DEFAULT_Y		2136

#define NT36532_TRANSFER_LEN		(63 * 1024)
#define NT36532_ENG_RST_ADDR		0x7FFF80

/* Event map (см. downstream nt36xxx.h). */
#define EVENT_HOST_CMD			0x50
#define EVENT_HANDSHAKING		0x51
#define EVENT_RESET_COMPLETE		0x60
#define EVENT_FWINFO			0x78

#define RESET_STATE_INIT		0xA0
#define RESET_STATE_REK			0xA1
#define RESET_STATE_MAX			0xAF

#define FLASH_SECTOR_SIZE		SIZE_4KB
#define FLASH_END_FLAG_LEN		3

/* mem_map NT36523 (используется NT36532). */
#define MMAP_EVENT_BUF_ADDR		0x2FE00
#define MMAP_RW_FLASH_DATA_ADDR		0x24002
#define MMAP_BOOT_RDY_ADDR		0x3F10D
#define MMAP_TX_AUTO_COPY_EN		0x3F7E8
#define MMAP_BLD_CRC_EN_ADDR		0x3F30E
#define MMAP_R_ILM_CHECKSUM_ADDR	0x3F120

struct nt36532_bin_map {
	char name[12];
	u32 bin_addr;
	u32 sram_addr;
	u32 size;
	u32 crc;
};

struct nt36532 {
	struct spi_device *spi;
	struct input_dev *input;
	struct touchscreen_properties prop;
	struct gpio_desc *reset_gpio;
	struct regulator_bulk_data supplies[2];
	const char *fw_name;

	struct mutex lock;
	struct mutex xbuf_lock;
	u8 *txbuf;
	u8 *rxbuf;
	u32 abs_x_max;
	u32 abs_y_max;

	u32 swrst_n8_addr;
	u32 fw_ver;
	u16 nvt_pid;
	u8 x_num;
	u8 y_num;
	u8 max_button_num;
	u8 hw_crc;

	const struct firmware *fw_entry;
	u8 *fwbuf;
	struct nt36532_bin_map *bin_map;
	u32 partition;
};

/* ------------------------------------------------------------------ */
/* SPI / регистровый доступ                                            */
/* ------------------------------------------------------------------ */

static int nt36532_spi_xfer(struct nt36532 *ts, u8 *buf, size_t len, bool read)
{
	struct spi_transfer xfer = {
		.tx_buf = ts->txbuf,
		.len = len + 1,
	};
	struct spi_message msg;
	int ret;

	memset(ts->txbuf, 0, len + 1);
	if (read) {
		buf[0] &= 0x7f;
		xfer.rx_buf = ts->rxbuf;
	} else {
		buf[0] |= 0x80;
	}
	memcpy(ts->txbuf, buf, len);

	spi_message_init(&msg);
	spi_message_add_tail(&xfer, &msg);
	ret = spi_sync(ts->spi, &msg);
	if (!ret && read)
		memcpy(buf + 1, ts->rxbuf + 2, len - 1);

	return ret;
}

static int nt36532_write(struct nt36532 *ts, u8 *buf, size_t len)
{
	return nt36532_spi_xfer(ts, buf, len, false);
}

static int nt36532_read(struct nt36532 *ts, u8 *buf, size_t len)
{
	return nt36532_spi_xfer(ts, buf, len, true);
}

static int nt36532_set_page(struct nt36532 *ts, u32 addr)
{
	u8 buf[3] = { 0xFF, (addr >> 15) & 0xff, (addr >> 7) & 0xff };

	return nt36532_write(ts, buf, 3);
}

static int nt36532_write_addr(struct nt36532 *ts, u32 addr, u8 data)
{
	u8 buf[3];
	int ret;

	ret = nt36532_set_page(ts, addr);
	if (ret)
		return ret;

	buf[0] = addr & 0x7f;
	buf[1] = data;

	return nt36532_write(ts, buf, 2);
}

/* ------------------------------------------------------------------ */
/* Состояние FW / fw info                                              */
/* ------------------------------------------------------------------ */

static int nt36532_clear_fw_status(struct nt36532 *ts)
{
	u8 buf[2];
	int i, ret;

	for (i = 0; i < 20; i++) {
		ret = nt36532_set_page(ts, MMAP_EVENT_BUF_ADDR | EVENT_HANDSHAKING);
		if (ret)
			return ret;

		buf[0] = EVENT_HANDSHAKING;
		buf[1] = 0x00;
		nt36532_write(ts, buf, 2);

		buf[0] = EVENT_HANDSHAKING;
		buf[1] = 0xff;
		nt36532_read(ts, buf, 2);
		if (buf[1] == 0x00)
			return 0;

		usleep_range(10000, 11000);
	}

	return -EIO;
}

static int nt36532_check_fw_reset_state(struct nt36532 *ts, u8 state)
{
	u8 buf[6];
	int i, retry_max = (state == RESET_STATE_INIT) ? 10 : 50;

	nt36532_set_page(ts, MMAP_EVENT_BUF_ADDR | EVENT_RESET_COMPLETE);

	for (i = 0; i < retry_max; i++) {
		buf[0] = EVENT_RESET_COMPLETE;
		buf[1] = 0x00;
		nt36532_read(ts, buf, 6);

		if (buf[1] >= state && buf[1] <= RESET_STATE_MAX)
			return 0;

		usleep_range(10000, 11000);
	}

	dev_err(&ts->spi->dev, "reset state timeout, buf[1]=0x%02x\n", buf[1]);
	return -EIO;
}

static int nt36532_get_fw_info(struct nt36532 *ts)
{
	u8 buf[39];
	int i, ret;

	for (i = 0; i < 3; i++) {
		ret = nt36532_set_page(ts, MMAP_EVENT_BUF_ADDR | EVENT_FWINFO);
		if (ret)
			return ret;

		buf[0] = EVENT_FWINFO;
		ret = nt36532_read(ts, buf, 39);
		if (ret)
			return ret;

		if ((u8)(buf[1] + buf[2]) == 0xff)
			break;
	}

	if ((u8)(buf[1] + buf[2]) != 0xff) {
		dev_err(&ts->spi->dev, "FW info broken\n");
		return -EIO;
	}

	ts->fw_ver = buf[1];
	ts->x_num = buf[3];
	ts->y_num = buf[4];
	ts->abs_x_max = (buf[5] << 8) | buf[6];
	ts->abs_y_max = (buf[7] << 8) | buf[8];
	ts->max_button_num = buf[11];
	ts->nvt_pid = (buf[36] << 8) | buf[35];

	dev_info(&ts->spi->dev, "fw_ver=0x%02x pid=0x%04x x=%u y=%u\n",
		 ts->fw_ver, ts->nvt_pid, ts->abs_x_max, ts->abs_y_max);

	return 0;
}

/* ------------------------------------------------------------------ */
/* Reset / boot                                                        */
/* ------------------------------------------------------------------ */

static void nt36532_eng_reset(struct nt36532 *ts)
{
	nt36532_write_addr(ts, NT36532_ENG_RST_ADDR, 0x5a);
	mdelay(1);
}

static void nt36532_sw_reset_idle(struct nt36532 *ts)
{
	if (ts->swrst_n8_addr)
		nt36532_write_addr(ts, ts->swrst_n8_addr, 0xaa);
	msleep(20);
}

static void nt36532_bootloader_reset(struct nt36532 *ts)
{
	if (ts->swrst_n8_addr)
		nt36532_write_addr(ts, ts->swrst_n8_addr, 0x69);
	mdelay(5);
}

static void nt36532_boot_ready(struct nt36532 *ts)
{
	nt36532_write_addr(ts, MMAP_BOOT_RDY_ADDR, 1);
	mdelay(5);
	if (!ts->hw_crc) {
		nt36532_write_addr(ts, MMAP_BOOT_RDY_ADDR, 0);
		/* POR_CD: 0xA0 при отсутствии hw crc (адрес см. downstream) */
	}
}

/* ------------------------------------------------------------------ */
/* Firmware download                                                   */
/* ------------------------------------------------------------------ */

static u32 nt36532_byte_to_word(const u8 *p)
{
	return p[0] | (p[1] << 8) | (p[2] << 16) | (p[3] << 24);
}

static u32 nt36532_checksum32(const u8 *data, size_t len)
{
	u32 sum = 0;
	size_t i;

	for (i = 0; i < len + 1; i++)
		sum += data[i];
	sum += len;

	return ~sum + 1;
}

static int nt36532_bin_header_parser(struct nt36532 *ts, const u8 *fw, size_t fwsize)
{
	u32 end = nt36532_byte_to_word(fw);
	u8 info_sec_num = 0, ovly_info, ovly_sec_num;
	u32 pos, list;

	pos = 0x30;
	while (pos < end) {
		info_sec_num++;
		pos += 0x10;
	}

	ovly_info = (fw[0x28] & 0x10) >> 4;
	ovly_sec_num = ovly_info ? (fw[0x28] & 0x0f) : 0;

	ts->partition = 2 + ovly_sec_num + info_sec_num;
	ts->bin_map = kcalloc(ts->partition + 1, sizeof(*ts->bin_map), GFP_KERNEL);
	if (!ts->bin_map)
		return -ENOMEM;

	for (list = 0; list < ts->partition; list++) {
		struct nt36532_bin_map *b = &ts->bin_map[list];

		if (list < 2) {
			b->bin_addr = nt36532_byte_to_word(&fw[0 + list * 12]);
			b->sram_addr = nt36532_byte_to_word(&fw[4 + list * 12]);
			b->size = nt36532_byte_to_word(&fw[8 + list * 12]);
			snprintf(b->name, sizeof(b->name), list ? "DLM" : "ILM");
		} else if (list < 2 + info_sec_num) {
			pos = 0x30 + 0x10 * (list - 2);
			b->sram_addr = nt36532_byte_to_word(&fw[pos]);
			b->size = nt36532_byte_to_word(&fw[pos + 4]);
			b->bin_addr = nt36532_byte_to_word(&fw[pos + 8]);
			snprintf(b->name, sizeof(b->name), "Info-%u", list - 2);
		} else {
			pos = ts->bin_map[1].bin_addr +
			      0x10 * (list - 2 - info_sec_num);
			b->sram_addr = nt36532_byte_to_word(&fw[pos]);
			b->size = nt36532_byte_to_word(&fw[pos + 4]);
			b->bin_addr = nt36532_byte_to_word(&fw[pos + 8]);
			snprintf(b->name, sizeof(b->name), "Ovly-%u",
				 list - 2 - info_sec_num);
		}

		if (ts->hw_crc)
			b->crc = nt36532_byte_to_word(&fw[0x18 + list * 4]);
		else if (b->bin_addr + b->size < fwsize)
			b->crc = nt36532_checksum32(&fw[b->bin_addr], b->size);

		if (b->bin_addr + b->size > fwsize)
			return -EINVAL;
	}

	return 0;
}

static int nt36532_write_sram(struct nt36532 *ts, const u8 *fw,
			      u32 sram_addr, u32 size, u32 bin_addr)
{
	u32 i, count;
	int ret;

	count = DIV_ROUND_UP(size, NT36532_TRANSFER_LEN);

	for (i = 0; i < count; i++) {
		u32 len = min_t(u32, size, NT36532_TRANSFER_LEN);

		ret = nt36532_set_page(ts, sram_addr);
		if (ret)
			return ret;

		ts->fwbuf[0] = sram_addr & 0x7f;
		memcpy(ts->fwbuf + 1, &fw[bin_addr], len);
		ret = nt36532_write(ts, ts->fwbuf, len + 1);
		if (ret)
			return ret;

		sram_addr += NT36532_TRANSFER_LEN;
		bin_addr += NT36532_TRANSFER_LEN;
		size -= len;
	}

	return 0;
}

static int nt36532_write_firmware(struct nt36532 *ts, const u8 *fw, size_t fwsize)
{
	u32 list;
	int ret;

	memset(ts->fwbuf, 0, NT36532_TRANSFER_LEN + 1);

	for (list = 0; list < ts->partition; list++) {
		struct nt36532_bin_map *b = &ts->bin_map[list];
		u32 size = b->size;

		if (!size)
			continue;
		if (b->bin_addr + size > fwsize)
			return -EINVAL;

		ret = nt36532_write_sram(ts, fw, b->sram_addr, size + 1, b->bin_addr);
		if (ret)
			return ret;
	}

	return 0;
}

static int nt36532_check_fw_checksum(struct nt36532 *ts)
{
	u32 len = ts->partition * 4;
	u8 *buf = ts->fwbuf;
	u32 list;
	int ret;

	memset(buf, 0, len + 1);
	nt36532_set_page(ts, MMAP_R_ILM_CHECKSUM_ADDR);
	buf[0] = MMAP_R_ILM_CHECKSUM_ADDR & 0x7f;
	ret = nt36532_read(ts, buf, len + 1);
	if (ret)
		return ret;

	for (list = 0; list < ts->partition; list++) {
		u32 fw_sum = nt36532_byte_to_word(&buf[1 + list * 4]);

		if (!ts->bin_map[list].size)
			continue;
		if (ts->bin_map[list].crc != fw_sum)
			return -EIO;
	}

	return 0;
}

static int nt36532_download_firmware(struct nt36532 *ts)
{
	int ret, retry;

	for (retry = 0; retry <= 2; retry++) {
		if (ts->reset_gpio) {
			gpiod_set_value_cansleep(ts->reset_gpio, 0);
			mdelay(1);
		}
		nt36532_eng_reset(ts);
		if (ts->reset_gpio) {
			gpiod_set_value_cansleep(ts->reset_gpio, 1);
			mdelay(10);
		}
		nt36532_bootloader_reset(ts);
		nt36532_sw_reset_idle(ts);
		nt36532_clear_fw_status(ts);

		nt36532_write_addr(ts, MMAP_EVENT_BUF_ADDR | EVENT_RESET_COMPLETE, 0x00);

		ret = nt36532_write_firmware(ts, ts->fw_entry->data,
					     ts->fw_entry->size);
		if (ret)
			continue;

		nt36532_boot_ready(ts);

		ret = nt36532_check_fw_reset_state(ts, RESET_STATE_INIT);
		if (ret)
			continue;

		ret = nt36532_check_fw_checksum(ts);
		if (!ret)
			return 0;
	}

	return ret ?: -EIO;
}

static int nt36532_update_firmware(struct nt36532 *ts)
{
	int ret;

	ret = request_firmware(&ts->fw_entry, ts->fw_name, &ts->spi->dev);
	if (ret) {
		dev_warn(&ts->spi->dev, "firmware '%s' not found: %d\n",
			 ts->fw_name, ret);
		return ret;
	}

	ts->fwbuf = kzalloc(NT36532_TRANSFER_LEN + 1 + 1, GFP_KERNEL);
	if (!ts->fwbuf) {
		ret = -ENOMEM;
		goto out;
	}

	ret = nt36532_bin_header_parser(ts, ts->fw_entry->data, ts->fw_entry->size);
	if (ret)
		goto out;

	ret = nt36532_download_firmware(ts);
	if (ret)
		dev_err(&ts->spi->dev, "firmware download failed: %d\n", ret);
	else
		dev_info(&ts->spi->dev, "firmware updated\n");

out:
	kfree(ts->bin_map);
	ts->bin_map = NULL;
	kfree(ts->fwbuf);
	ts->fwbuf = NULL;
	release_firmware(ts->fw_entry);
	ts->fw_entry = NULL;
	return ret;
}

/* ------------------------------------------------------------------ */
/* Обработка прерывания (report MT-B)                                  */
/* ------------------------------------------------------------------ */

static int nt36532_point_checksum(const u8 *buf)
{
	u8 checksum = 0;
	int i;

	for (i = 0; i < NT36532_CHECKSUM_LEN - 1; i++)
		checksum += buf[i + 1];
	checksum = ~checksum + 1;

	return checksum != buf[NT36532_CHECKSUM_LEN];
}

static irqreturn_t nt36532_irq(int irq, void *data)
{
	struct nt36532 *ts = data;
	u8 point_data[NT36532_POINT_DATA_LEN + 1] = {0};
	u8 press_id[NT36532_MAX_TOUCHES] = {0};
	int finger_cnt = 0;
	int ret, i;

	mutex_lock(&ts->lock);

	ret = nt36532_read(ts, point_data, NT36532_POINT_DATA_LEN + 1);
	if (ret || nt36532_point_checksum(point_data))
		goto out;

	for (i = 0; i < NT36532_MAX_TOUCHES; i++) {
		unsigned int position = 1 + 6 * i;
		u8 input_id = point_data[position] >> 3;
		unsigned int x, y, w, p;

		if (input_id == 0 || input_id > NT36532_MAX_TOUCHES)
			continue;
		if ((point_data[position] & 0x07) != 0x01 &&
		    (point_data[position] & 0x07) != 0x02)
			continue;

		x = (point_data[position + 1] << 4) | (point_data[position + 3] >> 4);
		y = (point_data[position + 2] << 4) | (point_data[position + 3] & 0x0f);
		if (x > ts->abs_x_max || y > ts->abs_y_max)
			continue;

		w = point_data[position + 4] ?: 1;
		p = point_data[position + 5];
		if (i < 2)
			p |= point_data[i + 63] << 8;
		p = clamp(p, 1U, (unsigned int)NT36532_FORCE_MAX);

		press_id[input_id - 1] = 1;
		input_mt_slot(ts->input, input_id - 1);
		input_mt_report_slot_state(ts->input, MT_TOOL_FINGER, true);
		input_report_abs(ts->input, ABS_MT_POSITION_X, x);
		input_report_abs(ts->input, ABS_MT_POSITION_Y, y);
		input_report_abs(ts->input, ABS_MT_TOUCH_MAJOR, w);
		input_report_abs(ts->input, ABS_MT_PRESSURE, p);
		finger_cnt++;
	}

	for (i = 0; i < NT36532_MAX_TOUCHES; i++) {
		if (press_id[i])
			continue;
		input_mt_slot(ts->input, i);
		input_mt_report_slot_state(ts->input, MT_TOOL_FINGER, false);
	}

	input_report_key(ts->input, BTN_TOUCH, finger_cnt > 0);
	input_mt_sync_frame(ts->input);
	input_sync(ts->input);

out:
	mutex_unlock(&ts->lock);
	return IRQ_HANDLED;
}

/* ------------------------------------------------------------------ */
/* Probe / remove                                                      */
/* ------------------------------------------------------------------ */

static int nt36532_probe(struct spi_device *spi)
{
	struct device *dev = &spi->dev;
	struct nt36532 *ts;
	int ret;

	ts = devm_kzalloc(dev, sizeof(*ts), GFP_KERNEL);
	if (!ts)
		return -ENOMEM;

	ts->spi = spi;
	spi_set_drvdata(spi, ts);
	mutex_init(&ts->lock);
	mutex_init(&ts->xbuf_lock);

	ts->txbuf = devm_kzalloc(dev, NT36532_XBUF_LEN, GFP_KERNEL);
	ts->rxbuf = devm_kzalloc(dev, NT36532_XBUF_LEN, GFP_KERNEL);
	if (!ts->txbuf || !ts->rxbuf)
		return -ENOMEM;

	ts->supplies[0].supply = "vdd";
	ts->supplies[1].supply = "vddio";
	ret = devm_regulator_bulk_get(dev, ARRAY_SIZE(ts->supplies), ts->supplies);
	if (ret)
		return dev_err_probe(dev, ret, "Failed to get regulators\n");

	ret = regulator_bulk_enable(ARRAY_SIZE(ts->supplies), ts->supplies);
	if (ret)
		return dev_err_probe(dev, ret, "Failed to enable regulators\n");

	ts->reset_gpio = devm_gpiod_get_optional(dev, "reset", GPIOD_OUT_HIGH);
	if (IS_ERR(ts->reset_gpio)) {
		ret = dev_err_probe(dev, PTR_ERR(ts->reset_gpio), "Failed to get reset gpio\n");
		goto err_regs;
	}

	spi->mode = SPI_MODE_0;
	ret = spi_setup(spi);
	if (ret)
		goto err_regs;

	ret = device_property_read_string(dev, "firmware-name", &ts->fw_name);
	if (ret)
		ts->fw_name = "novatek_nt36532_o82_fw_csot.bin";
	device_property_read_u32(dev, "novatek,swrst-n8-addr", &ts->swrst_n8_addr);

	/* reset и чтение fw info */
	if (ts->reset_gpio) {
		gpiod_set_value_cansleep(ts->reset_gpio, 0);
		msleep(10);
		gpiod_set_value_cansleep(ts->reset_gpio, 1);
		msleep(15);
	}
	ret = nt36532_check_fw_reset_state(ts, RESET_STATE_REK);
	if (ret)
		dev_warn(dev, "controller not ready (%d), пробуем прошить\n", ret);

	if (nt36532_get_fw_info(ts)) {
		dev_warn(dev, "нет валидного fw info, обновляем прошивку\n");
		ret = nt36532_update_firmware(ts);
		if (!ret)
			nt36532_get_fw_info(ts);
	}

	ts->input = devm_input_allocate_device(dev);
	if (!ts->input) {
		ret = -ENOMEM;
		goto err_regs;
	}

	ts->input->name = "Novatek NT36532 Touchscreen";
	ts->input->id.bustype = BUS_SPI;
	ts->input->id.vendor = 0x0603;
	ts->input->id.product = 0x3653;

	if (!ts->abs_x_max)
		ts->abs_x_max = NT36532_DEFAULT_X;
	if (!ts->abs_y_max)
		ts->abs_y_max = NT36532_DEFAULT_Y;

	input_set_abs_params(ts->input, ABS_MT_POSITION_X, 0, ts->abs_x_max, 0, 0);
	input_set_abs_params(ts->input, ABS_MT_POSITION_Y, 0, ts->abs_y_max, 0, 0);
	input_set_abs_params(ts->input, ABS_MT_TOUCH_MAJOR, 0, 255, 0, 0);
	input_set_abs_params(ts->input, ABS_MT_PRESSURE, 0, NT36532_FORCE_MAX, 0, 0);
	input_set_capability(ts->input, EV_KEY, BTN_TOUCH);
	touchscreen_parse_properties(ts->input, true, &ts->prop);

	ret = input_mt_init_slots(ts->input, NT36532_MAX_TOUCHES,
				  INPUT_MT_DIRECT | INPUT_MT_DROP_UNUSED);
	if (ret)
		goto err_regs;

	ret = input_register_device(ts->input);
	if (ret)
		goto err_regs;

	if (spi->irq > 0) {
		ret = devm_request_threaded_irq(dev, spi->irq, NULL, nt36532_irq,
						IRQF_ONESHOT | IRQF_TRIGGER_FALLING,
						"nt36532", ts);
		if (ret) {
			dev_err_probe(dev, ret, "Failed to request IRQ %d\n", spi->irq);
			goto err_regs;
		}
	} else {
		dev_warn(dev, "no IRQ configured — ввод не будет работать\n");
	}

	dev_info(dev, "Novatek NT36532 (uke) готов (черновик)\n");
	return 0;

err_regs:
	regulator_bulk_disable(ARRAY_SIZE(ts->supplies), ts->supplies);
	return ret;
}

static void nt36532_remove(struct spi_device *spi)
{
	struct nt36532 *ts = spi_get_drvdata(spi);

	regulator_bulk_disable(ARRAY_SIZE(ts->supplies), ts->supplies);
}

static const struct of_device_id nt36532_of_match[] = {
	{ .compatible = "novatek,NVT-ts" },
	{ .compatible = "novatek,NVT-ts-spi" },
	{ }
};
MODULE_DEVICE_TABLE(of, nt36532_of_match);

static struct spi_driver nt36532_driver = {
	.probe = nt36532_probe,
	.remove = nt36532_remove,
	.driver = {
		.name = "nt36532-uke",
		.of_match_table = nt36532_of_match,
	},
};
module_spi_driver(nt36532_driver);

MODULE_AUTHOR("uke-linux-port");
MODULE_DESCRIPTION("Novatek NT36532 touchscreen (Xiaomi Pad 7)");
MODULE_LICENSE("GPL");
