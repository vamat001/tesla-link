import googlemaps
import time
import requests


class TeslaApi:
    def __init__(self, access_token="", id=""):
        with open("secrets.txt", "r") as f:
            lines = f.read().splitlines()
        self.email = lines[0]
        self.pw = lines[1]
        self.api_key = lines[2]
        self.client_id = lines[3]
        self.client_secret = lines[4]
        self.base_url = "https://owner-api.teslamotors.com"
        self.access_token = access_token
        self.refresh_token = ""
        self.id = id
        self.header = {"Authorization": "Bearer " + self.access_token}
        self.state_url = self.base_url + "/api/1/vehicles/" + self.id + "/vehicle_data"
        self.command_url = self.base_url + "/api/1/vehicles/" + self.id + "/command/"
        self.commands = {
            "start": self.remote_start,
            "homelink": self.trigger_homelink,
            "sentry mode on": self.set_sentry_mode,
            "sentry mode off": self.set_sentry_mode,
            "lock": self.door_lock,
            "unlock": self.door_unlock,
            "start hvac": self.start_hvac,
            "stop hvac": self.stop_hvac,
            "start charge": self.charge_start,
            "stop charge": self.charge_stop,
            "charge max range": self.charge_max_range,
            "set charge limit": self.set_charge_limit
        }
        self.queries = {
            "temperature": self.get_internal_temp,
            "climate setting": self.get_climate_setting,
            "locked": self.get_locked,
            "odometer": self.get_odo,
            "charging status": self.get_charging_status,
            "range": self.get_range,
            "location": self.get_addr
        }

    def auth(self):
        auth_url = self.base_url + "/oauth/token?grant_type=password&client_id=" + self.client_id + "&client_secret=" + self.client_secret + "&email=" + self.email + "&password=" + self.pw
        response = requests.post(auth_url).json()
        # return response['access_token']
        self.access_token = response['access_token']
        self.refresh_token = response['refresh_token']
        self.header = {"Authorization": "Bearer " + self.access_token}

    def refresh(self):
        auth_url = self.base_url + "/oauth/token?grant_type=refresh_token&client_id=" + self.client_id + "&client_secret=" + self.client_secret + "&refresh_token=" + self.access_token
        response = requests.post(auth_url).json()
        self.access_token = response['access_token']
        self.refresh_token = response['refresh_token']
        self.header = {"Authorization": "Bearer " + self.access_token}

    def state(self, param):
        url = self.state_url
        response = requests.get(url, headers=self.header).json()
        return response['response'][param]

    def command(self, param, data=None):
        url = self.command_url + param
        if data is None:
            response = requests.post(url, headers=self.header).json()
        else:
            response = requests.post(url, headers=self.header, data=data).json()
        return response['response']['result']

    def wake(self):
        try:
            vehicles = requests.get(self.base_url + "/api/1/vehicles/", headers=self.header).json()
            self.id = vehicles['response'][0]['id_s']
            self.state_url = self.base_url + "/api/1/vehicles/" + self.id + "/vehicle_data"
            self.command_url = self.base_url + "/api/1/vehicles/" + self.id + "/command/"
            url = self.base_url + "/api/1/vehicles/" + self.id + "/wake_up"
            start = time.time()
            print("connecting to tesla...")
            response = requests.post(url, headers=self.header).json()
            state = response['response']['state']
            while state != 'online':
                res = requests.get(self.base_url + "/api/1/vehicles", headers=self.header).json()
                state = res['response'][0]['state']
                if time.time() - start > 8:
                    return "Tesla connection timed out try again"
            # print("%s seconds" % (time.time() - start))
            speech = "Connected to " + response['response']['display_name']
        except ValueError:
            speech = "Access Denied"
        except:
            speech = "Failed to connect to tesla"
        return speech

    def get_addr(self):
        drive_state = self.state('drive_state')
        maps = googlemaps.Client(key=self.api_key)
        res = maps.reverse_geocode((drive_state['latitude'], drive_state['longitude']))[0]
        speed = drive_state['speed']
        direction = ""
        if speed is None:
            prefix = "Parked at "
            x = 0
        else:
            cardinal = {
                1: "north",
                2: "northeast",
                3: "east",
                4: "southeast",
                5: "south",
                6: "southwest",
                7: "west",
                8: "northwest",
                9: "north"
            }
            heading = round((drive_state['heading'] % 360) / 45) + 1
            direction = cardinal[heading]
            prefix = "Heading " + direction + " on "
            x = 1
        addr = ""
        for i in range(x, 3):
            addr += res['address_components'][i]['long_name'] + ' '
        return prefix + addr

    def get_range(self):
        charge_state = self.state('charge_state')
        return "The battery is at %d percent with a range of %d miles" % (charge_state['battery_level'], charge_state['battery_range'])

    def get_charging_status(self):
        charge_state = self.state('charge_state')
        status = ""
        if charge_state['charging_state'] != 'Charging':
            status = "Not charging"
        else:
            status = "Charging to %d percent of full capacity at %d miles per hour with %d minutes remaining until completion" % (charge_state['charge_limit_soc'], charge_state['charge_rate'], charge_state['minutes_to_full_charge'])
        return status

    def get_odo(self):
        vehicle_state = self.state('vehicle_state')
        return "The odometer reads %d miles" % vehicle_state['odometer']

    def get_locked(self):
        vehicle_state = self.state('vehicle_state')
        status = "locked" if vehicle_state['locked'] else "unlocked"
        return "The car is " + status

    def get_climate_setting(self):
        state = self.state('climate_state')
        degrees = state['driver_temp_setting'] * 9.0/5.0 + 32
        return "Climate control is set to %d degrees fahrenheit" % degrees

    def get_internal_temp(self):
        state = self.state('climate_state')
        degrees = state['inside_temp'] * 9.0 / 5.0 + 32
        return "Temperature inside is %d degrees fahrenheit" % degrees

    def remote_start(self):
        response = self.command('remote_start_drive', {'password': self.pw})
        return "Remote start activated. You have 2 minutes to start driving" if response else "Remote start failed"

    def trigger_homelink(self):
        loc = self.state('drive_state')
        response = self.command('trigger_homelink', {'lat': loc['latitude'], 'lon': loc['longitude']})
        return "Opening garage" if response else "Unable to trigger homelink"

    def set_sentry_mode(self, switch):
        if switch == 'on':
            toggle = True
        elif switch == 'off':
            toggle = False
        else:
            return "Not a valid operation"
        response = self.command('set_sentry_mode', {'on': toggle})
        if toggle and response:
            return "Sentry mode turned on"
        elif not toggle and response:
            return "Sentry mode turned off"
        else:
            return "Set sentry mode failed"

    def door_lock(self):
        response = self.command('door_lock')
        return "Doors locked" if response else "Unable to lock doors"

    def door_unlock(self):
        response = self.command('door_unlock')
        # print(response)
        return "Doors unlocked" if response else "Unable to unlock doors"

    def start_hvac(self):
        response = self.command('auto_conditioning_start')
        return "Climate control started" if response else "Unable to start climate control"

    def stop_hvac(self):
        response = self.command('auto_conditioning_stop')
        return "Climate control stopped" if response else "Unable to stop climate control"

    def charge_start(self):
        response = self.command('charge_start')
        return "Charging started" if response else "Unable to start charging"

    def charge_stop(self):
        response = self.command('charge_stop')
        return "Charging stopped" if response else "Unable to stop charging"

    def charge_max_range(self):
        response = self.command('charge_max_range')
        return "Charging to max range" if response else "Unable to set charge limit to max range"

    def set_charge_limit(self, percent):
        if percent < 0 or percent > 100:
            return "Not a valid charge limit"
        response = self.command('set_charge_limit', data={'percent': percent})
        return "Charge limit set to %d" % percent if response else "Unable to set charge limit to %d" % percent

    def revoke_auth(self):
        data = {'token': self.access_token}
        response = requests.post(self.base_url + "/oauth/revoke", headers=self.header, data=data).json()
        return response

    def commandHandler(self, command, params=None):
        if command not in self.commands:
            return "Sorry I don't know how to do that"
        else:
            if params is None:
                return self.commands[command]()
            else:
                return self.commands[command](params)

    def dataHandler(self, query):
        if query not in self.queries:
            return "Sorry I can't get that information"
        else:
            return self.queries[query]()


# if __name__ == '__main__':
    # t = TeslaApi()
    # t.auth()
    # print(t.wake())
    # print(t.get_addr())
    # print(t.get_range())
    # print(t.charge_start())
    # print(t.get_charging_status())
    # print(t.get_odo())
    # print(t.door_lock())
    # print(t.get_locked())
    # print(t.get_climate_setting())
    # print(t.get_internal_temp())
    # print(t.stop_hvac())
    # t.revoke_auth()
