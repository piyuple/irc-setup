"""
awaypy.py — Python module for ZNC
Copyright (c) 2026 Piyush Ranjan <hello@piyuple.dev>

Automatically sets/clears the IRC away message based on client connectivity.
Away message records the exact time you disconnected,
e.g. "Away from Mon, 13th Mar '26, 14:35"

Commands:
  status   — show current away state
  away     — force-set away right now
  back     — force-clear away right now
  help     — show this list
"""

import znc
from datetime import datetime


def _ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")

    return f"{n}{suffix}"


def _format_away_message() -> str:
    now = datetime.now()
    day_name = now.strftime("%a")
    day_ord  = _ordinal(now.day)
    month    = now.strftime("%b")
    year     = now.strftime("%y")
    time_str = now.strftime("%H:%M")

    return f"Away from {day_name}, {day_ord} {month} '{year}, {time_str}"


def _format_duration(seconds: int) -> str:
    minutes, secs  = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours    = divmod(hours, 24)

    parts = []
    if days:    parts.append(f"{days}d")
    if hours:   parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    if secs and not days: parts.append(f"{secs}s")

    return " ".join(parts) if parts else "less than a second"


class awaypy(znc.Module):
    description = (
        "Auto-set AWAY when all clients disconnect; "
        "clears AWAY on reconnect."
    )
    module_types = [znc.CModInfo.NetworkModule]  # network scope for disconnect hook

    def OnLoad(self, args, message):
        self.is_away = False
        self.away_since = None

        return True

    def OnIRCConnected(self):
        if len(self.GetNetwork().GetClients()) == 0:
            self._set_away()

    def OnClientAttached(self):
#        self.PutModule("DEBUG: OnClientAttached fired")

        if self.is_away:
            duration = self._clear_away()
            self.PutModule(f"Welcome back! You were away for {duration}.")

#    def OnClientLogin(self):
#        pass

#    def OnClientDetached(self):
#        pass

    def OnClientDisconnect(self):
#        self.PutModule("DEBUG: OnClientDisconnect fired")
        
        count = len(self.GetNetwork().GetClients())
#        self.PutModule(f"DEBUG: clients still connected = {count}")
        if count == 0:
            self._set_away()

    def OnModCommand(self, command: str):
        cmd = command.strip().lower()

        if cmd == "help":
            self.PutModule("Commands: status | away | back | help")

        elif cmd == "status":
            state = "AWAY" if self.is_away else "BACK"
            self.PutModule(f"Current state: {state}")

            if self.is_away and self.away_since:
                elapsed = int((datetime.now() - self.away_since).total_seconds())
                self.PutModule(f"Away for: {_format_duration(elapsed)} so far")

            self.PutModule(f"Connected clients: {self.GetNetwork().GetClients()}")

        elif cmd == "away":
            self._set_away()
            self.PutModule("Manually set away.")

        elif cmd == "back":
            duration = self._clear_away()
            self.PutModule(f"Manually cleared away. You were away for {duration}.")

        else:
            self.PutModule(f"Unknown command '{command}'. Type 'help'.")

    def _set_away(self):
        self.away_since = datetime.now()
        self.GetNetwork().PutIRC(f"AWAY :{_format_away_message()}")
        self.is_away = True

    def _clear_away(self) -> str:
        duration = "unknown"
        if self.away_since:
            elapsed = int((datetime.now() - self.away_since).total_seconds())
            duration = _format_duration(elapsed)
            self.away_since = None

        self.GetNetwork().PutIRC("AWAY")
        self.is_away = False
        return duration

