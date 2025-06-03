import os
import json

def log_item(item):
    print(item)

def print_directory(path, tabs=0):
    log_item_name = ""
    size_str = ""
    log_item("Files on filesystem:")
    log_item("====================")
    for file in os.listdir(path):
        stats = os.stat(path + "/" + file)
        filesize = stats[6]
        isdir = stats[0] & 0x4000

        if filesize < 1000:
            size_str = str(filesize) + " by"
        elif filesize < 1000000:
            size_str = "%0.1f KB" % (filesize / 1000)
        else:
            size_str = "%0.1f MB" % (filesize / 1000000)

        log_item_name = ""
        for _ in range(tabs):
            log_item_name += "   "
        log_item_name += file
        if isdir:
            log_item_name += "/"
        log_item('{0:<40} Size: {1:>10}'.format(log_item_name, size_str))

        # recursively files.log_item directory contents
        if isdir:
            print_directory(path + "/" + file, tabs + 1)

def return_directory(prefix, path, fileType):
    file_list = []
    for file in os.listdir(path):  
        if "._" not in file and fileType in file:
            file_name = prefix + file.replace(fileType, '')
            file_list.append(file_name)
    file_list.sort()
    return file_list
 
def write_file_lines(file_name, lines):
    with open(file_name, "w") as f:
        for line in lines:
            f.write(line + "\n")

def read_file_lines(file_name):
    with open(file_name, "r") as f:
        lines = f.readlines()
        output_lines = [] 
        for line in lines:
            output_lines.append(line.strip())
        return output_lines
    
def write_file_line(file_name, line):
    with open(file_name, "w") as f:
        f.write(line + "\n")

def read_file_line(file_name):
    with open(file_name, "r") as f:
        line = f.read()
        output_line=line.strip()
        return output_line
    
def json_stringify(python_dictionary):
    json_string = json.dumps(python_dictionary)
    return json_string

def json_parse(my_object):
    python_dictionary = json.loads(my_object)
    return python_dictionary

def write_json_file(file_name, python_dictionary):
    json_string=json_stringify(python_dictionary)
    write_file_line(file_name, json_string)
    
def read_json_file(file_name):
    json_string=read_file_line(file_name)
    python_dictionary=json_parse(json_string)
    return python_dictionary
