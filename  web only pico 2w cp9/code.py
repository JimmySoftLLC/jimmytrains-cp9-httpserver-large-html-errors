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

import utilities
import gc
import files
import time
import audiocore
import audiomixer
import audiobusio
import sdcardio
import storage
import busio
import digitalio
import board
import random
import rtc
import microcontroller
from analogio import AnalogIn
import neopixel
from rainbowio import colorwheel
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
# Setup hardware

# Setup pin for v
a_in = AnalogIn(board.A0)

# setup pin for audio enable 21 on 5v aud board 22 on tiny 28 on large
aud_mute = digitalio.DigitalInOut(board.GP22)
aud_mute.direction = digitalio.Direction.OUTPUT
aud_mute.value = True

# Setup the switches
l_sw = digitalio.DigitalInOut(board.GP6)
l_sw.direction = digitalio.Direction.INPUT
l_sw.pull = digitalio.Pull.UP
l_sw = Debouncer(l_sw)

r_sw = digitalio.DigitalInOut(board.GP7)
r_sw.direction = digitalio.Direction.INPUT
r_sw.pull = digitalio.Pull.UP
r_sw = Debouncer(r_sw)

# setup i2s audio
i2s_bclk = board.GP18   # BCLK on MAX98357A
i2s_lrc = board.GP19  # LRC on MAX98357A
i2s_din = board.GP20  # DIN on MAX98357A

aud = audiobusio.I2SOut(bit_clock=i2s_bclk, word_select=i2s_lrc, data=i2s_din)

# Setup sdCard
aud_mute.value = False
sck = board.GP2
si = board.GP3
so = board.GP4
cs = board.GP5
spi = busio.SPI(sck, si, so)

# Setup the mixer
mix = audiomixer.Mixer(voice_count=1, sample_rate=22050,
                       channel_count=2, bits_per_sample=16, samples_signed=True, buffer_size=4096)
aud.play(mix)

mix.voice[0].level = .2

try:
    sd = sdcardio.SDCard(spi, cs)
    vfs = storage.VfsFat(sd)
    storage.mount(vfs, "/sd")
except:
    aud_mute.value = False
    w0 = audiocore.WaveFile(open("wav/no_card.wav", "rb"))
    mix.voice[0].play(w0, loop=False)
    while mix.voice[0].playing:
        pass
    card_in = False
    while not card_in:
        l_sw.update()
        if l_sw.fell:
            try:
                sd = sdcardio.SDCard(spi, cs)
                vfs = storage.VfsFat(sd)
                storage.mount(vfs, "/sd")
                card_in = True
                w0 = audiocore.WaveFile(
                    open("/sd/mvc/micro_sd_card_success.wav", "rb"))
                mix.voice[0].play(w0, loop=False)
                while mix.voice[0].playing:
                    pass
            except:
                w0 = audiocore.WaveFile(open("wav/no_card.wav", "rb"))
                mix.voice[0].play(w0, loop=False)
                while mix.voice[0].playing:
                    pass

aud_mute.value = True

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
            stp_a_0()
            gc_col("Home page.")
            return FileResponse(req, "index.html", "/")

        @server.route("/mui.min.css")
        def base(req: HTTPRequest):
            stp_a_0()
            return FileResponse(req, "/sd/mui.min.css", "/")

        @server.route("/mui.min.js")
        def base(req: HTTPRequest):
            stp_a_0()
            return FileResponse(req, "/sd/mui.min.js", "/")

        @server.route("/animation", [POST])
        def btn(req: Request):
            global cfg, c_run, ts_mode
            rq_d = req.json()
            cfg["option_selected"] = rq_d["an"]
            add_cmd(cfg["option_selected"])
            if not mix.voice[0].playing:
                files.write_json_file("/sd/cfg.json", cfg)
            return Response(req, "Animation " + cfg["option_selected"] + " started.")

        @server.route("/defaults", [POST])
        def btn(req: Request):
            global cfg
            stp_a_0()
            rq_d = req.json()
            if rq_d["an"] == "reset_animation_timing_to_defaults":
                for ts_fn in ts_json:
                    ts = files.read_json_file(
                        "/sd/t_s_def/" + ts_fn + ".json")
                    files.write_json_file(
                        "/sd/snd/"+ts_fn+".json", ts)
                ply_a_0("/sd/mvc/all_changes_complete.wav")
            elif rq_d["an"] == "reset_to_defaults":
                rst_def()
                files.write_json_file("/sd/cfg.json", cfg)
                ply_a_0("/sd/mvc/all_changes_complete.wav")
                st_mch.go_to('base_state')
            elif rq_d["an"] == "reset_incandescent_colors":
                rst_def_col()
                files.write_json_file("/sd/cfg.json", cfg)
                ply_a_0("/sd/mvc/all_changes_complete.wav")
                s = files.json_stringify(
                    {"bars": cfg["bars"], "bolts": cfg["bolts"], "v": cfg["v"]})
                st_mch.go_to('base_state')
                return Response(req, s)
            elif rq_d["an"] == "reset_white_colors":
                rst_wht_col()
                files.write_json_file("/sd/cfg.json", cfg)
                ply_a_0("/sd/mvc/all_changes_complete.wav")
                s = files.json_stringify(
                    {"bars": cfg["bars"], "bolts": cfg["bolts"], "v": cfg["v"]})
                st_mch.go_to('base_state')
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
                ply_a_0("/sd/mvc/continuous_mode_activated.wav")
            elif rq_d["an"] == "cont_mode_off":
                c_run = False
                stp_all_cmds()
                ply_a_0("/sd/mvc/continuous_mode_deactivated.wav")
            elif rq_d["an"] == "timestamp_mode_on":
                ts_mode = True
                ply_a_0("/sd/mvc/timestamp_mode_on.wav")
                ply_a_0("/sd/mvc/timestamp_instructions.wav")
            elif rq_d["an"] == "timestamp_mode_off":
                ts_mode = False
                ply_a_0("/sd/mvc/timestamp_mode_off.wav")
            return Response(req, "Utility: " + rq_d["an"])

        @server.route("/speaker", [POST])
        def btn(req: Request):
            global cfg
            stp_a_0()
            rq_d = req.json()
            if rq_d["an"] == "speaker_test":
                ply_a_0("/sd/mvc/left_speaker_right_speaker.wav")
            elif rq_d["an"] == "volume_pot_off":
                cfg["volume_pot"] = False
                files.write_json_file("/sd/cfg.json", cfg)
                ply_a_0("/sd/mvc/all_changes_complete.wav")
            elif rq_d["an"] == "volume_pot_on":
                cfg["volume_pot"] = True
                files.write_json_file("/sd/cfg.json", cfg)
                ply_a_0("/sd/mvc/all_changes_complete.wav")
            return Response(req, "Utility: " + rq_d["an"])

        @server.route("/lights", [POST])
        def btn(req: Request):
            stp_a_0()
            rq_d = req.json()
            v = rq_d["an"].split(",")
            led.fill((float(v[0]), float(v[1]), float(v[2])))
            led.show()
            return Response(req, "OK")

        @server.route("/bolt", [POST])
        def btn(req: Request):
            stp_a_0()
            led.fill((int(cfg["bolts"]["r"]), int(
                cfg["bolts"]["g"]), int(cfg["bolts"]["b"])))
            led.show()
            return Response(req, "OK")

        @server.route("/bar", [POST])
        def btn(req: Request):
            stp_a_0()
            led.fill((int(cfg["bars"]["r"]), int(
                cfg["bars"]["g"]), int(cfg["bars"]["b"])))
            led.show()
            return Response(req, "OK")

        @server.route("/bright", [POST])
        def btn(req: Request):
            rq_d = req.json()
            stp_a_0()
            led.brightness = float(rq_d["an"])
            led.show()
            return Response(req, "OK")

        @server.route("/update-host-name", [POST])
        def btn(req: Request):
            global cfg
            stp_a_0()
            rq_d = req.json()
            cfg["HOST_NAME"] = rq_d["text"]
            files.write_json_file("/sd/cfg.json", cfg)
            mdns.hostname = cfg["HOST_NAME"]
            spk_web()
            return Response(req, cfg["HOST_NAME"])

        @server.route("/get-host-name", [POST])
        def btn(req: Request):
            return Response(req, cfg["HOST_NAME"])

        @server.route("/update-volume", [POST])
        def btn(req: Request):
            global cfg
            rq_d = req.json()
            ch_vol(rq_d["action"])
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
                ply_a_0("/sd/mvc/all_changes_complete.wav")
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
            ply_a_0("/sd/mvc/all_changes_complete.wav")
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
            stp_a_0()
            return Response(req, local_ip)

    except Exception as e:
        web = False
        files.log_item(e)

gc_col("web server")

################################################################################
# Command queue
command_queue = []


def add_cmd(command, to_start=False):
    global ex_hdw
    ex_hdw = False
    if to_start:
        command_queue.insert(0, command)  # Add to the front
        print("Command added to the start:", command)
    else:
        command_queue.append(command)  # Add to the end
        print("Command added to the end:", command)


async def process_cmd():
    while command_queue:
        command = command_queue.pop(0)  # Retrieve from the front of the queue
        print("Processing command:", command)
        # Process each command as an async operation
        await an(command)
        await asyncio.sleep(0)  # Yield control to the event loop


def clr_cmd_queue():
    command_queue.clear()
    print("Command queue cleared.")


def stp_all_cmds():
    global ex_hdw
    clr_cmd_queue()
    ex_hdw = True
    print("Processing stopped and command queue cleared.")

################################################################################
# Global Methods


def rst_l_def():
    global cfg
    cfg["light_string"] = "bar-10,bolt-1,bar-10,bolt-1,bar-10,bolt-1"


def rst_def_col():
    global cfg
    cfg["bars"] = {"r": 255, "g": 136, "b": 26}
    cfg["bolts"] = {"r": 255, "g": 136, "b": 26}
    cfg["v"] = {"r1": 20, "g1": 8, "b1": 5, "r2": 20, "g2": 8, "b2": 5}


def rst_wht_col():
    global cfg
    cfg["bars"] = {"r": 255, "g": 255, "b": 255}
    cfg["bolts"] = {"r": 255, "g": 255, "b": 255}
    cfg["v"] = {"r1": 0, "g1": 0, "b1": 0, "r2": 0, "g2": 0, "b2": 0}


def rst_def():
    global cfg
    cfg["volume_pot"] = True
    cfg["HOST_NAME"] = "animator-lightning"
    cfg["option_selected"] = "thunder birds rain"
    cfg["volume"] = "20"
    cfg["can_cancel"] = True
    rst_l_def()
    rst_def_col()


################################################################################
# Dialog and sound play methods


def upd_vol(s):
    if cfg["volume_pot"]:
        v = a_in.value / 65536
        mix.voice[0].level = v
        time.sleep(s)
    else:
        try:
            v = int(cfg["volume"]) / 100
        except:
            v = .5
        if v < 0 or v > 1:
            v = .5
        mix.voice[0].level = v
        time.sleep(s)


async def upd_vol_async(s):
    if cfg["volume_pot"]:
        v = a_in.value / 65536
        mix.voice[0].level = v
        await asyncio.sleep(s)
    else:
        try:
            v = int(cfg["volume"]) / 100
        except Exception as e:
            files.log_item(e)
            v = .5
        if v < 0 or v > 1:
            v = .5
        mix.voice[0].level = v
        await asyncio.sleep(s)


def ch_vol(action):
    v = int(cfg["volume"])
    if "volume" in action:
        v = action.split("volume")
        v = int(v[1])
    if action == "lower1":
        v -= 1
    elif action == "raise1":
        v += 1
    elif action == "lower":
        if v <= 10:
            v -= 1
        else:
            v -= 10
    elif action == "raise":
        if v < 10:
            v += 1
        else:
            v += 10
    if v > 100:
        v = 100
    if v < 1:
        v = 1
    cfg["volume"] = str(v)
    cfg["volume_pot"] = False
    if not mix.voice[0].playing:
        files.write_json_file("/sd/cfg.json", cfg)
        ply_a_0("/sd/mvc/volume.wav")
        spk_str(cfg["volume"], False)


def ply_a_0(file_name):
    if mix.voice[0].playing:
        mix.voice[0].stop()
        while mix.voice[0].playing:
            upd_vol(0.02)
    w0 = audiocore.WaveFile(open(file_name, "rb"))
    mix.voice[0].play(w0, loop=False)
    while mix.voice[0].playing:
        exit_early()


def stp_a_0():
    mix.voice[0].stop()
    while mix.voice[0].playing:
        pass


def exit_early():
    global c_run
    sw = utilities.switch_state(
        l_sw, r_sw, time.sleep, 3.0, ovrde_sw_st)
    if sw == "left" and cfg["can_cancel"]:
        mix.voice[0].stop()
    if sw == "left_held":
        mix.voice[0].stop()
        c_run = False
        stp_all_cmds()
        ply_a_0("/sd/mvc/continuous_mode_deactivated.wav")


def spk_str(str_to_speak, addLocal):
    for character in str_to_speak:
        try:
            if character == " ":
                character = "space"
            if character == "-":
                character = "dash"
            if character == ".":
                character = "dot"
            ply_a_0("/sd/mvc/" + character + ".wav")
        except:
            print("Invalid character in string to speak")
    if addLocal:
        ply_a_0("/sd/mvc/dot.wav")
        ply_a_0("/sd/mvc/local.wav")


def l_r_but():
    ply_a_0("/sd/mvc/press_left_button_right_button.wav")


def sel_web():
    ply_a_0("/sd/mvc/web_menu.wav")
    l_r_but()


def opt_sel():
    ply_a_0("/sd/mvc/option_selected.wav")


def spk_sng_num(song_number):
    ply_a_0("/sd/mvc/song.wav")
    spk_str(song_number, False)


def spk_lght(play_intro):
    try:
        elements = cfg["light_string"].split(',')
        if play_intro:
            ply_a_0("/sd/mvc/current_light_settings_are.wav")
        for index, element in enumerate(elements):
            ply_a_0("/sd/mvc/position.wav")
            ply_a_0("/sd/mvc/" + str(index+1) + ".wav")
            ply_a_0("/sd/mvc/is.wav")
            ply_a_0("/sd/mvc/" + element + ".wav")
    except:
        ply_a_0("/sd/mvc/no_lights_in_light_string.wav")
        return


def no_trk():
    ply_a_0("/sd/mvc/no_user_soundtrack_found.wav")
    while True:
        l_sw.update()
        r_sw.update()
        if l_sw.fell:
            break
        if r_sw.fell:
            ply_a_0("/sd/mvc/create_sound_track_files.wav")
            break


def spk_web():
    ply_a_0("/sd/mvc/animator_available_on_network.wav")
    ply_a_0("/sd/mvc/to_access_type.wav")
    if cfg["HOST_NAME"] == "animator-lightning":
        ply_a_0("/sd/mvc/animator_dash_lightning.wav")
        ply_a_0("/sd/mvc/dot.wav")
        ply_a_0("/sd/mvc/local.wav")
    else:
        spk_str(cfg["HOST_NAME"], True)
    ply_a_0("/sd/mvc/in_your_browser.wav")

################################################################################
# animations


async def an(fn):
    global cfg
    print("Filename: " + fn)
    cur = fn
    try:
        if fn == "random built in":
            hi = len(snd_o) - 1
            cur = snd_o[random.randint(0, hi)]
        elif fn == "random my":
            hi = len(cus_o) - 1
            cur = cus_o[random.randint(0, hi)]
        elif fn == "random all":
            hi = len(all_o) - 1
            cur = all_o[random.randint(0, hi)]
        if ts_mode:
            ts(cur)
        else:
            if "customers_owned_music_" in cur:
                await an_ls(cur)
            elif cur == "alien lightshow":
                await an_ls(cur)
            elif cur == "inspiring cinematic ambient lightshow":
                await an_ls(cur)
            elif cur == "fireworks":
                await an_ls(cur)
            else:
                await t_l(cur)
    except Exception as e:
        files.log_item(e)
        no_trk()
        cfg["option_selected"] = "random built in"
        return
    gc_col("Animation complete.")


async def an_ls(fn):
    global ts_mode, ovrde_sw_st
    il = 1
    ih = 3

    if fn == "fireworks":
        il = 4
        ih = 4

    cf = "customers_owned_music_" in fn

    if cf:
        fn = fn.replace("customers_owned_music_", "")
        try:
            fls_t = files.read_json_file(
                "/sd/customers_owned_music/" + fn + ".json")
        except:
            ply_a_0("/sd/mvc/no_timestamp_file_found.wav")
            while True:
                l_sw.update()
                r_sw.update()
                if l_sw.fell:
                    ts_mode = False
                    return
                if r_sw.fell:
                    ts_mode = True
                    ply_a_0("/sd/mvc/timestamp_instructions.wav")
                    return
    else:
        fls_t = files.read_json_file(
            "/sd/snd/" + fn + ".json")
    
    ft = fls_t["flashTime"]

    ftl = len(ft)
    fti = 0

    if cf:
        w0 = audiocore.WaveFile(
            open("/sd/customers_owned_music/" + fn + ".wav", "rb"))
    else:
        w0 = audiocore.WaveFile(
            open("/sd/snd/" + fn + ".wav", "rb"))
    mix.voice[0].play(w0, loop=False)
    st = time.monotonic()
    i = 0

    mlt_c(.01)
    while True:
        pi = 0
        await asyncio.sleep(0)
        te = time.monotonic()-st
        if fti < len(ft)-2:
            d = ft[fti+1] - \
                ft[fti]-0.25
        else:
            d = 0.25
        if d < 0:
            d = 0
        if te > ft[fti] - 0.25:
            exit_early()
            print("TE: " + str(te) + " TS: " +
                  str(ft[fti]) + " Dif: " + str(te-ft[fti]))
            fti += 1
            i = random.randint(il, ih)
            while i == pi:
                i = random.randint(il, ih)
            if i == 1:
                rainbow(.005, d)
            elif i == 2:
                mlt_c(.01)
                upd_vol(d)
            elif i == 3:
                candle(d)
            elif i == 4:
                fwrk(d)
            pi = i
        if ftl == fti:
            fti = 0
        sw = utilities.switch_state(
            l_sw, r_sw, time.sleep, 3.0, ovrde_sw_st)
        if sw == "left" and cfg["can_cancel"]:
            mix.voice[0].stop()
        if sw == "left_held":
            mix.voice[0].stop()
            if cont_run:
                cont_run = False
                stp_all_cmds()
                ply_a_0("/sd/mvc/continuous_mode_deactivated.wav")
        if not mix.voice[0].playing:
            led.fill((0, 0, 0))
            led.show()
            break
        upd_vol(.001)


def ts(fn):
    print("Time stamp mode:")
    global ts_mode

    cf = "customers_owned_music_" in fn

    ts = files.read_json_file(
        "/sd/t_s_def/timestamp mode.json")
    ts["flashTime"] = []

    fn = fn.replace("customers_owned_music_", "")

    if cf:
        w0 = audiocore.WaveFile(
            open("/sd/customers_owned_music/" + fn + ".wav", "rb"))
    else:
        w0 = audiocore.WaveFile(
            open("/sd/snd/" + fn + ".wav", "rb"))
    mix.voice[0].play(w0, loop=False)

    st = time.monotonic()
    upd_vol(.1)

    while True:
        te = time.monotonic()-st
        r_sw.update()
        if r_sw.fell:
            ts["flashTime"].append(te)
            print(te)
        if not mix.voice[0].playing:
            led.fill((0, 0, 0))
            led.show()
            ts["flashTime"].append(5000)
            if cf:
                files.write_json_file(
                    "/sd/customers_owned_music/" + fn + ".json", ts)
            else:
                files.write_json_file(
                    "/sd/snd/" + fn + ".json", ts)
            break

    ts_mode = False
    ply_a_0("/sd/mvc/timestamp_saved.wav")
    ply_a_0("/sd/mvc/timestamp_mode_off.wav")
    ply_a_0("/sd/mvc/animations_are_now_active.wav")


async def t_l(file_name):
    global c_run

    ftd = files.read_json_file(
        "/sd/snd/" + file_name + ".json")

    ft = ftd["flashTime"]

    ftl = len(ft)
    fti = 0

    w0 = audiocore.WaveFile(
        open("/sd/snd/" + file_name + ".wav", "rb"))
    mix.voice[0].play(w0, loop=False)
    st = time.monotonic()

    while True:
        upd_vol(.1)
        await asyncio.sleep(0)
        te = time.monotonic()-st
        # amount of time before you here thunder 0.5 is synched with the lightning 2 is 1.5 seconds later
        rt = ft[fti] - random.uniform(.5, 1)
        if te > rt:
            exit_early()
            print("TE: " + str(te) + " TS: " +
                  str(rt) + " Dif: " + str(te-rt))
            fti += 1
            ltng()
        if ftl == fti:
            fti = 0
        exit_early()
        if not mix.voice[0].playing:
            break

##############################
# Led color effects


def rainbow(spd, dur):
    startTime = time.monotonic()
    for j in range(0, 255, 1):
        for i in range(n_px):
            pi = (i * 256 // n_px) + j
            led[i] = colorwheel(pi & 255)
        led.show()
        upd_vol(spd)
        te = time.monotonic()-startTime
        if te > dur:
            return
    for j in reversed(range(0, 255, 1)):
        for i in range(n_px):
            pi = (i * 256 // n_px) + j
            led[i] = colorwheel(pi & 255)
        led.show()
        upd_vol(spd)
        te = time.monotonic()-startTime
        if te > dur:
            return


def candle(dur):
    st = time.monotonic()
    led.brightness = 1.0

    bari = []
    bari.extend(bar_arr)

    bolti = []
    bolti.extend(nbolt_arr)

    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)

    for i in bolti:
        led[i] = (r, g, b)

    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)

    # Flicker, based on our initial RGB values
    while True:
        for i in bari:
            f = random.randint(0, 110)
            r1 = bnd(r-f, 0, 255)
            g1 = bnd(g-f, 0, 255)
            b1 = bnd(b-f, 0, 255)
            led[i] = (r1, g1, b1)
            led.show()
        upd_vol(random.uniform(0.05, 0.1))
        te = time.monotonic()-st
        if te > dur:
            return


def fwrk_sprd(arr):
    c = len(arr) // 2
    for i in range(c):
        l_i = c - 1 - i
        r_i = c + i
        yield (arr[l_i], arr[r_i])


def rst_bar():
    for b in bars:
        for i in b:
            led[i] = (0, 0, 0)


def r_w_b():
    i = random.randint(0, 2)
    if i == 0:  # white
        r = 255
        g = 255
        b = 255
    if i == 1:  # red
        r = 255
        g = 0
        b = 0
    if i == 2:  # blue
        r = 0
        g = 0
        b = 255
    return r, g, b


def fwrk(duration):
    st = time.monotonic()
    led.brightness = 1.0

    # choose which bar none to all to fire
    bar_f = []
    for i, arr in enumerate(bars):
        if i == random.randint(0, (len(bars)-1)):
            bar_f.append(i)

    if len(bar_f) == 0:
        i == random.randint(0, (len(bars)-1))
        bar_f.append(i)

    for nbolt in nbolts:
        for nbolt_index in nbolt:
            r, g, b = r_w_b()
            led[nbolt_index] = (r, g, b)

    # Burst from center
    ext = False
    while not ext:
        for i in bar_f:
            r, g, b = r_w_b()
            fs = fwrk_sprd(bars[i])
            for left, right in fs:
                rst_bar()
                led[left] = (r, g, b)
                led[right] = (r, g, b)
                led.show()
                upd_vol(0.1)
                te = time.monotonic()-st
                if te > duration:
                    rst_bar()
                    led.show()
                    break
            led.show()
            te = time.monotonic()-st
            if te > duration:
                rst_bar()
                led.show()
                break
        te = time.monotonic()-st
        if te > duration:
            rst_bar()
            led.show()
            return


def mlt_c(dur):
    st = time.monotonic()
    led.brightness = 1.0

    # Flicker, based on our initial RGB values
    while True:
        for i in range(0, n_px):
            r = random.randint(128, 255)
            g = random.randint(128, 255)
            b = random.randint(128, 255)
            c = random.randint(0, 2)
            if c == 0:
                r1 = r
                g1 = 0
                b1 = 0
            elif c == 1:
                r1 = 0
                g1 = g
                b1 = 0
            elif c == 2:
                r1 = 0
                g1 = 0
                b1 = b
            led[i] = (r1, g1, b1)
            led.show()
        upd_vol(random.uniform(.2, 0.3))
        te = time.monotonic()-st
        if te > dur:
            return


def col_it(col, var):
    col = int(col)
    var = int(var)
    l = int(bnd(col-var/100*col, 0, 255))
    h = int(bnd(col+var/100*col, 0, 255))
    return random.randint(l, h)


def ltng():
    # choose which nbolt or no bolt to fire
    nbolt = []
    b_i = random.randint(-1, (len(nbolts)-1))
    if b_i != -1:
        for i, arr in enumerate(nbolts):
            if i == b_i:
                nbolt.extend(arr)   
    # choose which bar one to all to fire
    bar = []
    for i, arr in enumerate(bars):
        if i == random.randint(0, (len(bars)-1)):
            bar.extend(arr)

    # number of flashes
    f_num = random.randint(5, 10)

    for i in range(0, f_num):
        # set bolt base color
        bolt_r = col_it(cfg["bolts"]["r"], cfg["v"]["r1"])
        bolt_g = col_it(cfg["bolts"]["g"], cfg["v"]["g1"])
        bolt_b = col_it(cfg["bolts"]["b"], cfg["v"]["b1"])

        # set bar base color
        bar_r = col_it(cfg["bars"]["r"], cfg["v"]["r2"])
        bar_g = col_it(cfg["bars"]["g"], cfg["v"]["g2"])
        bar_b = col_it(cfg["bars"]["b"], cfg["v"]["b2"])

        led.brightness = random.randint(150, 255) / 255
        for _ in range(4):
            for j in nbolt:
                led[j] = (
                    bolt_r, bolt_g, bolt_b)
            for j in bar:
                led[j] = (
                    bar_r, bar_g, bar_b)
            led.show()
            dly = random.randint(0, 75)  # flash offset range - ms
            dly = dly/1000
            time.sleep(dly)
            led.fill((0, 0, 0))
            led.show()

        dly = random.randint(1, 50)  # time to next flash range - ms
        dly = dly/1000
        time.sleep(dly)
        led.fill((0, 0, 0))
        led.show()


def bnd(cd, l, u):
    if (cd < l):
        cd = l
    if (cd > u):
        cd = u
    return cd

################################################################################
# State Machine


class StMch(object):

    def __init__(self):
        self.state = None
        self.states = {}
        self.paused_state = None

    def add(self, state):
        self.states[state.name] = state

    def go_to(self, state_name):
        if self.state:
            self.state.exit(self)
        self.state = self.states[state_name]
        self.state.enter(self)

    def upd(self):
        if self.state:
            self.state.upd(self)

################################################################################
# States

# Abstract parent state class.


class Ste(object):

    def __init__(self):
        pass

    @property
    def name(self):
        return ''

    def enter(self, mch):
        pass

    def exit(self, mch):
        pass

    def upd(self, mch):
        pass


class BseSt(Ste):

    def __init__(self):
        pass

    @property
    def name(self):
        return 'base_state'

    def enter(self, mch):
        ply_a_0("/sd/mvc/animations_are_now_active.wav")
        files.log_item("Entered base state")
        Ste.enter(self, mch)

    def exit(self, mch):
        Ste.exit(self, mch)

    def upd(self, mch):
        global c_run
        sw = utilities.switch_state(
            l_sw, r_sw, time.sleep, 3.0, ovrde_sw_st)
        if sw == "left_held" and not mix.voice[0].playing:
            if c_run:
                c_run = False
                stp_all_cmds()
                ply_a_0("/sd/mvc/continuous_mode_deactivated.wav")
            else:
                c_run = True
                ply_a_0("/sd/mvc/continuous_mode_activated.wav")
        elif (sw == "left" or c_run) and not mix.voice[0].playing:
            add_cmd(cfg["option_selected"])
        elif sw == "right":
            mch.go_to('main_menu')


class Main(Ste):

    def __init__(self):
        self.i = 0
        self.sel_i = 0

    @property
    def name(self):
        return 'main_menu'

    def enter(self, mch):
        ply_a_0("/sd/mvc/main_menu.wav")
        l_r_but()
        Ste.enter(self, mch)

    def exit(self, mch):
        Ste.exit(self, mch)

    def upd(self, mch):
        sw = utilities.switch_state(
            l_sw, r_sw, time.sleep, 3.0, ovrde_sw_st)
        if sw == "left":
            ply_a_0("/sd/mvc/" + m_mnu[self.i] + ".wav")
            self.sel_i = self.i
            self.i += 1
            if self.i > len(m_mnu)-1:
                self.i = 0
        if sw == "right":
            sel_mnu = m_mnu[self.sel_i]
            if sel_mnu == "choose_sounds":
                mch.go_to('choose_sounds')
            elif sel_mnu == "add_sounds_animate":
                mch.go_to('add_sounds_animate')
            elif sel_mnu == "light_string_setup_menu":
                mch.go_to('light_string_setup_menu')
            elif sel_mnu == "web_options":
                mch.go_to('web_options')
            elif sel_mnu == "volume_settings":
                mch.go_to('volume_settings')
            else:
                ply_a_0("/sd/mvc/all_changes_complete.wav")
                mch.go_to('base_state')


class Snds(Ste):

    def __init__(self):
        self.i = 0
        self.sel_i = 0

    @property
    def name(self):
        return 'choose_sounds'

    def enter(self, mch):
        files.log_item('Choose sounds menu')
        ply_a_0("/sd/mvc/sound_selection_menu.wav")
        l_r_but()
        Ste.enter(self, mch)

    def exit(self, mch):
        Ste.exit(self, mch)

    def upd(self, mch):
        sw = utilities.switch_state(
            l_sw, r_sw, time.sleep, 3.0, ovrde_sw_st)
        if sw == "left":
            if mix.voice[0].playing:
                mix.voice[0].stop()
                while mix.voice[0].playing:
                    pass
            else:
                try:
                    w0 = audiocore.WaveFile(open(
                        "/sd/snd_opt/option_" + mnu_o[self.i] + ".wav", "rb"))
                    mix.voice[0].play(w0, loop=False)
                except:
                    spk_sng_num(str(self.i+1))
                self.sel_i = self.i
                self.i += 1
                if self.i > len(mnu_o)-1:
                    self.i = 0
                while mix.voice[0].playing:
                    pass
        if sw == "right":
            if mix.voice[0].playing:
                mix.voice[0].stop()
                while mix.voice[0].playing:
                    pass
            else:
                cfg["option_selected"] = mnu_o[self.sel_i]
                files.write_json_file("/sd/cfg.json", cfg)
                w0 = audiocore.WaveFile(
                    open("/sd/mvc/option_selected.wav", "rb"))
                mix.voice[0].play(w0, loop=False)
                while mix.voice[0].playing:
                    pass
            mch.go_to('base_state')



class VolSet(Ste):

    def __init__(self):
        self.i = 0
        self.sel_i = 0

    @property
    def name(self):
        return 'volume_settings'

    def enter(self, mch):
        files.log_item('Set Web Options')
        ply_a_0("/sd/mvc/volume_settings_menu.wav")
        l_r_but()
        Ste.enter(self, mch)

    def exit(self, mch):
        Ste.exit(self, mch)

    def upd(self, mch):
        sw = utilities.switch_state(
            l_sw, r_sw, time.sleep, 3.0, ovrde_sw_st)
        if sw == "left":
            ply_a_0("/sd/mvc/" + v_s[self.i] + ".wav")
            self.sel_i = self.i
            self.i += 1
            if self.i > len(v_s)-1:
                self.i = 0
        if sw == "right":
            sel_mnu = v_s[self.sel_i]
            if sel_mnu == "volume_level_adjustment":
                ply_a_0("/sd/mvc/volume_adjustment_menu.wav")
                done = False
                while not done:
                    sw = utilities.switch_state(
                          l_sw, r_sw, time.sleep, 3.0, ovrde_sw_st)
                    if sw == "left":
                        ch_vol("lower")
                    elif sw == "right":
                        ch_vol("raise")
                    elif sw == "right_held":
                        files.write_json_file(
                            "/sd/cfg.json", cfg)
                        ply_a_0("/sd/mvc/all_changes_complete.wav")
                        done = True
                        mch.go_to('base_state')
                    upd_vol(0.1)
                    pass
            elif sel_mnu == "volume_pot_off":
                cfg["volume_pot"] = False
                if cfg["volume"] == 0:
                    cfg["volume"] = 10
                files.write_json_file("/sd/cfg.json", cfg)
                ply_a_0("/sd/mvc/all_changes_complete.wav")
                mch.go_to('base_state')
            elif sel_mnu == "volume_pot_on":
                cfg["volume_pot"] = True
                files.write_json_file("/sd/cfg.json", cfg)
                ply_a_0("/sd/mvc/all_changes_complete.wav")
                mch.go_to('base_state')



class Light(Ste):

    def __init__(self):
        self.i = 0
        self.sel_i = 0
        self.li = 0
        self.sel_li = 0
        self.a = False

    @property
    def name(self):
        return 'light_string_setup_menu'

    def enter(self, mch):
        files.log_item('Light string menu')
        ply_a_0("/sd/mvc/light_string_setup_menu.wav")
        l_r_but()
        Ste.enter(self, mch)

    def exit(self, mch):
        Ste.exit(self, mch)

    def upd(self, mch):
        sw = utilities.switch_state(
            l_sw, r_sw, time.sleep, 3.0, ovrde_sw_st)
        if self.a:
            if sw == "left":
                self.li -= 1
                if self.li < 0:
                    self.li = len(l_opt)-1
                self.sel_li = self.li
                ply_a_0("/sd/mvc/" + l_opt[self.li] + ".wav")
            elif sw == "right":
                self.li += 1
                if self.li > len(l_opt)-1:
                    self.li = 0
                self.sel_li = self.li
                ply_a_0("/sd/mvc/" + l_opt[self.li] + ".wav")
            elif sw == "left_held":
                files.write_json_file("/sd/cfg.json", cfg)
                upd_l_str()
                ply_a_0("/sd/mvc/all_changes_complete.wav")
                self.a = False
                mch.go_to('base_state')
            elif sw == "right_held":
                if cfg["light_string"] == "":
                    cfg["light_string"] = l_opt[self.sel_li]
                else:
                    cfg["light_string"] = cfg["light_string"] + \
                        "," + l_opt[self.sel_li]
                ply_a_0("/sd/mvc/" +
                        l_opt[self.sel_li] + ".wav")
                ply_a_0("/sd/mvc/added.wav")
            upd_vol(0.1)
        elif sw == "left":
            ply_a_0("/sd/mvc/" + l_mnu[self.i] + ".wav")
            self.sel_i = self.i
            self.i += 1
            if self.i > len(l_mnu)-1:
                self.i = 0
        elif sw == "right":
            sel_mnu = l_mnu[self.sel_i]
            if sel_mnu == "hear_light_setup_instructions":
                ply_a_0("/sd/mvc/string_instructions.wav")
            elif sel_mnu == "reset_lights_defaults":
                rst_l_def()
                ply_a_0("/sd/mvc/lights_reset_to.wav")
                spk_lght(False)
            elif sel_mnu == "hear_current_light_settings":
                spk_lght(True)
            elif sel_mnu == "clear_light_string":
                cfg["light_string"] = ""
                ply_a_0("/sd/mvc/lights_cleared.wav")
            elif sel_mnu == "add_lights":
                ply_a_0("/sd/mvc/add_light_menu.wav")
                self.a = True
            else:
                files.write_json_file("/sd/cfg.json", cfg)
                ply_a_0("/sd/mvc/all_changes_complete.wav")
                upd_l_str()
                mch.go_to('base_state')

###############################################################################
# Create the state machine


st_mch = StMch()
st_mch.add(BseSt())
st_mch.add(Main())
st_mch.add(Snds())
st_mch.add(VolSet())
st_mch.add(Light())

aud_mute.value = False

if (web):
    files.log_item("starting server...")
    try:
        server.start(str(wifi.radio.ipv4_address), port=80)
        files.log_item("Listening on http://%s:80" % wifi.radio.ipv4_address)
        spk_web()
    except OSError:
        time.sleep(5)
        files.log_item("restarting...")
        rst()

st_mch.go_to('base_state')
files.log_item("animator has started...")
gc_col("animations started.")

# Main task handling


async def process_cmd_tsk():
    """Task to continuously process commands."""
    while True:
        try:
            await process_cmd()  # Async command processing
        except Exception as e:
            files.log_item(e)
        await asyncio.sleep(0)  # Yield control to other tasks


async def server_poll_tsk(server):
    """Poll the web server."""
    while True:
        try:
            server.poll()  # Web server polling
        except Exception as e:
            files.log_item(e)
        await asyncio.sleep(0)  # Yield control to other tasks


async def state_mach_upd_task(st_mch):
    while True:
        st_mch.upd()
        await asyncio.sleep(0)


async def main():
    # Create asyncio tasks
    tasks = [
        process_cmd_tsk(),
        state_mach_upd_task(st_mch)
    ]

    if web:
        tasks.append(server_poll_tsk(server))

    # Run all tasks concurrently
    await asyncio.gather(*tasks)

# Run the asyncio event loop
try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass

