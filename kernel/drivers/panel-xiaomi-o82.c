// SPDX-License-Identifier: GPL-2.0-only
/*
 * Xiaomi Pad 7 (uke) O82 dual-DSI DSC LCD panel driver.
 *
 * ЧЕРНОВИК. Каркас основан на panel-novatek-nt35950.c (AngeloGioacchino Del Regno).
 * Init-последовательность сконвертирована из downstream MiCode (uke-v-oss)
 * через tools/dsi-cmds.py. Требует проверки на реальном железе.
 *
 * Панель: 3200x2136 (2x 1600), DSI video mode, DSC 10bpc -> 8bpp,
 * slice 800x24, режимы 120/144/90 Гц. Reset gpio2, ESD IRQ gpio168/169.
 */

#include <linux/backlight.h>
#include <linux/delay.h>
#include <linux/gpio/consumer.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/of_graph.h>
#include <linux/regulator/consumer.h>

#include <drm/display/drm_dsc.h>
#include <drm/display/drm_dsc_helper.h>
#include <drm/drm_connector.h>
#include <drm/drm_mipi_dsi.h>
#include <drm/drm_modes.h>
#include <drm/drm_panel.h>

#define O82_NUM_SUPPLIES	3

struct o82_panel {
	struct drm_panel panel;
	struct drm_connector *connector;
	struct mipi_dsi_device *dsi[2];
	struct regulator_bulk_data supplies[O82_NUM_SUPPLIES];
	struct gpio_desc *reset_gpio;
	bool prepared;
};

static inline struct o82_panel *to_o82_panel(struct drm_panel *panel)
{
	return container_of(panel, struct o82_panel, panel);
}

/* reset-sequence downstream: <0 10> <1 3> <0 3> <1 15> */
static void o82_reset(struct o82_panel *ctx)
{
	gpiod_set_value_cansleep(ctx->reset_gpio, 0);
	msleep(10);
	gpiod_set_value_cansleep(ctx->reset_gpio, 1);
	msleep(3);
	gpiod_set_value_cansleep(ctx->reset_gpio, 0);
	msleep(3);
	gpiod_set_value_cansleep(ctx->reset_gpio, 1);
	msleep(15);
}

static int o82_on(struct o82_panel *ctx)
{
	struct mipi_dsi_device *dsi = ctx->dsi[0];
	struct mipi_dsi_multi_context dsi_ctx = { .dsi = dsi };

	ctx->dsi[0]->mode_flags |= MIPI_DSI_MODE_LPM;
	ctx->dsi[1]->mode_flags |= MIPI_DSI_MODE_LPM;

	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xff, 0x27);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xfb, 0x01);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xd0, 0x31);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xd1, 0x20);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xd2, 0x38);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xde, 0x43);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xdf, 0x02);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x08, 0x24, 0x0a);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x0c, 0x1e, 0x00);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x10, 0x1e, 0x00);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x80, 0x57, 0x09);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x84, 0x2d, 0x00);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x88, 0x2d, 0x00);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xff, 0x23);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xfb, 0x01);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x00, 0x80);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x01, 0x84);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x05, 0xf6);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x06, 0x02);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x11, 0x03);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x12, 0x2a);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x15, 0xd0);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x16, 0x16);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x29, 0x0a);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x30, 0xff);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x31, 0xfe);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x32, 0xfd);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x33, 0xfb);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x34, 0xf8);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x35, 0xf5);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x36, 0xf3);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x37, 0xf2);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x38, 0xf2);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x39, 0xf2);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x3a, 0xef);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x3b, 0xec);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x3d, 0xe9);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x3f, 0xe5);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x40, 0xe5);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x41, 0xe5);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x2a, 0x13);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x45, 0xff);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x46, 0xf4);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x47, 0xe7);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x48, 0xda);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x49, 0xcd);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x4a, 0xc0);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x4b, 0xb3);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x4c, 0xb1);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x4d, 0xb1);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x4e, 0xb1);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x4f, 0x95);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x50, 0x79);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x51, 0x5c);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x52, 0x58);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x53, 0x58);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x54, 0x58);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xff, 0x23);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xfb, 0x01);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x58, 0xff);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x59, 0xfb);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x5a, 0xf7);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x5b, 0xf3);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x5c, 0xef);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x5d, 0xe3);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x5e, 0xd9);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x5f, 0xd7);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x60, 0xd7);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x61, 0xd7);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x62, 0xc9);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x63, 0xb9);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x64, 0xac);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x65, 0xaa);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x66, 0xaa);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x67, 0xaa);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xff, 0x25);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xfb, 0x01);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x0f, 0x20);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xff, 0x2a);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xfb, 0x01);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xc4, 0x82);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xff, 0x26);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xfb, 0x01);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x3b, 0x06);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x4b, 0x06);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xff, 0x22);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xfb, 0x01);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xc4, 0x06);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xff, 0xf0);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xfb, 0x01);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xfa, 0x05);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x76, 0x16);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xff, 0x20);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xfb, 0x01);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x30, 0x00);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xff, 0x10);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xfb, 0x01);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x51, 0x0f, 0xff);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x53, 0x24);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x3b, 0x03, 0x94, 0x1a, 0x04, 0x04, 0x00);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x90, 0x03);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x91, 0xab, 0x28, 0x00, 0x18, 0xd2, 0x00, 0x02, 0xb2, 0x02, 0x9f, 0x00, 0x0b, 0x04, 0x86, 0x02, 0xdc);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x92, 0x10, 0xf0);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x9d, 0x01);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb3, 0x40);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb2, 0x91);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x11);
	mipi_dsi_msleep(&dsi_ctx, 120);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x29);

	ctx->dsi[0]->mode_flags &= ~MIPI_DSI_MODE_LPM;
	ctx->dsi[1]->mode_flags &= ~MIPI_DSI_MODE_LPM;

	return dsi_ctx.accum_err;
}

static int o82_off(struct o82_panel *ctx)
{
	struct mipi_dsi_device *dsi = ctx->dsi[0];
	struct mipi_dsi_multi_context dsi_ctx = { .dsi = dsi };

	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x28);
	mipi_dsi_msleep(&dsi_ctx, 20);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x10);
	mipi_dsi_msleep(&dsi_ctx, 100);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x4f);

	return dsi_ctx.accum_err;
}

static int o82_prepare(struct drm_panel *panel)
{
	struct o82_panel *ctx = to_o82_panel(panel);
	int ret;

	if (ctx->prepared)
		return 0;

	ret = regulator_bulk_enable(O82_NUM_SUPPLIES, ctx->supplies);
	if (ret < 0)
		return ret;

	o82_reset(ctx);

	ret = o82_on(ctx);
	if (ret < 0)
		regulator_bulk_disable(O82_NUM_SUPPLIES, ctx->supplies);
	else
		ctx->prepared = true;

	return ret;
}

static int o82_unprepare(struct drm_panel *panel)
{
	struct o82_panel *ctx = to_o82_panel(panel);

	if (!ctx->prepared)
		return 0;

	o82_off(ctx);
	regulator_bulk_disable(O82_NUM_SUPPLIES, ctx->supplies);
	gpiod_set_value_cansleep(ctx->reset_gpio, 0);
	ctx->prepared = false;

	return 0;
}

/*
 * Режимы. TODO: clock/dual-DSI split уточнить на железе.
 * hdisplay — на один линк (1600); при bonded DSI MSM может ожидать полную 3200.
 */
static const struct drm_display_mode o82_modes[] = {
	{ /* 120 Hz */
		.clock = 483714,
		.hdisplay = 1600,
		.hsync_start = 1600 + 113,
		.hsync_end = 1600 + 113 + 16,
		.htotal = 1600 + 113 + 16 + 16,
		.vdisplay = 2136,
		.vsync_start = 2136 + 26,
		.vsync_end = 2136 + 26 + 2,
		.vtotal = 2136 + 26 + 2 + 146,
		.width_mm = 238,
		.height_mm = 163,
	},
	{ /* 144 Hz */
		.clock = 580457,
		.hdisplay = 1600,
		.hsync_start = 1600 + 18,
		.hsync_end = 1600 + 18 + 16,
		.htotal = 1600 + 18 + 16 + 16,
		.vdisplay = 2136,
		.vsync_start = 2136 + 26,
		.vsync_end = 2136 + 26 + 2,
		.vtotal = 2136 + 26 + 2 + 146,
		.width_mm = 238,
		.height_mm = 163,
	},
	{ /* 90 Hz */
		.clock = 362786,
		.hdisplay = 1600,
		.hsync_start = 1600 + 304,
		.hsync_end = 1600 + 304 + 16,
		.htotal = 1600 + 304 + 16 + 16,
		.vdisplay = 2136,
		.vsync_start = 2136 + 26,
		.vsync_end = 2136 + 26 + 2,
		.vtotal = 2136 + 26 + 2 + 146,
		.width_mm = 238,
		.height_mm = 163,
	},
};

static int o82_get_modes(struct drm_panel *panel,
			 struct drm_connector *connector)
{
	struct o82_panel *ctx = to_o82_panel(panel);
	int i;

	for (i = 0; i < ARRAY_SIZE(o82_modes); i++) {
		struct drm_display_mode *mode;

		mode = drm_mode_duplicate(connector->dev, &o82_modes[i]);
		if (!mode)
			return -ENOMEM;

		drm_mode_set_name(mode);
		mode->type |= DRM_MODE_TYPE_DRIVER;
		if (i == 0)
			mode->type |= DRM_MODE_TYPE_PREFERRED;
		drm_mode_probed_add(connector, mode);
	}

	connector->display_info.bpc = 10;
	connector->display_info.width_mm = o82_modes[0].width_mm;
	connector->display_info.height_mm = o82_modes[0].height_mm;
	ctx->connector = connector;

	return ARRAY_SIZE(o82_modes);
}

static const struct drm_panel_funcs o82_panel_funcs = {
	.prepare = o82_prepare,
	.unprepare = o82_unprepare,
	.get_modes = o82_get_modes,
};

static const char * const o82_supply_names[O82_NUM_SUPPLIES] = {
	"vddio",
	"vsp",
	"vsn",
};

static int o82_probe(struct mipi_dsi_device *dsi)
{
	struct device *dev = &dsi->dev;
	struct device_node *dsi_r;
	struct mipi_dsi_host *dsi_r_host;
	struct o82_panel *ctx;
	struct drm_dsc_config *dsc;
	int i, num_dsis = 1, ret;

	ctx = devm_drm_panel_alloc(dev, struct o82_panel, panel,
				   &o82_panel_funcs, DRM_MODE_CONNECTOR_DSI);
	if (IS_ERR(ctx))
		return PTR_ERR(ctx);

	for (i = 0; i < O82_NUM_SUPPLIES; i++)
		ctx->supplies[i].supply = o82_supply_names[i];

	ret = devm_regulator_bulk_get(dev, O82_NUM_SUPPLIES, ctx->supplies);
	if (ret)
		return dev_err_probe(dev, ret, "Failed to get regulators\n");

	ctx->reset_gpio = devm_gpiod_get(dev, "reset", GPIOD_ASIS);
	if (IS_ERR(ctx->reset_gpio))
		return dev_err_probe(dev, PTR_ERR(ctx->reset_gpio),
				     "Failed to get reset gpio\n");

	/* DSI1: вторичный линк (bonded dual-DSI). */
	dsi_r = of_graph_get_remote_node(dsi->dev.of_node, 1, -1);
	if (!dsi_r) {
		dev_err(dev, "Cannot get secondary DSI node\n");
		return -ENODEV;
	}
	dsi_r_host = of_find_mipi_dsi_host_by_node(dsi_r);
	of_node_put(dsi_r);
	if (!dsi_r_host)
		return dev_err_probe(dev, -EPROBE_DEFER, "Cannot get secondary DSI host\n");

	{
		const struct mipi_dsi_device_info info = {
			.type = "o82",
			.channel = 0,
			.node = NULL,
		};
		ctx->dsi[1] = mipi_dsi_device_register_full(dsi_r_host, &info);
	}
	if (IS_ERR(ctx->dsi[1])) {
		dev_err(dev, "Cannot register secondary DSI device\n");
		return PTR_ERR(ctx->dsi[1]);
	}
	num_dsis++;

	ctx->dsi[0] = dsi;
	mipi_dsi_set_drvdata(dsi, ctx);

	/* DSC: 10 bpc -> 8 bpp, slice 800x24, 2 slices на линк. */
	dsc = devm_kzalloc(dev, sizeof(*dsc), GFP_KERNEL);
	if (!dsc) {
		ret = -ENOMEM;
		goto err_unregister;
	}
	dsc->dsc_version_major = 0x1;
	dsc->dsc_version_minor = 0x1;
	dsc->slice_height = 24;
	dsc->slice_width = 800;
	dsc->slice_count = 2;
	dsc->bits_per_component = 10;
	dsc->bits_per_pixel = 8 << 4;
	dsc->block_pred_enable = true;
	dsi->dsc = dsc;

	ret = drm_panel_of_backlight(&ctx->panel);
	if (ret)
		goto err_unregister;

	drm_panel_add(&ctx->panel);

	for (i = 0; i < num_dsis; i++) {
		ctx->dsi[i]->lanes = 4;
		ctx->dsi[i]->format = MIPI_DSI_FMT_RGB101010;
		ctx->dsi[i]->mode_flags = MIPI_DSI_MODE_VIDEO |
					  MIPI_DSI_MODE_VIDEO_BURST |
					  MIPI_DSI_MODE_NO_EOT_PACKET |
					  MIPI_DSI_CLOCK_NON_CONTINUOUS |
					  MIPI_DSI_MODE_LPM;

		ret = mipi_dsi_attach(ctx->dsi[i]);
		if (ret < 0) {
			dev_err_probe(dev, ret, "Cannot attach to DSI%d host\n", i);
			goto err_panel_remove;
		}
	}

	gpiod_set_value_cansleep(ctx->reset_gpio, 0);
	return 0;

err_panel_remove:
	drm_panel_remove(&ctx->panel);
err_unregister:
	mipi_dsi_device_unregister(ctx->dsi[1]);
	return ret;
}

static void o82_remove(struct mipi_dsi_device *dsi)
{
	struct o82_panel *ctx = mipi_dsi_get_drvdata(dsi);

	mipi_dsi_detach(ctx->dsi[0]);
	mipi_dsi_detach(ctx->dsi[1]);
	mipi_dsi_device_unregister(ctx->dsi[1]);
	drm_panel_remove(&ctx->panel);
}

static const struct of_device_id o82_of_match[] = {
	{ .compatible = "xiaomi,o82" },
	{ }
};
MODULE_DEVICE_TABLE(of, o82_of_match);

static struct mipi_dsi_driver o82_driver = {
	.probe = o82_probe,
	.remove = o82_remove,
	.driver = {
		.name = "panel-xiaomi-o82",
		.of_match_table = o82_of_match,
	},
};
module_mipi_dsi_driver(o82_driver);

MODULE_AUTHOR("uke-linux-port");
MODULE_DESCRIPTION("Xiaomi Pad 7 O82 dual-DSI DSC LCD panel");
MODULE_LICENSE("GPL");
