import shutil
from src.steam_local import EResult, EncryptedAppTicketResponse_t, SteamAppTicket
from src.dokken import DokkenAPI
from src.zip_it import zip_folder

APP_ID = 1818750
STORE_PATH = "profiles/{account_id}"

def main() -> SteamAppTicket:
    print("Steam Login")
    try:
        steam = SteamAppTicket(str(APP_ID))
        steam.initialize_apis()
    except Exception as e:
        print(f"Error during initializing SteamAPI! Steam must be on and you need to have MultiVersus in your library.")
        try:
            steam.shutdown()
        except Exception:
            pass
        return steam
    
    steam_id = display_name = ""
    try:
        steam_id = steam.get_steam_id()
    except Exception:
        pass
    try:
        display_name = steam.get_steam_name()
    except Exception:
        pass
    print(f"Logged in as steam user {display_name} ({steam_id})")
    
    try:
        steam.request_and_wait_for_encrypted_app_ticket()
    except Exception as e:
        print("Attempting to re-use existing login!")
        
    try:
        ticket = steam.get_encrypted_app_ticket().hex()
        print(f"Received ticket", ticket)
    except RuntimeError:
        print(f"Steam Login Failed: Open the game through steam and reach the main menu, then come back and use this tool again.")
        return steam
    except Exception as e:
        print(f"Error during steam log in: {e}")
        return steam

    print("MultiVersus Login")
    mvs = DokkenAPI(ticket)
    account_id = mvs.backup_profile(STORE_PATH)

    try:
        mvs.logout()
    except Exception:
        pass

    store_to = STORE_PATH.format(account_id=account_id)

    print("Compressing files...")
    zip_folder(
        store_to,
        f"{store_to}.zip",
    )

    shutil.rmtree(store_to, ignore_errors=True)

    print(f"Profile info saved to {store_to}.zip! Send this data to the MVSI team once their servers are up to import your profile.")
    return steam

if __name__ == "__main__":
    main().shutdown()
    input("Press Enter to quit...")
