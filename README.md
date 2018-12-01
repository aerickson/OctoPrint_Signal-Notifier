# OctoPrint_Signal-Notifier

Recieve Signal (https://signal.org/) messages when OctoPrint jobs are complete.

![Settings tab screenshot](extras/signalnotifier.png)

## Setup

Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

    https://github.com/aerickson/OctoPrint_Signal-Notifier/archive/master.zip

## Configuration

Ensure that signal-cli (https://github.com/AsamK/signal-cli) is installed and working on the host. 
  
Raspbian Notes:
  - https://github.com/AsamK/signal-cli/wiki/HowToUbuntu applies to Raspbian (and Octopi).
  - https://gist.github.com/ribasco/fff7d30b31807eb02b32bcf35164f11f works for upgrading your Java.

Test by running the following as the user Octoprint runs as. 

```
signal-cli -u <sender> send -m "signal-cli works from $USER@$HOST" <recipient>
```

## Acknowledgements

Loosely based on [OctoPrint_FreeMobile-Notifier](https://github.com/Pinaute/OctoPrint_FreeMobile-Notifier).

## License

Licensed under the terms of the [AGPLv3](http://opensource.org/licenses/AGPL-3.0).
