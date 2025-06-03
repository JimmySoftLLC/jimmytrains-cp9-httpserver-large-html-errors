# MIT License
#
# Copyright (c) 2024 JimmySoftLLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

#######################################################

import gc
import files
import time
import sdcardio
import storage
import busio
import digitalio
import board
import rtc
import microcontroller
import neopixel
from adafruit_debouncer import Debouncer
import asyncio


def gc_col(c_p):
    gc.collect()
    start_mem = gc.mem_free()
    files.log_item("Point " + c_p +
                   " Available memory: {} bytes".format(start_mem))


def rst():
    microcontroller.on_next_reset(microcontroller.RunMode.NORMAL)
    microcontroller.reset()


gc_col("Imports gc, files")

################################################################################
# Setup the switches
l_sw = digitalio.DigitalInOut(board.GP6)
l_sw.direction = digitalio.Direction.INPUT
l_sw.pull = digitalio.Pull.UP
l_sw = Debouncer(l_sw)

r_sw = digitalio.DigitalInOut(board.GP7)
r_sw.direction = digitalio.Direction.INPUT
r_sw.pull = digitalio.Pull.UP
r_sw = Debouncer(r_sw)

# Setup sdCard
sck = board.GP2
si = board.GP3
so = board.GP4
cs = board.GP5
spi = busio.SPI(sck, si, so)

sd = sdcardio.SDCard(spi, cs)
vfs = storage.VfsFat(sd)
storage.mount(vfs, "/sd")

# Setup time
r = rtc.RTC()
r.datetime = time.struct_time((2019, 5, 29, 15, 14, 15, 0, -1, -1))

################################################################################
# Sd card data Variables

cfg = files.read_json_file("/sd/cfg.json")

snd_o = files.return_directory("", "/sd/snd", ".wav")

cus_o = files.return_directory(
    "customers_owned_music_", "/sd/customers_owned_music", ".wav")

all_o = []
all_o.extend(snd_o)
all_o.extend(cus_o)

mnu_o = []
mnu_o.extend(snd_o)
rnd_o = ['random all', 'random built in', 'random my']
mnu_o.extend(rnd_o)
mnu_o.extend(cus_o)

ts_json = files.return_directory(
    "", "/sd/t_s_def", ".json")

web = cfg["serve_webpage"]

c_m = files.read_json_file("/sd/mvc/main_menu.json")
m_mnu = c_m["main_menu"]

c_w = files.read_json_file("/sd/mvc/web_menu.json")
w_mnu = c_w["web_menu"]

c_l = files.read_json_file(
    "/sd/mvc/light_string_menu.json")
l_mnu = c_l["light_string_menu"]

c_l_o = files.read_json_file("/sd/mvc/light_options.json")
l_opt = c_l_o["light_options"]

c_v = files.read_json_file("/sd/mvc/volume_settings.json")
v_s = c_v["volume_settings"]

c_a_s = files.read_json_file(
    "/sd/mvc/add_sounds_animate.json")
a_s = c_a_s["add_sounds_animate"]

c_run = False
ts_mode = False

local_ip = ""

ovrde_sw_st = {}
ovrde_sw_st["switch_value"] = ""
exit_set_hdw_async = False

gc_col("config setup")

################################################################################
# Setup neo pixels

bars = []
nbolts = []

bar_arr = []
nbolt_arr = []

n_px = 2
neo_pin = board.GP10
led = neopixel.NeoPixel(neo_pin, n_px)


def bld_bar():
    i = []
    for b in bars:
        for l in b:
            si = l
            break
        for l in range(0, 10):
            i.append(l+si)
    return i

def bld_nbolt():
    i = []
    for b in nbolts:
        for l in b:
            si = l
            break
        for l in range(0, len(b)):
            i.append(l+si)
    return i

def l_tst():
    global bar_arr # bolt_arr
    bar_arr = bld_bar()
    # bolt_arr = bld_bolt()
    for b in bars:
        for l in b:
            led[l] = (50, 50, 50)
        led.show()
        time.sleep(.3)
        led.fill((0, 0, 0))
        led.show()
    for b in nbolts:
        for l in b:
            led[l] = (50, 50, 50)
        led.show()
        time.sleep(.3)
        led.fill((0, 0, 0))
        led.show()


def upd_l_str():
    global bars,  n_px, led, nbolts
    bars = []
    nbolts = []

    n_px = 0

    els = cfg["light_string"].split(',')

    for el in els:
        p = el.split('-')
        if len(p) == 2:
            typ, qty = p
            qty = int(qty)
            if typ == 'bar':
                s = list(range(n_px, n_px + qty))
                bars.append(s)
                n_px += qty
            elif typ == 'nbolt':
                s = list(range(n_px, n_px + qty))
                nbolts.append(s)
                n_px += qty

    led.deinit()
    gc_col("Deinit ledStrip")
    led = neopixel.NeoPixel(neo_pin, n_px)
    led.auto_write = False
    led.brightness = 1.0
    l_tst()


upd_l_str()

gc_col("Neopixels setup")

################################################################################
# Setup wifi and web server

if (web):
    import socketpool
    import mdns
    gc_col("config wifi imports")
    import wifi
    gc_col("config wifi imports")
    from adafruit_httpserver import Server, Request, FileResponse, Response, POST
    gc_col("config wifi imports")

    files.log_item("Connecting to WiFi")

    # default for manufacturing and shows
    SSID = "jimmytrainsguest"
    PASS = ""

    try:
        env = files.read_json_file("/sd/env.json")
        SSID = env["WIFI_SSID"]
        PASS = env["WIFI_PASSWORD"]
        gc_col("wifi env")
        print("Using env ssid")
    except:
        print("Using default ssid")

    try:
        # connect to your SSID
        wifi.radio.connect(SSID, PASS)
        gc_col("wifi connect")

        # setup mdns server
        mdns = mdns.Server(wifi.radio)
        mdns.hostname = cfg["HOST_NAME"]
        mdns.advertise_service(
            service_type="_http", protocol="_tcp", port=80)

        local_ip = str(wifi.radio.ipv4_address)

        # files.log_items IP address to REPL
        files.log_item("IP is" + local_ip)
        files.log_item("Connected")

        # set up server
        pool = socketpool.SocketPool(wifi.radio)
        server = Server(pool, "/static", debug=True)

        gc_col("wifi server")

        ################################################################################
        # Setup routes

        @server.route("/")
        def base(req: HTTPRequest):
            gc_col("Home page.")
            return FileResponse(req, "index.html", "/")

        @server.route("/mui.min.css")
        def base(req: HTTPRequest):
            return FileResponse(req, "/sd/mui.min.css", "/")

        @server.route("/mui.min.js")
        def base(req: HTTPRequest):
            return FileResponse(req, "/sd/mui.min.js", "/")

        @server.route("/animation", [POST])
        def btn(req: Request):
            global cfg, c_run, ts_mode
            rq_d = req.json()
            cfg["option_selected"] = rq_d["an"]
            add_cmd(cfg["option_selected"])
            files.write_json_file("/sd/cfg.json", cfg)
            return Response(req, "Animation " + cfg["option_selected"] + " started.")

        @server.route("/defaults", [POST])
        def btn(req: Request):
            global cfg
            rq_d = req.json()
            if rq_d["an"] == "reset_animation_timing_to_defaults":
                for ts_fn in ts_json:
                    ts = files.read_json_file(
                        "/sd/t_s_def/" + ts_fn + ".json")
                    files.write_json_file(
                        "/sd/snd/"+ts_fn+".json", ts)
            elif rq_d["an"] == "reset_to_defaults":
                files.write_json_file("/sd/cfg.json", cfg)
            elif rq_d["an"] == "reset_incandescent_colors":
                files.write_json_file("/sd/cfg.json", cfg)
                s = files.json_stringify(
                    {"bars": cfg["bars"], "bolts": cfg["bolts"], "v": cfg["v"]})
                return Response(req, s)
            elif rq_d["an"] == "reset_white_colors":
                files.write_json_file("/sd/cfg.json", cfg)
                s = files.json_stringify(
                    {"bars": cfg["bars"], "bolts": cfg["bolts"], "v": cfg["v"]})
                return Response(req, s)
            return Response(req, "Utility: " + rq_d["an"])

        @server.route("/mode", [POST])
        def btn(req: Request):
            global cfg, c_run, ts_mode
            rq_d = req.json()
            if rq_d["an"] == "left":
                ovrde_sw_st["switch_value"] = "left"
            elif rq_d["an"] == "left_held":
                ovrde_sw_st["switch_value"] = "left_held"
            elif rq_d["an"] == "right":
                ovrde_sw_st["switch_value"] = "right"
            elif rq_d["an"] == "right_held":
                ovrde_sw_st["switch_value"] = "right_held"
            elif rq_d["an"] == "cont_mode_on":
                c_run = True
            elif rq_d["an"] == "cont_mode_off":
                c_run = False
            elif rq_d["an"] == "timestamp_mode_on":
                ts_mode = True
            elif rq_d["an"] == "timestamp_mode_off":
                ts_mode = False
            return Response(req, "Utility: " + rq_d["an"])

        @server.route("/speaker", [POST])
        def btn(req: Request):
            global cfg
            rq_d = req.json()
            if rq_d["an"] == "volume_pot_off":
                cfg["volume_pot"] = False
                files.write_json_file("/sd/cfg.json", cfg)
            elif rq_d["an"] == "volume_pot_on":
                cfg["volume_pot"] = True
                files.write_json_file("/sd/cfg.json", cfg)
            return Response(req, "Utility: " + rq_d["an"])

        @server.route("/lights", [POST])
        def btn(req: Request):
            rq_d = req.json()
            v = rq_d["an"].split(",")
            led.fill((float(v[0]), float(v[1]), float(v[2])))
            led.show()
            return Response(req, "OK")

        @server.route("/bolt", [POST])
        def btn(req: Request):
            led.fill((int(cfg["bolts"]["r"]), int(
                cfg["bolts"]["g"]), int(cfg["bolts"]["b"])))
            led.show()
            return Response(req, "OK")

        @server.route("/bar", [POST])
        def btn(req: Request):
            led.fill((int(cfg["bars"]["r"]), int(
                cfg["bars"]["g"]), int(cfg["bars"]["b"])))
            led.show()
            return Response(req, "OK")

        @server.route("/bright", [POST])
        def btn(req: Request):
            rq_d = req.json()
            led.brightness = float(rq_d["an"])
            led.show()
            return Response(req, "OK")

        @server.route("/update-host-name", [POST])
        def btn(req: Request):
            global cfg
            rq_d = req.json()
            cfg["HOST_NAME"] = rq_d["text"]
            files.write_json_file("/sd/cfg.json", cfg)
            mdns.hostname = cfg["HOST_NAME"]
            return Response(req, cfg["HOST_NAME"])

        @server.route("/get-host-name", [POST])
        def btn(req: Request):
            return Response(req, cfg["HOST_NAME"])

        @server.route("/update-volume", [POST])
        def btn(req: Request):
            global cfg
            rq_d = req.json()
            return Response(req, rq_d["action"])

        @server.route("/get-volume", [POST])
        def btn(req: Request):
            return Response(req, cfg["volume"])

        @server.route("/update-light-string", [POST])
        def btn(req: Request):
            global cfg
            rq_d = req.json()
            if rq_d["action"] == "save" or rq_d["action"] == "clear" or rq_d["action"] == "defaults":
                cfg["light_string"] = rq_d["text"]
                print("action: " +
                      rq_d["action"] + " data: " + cfg["light_string"])
                files.write_json_file("/sd/cfg.json", cfg)
                upd_l_str()
                return Response(req, cfg["light_string"])
            if cfg["light_string"] == "":
                cfg["light_string"] = rq_d["text"]
            else:
                cfg["light_string"] = cfg["light_string"] + \
                    "," + rq_d["text"]
            print("action: " + rq_d["action"] +
                  " data: " + cfg["light_string"])
            files.write_json_file("/sd/cfg.json", cfg)
            upd_l_str()
            return Response(req, cfg["light_string"])

        @server.route("/get-light-string", [POST])
        def btn(req: Request):
            return Response(req, cfg["light_string"])

        @server.route("/get-customers-sound-tracks", [POST])
        def btn(req: Request):
            s = files.json_stringify(cus_o)
            return Response(req, s)

        @server.route("/get-built-in-sound-tracks", [POST])
        def btn(req: Request):
            s = []
            s.extend(snd_o)
            s = files.json_stringify(s)
            return Response(req, s)

        @server.route("/get-bar-colors", [POST])
        def btn(req: Request):
            s = files.json_stringify(cfg["bars"])
            return Response(req, s)

        @server.route("/get-bolt-colors", [POST])
        def btn(req: Request):
            s = files.json_stringify(cfg["bolts"])
            return Response(req, s)

        @server.route("/get-color-variation", [POST])
        def btn(req: Request):
            s = files.json_stringify(cfg["v"])
            return Response(req, s)

        @server.route("/set-lights", [POST])
        def btn(req: Request):
            global cfg
            rq_d = req.json()
            if rq_d["item"] == "bars":
                cfg["bars"] = {"r": rq_d["r"],
                               "g": rq_d["g"], "b": rq_d["b"]}
                bi = []
                bi.extend(bar_arr)
                for i in bi:
                    led[i] = (rq_d["r"],
                              rq_d["g"], rq_d["b"])
                    led.show()
            elif rq_d["item"] == "nbolts":
                    cfg["nbolts"] = {"r": rq_d["r"],
                                     "g": rq_d["g"], "b": rq_d["b"]}
                    bi = []
                    bi.extend(nbolt_arr)
                    for i in bi:
                        led[i] = (rq_d["r"],
                                  rq_d["g"], rq_d["b"])
                        led.show()
            elif rq_d["item"] == "variationBolt":
                print(rq_d)
                cfg["v"] = {"r1": rq_d["r"], "g1": rq_d["g"], "b1": rq_d["b"],
                            "r2": cfg["v"]["r2"], "g2": cfg["v"]["g2"], "b2": cfg["v"]["b2"]}
            elif rq_d["item"] == "variationBar":
                cfg["v"] = {"r1": cfg["v"]["r1"], "g1": cfg["v"]["g1"], "b1": cfg["v"]
                            ["b1"], "r2": rq_d["r"], "g2": rq_d["g"], "b2": rq_d["b"]}
            files.write_json_file("/sd/cfg.json", cfg)
            return Response(req, "OK")
        
        @server.route("/get-local-ip", [POST])
        def buttonpress(req: Request):
            return Response(req, local_ip)

    except Exception as e:
        web = False
        files.log_item(e)

gc_col("web server")

if (web):
    files.log_item("starting server...")
    try:
        server.start(str(wifi.radio.ipv4_address), port=80)
        files.log_item("Listening on http://%s:80" % wifi.radio.ipv4_address)

    except OSError:
        time.sleep(5)
        files.log_item("restarting...")
        rst()

# Main task handling

async def server_poll_tsk(server):
    """Poll the web server."""
    while True:
        try:
            server.poll()  # Web server polling
        except Exception as e:
            files.log_item(e)
        await asyncio.sleep(0)  # Yield control to other tasks

async def main():
    # Create asyncio tasks
    tasks = []

    if web:
        tasks.append(server_poll_tsk(server))

    # Run all tasks concurrently
    await asyncio.gather(*tasks)

# Run the asyncio event loop
try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass



