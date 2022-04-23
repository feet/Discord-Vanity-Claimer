import sys
import time
import json
import toml
import base64
import random
import requests
import threading

from loguru import logger
from colorama import Fore, init
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor
init(convert=True)


class claimer:
    def __init__(self):
        logger.remove()
        logger.add(sys.stdout, colorize=True, level=5,
                   format="<w>{time:HH:mm:ss.SS}</w> | <c>Elapsed: {elapsed.seconds}:{elapsed.microseconds}</c> | <e>Line: {line} - {function}</e> | <w>></w> {message}")
        self.log = logger.debug

        data = toml.load("config.toml")

        self.token: str = data.get('token')
        self.vanities: list = data.get('vanities')
        self.guild_ids: list = data.get('guild_ids')
        self.threads: str = data.get('threads')
        self.proxies = data.get('proxies')

        self.headers = self.create_headers()

        self.eligible = []
        self.lock = threading.Lock()
        self.run = True

        self.main()

    def claim_vanity(self):
        self.log(Fore.WHITE + "Started claimer")
        while self.run:
            if len(self.eligible) == 0:
                pass
            else:
                for invite in self.eligible:
                    try:
                        try:
                            guild_id = random.choice(self.guild_ids)
                        except Exception as e:
                            self.log(
                                Fore.RED + "No guilds left to claim vanities on, turning bot off")
                            self.run = False
                            quit()
                        req = requests.patch(
                            f"https://discord.com/api/v9/guilds/{guild_id}/vanity-url", headers=self.headers, json={"code": invite}, proxies=self.proxy())
                        if req.status_code == 200:
                            self.log(
                                Fore.GREEN + f"successfully claimed {invite}")
                            self.guild_ids.remove(guild_id)
                            self.vanities.remove(invite)
                        elif req.json()['code'] == 50035:
                            self.log(
                                Fore.RED + f"{invite} is permanently banned")
                            self.vanities.remove(invite)
                        elif req.json()['code'] == 50020:
                            self.log(
                                Fore.RED + f"{invite} has already been claimed")
                        else:
                            self.log(
                                Fore.RED + f"{req.status_code} - unknown error: {req.text}")
                        self.eligible.remove(invite)

                    except Exception as e:
                        self.log(Fore.RED + str(e))

    def super_prop(self, os, browser, useragent, browser_version, os_version, client_build):
        sp = {
            "os": os,
            "browser": browser,
            "device": "",
            "system_locale": "de-DE",
            "browser_user_agent": useragent,
            "browser_version": browser_version,
            "os_version": os_version,
            "referrer": "",
            "referring_domain": "",
            "referrer_current": "https://discord.com/",
            "referring_domain_current": "discord.com",
            "release_channel": "stable",
            "client_build_number": client_build,
            "client_event_source": None
        }
        return sp

    def create_headers(self):
        uc = UserAgent().chrome
        if "Windows" in uc:
            os = "Windows"
            osver = "10"
        elif "Linux" in uc:
            os = "Linux"
            osver = "X11"
        else:
            os = "Apple"
            osver = "10_9_3"
        browserver = ' '.join(str(uc).split('/')[3:4]).split(' ')[0]
        superProp = self.super_prop(
            os, "Chrome", uc, browserver, osver, random.randint(84451, 124397))
        headers = {"accept": "*/*",
                   "accept-encoding": "gzip, deflate, br",
                   "accept-language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
                   "authorization": self.token,
                   "content-length": "28",
                   "content-type": "application/json",
                   "origin": "https://discord.com",
                   "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"100\", \"Google Chrome\";v=\"100\"",
                   "sec-ch-ua-mobile": "?0",
                   "sec-ch-ua-platform": "\"Windows\"",
                   "sec-fetch-dest": "empty",
                   "sec-fetch-mode": "cors",
                   "sec-fetch-site": "same-origin",
                   "user-agent": str(uc),
                   "x-debug-options": "bugReporterEnabled",
                   "x-discord-locale": "de",
                   "x-super-properties": str(base64.b64encode(json.dumps(superProp, separators=",:").encode()).decode())
                   }
        return headers

    def test_invite(self):
        self.log(Fore.WHITE + "Started invite checker")
        while self.run:
            vanity = random.choice(self.vanities)
            try:
                req = requests.get(
                    f"https://discord.com/api/v9/invites/{vanity}", proxies=self.proxy())

                if "unknown" in req.text.lower():
                    if vanity not in self.eligible:
                        self.eligible.append(vanity)
                        self.log(
                            Fore.BLUE + f"{vanity} is claimable")
                elif req.status_code == 429:
                    self.log(
                        Fore.RED + "we are ratelimited, adding 5 second sleep")
                    time.sleep(5)
                else:
                    self.log(
                        Fore.MAGENTA + f"{vanity} is already claimed")
                    pass

            except Exception as e:
                self.log(Fore.RED + str(e))

    def make_threads(self, function):
        try:
            with ThreadPoolExecutor(max_workers=int(self.threads)) as run:
                for x in range(int(self.threads)):
                    run.submit(function())

        except Exception as e:
            self.log(Fore.RED + str(e))

    def proxy(self):
        try:
            if self.proxies is not None:
                allproxies = open(self.proxies).read().splitlines()
                chosenproxy = random.choice(allproxies)
                return {'https': 'http://%s' % (chosenproxy)}

            else:
                return None
        except Exception as e:
            self.log(Fore.RED + str(e))

    def main(self):
        try:
            threading.Thread(target=self.make_threads,
                             args=(self.test_invite,)).start()
            self.claim_vanity()
        except Exception as e:
            self.log(Fore.RED + str(e))


claimer()
