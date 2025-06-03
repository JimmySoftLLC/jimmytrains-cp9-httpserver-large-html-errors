def switch_state(l_sw, r_sw, upd_vol, h_down_sec, override_switch_state = None):
    if override_switch_state and override_switch_state["switch_value"]:
        return_parameter = override_switch_state["switch_value"]
        override_switch_state["switch_value"] = ""
        return return_parameter
    l_sw.update()
    r_sw.update()
    if l_sw.fell: 
        chk = True
        cyc = 0  
        while chk:
            upd_vol(.1)
            l_sw.update()
            cyc += 1
            if cyc > h_down_sec*10:
                return "left_held" 
            if l_sw.rose:
                print ("left pressed")
                return "left" 
    if r_sw.fell:
        chk = True
        cyc = 0  
        while chk:
            upd_vol(.1)
            r_sw.update()
            cyc += 1
            if cyc > h_down_sec*10:
                return "right_held" 
            if r_sw.rose:
                print ("right pressed")
                return "right"
    if not l_sw.value:
        chk = True
        cyc = 0  
        while chk:
            upd_vol(.1)
            l_sw.update()
            cyc += 1
            if cyc > h_down_sec*10:
                return "left_held" 
            if l_sw.rose:
                return "none"
    if not r_sw.value:
        chk = True
        cyc = 0  
        while chk:
            upd_vol(.1)
            r_sw.update()
            cyc += 1
            if cyc > h_down_sec*10:
                return "right_held" 
            if r_sw.rose:
                return "none"
    upd_vol(0.1)
    return "none"

def switch_state_four_switches(l_sw, r_sw, three_sw, four_sw, upd_vol, h_down_sec, override_switch_state = None):
    if override_switch_state and override_switch_state["switch_value"]:
        return_parameter = override_switch_state["switch_value"]
        override_switch_state["switch_value"] = ""
        return return_parameter
    l_sw.update()
    r_sw.update()
    three_sw.update()
    four_sw.update()
    if l_sw.fell: 
        chk = True
        cyc = 0  
        while chk:
            upd_vol(.1)
            l_sw.update()
            cyc += 1
            if cyc > h_down_sec*10:
                return "left_held" 
            if l_sw.rose:
                print ("left pressed")
                return "left" 
    if r_sw.fell:
        chk = True
        cyc = 0  
        while chk:
            upd_vol(.1)
            r_sw.update()
            cyc += 1
            if cyc > h_down_sec*10:
                return "right_held" 
            if r_sw.rose:
                print ("right pressed")
                return "right"
    if three_sw.fell:
        chk = True
        cyc = 0  
        while chk:
            upd_vol(.1)
            three_sw.update()
            cyc += 1
            if cyc > h_down_sec*10:
                return "three_held" 
            if three_sw.rose:
                print ("three pressed")
                return "three"
    if four_sw.fell:
        chk = True
        cyc = 0  
        while chk:
            upd_vol(.1)
            four_sw.update()
            cyc += 1
            if cyc > h_down_sec*10:
                return "four_held" 
            if four_sw.rose:
                print ("four pressed")
                return "four"
    if not l_sw.value:
        chk = True
        cyc = 0  
        while chk:
            upd_vol(.1)
            l_sw.update()
            cyc += 1
            if cyc > h_down_sec*10:
                return "left_held" 
            if l_sw.rose:
                return "none"
    if not r_sw.value:
        chk = True
        cyc = 0  
        while chk:
            upd_vol(.1)
            r_sw.update()
            cyc += 1
            if cyc > h_down_sec*10:
                return "right_held" 
            if r_sw.rose:
                return "none"
    if not three_sw.value:
        chk = True
        cyc = 0  
        while chk:
            upd_vol(.1)
            three_sw.update()
            cyc += 1
            if cyc > h_down_sec*10:
                return "three_held" 
            if three_sw.rose:
                return "none"        
    if not four_sw.value:
        chk = True
        cyc = 0  
        while chk:
            upd_vol(.1)
            four_sw.update()
            cyc += 1
            if cyc > h_down_sec*10:
                return "four_held" 
            if four_sw.rose:
                return "none"   
    upd_vol(0.1)
    return "none"