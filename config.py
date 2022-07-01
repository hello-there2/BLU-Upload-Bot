#!/usr/bin/python3.8

# Imports and requirements
import re
from pathlib import Path
import sys
from configparser import ConfigParser, ExtendedInterpolation, DuplicateSectionError
import constants, helpers
import argparse
from classes import SmartFormatter

parser = argparse.ArgumentParser(
    description="Interface to edit a config file and generate one.",
    formatter_class=SmartFormatter,
)

parser.add_argument(
    "--config",
    dest="config_path",
    default=constants.CONFIG_PATH,
    type=str,
    help=f"Config file path, used for when not in default location {constants.CONFIG_PATH}",
)

parser.add_argument(
    "command",
    type=str,
    metavar="Command",
    help="Command to run: Print | Generate | Browse",
)
command_list = ["print", "generate", "browse"]

# read arguments from the command line
args = parser.parse_args()
config = ConfigParser(interpolation=ExtendedInterpolation())
UNSAVED = False


def quit(conf):
    global UNSAVED
    helpers.cls()
    if UNSAVED:
        print("There are some unsaved changes...")
        if helpers.check_string_boolean(input("Would you like to save?: ")):
            save(conf)


def save(conf):
    global UNSAVED
    UNSAVED = False
    with open(f"{args.config_path}", "w") as configfile:
        conf.write(configfile)
    input(f"\nChanges saved... Press Enter to continue...")


def generate_config(conf):
    global UNSAVED
    UNSAVED = True
    conf.read("DEFAULT.ini")
    conf["DEFAULT"]["Client"] = "Watch" if helpers.is_windows() else "rTorrent"
    conf["Paths"]["Home"] = str(Path.home())
    print_config(conf)
    return conf


def set_value(config, section, variable, value):
    global UNSAVED
    UNSAVED = True
    config[section][variable] = value


def add_tracker(conf):
    global UNSAVED
    UNSAVED = True
    helpers.cls()
    tracker_name = input("Tracker: ")
    try:
        if not tracker_name:
            print("No tracker given... returning...")
            return
        conf.add_section(tracker_name)
        print(f"\nFill out each that are needed, unneeded ones just press enter")
        print(f"-----------------------------------------------------\n")
        PID = input("PID: ")
        API_Key = input("API Key: ")
        API_User = input("API User: ")
        API_Endpoint = input("API Endpoint: ")
        Username = input("Username (For ones using this to login): ")
        Announce = input("Announce URL (${PID} can be used for the PID): ")
        Torrent_Source = input("Source flag (for .torrent): ")
        Auto = input("Auto (True/False for auto searching a release): ")
        Add_Custom = input("Add Custom Sections?: ")
        # Add the ones filled out.
        if PID:
            # PID sets it both as Passkey and PID, some use that naming.
            conf[tracker_name]["PID"] = PID
            conf[tracker_name]["Passkey"] = PID
        if API_Key:
            conf[tracker_name]["API Key"] = API_Key
        if API_User:
            conf[tracker_name]["API User"] = API_User
        if API_Endpoint:
            conf[tracker_name]["API Endpoint"] = API_Endpoint
        if Announce:
            conf[tracker_name]["Announce"] = Announce
        if Torrent_Source:
            conf[tracker_name]["Torrent Source"] = Torrent_Source
        if Auto:
            conf[tracker_name]["Auto"] = (
                "True" if helpers.check_string_boolean(Auto) else "False"
            )
        if helpers.check_string_boolean(Add_Custom):
            edit_option_sections(conf, tracker_name)
    except DuplicateSectionError:
        print("Section already exists... Use edit tracker...")
        input("Press Enter to continue...")


def print_config(conf, section=""):
    section_list = ["DEFAULT"] + conf.sections()
    if section in section_list:
        section_list = [section]
    for section in section_list:
        print_section_key_value(conf, section)


def print_section_key_value(conf, section):
    print(f"[{section}]")
    for key in conf[section]:
        val = conf[section][key]
        print(f"{key} = {val}")
    print("")


def print_section_keys(conf, section, val=False):
    key_num = 1
    keys = []
    for key in conf[section]:
        val = conf[section][key]
        if val:
            val = conf[section][key]
            print(f"{key_num}) {key} = {val}")
        else:
            print(f"{key_num}) {key} = ")
        key_num += 1
        keys += [key]
    print("")
    return keys


def browse(conf, invalid=False, invalid_option=""):
    helpers.cls()
    if invalid:
        print(f"{invalid_option} is not a valid selection, please try again...\n\n")
    print(f"Browsing config file: {args.config_path}\n")
    print(f"Select an option...\n")
    print(
        f"1) Print all\n2) Paths\n3) Trackers\n4) Image Hosts\n5) Groups\n\nSave)\nExit)\n\n"
    )
    selection = input("Selection: ").lower()
    exit_options = ["", "e", "exit"]
    save_options = ["s", "save"]
    valid_options = [f"{x}" for x in range(1, 6)] + exit_options + save_options
    if selection not in valid_options:
        conf = browse(conf, invalid=True, invalid_option=selection)
    if selection in save_options:
        save(conf)
    if selection in exit_options:
        print("\nExiting...")
        quit(conf)
        exit()
    if selection == "1":
        print_config(conf)
        input("Press Enter to continue...")
    elif selection == "2":
        browse_paths(conf)
    elif selection == "3":
        browse_trackers(conf)
    elif selection == "4":
        browse_image_hosts(conf)
    elif selection == "5":
        browse_groups(conf)
    browse(conf)


def browse_paths(conf, invalid=False, invalid_option=""):
    global UNSAVED
    helpers.cls()
    if invalid:
        print(f"{invalid_option} is not a valid selection, please try again...\n\n")
    print(f"Browsing Paths for config file: {args.config_path}\n")
    print(f"Select an option...\n")
    print(f"1) Print\n2) Edit Path(s)\n3) Remove Path\n\nBack)\nSave)\nExit)\n\n")
    selection = input("Selection: ").lower()
    exit_options = ["e", "exit"]
    save_options = ["s", "save"]
    back_options = ["", "b", "back", "r", "return"]
    valid_options = (
        [f"{x}" for x in range(1, 5)] + exit_options + back_options + save_options
    )
    if selection not in valid_options:
        browse_trackers(conf, invalid=True, invalid_option=selection)
    if selection in exit_options:
        print("\nExiting...")
        quit(conf)
        exit()
    if selection in save_options:
        save(conf)
        browse_trackers(conf)
    if selection in back_options:
        return conf
    print()
    if selection in ["1", "2"]:
        paths = print_section_keys(conf, "Paths", val=True)
    if selection == "1":
        input(f"\nPress Enter to continue...")
    elif selection == "2":
        conf = edit_option_sections(conf, "Paths", paths)
    elif selection == "3":
        conf = remove_option(conf, "Paths")
        input(f"\nPress Enter to continue...")

    browse_paths(conf)


def browse_trackers(conf, invalid=False, invalid_option=""):
    global UNSAVED
    helpers.cls()
    if invalid:
        print(f"{invalid_option} is not a valid selection, please try again...\n\n")
    print(f"Browsing Trackers for config file: {args.config_path}\n")
    print(f"Select an option...\n")
    print(
        f"1) Print\n2) Add new tracker\n3) Edit tracker\n4) Remove tracker\n\nBack)\nSave)\nExit) Exit\n\n"
    )
    selection = input("Selection: ").lower()
    exit_options = ["e", "exit"]
    save_options = ["s", "save"]
    back_options = ["", "b", "back", "r", "return"]
    valid_options = (
        [f"{x}" for x in range(1, 5)] + exit_options + back_options + save_options
    )
    if selection not in valid_options:
        browse_trackers(conf, invalid=True, invalid_option=selection)
    if selection in exit_options:
        print("\nExiting...")
        quit(conf)
        exit()
    if selection in save_options:
        save(conf)
        browse_trackers(conf)
    if selection in back_options:
        return conf
    trackers = print_trackers(conf)
    if selection == "1":
        selection = input(f"\nPress Enter to continue...")
    if selection == "2":
        add_tracker(conf)
    if selection == "3":
        tracker_selection = input(f"\nWhich tracker do you want to edit?: ")
        if tracker_selection.isnumeric() and 0 < int(tracker_selection) <= len(
            trackers
        ):
            conf = edit_tracker(conf, trackers[int(tracker_selection) - 1])
    if selection == "4":
        UNSAVED = True
        tracker_selection = input(f"\nWhich tracker do you want to remove?: ")
        if tracker_selection.isnumeric() and 0 < int(tracker_selection) <= len(
            trackers
        ):
            UNSAVED = True
            conf.remove_section(trackers[int(tracker_selection) - 1])
        input(f"\nPress Enter to continue...")
    browse_trackers(conf)


def edit_tracker(conf, tracker, invalid=False, invalid_option=""):
    global UNSAVED
    helpers.cls()
    if invalid:
        print(f"{invalid_option} is not a valid selection, please try again...\n\n")
    print(f'Browsing Tracker "{tracker}" for config file: {args.config_path}\n')
    print(f"Select an option...\n")
    print(
        f"1) Print\n2) Add/Edit option\n3) Remove option\n\nBack)\nSave)\nExit) Exit\n\n"
    )
    selection = input("Selection: ").lower()
    exit_options = ["e", "exit"]
    save_options = ["s", "save"]
    back_options = ["", "b", "back", "r", "return"]
    valid_options = (
        [f"{x}" for x in range(1, 4)] + exit_options + back_options + save_options
    )
    if selection not in valid_options:
        edit_tracker(conf, tracker, invalid=True, invalid_option=selection)
    if selection in exit_options:
        print("\nExiting...")
        quit(conf)
        exit()
    if selection in save_options:
        save()
    if selection in back_options:
        return conf
    if selection == "1":
        print_config(conf, tracker)
        input(f"\nPress Enter to continue...")
    if selection == "2":
        print()
        conf = edit_option_section(conf, tracker)
        input(f"\nPress Enter to continue...")
    if selection == "3":
        conf = remove_option(conf, tracker)
        input(f"\nPress Enter to continue...")
    conf = edit_tracker(conf, tracker)


def browse_image_hosts(conf, invalid=False, invalid_option=""):
    global UNSAVED
    helpers.cls()
    if invalid:
        print(f"{invalid_option} is not a valid selection, please try again...\n\n")
    print(f"Browsing Image Hosts for config file: {args.config_path}\n")
    print(f"Select an option...\n")
    print(
        f"1) Print\n2) Add new Image Host\n3) Edit Image Host\n4) Remove Image Host\n\nBack)\nSave)\nExit) Exit\n\n"
    )
    selection = input("Selection: ").lower()
    exit_options = ["e", "exit"]
    save_options = ["s", "save"]
    back_options = ["", "b", "back", "r", "return"]
    valid_options = (
        [f"{x}" for x in range(1, 5)] + exit_options + back_options + save_options
    )
    if selection not in valid_options:
        browse_trackers(conf, invalid=True, invalid_option=selection)
    if selection in exit_options:
        print("\nExiting...")
        quit(conf)
        exit()
    if selection in save_options:
        save(conf)
        conf = browse_image_hosts(conf)
    if selection in back_options:
        return conf
    if selection in ["1", "3", "4"]:
        hosts = print_image_hosts(conf)
    if selection == "1":
        selection = input(f"\nPress Enter to continue...")
    if selection == "2":
        conf = add_image_host(conf)
    if selection == "3":
        image_selection = input(f"\nWhich tracker do you want to edit?: ")
        if image_selection.isnumeric() and 0 < int(image_selection) <= len(trackers):
            conf = edit_tracker(conf, trackers[int(image_selection) - 1])  # Todo
    if selection == "4":
        UNSAVED = True
        image_selection = input(f"\nWhich tracker do you want to remove?: ")
        if image_selection.isnumeric() and 0 < int(image_selection) <= len(trackers):
            UNSAVED = True
            conf.remove_section(trackers[int(image_selection) - 1])
        input(f"\nPress Enter to continue...")
    conf = browse_image_hosts(conf)


def add_image_host(conf):
    global UNSAVED
    UNSAVED = True
    helpers.cls()
    image_host_name = input("Image Host: ").replace("Image_", "")
    try:
        if not image_host_name:
            print("No Image Host given... returning...")
            return
        section_name = "Image_" + image_host_name
        conf.add_section(section_name)
        print(f"\nFill out each that are needed, unneeded ones just press enter")
        print(f"-----------------------------------------------------\n")
        API_Key = input("API Key: ")
        API_User = input("API User: ")
        Username = input("Username: ")
        Password = input("Password: ")
        Add_Custom = input("Add Custom Sections?: ")
        if API_Key:
            conf[section_name]["API Key"] = API_Key
        if API_User:
            conf[section_name]["API User"] = API_User
        if Username:
            conf[section_name]["Username"] = Username
        if Password:
            conf[section_name]["Password"] = Password
        if helpers.check_string_boolean(Add_Custom):
            add_image_host = edit_option_sections(conf, section_name)
    except DuplicateSectionError:
        print("Section already exists... Use edit host...")
        input("Press Enter to continue...")
    return conf


def edit_group(conf, group, invalid=False, invalid_option=""):
    global UNSAVED
    helpers.cls()
    if invalid:
        print(f"{invalid_option} is not a valid selection, please try again...\n\n")
    print(f'Browsing Group "{group}" for config file: {args.config_path}\n')
    print(f"Select an option...\n")
    print(
        f"1) Print\n2) Add/Edit option\n3) Remove option\n\nBack)\nSave)\nExit) Exit\n\n"
    )
    selection = input("Selection: ").lower()
    exit_options = ["e", "exit"]
    save_options = ["s", "save"]
    back_options = ["", "b", "back", "r", "return"]
    valid_options = (
        [f"{x}" for x in range(1, 4)] + exit_options + back_options + save_options
    )
    if selection not in valid_options:
        edit_tracker(conf, tracker, invalid=True, invalid_option=selection)
    if selection in exit_options:
        print("\nExiting...")
        quit(conf)
        exit()
    if selection in save_options:
        save()
    if selection in back_options:
        return conf
    if selection == "1":
        print_config(conf, group)
        input(f"\nPress Enter to continue...")
    if selection == "2":
        group_keys = print_section_keys(conf, group, val=True)
        conf = edit_option_section(conf, group, section_list=group_keys)
        input(f"\nPress Enter to continue...")
    if selection == "3":
        group_keys = print_section_keys(conf, group, val=False)
        conf = remove_option(conf, group, section_list=group_keys)
        input(f"\nPress Enter to continue...")
    conf = edit_group(conf, group)


def add_group(conf):
    global UNSAVED
    UNSAVED = True
    helpers.cls()
    group_name = input("Group: ").replace("_Group", "")
    try:
        if not group_name:
            print("No Group given... returning...")
            return
        section_name = group_name + "_Group"
        conf.add_section(section_name)
        print(f"\nFill out each that are needed, unneeded ones just press enter")
        print(f"-----------------------------------------------------\n")
        anonymous = input("Anonymous: ")
        free = input("Freeleech: ")
        double = input("Double Upload: ")
        internal = input("Internal: ")
        description = input("Description (Use <br> for new lines): ")
        Add_Custom = input("Add Custom Sections?: ")
        if anonymous:
            conf[section_name]["Anonymous"] = (
                "True" if helpers.check_string_boolean(anonymous) else "False"
            )
        if free:
            conf[section_name]["Freeleech"] = (
                "True" if helpers.check_string_boolean(free) else "False"
            )
        if double:
            conf[section_name]["Double Up"] = (
                "True" if helpers.check_string_boolean(double) else "False"
            )
        if internal:
            conf[section_name]["Internal"] = (
                "True" if helpers.check_string_boolean(internal) else "False"
            )
        if description:
            conf[section_name]["Description"] = description
        if helpers.check_string_boolean(Add_Custom):
            add_image_host = edit_option_sections(conf, section_name)
    except DuplicateSectionError:
        print("Section already exists... Use edit host...")
        input("Press Enter to continue...")
    return conf


def browse_groups(conf, invalid=False, invalid_option=""):
    global UNSAVED
    helpers.cls()
    if invalid:
        print(f"{invalid_option} is not a valid selection, please try again...\n\n")
    print(f"Browsing Groups for config file: {args.config_path}\n")
    print(f"Select an option...\n")
    print(
        f"1) Print\n2) Add new Group\n3) Edit Group\n4) Remove Group\n\nBack)\nSave)\nExit) Exit\n\n"
    )
    selection = input("Selection: ").lower()
    exit_options = ["e", "exit"]
    save_options = ["s", "save"]
    back_options = ["", "b", "back", "r", "return"]
    valid_options = (
        [f"{x}" for x in range(1, 5)] + exit_options + back_options + save_options
    )
    if selection not in valid_options:
        browse_groups(conf, invalid=True, invalid_option=selection)
    if selection in exit_options:
        print("\nExiting...")
        quit(conf)
        exit()
    if selection in save_options:
        save(conf)
        conf = browse_groups(conf)
    if selection in back_options:
        return conf
    if selection in ["1", "3", "4"]:
        groups = print_groups(conf)
    if selection == "1":
        selection = input(f"\nPress Enter to continue...")
    if selection == "2":
        conf = add_group(conf)
    if selection == "3":
        group_selection = input(f"\nWhich Group do you want to edit?: ")
        if group_selection.isnumeric() and 0 < int(group_selection) <= len(groups):
            conf = edit_group(conf, groups[int(group_selection) - 1])  # Tracker
    if selection == "4":
        UNSAVED = True
        selection = input(f"\nWhich Group do you want to remove?: ")
        if group_selection.isnumeric() and 0 < int(group_selection) <= len(trackers):
            UNSAVED = True
            conf.remove_section(groups[int(group_selection) - 1])
        input(f"\nPress Enter to continue...")
    conf = browse_groups(conf)


def remove_option(conf, section):
    keys = conf[section].keys()
    print(f"\nOptions: {list(keys)}")
    remove = input(f"\nWhich option do you want to remove?: ")
    if remove:
        UNSAVED = True
        conf.remove_option(section, remove)
    return conf


def edit_option_sections(conf, section, section_list=[]):
    print(f'\nTo stop adding new sections do not input a "Key" and just press enter')
    old_conf = conf
    while True:
        conf = edit_option_section(conf, section, section_list)
        if old_conf == conf:
            break
        old_conf = conf
    return conf


def edit_option_section(conf, section, section_list=[]):
    global UNSAVED
    UNSAVED = True
    if section_list != []:
        Section_Key = input("Key (number from list or name): ")
    else:
        Section_Key = input("Key: ")
    if not Section_Key:
        return conf
    try:
        Section_Val = input(f"Value for {section_list[int(Section_Key)-1]}: ")
        conf[section][section_list[int(Section_Key) - 1]] = Section_Val
    except:
        Section_Val = input(f"Value for {Section_Key}: ")
        conf[section][Section_Key] = Section_Val
    return conf


def print_trackers(conf):
    trackers = conf.sections()
    trackers.remove("Paths")
    trackers.remove("qBittorrent")
    trackers = filter(lambda x: not x.endswith("_Group"), trackers)
    trackers = filter(lambda x: not x.startswith("Image_"), trackers)
    trackers = list(trackers)
    if not trackers:
        print("No trackers in the config file...  Think about adding one...")
    else:
        helpers.cls()
        print_sections(trackers, section_name="tracker")
    return trackers


def print_image_hosts(conf):
    hosts = filter(lambda x: x.startswith("Image_"), conf.sections())
    hosts = list(hosts)
    if not hosts:
        print("No Image Hosts in the config file...  Think about adding one...")
    else:
        helpers.cls()
        print_sections(hosts, section_name="Image Host", remove="Image_")
    return hosts


def print_groups(conf):
    hosts = filter(lambda x: x.endswith("_Group"), conf.sections())
    hosts = list(hosts)
    if not hosts:
        print("No Groups in the config file...  Think about adding one...")
    else:
        helpers.cls()
        print_sections(hosts, section_name="Group", remove="_Group")
    return hosts


def print_sections(sections, section_name="section", remove=""):
    section_num = 1
    helpers.cls()
    print(f"Availiable {section_name}s...\n")
    for section in sections:
        print(f"{section_num}) {section}".replace(remove, ""))
        section_num += 1


args.command = args.command.lower()
if args.command.lower() not in command_list:
    print(f"Invalid command given...")

if args.command == "generate":
    if Path(args.config_path).exists():
        print(f'Config file already exists... Use edit...\n"{args.config_path}"')
        exit()
    conf = generate_config(config)
    save(conf)
    exit()

config = ConfigParser()
assert Path(args.config_path).exists()
config.read(args.config_path)

if args.command == "print":
    print_config(config)
if args.command == "browse":
    browse(config)
