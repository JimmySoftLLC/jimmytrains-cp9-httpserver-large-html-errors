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
import microcontroller
import asyncio


def gc_col(c_p):
    #gc.collect()
    start_mem = gc.mem_free()
    files.log_item("Point " + c_p +
                   " Available memory: {} bytes".format(start_mem))


def rst():
    microcontroller.on_next_reset(microcontroller.RunMode.NORMAL)
    microcontroller.reset()


gc_col("Imports gc, files")

sd_loc = "sim_sd/"

################################################################################
# Sd card data Variables

cfg = files.read_json_file(sd_loc + "cfg.json")

snd_o = files.return_directory("", sd_loc + "snd", ".wav")

cus_o = files.return_directory(
    "customers_owned_music_", sd_loc + "customers_owned_music", ".wav")

all_o = []
all_o.extend(snd_o)
all_o.extend(cus_o)

mnu_o = []
mnu_o.extend(snd_o)
rnd_o = ['random all', 'random built in', 'random my']
mnu_o.extend(rnd_o)
mnu_o.extend(cus_o)

ts_json = files.return_directory(
    "", sd_loc + "t_s_def", ".json")

web = cfg["serve_webpage"]

c_run = False
ts_mode = False

local_ip = ""

ovrde_sw_st = {}
ovrde_sw_st["switch_value"] = ""

gc_col("config setup")

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
        env = files.read_json_file(sd_loc + "env.json")
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
            return FileResponse(req, sd_loc + "mui.min.css", "/")

        @server.route("/mui.min.js")
        def base(req: HTTPRequest):
            return FileResponse(req, sd_loc + "mui.min.js", "/")

        @server.route("/animation", [POST])
        def btn(req: Request):
            global cfg, c_run, ts_mode
            rq_d = req.json()
            cfg["option_selected"] = rq_d["an"]
            files.write_json_file(sd_loc + "cfg.json", cfg)
            return Response(req, "Animation " + cfg["option_selected"] + " started.")

        @server.route("/defaults", [POST])
        def btn(req: Request):
            global cfg
            rq_d = req.json()
            if rq_d["an"] == "reset_animation_timing_to_defaults":
                for ts_fn in ts_json:
                    ts = files.read_json_file(
                        sd_loc + "t_s_def/" + ts_fn + ".json")
                    files.write_json_file(
                        sd_loc + "snd/"+ts_fn+".json", ts)
            elif rq_d["an"] == "reset_to_defaults":
                files.write_json_file(sd_loc + "cfg.json", cfg)
            elif rq_d["an"] == "reset_incandescent_colors":
                files.write_json_file(sd_loc + "cfg.json", cfg)
                s = files.json_stringify(
                    {"bars": cfg["bars"], "bolts": cfg["bolts"], "v": cfg["v"]})
                return Response(req, s)
            elif rq_d["an"] == "reset_white_colors":
                files.write_json_file(sd_loc + "cfg.json", cfg)
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
                files.write_json_file(sd_loc + "cfg.json", cfg)
            elif rq_d["an"] == "volume_pot_on":
                cfg["volume_pot"] = True
                files.write_json_file(sd_loc + "cfg.json", cfg)
            return Response(req, "Utility: " + rq_d["an"])

        @server.route("/lights", [POST])
        def btn(req: Request):
            rq_d = req.json()
            return Response(req, "OK")

        @server.route("/bolt", [POST])
        def btn(req: Request):
            return Response(req, "OK")

        @server.route("/bar", [POST])
        def btn(req: Request):
            return Response(req, "OK")

        @server.route("/bright", [POST])
        def btn(req: Request):
            rq_d = req.json()
            return Response(req, "OK")

        @server.route("/update-host-name", [POST])
        def btn(req: Request):
            global cfg
            rq_d = req.json()
            cfg["HOST_NAME"] = rq_d["text"]
            files.write_json_file(sd_loc + "cfg.json", cfg)
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
                files.write_json_file(sd_loc + "cfg.json", cfg)
                return Response(req, cfg["light_string"])
            if cfg["light_string"] == "":
                cfg["light_string"] = rq_d["text"]
            else:
                cfg["light_string"] = cfg["light_string"] + \
                    "," + rq_d["text"]
            print("action: " + rq_d["action"] +
                  " data: " + cfg["light_string"])
            files.write_json_file(sd_loc + "cfg.json", cfg)
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

