""" Telegram Bot Helper """
import os
import platform
import subprocess
import json
import logging
from json.decoder import JSONDecodeError
from time import sleep
from datetime import datetime
from typing import List
from telegram import InlineKeyboardMarkup, Update
from telegram.ext.callbackcontext import CallbackContext

if not os.path.exists(os.path.join(os.curdir, "telegram_logs")):
    os.mkdir(os.path.join(os.curdir, "telegram_logs"))

logging.basicConfig(
    filename=os.path.join(os.curdir, "telegram_logs", f"telegrambot {datetime.now().strftime('%Y-%m-%d')}.log"),
    filemode='w',
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)

# logger = logging.getLogger(__name__)

class TelegramHelper:
    """ Telegram Bot Helper """
    def __init__(self, datafolder, config, configfile) -> None:
        self.datafolder = datafolder
        self.data = {}
        self.config = config
        self.config_file = configfile
        self.screener = {}
        self.settings = {}
        self.use_default_scanner = True
        self.atr72pcnt = 2.0
        self.enableleverage = False
        self.maxbotcount = 0
        self.autoscandelay = 0
        self.enable_buy_next = True
        self.autostart = False
        self.logger = logging.getLogger(__name__)

        self.load_config()
        self.read_screener_config()

    def load_config(self):
        ''' Load/Reread config file from file '''
        self.read_config()

        if "scanner" in self.config:
            self.atr72pcnt = (
                self.config["scanner"]["atr72_pcnt"]
                if "atr72_pcnt" in self.config["scanner"]
                else self.atr72pcnt
            )
            self.enableleverage = (
                self.config["scanner"]["enableleverage"]
                if "enableleverage" in self.config["scanner"]
                else self.enableleverage
            )
            self.use_default_scanner = (
                bool(self.config["scanner"]["use_default_scanner"])
                if "use_default_scanner" in self.config["scanner"]
                else self.use_default_scanner
            )
            self.maxbotcount = (
                self.config["scanner"]["maxbotcount"]
                if "maxbotcount" in self.config["scanner"]
                else self.maxbotcount
            )
            self.autoscandelay = (
                self.config["scanner"]["autoscandelay"]
                if "autoscandelay" in self.config["scanner"]
                else 0
            )
            self.enable_buy_next = (
                self.config["scanner"]["enable_buy_next"]
                if "enable_buy_next" in self.config["scanner"]
                else True
            )

    def send_telegram_message(
        self, update: Update , reply, markup: InlineKeyboardMarkup = None, context: CallbackContext = None
    ):
        ''' Send telegram messages '''
        try:
            query = update.callback_query
            query.answer()
        except:
            pass
        try:
            if markup is None:
                query.edit_message_text(reply, parse_mode="HTML")
            else:
                query.edit_message_text(reply, reply_markup=markup, parse_mode="HTML")
        except Exception as err:
            try:
                context.bot.edit_message_text(chat_id=update.effective_message.chat_id,
                                message_id=update.effective_message.message_id,
                                text=reply,
                                reply_markup=markup,
                                parse_mode="HTML"
                                )
            except:
                context.bot.send_message(chat_id=update.effective_message.chat_id,
                                text=reply,
                                reply_markup=markup,
                                parse_mode="HTML")

    def read_data(self, name: str = "data.json") -> bool:
        ''' Read data from json file '''
        try:
            fname = name if name.__contains__(".json") else f"{name}.json"
            with open(
                os.path.join(self.datafolder, "telegram_data", fname),
                "r",
                encoding="utf8",
            ) as json_file:
                self.data = json.load(json_file)
        except FileNotFoundError:
            self.logger.warning(f"read_data file not found for {name}")
            return False
        except JSONDecodeError:
            self.logger.warning(f"read_data Json Decode for {name}")
            return False
        return True

    def write_data(self, name: str = "data.json") -> None:
        ''' Write data to json file '''
        fname = name if name.__contains__(".json") else f"{name}.json"
        try:
            with open(
                os.path.join(self.datafolder, "telegram_data", fname),
                "w",
                encoding="utf8",
            ) as outfile:
                json.dump(self.data, outfile, indent=4)
                return True
        except JSONDecodeError as err:
            self.logger.error(err)
            return False

    def read_config(self):
        ''' Read config file '''
        try:
            with open(
                os.path.join(self.config_file), "r", encoding="utf8"
            ) as json_file:
                self.config = json.load(json_file)
        except FileNotFoundError:
            return
        except json.decoder.JSONDecodeError:
            return

    def write_config(self):
        ''' Write config file '''
        try:
            with open(
                os.path.join(self.config_file),
                "w",
                encoding="utf8",
            ) as outfile:
                json.dump(self.config, outfile, indent=4)
        except:
            return

    def read_screener_config(self):
        ''' Read screener config file '''
        try:
            with open(
                "screener.json", "r", encoding="utf8"
            ) as json_file:
                self.screener = json.load(json_file)
        except FileNotFoundError:
            return
        except json.decoder.JSONDecodeError:
            return

    def write_screener_config(self):
        ''' Write screener config file '''
        try:
            with open(
                "screener.json",
                "w",
                encoding="utf8",
            ) as outfile:
                json.dump(self.screener, outfile, indent=4)
        except:
            return

    def get_all_bot_list(self) -> List[str]:
        """Return ALL contents of telegram_data folder"""
        jsonfiles = sorted(os.listdir(os.path.join(self.datafolder, "telegram_data")))

        i = len(jsonfiles) - 1
        while i >= 0:
            if (
                jsonfiles[i] == "data.json"
                or jsonfiles[i].__contains__("output.json")
                or jsonfiles[i].__contains__(".csv")
                or jsonfiles[i] == "settings.json"
            ):
                jsonfiles.pop(i)
            else:
                read_ok, try_cnt = False, 0
                while not read_ok and try_cnt <= 5:
                    try_cnt += 1
                    read_ok = self.read_data(jsonfiles[i])
                    sleep(0.1)

                if not read_ok:
                    jsonfiles.pop(i)
            i -= 1
        jsonfiles.sort()
        return [
            x.replace(".json", "") if x.__contains__(".json") else x for x in jsonfiles
        ]

    def get_active_bot_list(self, state: str = "active") -> List[str]:
        """Return contents of telegram_data folder"""
        jsonfiles = self.get_all_bot_list()

        i = len(jsonfiles) - 1
        while i >= 0:
            read_ok, try_cnt = False, 0
            while not read_ok and try_cnt <= 5:
                try_cnt += 1
                read_ok = self.read_data(jsonfiles[i])
                sleep(0.2)
            if try_cnt >= 5:
                self.logger.error(f"Get Active Bot list for bot {jsonfiles[i]} read_data retry count {try_cnt} failed!")
            if "botcontrol" in self.data:
                if not self.data["botcontrol"]["status"] == state:
                    jsonfiles.pop(i)
            i -= 1
        jsonfiles.sort()
        return [
            x.replace(".json", "") if x.__contains__(".json") else x for x in jsonfiles
        ]

    def get_active_bot_list_with_open_orders(self, state: str = "active") -> List[str]:
        """Return contents of telegram_data folder active bots with an open order"""
        jsonfiles = self.get_all_bot_list()

        i = len(jsonfiles) - 1
        while i >= 0:
            while self.read_data(jsonfiles[i]) is False:
                sleep(0.1)
            if "botcontrol" in self.data:
                margin_string = str(self.data["margin"]).strip()
                if (
                    not self.data["botcontrol"]["status"] == state
                    and margin_string != ""
                ):
                    jsonfiles.pop(i)
            i -= 1
        jsonfiles.sort()
        return [
            x.replace(".json", "") if x.__contains__(".json") else x for x in jsonfiles
        ]

    def get_hung_bot_list(self, state: str = "active") -> List[str]:
        """Return contents of telegram_data folder - working out which are hung bots"""
        jsonfiles = self.get_all_bot_list()

        i = len(jsonfiles) - 1
        while i >= 0:
            while self.read_data(jsonfiles[i]) is False:
                sleep(0.2)
            if "botcontrol" in self.data:
                if "watchdog_ping" in self.data["botcontrol"]:
                    last_ping = datetime.strptime(self.data["botcontrol"]["watchdog_ping"], "%Y-%m-%dT%H:%M:%S.%f")
                    current_dt = datetime.now()
                    ping_delta = int((current_dt - last_ping).total_seconds())
                    if (self.data["botcontrol"]["status"] == state and ping_delta < 600):
                        jsonfiles.pop(i)
                else:
                    start_time = datetime.strptime(self.data["botcontrol"]["started"], "%Y-%m-%dT%H:%M:%S.%f")
                    current_dt = datetime.now()
                    start_delta = int((current_dt - start_time).total_seconds())
                    if (self.data["botcontrol"]["status"] == state and start_delta < 300):
                        jsonfiles.pop(i)
            i -= 1
        jsonfiles.sort()
        return [
            x.replace(".json", "") if x.__contains__(".json") else x for x in jsonfiles
        ]

    def is_bot_running(self, pair) -> bool:
        ''' Check is bot running (pair.json file exists)'''
        if os.path.isfile(
            os.path.join(self.datafolder, "telegram_data", f"{pair}.json")
        ):
            return True

        return False

    def get_running_bot_exchange(self, pair) -> str:
        ''' Get bots exchange '''
        if self.read_data(f"{pair}.json") is True:
            return self.data["exchange"]
        return "None"

    def start_process(
        self,
        pair,
        exchange,
        overrides,
        startmethod: str = "telegram",
        return_output: bool = False,
    ):
        """Start a new subprocess"""

        if self.is_bot_running(pair):
            return False

        if return_output is True:
            return subprocess.getoutput(
                f"python3 pycryptobot.py --exchange {exchange} --market {pair} {overrides}"
            )

        command = "python3 pycryptobot.py"
        command = f"{command} --startmethod {startmethod}"

        if pair != "":
            command = f"{command} --market {pair}"
        if exchange != "":
            command = f"{command} --exchange {exchange}"

        if platform.system() == "Windows":
            os.system(
                f"start powershell -Command $host.UI.RawUI.WindowTitle = '{pair}' ; "
                f"{command} --logfile './logs/{exchange}-{pair}-{datetime.now().date()}.log' "\
                    f"{overrides}"
            )
        else:
            subprocess.Popen(
                f"{command} --logfile './logs/{exchange}-{pair}-{datetime.now().date()}.log' "\
                    f"{overrides}",
                shell=True,
            )

        return True

    def update_bot_control(self, pair, status) -> bool:
        """used to update bot json files for controlling state"""
        self.read_data(pair)

        if "botcontrol" in self.data:
            self.data["botcontrol"]["status"] = status
            self.write_data(pair)
            return True

        return False

    def stop_running_bot(self, pair, state, is_open: bool = False):
        ''' Stop current running bots '''
        if self.is_bot_running(pair):
            done = False
            while done is False:
                try:
                    self.read_data(pair)
                    if is_open:
                        self.update_bot_control(pair, state)
                    elif "margin" in self.data and self.data["margin"] == " ":
                        self.update_bot_control(pair, state)
                    done = True
                except:
                    pass

    def create_callback_data(self, callback_tag, exchange: str = "", parameter: str = ""):
        return json.dumps({'c':callback_tag,'e': exchange,'p':parameter})