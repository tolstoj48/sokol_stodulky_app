import kivy
from kivy.app import App
from kivy.uix.recycleview import RecycleView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import StringProperty, ListProperty
from functools import partial
from kivy.uix.scrollview import ScrollView
from kivy.network.urlrequest import UrlRequest
from kivy.uix.popup import Popup
from kivy.cache import Cache
import certifi as cfi
import requests

class ManagerScreen(ScreenManager):
    pass

class FirstScreen(Screen):
    pass

class ATeamScreen(Screen):
    pass

class BTeamScreen(Screen):
    pass

class CTeamScreen(Screen):
    pass

class RozpisyScreen(Screen):
    pass

class ScrollableLabel(ScrollView):
    text = StringProperty('')

class Popupnoconn_label(Label):
    pass

class Popupnoconn_button(Button):
    pass

class RVA(RecycleView):
    """Recycleview of the matches of the first team"""
    def __init__(self, link="", tym="", **kwargs):
        super(RVA, self).__init__(**kwargs)
        app = App.get_running_app()
        data_matches = app.get_team_data(data_matches=Cache.get("tymy", "tymy_vysledky"),
                team="A-tým", matches=True)
        self.data = [{'text': str(values["souperi"]) + " - " + 
        str(values["vysledek"])} for values in data_matches]
 
class RVB(RecycleView):
    """Recycleview of the matches of the second team"""
    def __init__(self, link="", tym="", **kwargs):
        super(RVB, self).__init__(**kwargs)
        app = App.get_running_app()
        data_matches = app.get_team_data(data_matches=Cache.get("tymy", "tymy_vysledky"), 
            team="B-tým", matches=True)
        self.data = [{'text': str(values["souperi"]) + " - " + 
        str(values["vysledek"])} for values in data_matches]

class RVC(RecycleView):
    """Recycleview of the matches of the third team"""
    def __init__(self, link="", tym="", **kwargs):
        super(RVC, self).__init__(**kwargs)
        app = App.get_running_app()
        data_matches = app.get_team_data(data_matches=Cache.get("tymy", "tymy_vysledky"), 
            team="C-tým", matches=True)
        self.data = [{'text': str(values["souperi"]) + " - " + 
        str(values["vysledek"])} for values in data_matches]

class MainApp(App):
    """Main app building class."""

    def on_pause(self):
        """On pause kivy."""
        return True

    def build(self):
        """Build."""
        self.icon = 'icon.png'
        try:
            req = requests.get('https://tolstoj48.pythonanywhere.com/appis/tymy/')
        except:
            self.pop_up_no_connection()
        else:
            self.pop_up()
            result = req.json()
            Cache.register('tymy', limit=1, timeout=20)
            key = "tymy_vysledky"
            instance = result
            Cache.append("tymy", key, instance)
            self.manager = ManagerScreen()
            self.url_req()
            return self.manager

    def url_req(self):
        """Requests the server api. Stores the data."""
        self.api_queries =  ['https://tolstoj48.pythonanywhere.com/appis/rozpisy/',
            'https://tolstoj48.pythonanywhere.com/appis/aktualni_rozpis/']
        self.response_matches_result = Cache.get("tymy", "tymy_vysledky")
        self.success_results_matches()
        self.response_schedules = UrlRequest(self.api_queries[0], 
            on_success=self.success_results_schedules, 
            on_error=self.pop_up_no_connection,ca_file=cfi.where(), 
            verify=True)
        self.response_recent = UrlRequest(self.api_queries[1], 
            on_success=self.success_results_next_matches, 
            on_error=self.pop_up_no_connection,
            ca_file=cfi.where(), verify=True)

    def pop_up(self, *args):
        """Popups when the data are downloaded."""
        self.popup = Popup(title='Sokol Stodůlky', size_hint=(0.5 , 0.5), 
            separator_height = 0)
        dism = Label(text="Aplikace stahuje data...", size_hint=(1,1), 
            valign="middle", halign="center")
        self.popup.bind(on_dismiss=self.check_result)
        self.popup.add_widget(dism)
        dism.text_size = (dism.parent.width * 2, dism.parent.height * 2)
        self.popup.open()

    def pop_up_no_connection(self, *args):
        """Popups when the device is without connection."""
        self.popup_no_conn = Popup(title='Nedostupné internetové připojení', 
            size_hint=(1 , 1))
        dism = BoxLayout(orientation="vertical")
        label = Popupnoconn_label(text = "Vypněte aplikaci, připojte se a znovu ji zapněte")
        #label.size = label.texture_size
        button = Popupnoconn_button(text="Vypnout aplikaci")
        dism.add_widget(label)
        dism.add_widget(button)
        button.bind(on_release=self.kill)
        self.popup_no_conn.add_widget(dism)
        self.popup_no_conn.bind(on_dismiss=self.check_result)
        self.popup_no_conn.open()

    def kill(self, *args):
        App.get_running_app().stop()

    def check_result(self, *args):
        return True

    def let_dismiss(self, *args):
        return False

    def success_results_matches(self):
        """Process the obtained data of the played matches."""
        self.popup.unbind(on_dismiss=self.check_result)
        self.popup.dismiss()
        data_matches = self.get_team_data(data_matches=self.response_matches_result, 
            team="", final="all", matches=True)
        for i in data_matches:
            self.fetch_match_detail(i, i["tym"])
    
    def success_results_schedules(self, req, result):
        """Process the obtained data of the scheduled matches."""
        data_schedules = self.get_team_data(data_matches=
            self.response_schedules.result, matches=False)
        data_schedule_choice = ["rozpis_a", "rozpis_b", "rozpis_c", 
        "rozpis_st_d", "rozpis_ml_d", "rozpis_st_z", "rozpis_ml_z_a", 
        "rozpis_ml_z_b", "rozpis_ml_z_c"]
        helper_variable = 0
        for data in data_schedules:
            self.fetch_team_schedules("".join(data), 
                data_schedule_choice[helper_variable])
            helper_variable += 1
        
    def success_results_next_matches(self, req, result):
        """Process the obtained data of the planned scheduled matches."""
        self.fetch_next_matches()

    def fetch_match_detail(self, data, tym):
        """Creates the screens for the display of the details of the 
        particular matches.
        """
        screen = Screen(name = data["souperi"] + " - " + data["vysledek"])
        layout = BoxLayout(orientation="vertical")
        screen.add_widget(layout)
        label = ScrollableLabel(text =
                "[b]Soupeři[/b]: " + data["souperi"] + "\n\n" + 
                "[b]Výsledek[/b]: " + data["vysledek"] + "\n\n" + 
                "[b]Kolo[/b]: " + data["kolo"] + "\n\n" + 
                "[b]Datum[/b]: " + data["datum"] + "\n\n" + 
                "[b]Sestava[/b]: " + data["sestava"] + "\n\n" +
                "[b]Náhradnící[/b]: " + data["nahradnici"] + "\n\n" + 
                "[b]Góly[/b]: " + data["goly"] + "\n\n" + 
                "[b]Komentář[/b]: " + data["koment"] + "\n\n", 
                size_hint=[1,5])
        button = Button(text = "Zpět na hlavní menu", size_hint_y = 1)
        button.bind(on_release = partial(self.switch_screen, 
            "_first_screen_"))
        layout.add_widget(button)
        button = Button(text = "Zpět na přehled utkání " + tym + "u", 
            size_hint_y = 1)
        button.bind(on_release = partial(self.switch_screen, tym))
        layout.add_widget(button)
        layout.add_widget(label)
        self.manager.add_widget(screen)

    def fetch_team_schedules(self, data, rozpis):
        """Creates the screens for the display of the details of the 
        particular team schedules.
        """
        screen = Screen(name = rozpis)
        layout = BoxLayout(orientation="vertical")
        screen.add_widget(layout)
        label = ScrollableLabel(text = data,
               size_hint=[1,5])
        button = Button(text = "Zpět na hlavní menu", size_hint_y = 1)
        button.bind(on_release = partial(self.switch_screen, "_first_screen_"))
        layout.add_widget(button)
        button = Button(text = "Zpět na výběr rozpisů", size_hint_y = 1)
        button.bind(on_release = partial(self.switch_screen, "rozpisy"))
        layout.add_widget(button)
        layout.add_widget(label)
        self.manager.add_widget(screen)

    def fetch_next_matches(self):
        """Creates the screen with information about scheduled matches 
        in the next 6 days. Uses data from the api connection to the 
        remote server. Then sends data to prepare_data_for_next_macthes()
        method and puts them in the text.
        """
        screen = Screen(name = "rozpisy_aktualni")
        layout = BoxLayout(orientation="vertical")
        screen.add_widget(layout)
        label = ScrollableLabel(text = str(self.prepare_data_for_next_macthes()),
            size_hint=[1,5])
        button = Button(text = "Zpět na hlavní menu", size_hint_y = 1)
        button.bind(on_release = partial(self.switch_screen, "_first_screen_"))
        layout.add_widget(button)
        button = Button(text = "Zpět na přehled rozpisů", size_hint_y = 1)
        button.bind(on_release = partial(self.switch_screen, "rozpisy"))
        layout.add_widget(button)
        layout.add_widget(label)
        self.manager.add_widget(screen)

    def prepare_data_for_next_macthes(self):
        """Returns only data from request to the api to the 
        fetch_next_matches() method.
        """
        return "".join(self.response_recent.result[0])

    def get_team_data(self, data_matches="", team="", final="", matches=""):
        """Format the requested data to suitable list format for all the input 
        data,
        """
        if matches == True:
            a_team = []
            b_team = []
            c_team = []
            for i in data_matches:
                if i["tym"] == "A-tým":
                    a_team.append(i)
                elif i["tym"] == "B-tým":
                    b_team.append(i)
                else:
                    c_team.append(i)
            if team == "A-tým":
                return a_team
            elif team == "B-tým":
                return b_team
            elif team == "C-tým":
                return c_team
            if final == "all":
                return data_matches
        else:
            return data_matches

    def switch_screen(self, switch_to, *args, **kwargs):
        """Switches screens on screenmanager."""
        self.manager.current = switch_to


if __name__ == "__main__":
    MainApp().run()