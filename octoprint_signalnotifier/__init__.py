# coding=utf-8

from __future__ import absolute_import
import datetime
import getpass
import octoprint.plugin
import octoprint.util
import os
import shlex
import socket
import subprocess

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
            enabled=False,
            path="signal-cli",
            sender="",
            recipient="",
            message_format=dict(
                body="OctoPrint@{host}: Job complete: {filename} done printing after {elapsed_time}." 
            )
        )

    def get_settings_restricted_paths(self):
        return dict(admin=[["path"], ["sender"], ["recipient"]],
                    user=[["message_format", "body"]],
                    never=[])        

    def get_settings_version(self):
        return 1

    #~~ TemplatePlugin
    def get_template_configs(self):
        return [dict(type="settings", name="Signal Notifier", custom_bindings=False)]

    #~~ EventPlugin
    def on_event(self, event, payload):
        if event != "PrintDone":
            return
        
        if not self._settings.get(['enabled']):
            return
        
        filename = os.path.basename(payload["file"])

        elapsed_time = octoprint.util.get_formatted_timedelta(datetime.timedelta(seconds=payload["time"]))

        tags = {'filename': filename, 
                'elapsed_time': elapsed_time,
                'host': socket.gethostname(),
                'user': getpass.getuser()}
        path = self._settings.get(["path"])
        sender = self._settings.get(["sender"])
        recipient = self._settings.get(["recipient"])
        message = self._settings.get(["message_format", "body"]).format(**tags)

        # check that path is a valid executable
        if not self.is_exe(path):
            self._logger.error("The path to signal-cli ('%s') doesn't point at an executable!" % path)
            return

        # check that sender is defined
        if sender.strip() == '':
            self._logger.error("The sender ('%s') seems empty!" % sender)
            return      

        # check that recipient is defined
        if recipient.strip() == '':
            self._logger.error("The recipient ('%s') seems empty!" % recipient)
            return      

        # check that sender is in list of valid senders?
        list_identities_cmd = "%s -u %s listIdentities" % (path, sender)
        rc, osstdout = self.run_command(list_identities_cmd)
        if rc != 0:
            self._logger.error("The sender ('%s') is not registered!" % sender)
            self._logger.error("Command: '%s'" % list_identities_cmd)
            self._logger.error("Command output: '%s'" % osstdout)
            return               

        # ./signal-cli -u +4915151111111 send -m "My first message from the CLI" +4915152222222
        the_command = "%s -u %s send -m \"%s\" %s" % (path, sender, message, recipient)
        self._logger.debug("Command plugin will run is: '%s'" % the_command)
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
                return
            # report notification was sent
            self._logger.info("Print notification sent to %s" % (self._settings.get(['recipient'])))

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

__plugin_name__ = "Signal Notifier"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = SignalNotifierPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
