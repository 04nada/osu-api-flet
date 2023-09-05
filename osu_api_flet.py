from __future__ import annotations
from typing import Any, Literal
from dataclasses import dataclass, field
import flet as ft
from flet_runtime.auth.oauth_provider import OAuthProvider # type: ignore
#import aiohttp
import math
import os
import ossapi as ossapi # type: ignore
import ossapi.models # type: ignore
from ossapi import OssapiAsync # type: ignore

# --- -----

ModWorthPP = Literal['HD', 'HR', 'EZ', 'DT', 'NC', 'HT', 'FL', 'NF', 'SO']

def get_beatmap_cs_with_mods(cs: float, mods: list[ModWorthPP]) -> float:
    if 'EZ' in mods:
        return cs*0.5
    elif 'HR' in mods:
        return min(cs*1.3, 10.0)
    else:
        return cs

def get_beatmap_hp_with_mods(hp: float, mods: list[ModWorthPP]) -> float:
    if 'EZ' in mods:
        return hp*0.5
    elif 'HR' in mods:
        return min(hp*1.4, 10.0)
    else:
        return hp

# --- -----

Scene = Literal['login', 'search']

@dataclass
class App:
    page: ft.Page

    ### API Access 
    REDIRECT_URL: str = 'https://zero4nada-osu-api-flet.onrender.com/api/oauth/redirect'

    client_id: str = field(init=False)
    client_secret: str = field(init=False)
    OAUTH_ENDPOINT: str = 'https://osu.ppy.sh/oauth/authorize'
    TOKEN_ENDPOINT: str = 'https://osu.ppy.sh/oauth/token'
    USER_SCOPES: list[str] = field(default_factory=lambda: ['identify', 'public'])
    API_ENDPOINT: str = 'https://osu.ppy.sh/api/v2'   
    ossapi_handler: OssapiAsync = field(init=False)

    OSU_PINK = '#FF66AA'
    OSU_COLOR_HD = '#F1C232'
    OSU_COLOR_HR = '#CC0000'
    OSU_COLOR_EZ = '#6AA84F'
    OSU_COLOR_DT = '#674EA7'
    OSU_COLOR_NC = '#674EA7'
    OSU_COLOR_HT = '#45818E'
    OSU_COLOR_FL = '#434343'

    ### Data
        # search beatmap
    beatmap_search_id: str = field(init=False)
    beatmap_search_results_obj: BeatmapRenderer | None = field(init=False)
    beatmap_search_results_text: str = field(init=False)
        # search user
    user_search_id_or_name: str = field(init=False)
    user_search_results_obj: UserRenderer | None = field(init=False)
    user_search_results_text: str = field(init=False)
    
    ### Controls
    # login
    appbar_login_navigation: ft.AppBar = field(init=False)
    button_login: ft.ElevatedButton = field(init=False)
    # search
    appbar_search_navigation: ft.AppBar = field(init=False)
    container_search_navigation_body: ft.Container = field(init=False)
    navbar_search_navigation: ft.NavigationBar = field(init=False)
    popupmenuitem_logout: ft.PopupMenuItem = field(init=False)
        # search beatmap
    textfield_beatmap_id: ft.TextField = field(init=False)
    button_beatmap_search: ft.ElevatedButton = field(init=False)
    container_beatmap_search_results: ft.Container = field(init=False)
    text_beatmap_search_results: ft.Text = field(init=False)
        # search user
    textfield_user_id_or_name: ft.TextField = field(init=False)
    button_user_search: ft.ElevatedButton = field(init=False)
    container_user_search_results: ft.Container = field(init=False)
    text_user_search_results: ft.Text = field(init=False)

    def __post_init__(self) -> None:
        """after running page.on_login, go to the beatmap search scene of the App (now with an access token inside page.auth)
        likewise, after running page.on_logout, return to the login scene of the App (now without an access token)
        """
        self.client_id: str = os.environ.get('OSU_CLIENT_ID', '')
        self.client_secret: str = os.environ.get('OSU_CLIENT_SECRET', '')

        async def login_actual(_: ft.ControlEvent) -> None:
            self.ossapi_handler = OssapiAsync(
                client_id = int(self.client_id),
                client_secret = self.client_secret,
                access_token = str(self.page.auth.token.access_token) # type: ignore
            )

            await self.display('search')
        
        async def logout_actual(_: ft.ControlEvent) -> None:
            await self.display('login')

        self.page.on_login = login_actual
        self.page.on_logout = logout_actual

    async def login_click(self, _: ft.ControlEvent) -> None:
        provider = OAuthProvider(
            client_id = self.client_id,
            client_secret = self.client_secret,
            authorization_endpoint = App.OAUTH_ENDPOINT,
            token_endpoint = App.TOKEN_ENDPOINT,
            redirect_url = App.REDIRECT_URL,
            user_scopes = self.USER_SCOPES
        )

        await self.page.login_async(provider) # type: ignore

    '''
    async def get_beatmap_raw(self, _: ft.ControlEvent) -> None:
        if not self.textfield_beatmap_id.value:
            self.beatmap_search_results_text = 'Search is empty'
            
            self.text_beatmap_search_results.value = self.beatmap_search_results_text
            await self.page.update_async() # type: ignore
        else:
            self.beatmap_search_id = self.textfield_beatmap_id.value

            if self.page.auth.token.access_token: # type: ignore
                try:
                    access_token: str = self.page.auth.token.access_token # type: ignore

                    endpoint_url: str = f'{self.API_ENDPOINT}/beatmaps/{self.beatmap_search_id}'
                    endpoint_headers: dict[str, str] = {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'Authorization': f'Bearer {access_token}'
                    }

                    async with aiohttp.request(method='get', url=endpoint_url, headers=endpoint_headers) as response:
                        data = await response.json()

                    self.beatmap_search_results_text = str(data)

                    self.text_beatmap_search_results.value = self.beatmap_search_results_text
                    await self.page.update_async() # type: ignore
                except aiohttp.ContentTypeError:
                    self.beatmap_search_results_text = 'Could not retrieve beatmap ID'
                    
                    self.text_beatmap_search_results.value = self.beatmap_search_results_text
                    await self.page.update_async() # type: ignore
            else:
                self.beatmap_search_results_text = 'Could not get authorization'

                self.text_beatmap_search_results.value = self.beatmap_search_results_text
                await self.page.update_async() # type: ignore
    '''

    async def get_beatmap(self, _: ft.ControlEvent) -> None:
        if not self.textfield_beatmap_id.value:
            self.beatmap_search_results_obj = None
            self.beatmap_search_results_text = 'Search is empty'
            
            self.container_beatmap_search_results = ft.Container()
            self.text_beatmap_search_results.value = self.beatmap_search_results_text
            await self.page.update_async() # type: ignore
        else:
            self.beatmap_search_id = self.textfield_beatmap_id.value

            if self.page.auth.token.access_token: # type: ignore
                try:
                    beatmap_ossapi: ossapi.Beatmap = await self.ossapi_handler.beatmap(int(self.beatmap_search_id))
                    self.beatmap_search_results_obj = await BeatmapRenderer.init_async(self, beatmap_ossapi)
                    self.beatmap_search_results_text = ''
                    
                    self.container_beatmap_search_results.content = self.beatmap_search_results_obj.render_osu_beatmap_info()
                    self.text_beatmap_search_results.value = ''
                    await self.page.update_async() # type: ignore
                except:
                    self.beatmap_search_results_obj = None
                    self.beatmap_search_results_text = 'Could not find beatmap'

                    self.container_beatmap_search_results.content = None
                    self.text_beatmap_search_results.value = self.beatmap_search_results_text
                    await self.page.update_async() # type: ignore
            else:
                self.beatmap_search_results_obj = None
                self.beatmap_search_results_text = 'Could not get authorization'

                self.container_beatmap_search_results.content = None
                self.text_beatmap_search_results.value = self.beatmap_search_results_text
                await self.page.update_async() # type: ignore

    '''
    async def get_user_raw(self, _: ft.ControlEvent) -> None:
        if not self.textfield_user_id_or_name.value:
            self.user_search_results_text = 'Search is empty'
            
            self.text_user_search_results.value = self.user_search_results_text
            await self.page.update_async() # type: ignore
        else:
            self.user_search_id_or_name = self.textfield_user_id_or_name.value

            if self.page.auth.token.access_token: # type: ignore
                try:
                    access_token: str = self.page.auth.token.access_token # type: ignore

                    endpoint_url: str = f'{self.API_ENDPOINT}/users/{self.user_search_id_or_name}'
                    endpoint_headers: dict[str, str] = {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'Authorization': f'Bearer {access_token}'
                    }

                    async with aiohttp.request(method='get', url=endpoint_url, headers=endpoint_headers) as response:
                        data = await response.json()

                    self.user_search_results_text = str(data)

                    self.text_user_search_results.value = self.user_search_results_text
                    await self.page.update_async() # type: ignore
                except aiohttp.ContentTypeError:
                    self.user_search_results_text = 'Could not retrieve user ID or username'
                    
                    self.text_user_search_results.value = self.user_search_results_text
                    await self.page.update_async() # type: ignore
            else:
                self.beatmap_search_results_text = 'Could not get authorization'

                self.text_beatmap_search_results.value = self.beatmap_search_results_text
                await self.page.update_async() # type: ignore
    '''

    async def get_user(self, _: ft.ControlEvent) -> None:
        if not self.textfield_user_id_or_name.value:
            self.user_search_results_text = 'Search is empty'
            
            self.text_user_search_results.value = self.user_search_results_text
            await self.page.update_async() # type: ignore
        else:
            self.user_search_id_or_name = self.textfield_user_id_or_name.value

            if self.page.auth.token.access_token: # type: ignore
                try:
                    user_ossapi: ossapi.User = await self.ossapi_handler.user(self.user_search_id_or_name)
                    self.user_search_results_obj = UserRenderer(self, user_ossapi)
                    self.user_search_results_text = ''

                    self.container_user_search_results.content = self.user_search_results_obj.render_osu_user_info()
                    self.text_user_search_results.value = ''
                    await self.page.update_async() # type: ignore
                except:
                    self.user_search_results_obj = None
                    self.user_search_results_text = 'Could not find user'

                    self.container_user_search_results.content = None
                    self.text_user_search_results.value = self.user_search_results_text
                    await self.page.update_async() # type: ignore
            else:
                self.user_search_results_obj = None
                self.user_search_results_text = 'Could not get authorization'

                self.container_user_search_results.content = None
                self.text_user_search_results.value = self.user_search_results_text
                await self.page.update_async() # type: ignore
    
    async def logout_click(self, _: ft.ControlEvent) -> None:
        """use Flet's built-in logout function to clear the page.auth access token and (manually) return to the login page
        """
        await self.page.logout_async()
    
    # ---

    async def display(self, sc:Scene='login', **kwargs:Any) -> None:
        # set the App scene to the inputted scene, or to the login page by default
        self.scene = sc

        # create a new empty View instance to represent the current page
        view: ft.View = ft.View(controls=[])
        view.scroll = ft.ScrollMode.AUTO # set the view to have a vertical scrollbar if content overflows
        
        # add different controls to the View depending on what scene is asked to be displayed
        match self.scene:
            case 'login':
                ### Controls
                self.appbar_beatmap_search_navigation = ft.AppBar(
                    title=ft.Text('osu! API Test', color=ft.colors.BLACK),
                    bgcolor=App.OSU_PINK,
                    automatically_imply_leading=False
                )
                self.button_login = ft.ElevatedButton('Login', on_click=self.login_click)

                ### View
                view.controls.append(self.button_login)
            case 'search':
                ### Data
                self.beatmap_search_id = ''
                self.beatmap_search_results_text = ''

                self.user_search_id_or_name = ''
                self.user_search_results_text = ''

                ### Controls
                self.popupmenuitem_logout = ft.PopupMenuItem(text="Log Out", checked=False, on_click=self.logout_click)
                self.appbar_search_navigation = ft.AppBar(
                    title=ft.Text(value='osu! API Test', color=ft.colors.BLACK),
                    bgcolor=App.OSU_PINK,
                    automatically_imply_leading=False,
                    actions=[
                        ft.PopupMenuButton(
                            items=[
                                self.popupmenuitem_logout
                            ]
                        )
                    ]
                )

                # search beatmap
                self.textfield_beatmap_id = ft.TextField(label='Beatmap ID', value=self.beatmap_search_id, on_submit=self.get_beatmap, width=200, autofocus=True)
                self.button_beatmap_search = ft.ElevatedButton('Search', on_click=self.get_beatmap)
                self.container_beatmap_search_results = ft.Container()
                self.text_beatmap_search_results = ft.Text(value=self.beatmap_search_results_text, color=ft.colors.RED, selectable=True)
                
                # search user
                self.textfield_user_id_or_name = ft.TextField(label='Username or User ID', value=self.user_search_id_or_name, on_submit=self.get_user, width=200, autofocus=True)
                self.button_user_search = ft.ElevatedButton('Search', on_click=self.get_user)
                self.container_user_search_results = ft.Container()
                self.text_user_search_results = ft.Text(value=self.user_search_results_text, color=ft.colors.RED, selectable=True)

                # navigate between searches
                self.container_search_navigation_body = ft.Container()

                # function to change the contents of the navigation body to a specific "scene"
                async def set_navigation_body(navigation_scene:int) -> None:
                    match navigation_scene:
                        case 0:
                            # search beatmap
                            self.container_search_navigation_body.content = ft.Column(
                                controls = [
                                    self.textfield_beatmap_id,
                                    self.button_beatmap_search,
                                    self.container_beatmap_search_results,
                                    self.text_beatmap_search_results
                                ]
                            )
                        case 1:
                            # search user
                            self.container_search_navigation_body.content = ft.Column(
                                controls = [
                                    self.textfield_user_id_or_name,
                                    self.button_user_search,
                                    self.container_user_search_results,
                                    self.text_user_search_results
                                ]
                            )
                        case _:
                            self.container_search_navigation_body.content = ft.Text('Could not navigate click', color=ft.colors.BLACK)
                        
                    await self.page.update_async() # type: ignore

                # set default navigation body to beatmap search
                await set_navigation_body(0)

                # function to set navigation body to whichever Destination is clicked in the Navigation Bar
                async def navigate_click(e: ft.ControlEvent) -> None:
                    await set_navigation_body(e.control.selected_index) # type: ignore
                
                # navigation bar destinations
                self.navbar_search_navigation = ft.NavigationBar(
                    selected_index=0,
                    destinations=[
                        ft.NavigationDestination(
                            label='Beatmap'
                        ),
                        ft.NavigationDestination(
                            label='User'
                        )
                    ],
                    height=80,
                    on_change=navigate_click 
                )
                
                ### View
                view.controls.append(self.appbar_search_navigation)
                view.controls.append(self.container_search_navigation_body)
                view.controls.append(self.navbar_search_navigation)

        self.page.views.append(view)
        await self.page.update_async() # type: ignore

    @classmethod
    async def main(cls, page: ft.Page) -> None:
        page.title = 'osu! API test'
        page.scroll = ft.ScrollMode.AUTO

        await App(page).display()

@dataclass
class BeatmapRenderer:
    ### __init__()
    _app: App
    osu_beatmap: ossapi.Beatmap

    ### Ossapi
    osu_beatmapset: ossapi.Beatmapset = field(init=False)
    osu_beatmap_owner: ossapi.User = field(init=False)
    osu_beatmap_difficulty_attributes: ossapi.models.DifficultyAttributes | None = field(init=False)

    ### Data
    selected_mods_list: list[ModWorthPP] = field(init=False)

    ### Controls
    container_beatmap_metadata: ft.Container = field(init=False)
    image_beatmap_banner: ft.Image = field(init=False)
    text_beatmap_artist_title: ft.Text = field(init=False)
    text_beatmapset_creator: ft.Text = field(init=False)
    text_beatmap_version_owner: ft.Text = field(init=False)
        # beatmap statistics
    container_beatmap_statistics: ft.Container = field(init=False)
    text_beatmap_stars: ft.Text = field(init=False)
    text_beatmap_length: ft.Text = field(init=False)
    text_beatmap_bpm: ft.Text = field(init=False)
    text_beatmap_max_combo: ft.Text = field(init=False)
    text_beatmap_number_of_circles: ft.Text = field(init=False)
    text_beatmap_number_of_sliders: ft.Text = field(init=False)
    text_beatmap_number_of_spinners: ft.Text = field(init=False)
        # beatmap settings
    datatable_beatmap_settings: ft.DataTable = field(init=False)
    text_beatmap_cs: ft.Text = field(init=False)
    text_beatmap_ar: ft.Text = field(init=False)
    text_beatmap_od: ft.Text = field(init=False)
    text_beatmap_hp: ft.Text = field(init=False)
        # beatmap mods
    container_beatmap_mods: ft.Container = field(init=False)
    text_selected_mods: ft.Text = field(init=False)
    button_mod_nm: ft.IconButton = field(init=False)
    button_mod_hd: ft.IconButton = field(init=False)
    button_mod_hr: ft.IconButton = field(init=False)
    button_mod_ez: ft.IconButton = field(init=False)
    button_mod_dt: ft.IconButton = field(init=False)
    button_mod_nc: ft.IconButton = field(init=False)
    button_mod_ht: ft.IconButton = field(init=False)

    def __post_init__(self) -> None:
        self.osu_beatmapset = self.osu_beatmap.beatmapset()

        # --- -----

        self.image_beatmap_banner = ft.Image(
            self.osu_beatmapset.covers.cover_2x,
            width=400,
            fit=ft.ImageFit.CONTAIN,
            gapless_playback=True
        )
        self.text_beatmap_artist_title = ft.Text(
            spans=[
                ft.TextSpan(
                    spans = [
                        ft.TextSpan(
                            text=f'{self.osu_beatmapset.artist}',
                            style=ft.TextStyle(
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.BLACK
                            ),
                            url = f'{self.osu_beatmap.url}'
                        ),
                        ft.TextSpan(text=' - ', style=ft.TextStyle(color=ft.colors.BLACK), url = f'{self.osu_beatmap.url}'),
                        ft.TextSpan(
                            text=f'{self.osu_beatmapset.title}',
                            style=ft.TextStyle(
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.BLACK
                            ),
                            url = f'{self.osu_beatmap.url}'
                        )
                    ]
                )                
            ],
            tooltip=f'{self.osu_beatmapset.artist} - {self.osu_beatmapset.title}',
            size=20,
            selectable=True
        )
        self.text_beatmapset_creator = ft.Text(
            spans=[
                ft.TextSpan(text='Mapset by '),
                ft.TextSpan(
                    text=f'{self.osu_beatmapset.creator}',
                    style=ft.TextStyle(
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLACK
                    ),
                    url=f'https://osu.ppy.sh/u/{self.osu_beatmapset.creator}'
                )
            ],
            tooltip=f'{self.osu_beatmapset.creator}',
            selectable=True,
        )

        # Beatmap Container without diff owner
        self.container_beatmap_body = ft.Container(
            content=ft.Column(
                controls=[
                    self.image_beatmap_banner,
                    self.text_beatmap_artist_title,
                    self.text_beatmapset_creator
                ]
            ),
            bgcolor='#DDDDDD',#App.OSU_PINK,
            padding=ft.padding.all(20)
        )

        # --- -----

        self.text_beatmap_stars = ft.Text(value=f'Stars: {self.osu_beatmap.difficulty_rating}', tooltip=f'{self.osu_beatmap.difficulty_rating}', color=ft.colors.BLACK)
        self.text_beatmap_length = ft.Text(value=f'Length: {self.osu_beatmap.total_length}', tooltip=f'{self.osu_beatmap.total_length}', color=ft.colors.BLACK)
        self.text_beatmap_max_combo = ft.Text(value=f'Max Combo: {self.osu_beatmap.max_combo}', tooltip=f'{self.osu_beatmap.max_combo}', color=ft.colors.BLACK)
        self.text_beatmap_bpm = ft.Text(value=f'BPM: {self.osu_beatmap.bpm:g}' if self.osu_beatmap.bpm else 'BPM: ?', tooltip=f'{self.osu_beatmap.bpm if self.osu_beatmap.bpm else "?"}', color=ft.colors.BLACK) 

        self.container_beatmap_statistics = ft.Container(
            content=ft.Column(
                controls=[
                    self.text_beatmap_stars,
                    self.text_beatmap_length,
                    self.text_beatmap_max_combo,
                    self.text_beatmap_bpm
                ]
            ),
            bgcolor='#DDDDDD',#App.OSU_PINK,
            padding=ft.padding.all(20)
        )

        self.text_beatmap_cs = ft.Text(value=f'{self.osu_beatmap.cs}', tooltip=f'{self.osu_beatmap.cs}')
        self.text_beatmap_ar = ft.Text(value=f'{self.osu_beatmap.ar}', tooltip=f'{self.osu_beatmap.ar}')
        self.text_beatmap_od = ft.Text(value=f'{self.osu_beatmap.accuracy}', tooltip=f'{self.osu_beatmap.accuracy}')
        self.text_beatmap_hp = ft.Text(value=f'{self.osu_beatmap.drain}', tooltip=f'{self.osu_beatmap.drain}')

        self.datatable_beatmap_settings = ft.DataTable(
            columns=[
                ft.DataColumn(
                    label=ft.Container(
                        content=ft.Text(value='CS'),
                        #bgcolor='#FFDDDD',
                        alignment=ft.alignment.center
                    )
                ),
                ft.DataColumn(
                    label=ft.Container(
                        content=ft.Text(value='AR'),
                        #bgcolor='#FFDDDD',
                        alignment=ft.alignment.center
                    )
                ),
                ft.DataColumn(
                    label=ft.Container(
                        content=ft.Text(value='OD'),
                        #bgcolor='#FFDDDD',
                        alignment=ft.alignment.center
                    )
                ),
                ft.DataColumn(
                    label=ft.Container(
                        content=ft.Text(value='HP'),
                        #bgcolor='#FFDDDD',
                        alignment=ft.alignment.center
                    )
                ),
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            content=ft.Container(
                                content=self.text_beatmap_cs,
                                #bgcolor='#FFDDDD',
                                alignment=ft.alignment.center
                            )
                        ),
                        ft.DataCell(
                            content=ft.Container(
                                content=self.text_beatmap_ar,
                                #bgcolor='#FFDDDD',
                                alignment=ft.alignment.center
                            )
                        ),
                        ft.DataCell(
                            content=ft.Container(
                                content=self.text_beatmap_od,
                                #bgcolor='#FFDDDD',
                                alignment=ft.alignment.center
                            )
                        ),
                        ft.DataCell(
                            content=ft.Container(
                                content=self.text_beatmap_hp,
                                #bgcolor='#FFDDDD',
                                alignment=ft.alignment.center
                            )
                        ),
                    ]
                )
            ],
                # borders
            border=ft.border.all(2, "black"),
            vertical_lines=ft.border.BorderSide(1, "black"),
            horizontal_lines=ft.border.BorderSide(1, "black"),
                # padding (column)
            horizontal_margin=15,
            column_spacing=15*2, # 2x horizontal margin
                # heading row
            heading_row_height=25,
            heading_row_color=ft.colors.WHITE,
            heading_text_style=ft.TextStyle(color=ft.colors.BLACK),
                # data row
            data_row_min_height=25,
            data_row_color=ft.colors.WHITE,
            data_text_style=ft.TextStyle(color=ft.colors.BLACK)
        )

        # --- -----
        
        self.selected_mods_list = []
        self.text_selected_mods = ft.Text(
            value=f'Mods: {ossapi.Mod(self.selected_mods_list)}',
            tooltip=f'{ossapi.Mod(self.selected_mods_list)}'
        )

        # NoMod
        self.button_mod_nm = ft.IconButton(
            content=ft.Text('NM'),
            on_click=self.toggle_mod_button('NM')
        )

        # HD
        self.button_mod_hd = ft.IconButton(
            content=ft.Text('HD'),
            on_click=self.toggle_mod_button('HD')
        )
        
        # HR, EZ
        self.button_mod_hr = ft.IconButton(
            content=ft.Text('HR'),
            on_click=self.toggle_mod_button('HR')
        )
        self.button_mod_ez = ft.IconButton(
            content=ft.Text('EZ'),
            on_click=self.toggle_mod_button('EZ')
        )

        # DT, NC, HT
        self.button_mod_dt = ft.IconButton(
            content=ft.Text('DT'),
            on_click=self.toggle_mod_button('DT')
        )
        self.button_mod_nc = ft.IconButton(
            content=ft.Text('NC'),
            on_click=self.toggle_mod_button('NC')
        )
        self.button_mod_ht = ft.IconButton(
            content=ft.Text('HT'),
            on_click=self.toggle_mod_button('HT')
        )

        # FL
        self.button_mod_fl = ft.IconButton(
            content=ft.Text('FL'),
            on_click=self.toggle_mod_button('FL')
        )

        # NF
        self.button_mod_nf = ft.IconButton(
            content=ft.Text('NF'),
            on_click=self.toggle_mod_button('NF')
        )

        # SO
        self.button_mod_so = ft.IconButton(
            content=ft.Text('SO'),
            on_click=self.toggle_mod_button('SO')
        )

        self.container_beatmap_mods = ft.Container(
            content=ft.Column(
                controls=[
                    self.text_selected_mods,
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    self.button_mod_nm
                                ]
                            ),
                            ft.Column(
                                controls=[
                                    self.button_mod_hd
                                ]
                            ),
                            ft.Column(
                                controls=[
                                    self.button_mod_hr,
                                    self.button_mod_ez
                                ]
                            ),
                            ft.Column(
                                controls=[
                                    self.button_mod_dt,
                                    self.button_mod_nc,
                                    self.button_mod_ht,
                                ]
                            ),
                            ft.Column(
                                controls=[
                                    self.button_mod_fl
                                ]
                            ),
                            ft.Column(
                                controls=[
                                    self.button_mod_nf
                                ]
                            ),
                            ft.Column(
                                controls=[
                                    self.button_mod_so
                                ]
                            )
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.START
                    )
                ]
            ),
            bgcolor='#DDDDDD',#App.OSU_PINK,
            padding=ft.padding.all(20)
        )

    async def _post_init_async(self):
        # await coroutine to get the user that mapped the beatmap
            # ignore type until Ossapi fixes the type hint of user() to be Union[User, Awaitable[User]] instead of just User
        #assert isawaitable(self.osu_beatmap.user())
        self.osu_beatmap_owner = await self.osu_beatmap.user() # type: ignore       
        assert isinstance(self.osu_beatmap_owner, ossapi.User)

        # --- -----

        self.text_beatmap_version_owner = ft.Text(
            spans=[
                ft.TextSpan(text='[', style=ft.TextStyle(color=ft.colors.BLACK)),
                ft.TextSpan(
                    text=f'{self.osu_beatmap.version}',
                    style=ft.TextStyle(
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLACK
                    ),
                ),
                ft.TextSpan(text='] mapped by ', style=ft.TextStyle(color=ft.colors.BLACK)),
                ft.TextSpan(
                    text=f'{self.osu_beatmap_owner.username}',
                    style=ft.TextStyle(
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLACK
                    ),
                    url=f'https://osu.ppy.sh/u/{self.osu_beatmap_owner.username}'
                )
            ],
            selectable=True
        )
        
        # Beatmap Container with diff owner
        self.container_beatmap_metadata = ft.Container(
            content=ft.Column(
                controls=[
                    self.image_beatmap_banner,
                    self.text_beatmap_artist_title,
                    self.text_beatmapset_creator,
                    self.text_beatmap_version_owner
                ]
            ),
            bgcolor='#DDDDDD',#App.OSU_PINK,
            padding=ft.padding.all(20)
        )
    
    def toggle_mod_button(self, mod:ModWorthPP | Literal['NM']):
        async def callback(_: ft.ControlEvent) -> None:
            if mod == 'NM':
                self.selected_mods_list = []
            else:
                if mod in self.selected_mods_list:
                    self.selected_mods_list = [selected_mod for selected_mod in self.selected_mods_list if selected_mod != mod]
                else:
                    # dict denoting a list of all mods that conflict with a given mod
                    conflict_mods: dict[ModWorthPP, list[ModWorthPP]] = {
                        'HR': ['EZ'],
                        'EZ': ['HR'],
                        'DT': ['NC', 'HT'],
                        'NC': ['DT', 'HT'],
                        'HT': ['DT', 'NC']
                    }

                    # remove all mods that conflict with a newly selected mod
                    self.selected_mods_list = [selected_mod for selected_mod in self.selected_mods_list if selected_mod not in conflict_mods.get(mod, [])]

                    # add the actual mod to the list of selected mods
                    self.selected_mods_list.append(mod)

            # store difficulty attributes in instance variable to preserve API call results
            self.osu_beatmap_difficulty_attributes = await self._app.ossapi_handler.beatmap_attributes(self.osu_beatmap.id, mods=ossapi.Mod(self.selected_mods_list))

            # ---

            ### update beatmap settings based on mods, text rounded off to 2 decimal places, tooltips with exact value
            
            # Stars
            self.text_beatmap_stars.value = f'Stars: {round(self.osu_beatmap_difficulty_attributes.attributes.star_rating, 2)}'
            self.text_beatmap_stars.tooltip = f'{self.osu_beatmap_difficulty_attributes.attributes.star_rating}'
            
            # Length, BPM
            if 'DT' in self.selected_mods_list or 'NC' in self.selected_mods_list:
                self.text_beatmap_length.value = f'Length: {math.floor(self.osu_beatmap.total_length * 2/3)}'
                self.text_beatmap_length.tooltip = f'{math.floor(self.osu_beatmap.total_length * 2/3)}'
                self.text_beatmap_bpm.value = f'BPM: {round(self.osu_beatmap.bpm * 3/2, 3):g}' if self.osu_beatmap.bpm is not None else 'BPM: ?'
                self.text_beatmap_bpm.tooltip = f'{(self.osu_beatmap.bpm * 3/2):g}' if self.osu_beatmap.bpm is not None else '?'
            elif 'HT' in self.selected_mods_list:
                self.text_beatmap_length.value = f'Length: {math.floor(self.osu_beatmap.total_length * 4/3)}'
                self.text_beatmap_length.tooltip = f'{math.floor(self.osu_beatmap.total_length * 4/3)}'
                self.text_beatmap_bpm.value = f'BPM: {round(self.osu_beatmap.bpm * 3/4, 3):g}' if self.osu_beatmap.bpm is not None else 'BPM: ?'
                self.text_beatmap_bpm.tooltip = f'{(self.osu_beatmap.bpm * 3/4):g}' if self.osu_beatmap.bpm is not None else '?'
            else:
                self.text_beatmap_length.value = f'Length: {self.osu_beatmap.total_length}'
                self.text_beatmap_length.tooltip = f'{self.osu_beatmap.total_length}'
                self.text_beatmap_bpm.value = f'BPM: {self.osu_beatmap.bpm:g}' if self.osu_beatmap.bpm is not None else 'BPM: ?'
                self.text_beatmap_bpm.tooltip = f'{self.osu_beatmap.bpm:g}' if self.osu_beatmap.bpm is not None else '?'
            
            # CS
            self.text_beatmap_cs.value = f'{round(get_beatmap_cs_with_mods(self.osu_beatmap.cs, self.selected_mods_list), 2):g}'
            self.text_beatmap_cs.tooltip = f'{get_beatmap_cs_with_mods(self.osu_beatmap.cs, self.selected_mods_list):g}'

            # AR
            if self.osu_beatmap_difficulty_attributes.attributes.approach_rate is not None:
                self.text_beatmap_ar.value = f'{round(self.osu_beatmap_difficulty_attributes.attributes.approach_rate, 2):g}'
                self.text_beatmap_ar.tooltip = f'{self.osu_beatmap_difficulty_attributes.attributes.approach_rate:g}'
            else:
                self.text_beatmap_ar.value = '?'
                self.text_beatmap_ar.tooltip = '?'
            
            # OD
            if self.osu_beatmap_difficulty_attributes.attributes.overall_difficulty is not None:
                self.text_beatmap_od.value = f'{round(self.osu_beatmap_difficulty_attributes.attributes.overall_difficulty, 2):g}'
                self.text_beatmap_od.tooltip = f'{self.osu_beatmap_difficulty_attributes.attributes.overall_difficulty:g}'
            else:
                self.text_beatmap_od.value = '?'
                self.text_beatmap_od.tooltip = '?'
            
            # HP
            self.text_beatmap_hp.value = f'{round(get_beatmap_hp_with_mods(self.osu_beatmap.drain, self.selected_mods_list), 2):g}'
            self.text_beatmap_hp.tooltip = f'{get_beatmap_hp_with_mods(self.osu_beatmap.drain, self.selected_mods_list):g}'

            # ---

            # change color of beatmap settings depending on mod affecting each stat
            # if FL is detected, override only Stars
            if 'FL' in self.selected_mods_list:
                self.text_beatmap_stars.color = App.OSU_COLOR_FL
            # if HR/EZ/NM, override main color for all settings
            if 'HR' in self.selected_mods_list:
                self.text_beatmap_stars.color = App.OSU_COLOR_HR
                self.text_beatmap_cs.color = App.OSU_COLOR_HR
                self.text_beatmap_ar.color = App.OSU_COLOR_HR
                self.text_beatmap_od.color = App.OSU_COLOR_HR
                self.text_beatmap_hp.color = App.OSU_COLOR_HR
            elif 'EZ' in self.selected_mods_list:
                self.text_beatmap_stars.color = App.OSU_COLOR_EZ
                self.text_beatmap_cs.color = App.OSU_COLOR_EZ
                self.text_beatmap_ar.color = App.OSU_COLOR_EZ
                self.text_beatmap_od.color = App.OSU_COLOR_EZ
                self.text_beatmap_hp.color = App.OSU_COLOR_EZ
            else:
                self.text_beatmap_stars.color = ft.colors.BLACK
                self.text_beatmap_cs.color = ft.colors.BLACK
                self.text_beatmap_ar.color = ft.colors.BLACK
                self.text_beatmap_od.color = ft.colors.BLACK
                self.text_beatmap_hp.color = ft.colors.BLACK
            # if DT/NC/HT is detected, override only Stars, Length, BPM, AR, and OD
            if 'DT' in self.selected_mods_list or 'NC' in self.selected_mods_list:
                self.text_beatmap_stars.color = App.OSU_COLOR_DT
                self.text_beatmap_length.color = App.OSU_COLOR_DT
                self.text_beatmap_bpm.color = App.OSU_COLOR_DT
                self.text_beatmap_ar.color = App.OSU_COLOR_DT
                self.text_beatmap_od.color = App.OSU_COLOR_DT
            elif 'HT' in self.selected_mods_list:
                self.text_beatmap_stars.color = App.OSU_COLOR_HT
                self.text_beatmap_length.color = App.OSU_COLOR_HT
                self.text_beatmap_bpm.color = App.OSU_COLOR_HT
                self.text_beatmap_ar.color = App.OSU_COLOR_HT
                self.text_beatmap_od.color = App.OSU_COLOR_HT
            else:
                self.text_beatmap_length.color = ft.colors.BLACK
                self.text_beatmap_bpm.color = ft.colors.BLACK

            # update displayed list of selected mods
            self.text_selected_mods.value = f'Mods: {ossapi.Mod(self.selected_mods_list)}'
            self.text_selected_mods.tooltip = f'{ossapi.Mod(self.selected_mods_list)}'

            await self._app.page.update_async() # type: ignore

        return callback

    @classmethod
    async def init_async(cls, app:App, osu_beatmap:ossapi.Beatmap) -> BeatmapRenderer:
        beatmap_renderer = BeatmapRenderer(app, osu_beatmap)
        await beatmap_renderer._post_init_async()
        return beatmap_renderer

    def render_osu_beatmap_info(self) -> ft.Container:
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            self.container_beatmap_metadata,
                            self.container_beatmap_statistics,
                        ]
                    ),
                    ft.Column(
                        controls=[
                            self.datatable_beatmap_settings,
                            self.container_beatmap_mods
                        ]
                    )
                ],
                vertical_alignment=ft.CrossAxisAlignment.START
            )
        )

@dataclass
class UserRenderer:
    ###__init__()
    _app: App
    osu_user: ossapi.User

    ### Ossapi
    osu_user_statistics: ossapi.models.UserStatistics = field(init=False)
    osu_user_country: ossapi.models.Country = field(init=False)

    ### Controls
    container_user_body: ft.Container = field(init=False)
    image_user_profile_url: ft.Image = field(init=False)
    text_user_username: ft.Text = field(init=False)
    text_user_title: ft.Text = field(init=False)
    text_user_country: ft.Text = field(init=False)

    text_user_rank: ft.Text = field(init=False)
    text_user_country_rank: ft.Text = field(init=False)
    text_user_pp: ft.Text = field(init=False)
    text_user_accuracy: ft.Text = field(init=False)
    text_user_ranked_score: ft.Text = field(init=False)

    def __post_init__(self):
        if self.osu_user.statistics:
            self.osu_user_statistics = self.osu_user.statistics
        if self.osu_user.country:
            self.osu_user_country = self.osu_user.country

        # --- -----

        # User Avatar
        self.image_user_profile_url = ft.Image(
            src=self.osu_user.avatar_url,
            width=150,
            height=150,
            fit=ft.ImageFit.CONTAIN
        )

        # User Identification
        self.text_user_username = ft.Text(
            value=f'{self.osu_user.username}',
            tooltip=f'{self.osu_user.username}',
            color=ft.colors.BLACK,
            selectable=True
        )
        self.text_user_title = ft.Text(
            value=f'"{self.osu_user.title}"',
            tooltip=f'"{self.osu_user.title}"',
            color=ft.colors.BLACK,
            selectable=True
        )
        self.text_user_country = ft.Text(
            value=f'{self.osu_user.country_code} {self.osu_user_country.name}',
            tooltip=f'{self.osu_user_country.name}',
            color=ft.colors.BLACK,
            selectable=True
        )

        # User Statistics
        self.text_user_rank = ft.Text(
            spans=[
                ft.TextSpan(text='Global: ', style=ft.TextStyle(color=ft.colors.BLACK)),
                ft.TextSpan(
                    text=f'#{self.osu_user_statistics.global_rank if self.osu_user_statistics.global_rank else "--"}',
                    style=ft.TextStyle(
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLACK
                    )
                )
            ],
            tooltip=f'Global: #{self.osu_user_statistics.global_rank if self.osu_user_statistics.global_rank else "--"}',
            selectable=True
        )
        self.text_user_country_rank = ft.Text(
            spans=[
                ft.TextSpan(text='Country: ', style=ft.TextStyle(color=ft.colors.BLACK)),
                ft.TextSpan(
                    text=f'#{self.osu_user_statistics.country_rank if self.osu_user_statistics.country_rank else "--"}' ,
                    style=ft.TextStyle(
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLACK
                    )
                )
            ],
            tooltip=f'Country: #{self.osu_user_statistics.country_rank if self.osu_user_statistics.country_rank else "--"}',
            selectable=True
        )
        self.text_user_pp = ft.Text(
            spans=[
                ft.TextSpan(text='pp: ', style=ft.TextStyle(color=ft.colors.BLACK)),
                ft.TextSpan(
                    text='{:,}pp'.format(self.osu_user_statistics.pp),
                    style=ft.TextStyle(
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLACK
                    )
                )
            ],
            tooltip='{:,}pp'.format(self.osu_user_statistics.pp),
            selectable=True
        )
        self.text_user_accuracy = ft.Text(
            spans=[
                ft.TextSpan(text='Hit Accuracy: ', style=ft.TextStyle(color=ft.colors.BLACK)),
                ft.TextSpan(
                    text=f'{self.osu_user_statistics.hit_accuracy}%',
                    style=ft.TextStyle(
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLACK
                    )
                )
            ],
            tooltip=f'Hit Accuracy: {self.osu_user_statistics.hit_accuracy}%',
            selectable=True
        )
        self.text_user_ranked_score = ft.Text(
            spans=[
                ft.TextSpan(text='Ranked Score: ', style=ft.TextStyle(color=ft.colors.BLACK)),
                ft.TextSpan(
                    text='{:,}'.format(self.osu_user_statistics.ranked_score), # format ranked score with commas between every thousand
                    style=ft.TextStyle(
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLACK
                    )
                )
            ],
            tooltip='Ranked Score: {:,}'.format(self.osu_user_statistics.ranked_score),
            selectable=True
        )

        # Beatmap Container
        self.container_user_body = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self.image_user_profile_url,
                            ft.Column(
                                controls=[
                                    self.text_user_username,
                                    self.text_user_title,
                                    self.text_user_country,
                                    self.text_user_rank,
                                    self.text_user_country_rank
                                ] if self.osu_user.title else [
                                    self.text_user_username,
                                    self.text_user_country,
                                    self.text_user_rank,
                                    self.text_user_country_rank
                                ]
                            )
                        ]
                    ),
                    self.text_user_ranked_score,
                    self.text_user_pp,
                    self.text_user_accuracy
                ]
            ),
            bgcolor='#DDDDDD',#App.OSU_PINK,
            width=500,
            padding=ft.padding.all(20)
        )

        # --- -----

    def render_osu_user_info(self) -> ft.Container:
        return self.container_user_body

ft.app(target=App.main, port=80, view=ft.AppView.WEB_BROWSER, web_renderer=ft.WebRenderer.HTML) # type: ignore