# coding=utf-8

from __future__ import absolute_import
import datetime
import getpass
import os
import shlex
import socket
import subprocess
import time

import octoprint.plugin
import octoprint.util
from octoprint.timelapse import Timelapse as timelapse
from octoprint.settings import settings

class SignalNotifierPlugin(octoprint.plugin.EventHandlerPlugin,
                               octoprint.plugin.SettingsPlugin,
                               octoprint.plugin.AssetPlugin,
                               octoprint.plugin.TemplatePlugin):

    ## Helpers    
    def is_exe(self, fpath):
        if os.path.isfile(fpath) and os.access(fpath, os.X_OK):
            return True
        return False

    def run_command(self, cmd):
        parsed_cmd = shlex.split(cmd)     
        proc = subprocess.Popen(parsed_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, _err = proc.communicate()
        return (proc.returncode, out.rstrip())

    #~~ SettingsPlugin
    def get_settings_defaults(self):
        return dict(
            # TODO: remove enabled (now we have individual settings)
            enabled=False,
            enabled_done=False,
            enabled_paused=False,
            path="/usr/local/bin/signal-cli",
            sender="",
            recipient="",
            message_format=dict(
                body="OctoPrint@{host}: {filename}: Job complete after {elapsed_time}."
            ),
            paused_message_format=dict(
                body="OctoPrint@{host}: {filename}: Job paused!"
            ),
            send_snapshot=False
        )

    def get_settings_restricted_paths(self):
        return dict(admin=[["path"], ["sender"], ["recipient"]],
                    user=[["message_format", "body"],
                          ["paused_message_format", "body"],
                          ["send_snapshot"],
                          ],
                    never=[])

    def get_settings_version(self):
        return 2

    #~~ TemplatePlugin
    def get_template_configs(self):
        return [dict(type="settings", name="Signal Notifier", custom_bindings=False)]

    def on_settings_migrate(self, target, current):
        if current == 1 and target == 2:
            if self._settings.get_boolean(['enabled']):
                self._settings.set(['enabled_paused'], True)
                self._settings.set(['enabled_done'], True)

    #~~ EventPlugin
    def on_event(self, event, payload):
        # self._logger.info("TESTING: event is %s: %s" % (event, payload))

        if not self.configuration_ok():
            return

        if event == "PrintDone":
            if self._settings.get(['enabled_done']):
                self.handle_event_type(event, payload, 'done')
        elif event == 'PrintPaused':
            if self._settings.get(['enabled_paused']):
                self.handle_event_type(event, payload, 'paused')

    ##~~ Softwareupdate hook
    def get_update_information(self):
        return dict(
            signalnotifier=dict(
                displayName=self._plugin_name,
                displayVersion=self._plugin_version,
                current=self._plugin_version,

                # version check: github repository
                #type="github_release",
                type="github_commit",
                user="aerickson",
                repo="OctoPrint_Signal-Notifier",
                branch="master",

                # update method: pip
                # - release
                #pip="https://github.com/aerickson/OctoPrint_Signal-Notifier/archive/{target_version}.zip"
                # - master tarball
                pip="https://github.com/aerickson/OctoPrint_Signal-Notifier/archive/{target}.zip"
            )
        )

    # TODO: pull out to util lib for easy testing (requiring octoprint is annoying)
    def generate_command(self, path, sender, message, recipient, attachment):
        # basic
        #   ./signal-cli -u +4915151111111 send -m "My first message from the CLI" +4915152222222
        # group
        #   ./signal-cli -u +4915151111111 send -g <group_id> -m "My first message from the CLI to a group"

        attachment_argument = ""
        if attachment:
            attachment_argument = "-a \"%s\"" % attachment

        group_string = ""
        recipient_string = ""
        # if a single recipient
        if recipient[:1] == "+":
            recipient_string = recipient
        # if a group
        else:
            group_string = "-g %s" % (recipient)

        the_command = "%s -u %s send %s %s -m \"%s\" %s" % (
            path, sender, group_string, attachment_argument, message, recipient_string)

        return the_command

    def send_message(self, path, sender, message, recipient, attachment):
        the_command = self.generate_command(path, sender, message, recipient, attachment)

        self._logger.info("Command plugin will run is: '%s'" % the_command)
        try:
            rc, osstdout = self.run_command(the_command)
        # TODO: catch subprocess.CalledProcessError vs generic error?
        except Exception as e:
            # report problem sending message
            self._logger.exception("Signal notification error: %s" % (str(e)))
        else:
            if rc != 0:
                self._logger.error("Command exited with a non-zero exit code!")
                self._logger.error("Command: '%s'" % the_command)
                self._logger.error("Command output: '%s'" % osstdout)
                return False
            return True

    def configuration_ok(self):
        # load config data
        path = self._settings.get(["path"])
        sender = self._settings.get(["sender"])
        recipient = self._settings.get(["recipient"])

        # check that path is a valid executable
        if not self.is_exe(path):
            self._logger.error("The path to signal-cli ('%s') doesn't point at an executable!" % path)
            return False

        # check that sender is defined
        if sender.strip() == '':
            self._logger.error("The sender ('%s') seems empty!" % sender)
            return False

        # check that recipient is defined
        if recipient.strip() == '':
            self._logger.error("The recipient ('%s') seems empty!" % recipient)
            return False

        # check that sender is in list of valid senders?
        # - disabled as it takes so long...
        #
        # list_identities_cmd = "%s -u %s listIdentities" % (path, sender)
        # rc, osstdout = self.run_command(list_identities_cmd)
        # if rc != 0:
        #     self._logger.error("The sender ('%s') is not registered!" % sender)
        #     self._logger.error("Command: '%s'" % list_identities_cmd)
        #     self._logger.error("Command output: '%s'" % osstdout)
        #     return False

        return True

    def handle_event_type(self, event, payload, type):
        filename = payload["name"]
        tags = {'filename': filename,
                'elapsed_time': None,
                'host': socket.gethostname(),
                'user': getpass.getuser()}

        if type == 'done':
            # payload only has time for done events
            elapsed_time = octoprint.util.get_formatted_timedelta(datetime.timedelta(seconds=payload["time"]))
            tags['elapsed_time'] = elapsed_time

            message = self._settings.get(["message_format", "body"]).format(**tags)
        elif type == 'paused':
            message = self._settings.get(["paused_message_format", "body"]).format(**tags)
        else:
            self._logger.error("handle_event_type: unknown event type ('%s')" % type)

        path = self._settings.get(["path"])
        sender = self._settings.get(["sender"])
        recipient = self._settings.get(["recipient"])
        send_snapshot = self._settings.get(["send_snapshot"])

        snapshot_file = None
        if send_snapshot:
            # TODO: use octoprint.plugin.PluginSettings per
            #   http://docs.octoprint.org/en/master/modules/plugin.html?highlight=_settings#octoprint.plugin.PluginSettings

            # self._logger.info("snapshot url: %s" % settings().get(["webcam", "snapshot"]))
            # only try to grab a snapshot if the url has been configured
            if settings().get(["webcam", "snapshot"]):
                tl = timelapse()
                tl._image_number = 0
                tl._capture_errors = 0
                tl._capture_success = 0
                tl._in_timelapse = True
                tl._file_prefix = time.strftime("%Y%m%d%H%M%S")
                snapshot_file = tl.capture_image()
            else:
                self._logger.info("Please configure the webcam before enabling snapshots!")

        send_successful = self.send_message(path, sender, message, recipient, snapshot_file)
        if send_successful:
            self._logger.info("Notification (%s) sent to %s." % (type, recipient))


__plugin_name__ = "Signal Notifier"
__plugin_pythoncompat__ = ">=2.7,<4"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = SignalNotifierPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
