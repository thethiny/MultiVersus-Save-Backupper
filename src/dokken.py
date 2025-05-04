from copy import deepcopy
import json
import requests
import os

class DokkenAPI:
    ROOT_URL = "https://dokken-api.wbagora.com"
    API_KEY = "51586fdcbd214feb84b0e475b130fce0"

    def __init__(self, ticket: str):
        if not ticket or not ticket.strip(): 
            raise ValueError(f"Missing token")

        self.ticket = ticket
        self.token = None

    def backup_profile(self, store_path):
        print("Logging in to MultiVersus Servers!")

        access_info = self.login()

        account_id = access_info.get("account", {}).get("id")
        if not account_id:
            raise ValueError("Couldn't find account id!")
        print(f"Logged in as user {account_id}")

        print(f"Retreiving Stats and Inventory")
        profile_info = self.get_profile_info(account_id)

        base_path = store_path.format(account_id=account_id)
        os.makedirs(base_path, exist_ok=True)

        print(f"Saving User information to {base_path}")

        with open(os.path.join(base_path, "access.json"), "w", encoding="utf-8") as f:
            json.dump(access_info, f, ensure_ascii=False, indent=4)

        for key, data in profile_info.items():
            with open(
                os.path.join(base_path, f"{key}.json"), "w", encoding="utf-8"
            ) as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

        return account_id

    def get_profile_info(self, account_id):
        main_url = self.make_url("/batch")
        headers = self.get_headers(True)

        options = {
            "allow_failures": True,
            "parallel": True,
        }
        batch_requests = []
        payload = {"options": options, "requests": batch_requests,}

        request_template = {
            "headers": {},
            "url": "",
            "verb": "GET"
        }

        urls = {
            "account": "/accounts/me",
            "profile": "/profiles/me",
            "inventory": "/profiles/me/inventory",
            "preferences": f"/objects/preferences/unique/{account_id}/me",
            "matches": f"/matches/all/{account_id}?count=10&page=1&fields=server_data&templates=2v2_container&templates=1v1_container&templates=ffa_container&templates=2v2_gamelift&templates=1v1_gamelift&templates=ffa_gamelift&templates=custom_container_one_player&templates=custom_container_two_player&templates=custom_container_three_player&templates=custom_container_four_player&templates=custom_gamelift_two_player&templates=custom_gamelift_three_player&templates=custom_gamelift_four_player&templates=1v1_container_bot&templates=1v3_container_bot&templates=2v2_container_bot&templates=2v2_gamelift_bot&templates=arena_container_parent&templates=rift_container_one_player&templates=rift_container_two_player&templates=rift_gamelift_two_player",
            "reward_tracks": "/ssc/invoke/get_milestone_reward_tracks",
            "equipped_cosmetics": "/ssc/invoke/get_equipped_cosmetics",
            "perks": "/ssc/invoke/perks_get_all_pages",
            "ranked_data": "/ssc/invoke/ranked_data",
        }

        for url in urls.values():
            p = deepcopy(request_template)
            p["url"] = url
            batch_requests.append(p)

        resp = requests.put(main_url, headers=headers, json=payload)

        if not resp.status_code // 100 == 2:
            raise ValueError(
                f"Error {resp.status_code} in resp: {resp.json().get('msg', '')}"
            )

        response = resp.json()

        responses = {}
        for key, r in zip(urls.keys(), response.get("responses", [])):
            status_code = r.get("status_code", 200)
            if status_code != 200:
                raise ValueError(f"Error in {key}: {status_code}")
            returned = r.get("body", None)
            if not returned:
                print(f"Warning: {key}'s return was empty!")
            responses[key] = returned

        return responses

    @classmethod
    def make_url(cls, url: str):
        url = cls.ROOT_URL.rstrip("/") + '/' + url.lstrip("/")
        return url

    def get_headers(self, auth: bool = False):
        headers = {
            "X-Hydra-Api-Key": self.API_KEY
        }
        if auth:
            if not self.token:
                raise ValueError(f"Missing access token or invalid!")
            headers["X-Hydra-Access-Token"] = self.token

        return headers

    def login(self):
        url = self.make_url("/access")
        headers = self.get_headers()

        payload = {
            "auth": {
                "fail_on_missing": False,
                "steam": self.ticket,
            },
            # "metadata": {
            #     "Platform": "PC"
            # },
            "options": [
                "configuration",
                "achievements",
                "account",
                "profile",
                "notifications",
                "maintenance",
                "wb_network"
            ]
        }

        resp = requests.post(url, headers=headers, json=payload)

        if not resp.status_code // 100 == 2:
            raise ValueError(f"Error {resp.status_code} in resp: {resp.json().get('msg', '')}")

        response = resp.json()
        token = response.get("token")
        if not token:
            raise ValueError(f"Received invalid token from server!")

        self.token = token

        return response

    def logout(self):
        url = self.make_url("/access")
        headers = self.get_headers(True)
        resp = requests.delete(url, headers=headers)