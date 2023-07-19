from __future__ import annotations
from typing import Any, Literal
from dataclasses import dataclass, field
import flet as ft
from flet_runtime.auth.oauth_provider import OAuthProvider # type: ignore
#import aiohttp
import os
import ossapi as ossapi # type: ignore
import ossapi.models # type: ignore
from ossapi import OssapiAsync # type: ignore

# ---

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

        async def login_actual(_) -> None:
            self.ossapi_handler = OssapiAsync(
                client_id = int(self.client_id),
                client_secret = self.client_secret,
                access_token = str(self.page.auth.token.access_token) # type: ignore
            )

            await self.display('search')
        
        async def logout_actual(_) -> None:
            await self.display('login')

        self.page.on_login = login_actual
        self.page.on_logout = logout_actual

    async def login_click(self, _) -> None:
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
    async def get_beatmap_raw(self, _) -> None:
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

    async def get_beatmap(self, _) -> None:
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
                    self.beatmap_search_results_obj = BeatmapRenderer(self, beatmap_ossapi)
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
    async def get_user_raw(self, _) -> None:
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

    async def get_user(self, _) -> None:
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

    async def logout_click(self, _) -> None:
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
                    title=ft.Text('osu! API Test'),
                    bgcolor=App.OSU_PINK,
                    automatically_imply_leading=False
                )
                self.button_login = ft.ElevatedButton('Login', on_click=self.login_click) # type: ignore

                ### View
                view.controls.append(self.button_login)
            case 'search':
                ### Data
                self.beatmap_search_id = ''
                self.beatmap_search_results_text = ''

                self.user_search_id_or_name = ''
                self.user_search_results_text = ''

                ### Controls
                self.popupmenuitem_logout = ft.PopupMenuItem(text="Log Out", checked=False, on_click=self.logout_click) # type: ignore
                self.appbar_search_navigation = ft.AppBar(
                    title=ft.Text('osu! API Test'),
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
                self.textfield_beatmap_id = ft.TextField(label='Beatmap ID', value=self.beatmap_search_id, on_submit=self.get_beatmap, width=200, autofocus=True) # type: ignore
                self.button_beatmap_search = ft.ElevatedButton('Search', on_click=self.get_beatmap) # type: ignore
                self.container_beatmap_search_results = ft.Container(content=None)
                self.text_beatmap_search_results = ft.Text(value=self.beatmap_search_results_text, color='red', selectable=True)
                
                # search user
                self.textfield_user_id_or_name = ft.TextField(label='Username or User ID', value=self.user_search_id_or_name, on_submit=self.get_user, width=200, autofocus=True) # type: ignore
                self.button_user_search = ft.ElevatedButton('Search', on_click=self.get_user) # type: ignore
                self.container_user_search_results = ft.Container()
                self.text_user_search_results = ft.Text(value=self.user_search_results_text, color='red', selectable=True)

                # navigate between searches
                self.container_search_navigation_body = ft.Container(
                    content=ft.Column(
                        controls = [
                            self.textfield_beatmap_id,
                            self.button_beatmap_search,
                            self.container_beatmap_search_results,
                            self.text_beatmap_search_results
                        ]
                    )
                )

                async def navigate_click(e: ft.ControlEvent) -> None:
                    match int(e.control.selected_index): # type: ignore
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
                            self.container_search_navigation_body.content = ft.Text('Could not navigate click')
                        
                    await self.page.update_async() # type: ignore
                
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

    ### Controls
    container_beatmap_body: ft.Container = field(init=False)
    image_beatmap_banner: ft.Image = field(init=False)
    text_beatmap_artist_title: ft.Text = field(init=False)

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
            value=f'{self.osu_beatmapset.artist} - {self.osu_beatmapset.title}'
        )

        # Beatmap Container
        self.container_beatmap_body = ft.Container(
            content=ft.Column(
                controls=[
                    self.image_beatmap_banner,
                    self.text_beatmap_artist_title
                ]
            ),
            bgcolor='#DDDDDD',#App.OSU_PINK,
            padding=ft.padding.all(20)
        )

    def render_osu_beatmap_info(self) -> ft.Container:
        return self.container_beatmap_body

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

    def render_osu_user_info(self) -> ft.Container:
        # User Avatar
        self.image_user_profile_url = ft.Image(
            src=self.osu_user.avatar_url,
            width=150,
            height=150,
            fit=ft.ImageFit.CONTAIN,
            gapless_playback=True,
        )

        # User Identification
        self.text_user_username = ft.Text(
            value=f'{self.osu_user.username}',
            selectable=True
        )
        self.text_user_title = ft.Text(
            value=f'"{self.osu_user.title}"',
            selectable=True
        )
        self.text_user_country = ft.Text(
            value=f'{self.osu_user.country_code} {self.osu_user_country.name}',
            selectable=True
        )

        # User Statistics
        self.text_user_rank = ft.Text(
            value=f'Global: #{self.osu_user_statistics.global_rank}' if self.osu_user_statistics.global_rank else 'Global: #--',
            selectable=True
        )
        self.text_user_country_rank = ft.Text(
            value=f'Country: #{self.osu_user_statistics.country_rank}' if self.osu_user_statistics.country_rank else 'Country: #--',
            selectable=True
        )
        self.text_user_pp = ft.Text(
            value=f'pp: {self.osu_user_statistics.pp}',
            selectable=True
        )
        self.text_user_accuracy = ft.Text(
            value=f'Hit Accuracy: {self.osu_user_statistics.hit_accuracy}',
            selectable=True
        )
        self.text_user_ranked_score = ft.Text(
            value=f'Ranked Score: {self.osu_user_statistics.ranked_score}',
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

        return self.container_user_body

ft.app(target=App.main, port=80, view=ft.WEB_BROWSER, web_renderer=ft.WebRenderer.HTML) # type: ignore