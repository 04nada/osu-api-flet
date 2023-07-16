from __future__ import annotations
from dataclasses import dataclass, field
import flet as ft
from flet.auth.oauth_provider import OAuthProvider
import aiohttp
#import pprint
from typing import Any, Literal
import os

# ---

Scene = Literal['login', 'search_beatmap', 'search_user']

@dataclass
class App:
    page: ft.Page

    ### API Access 
    REDIRECT_URL: str = 'http://localhost/api/oauth/redirect'

    CLIENT_ID: str = os.environ.get('OSU_CLIENT_ID', '')
    CLIENT_SECRET: str = os.environ.get('OSU_CLIENT_SECRET', '')
    OAUTH_ENDPOINT: str = 'https://osu.ppy.sh/oauth/authorize'
    TOKEN_ENDPOINT: str = 'https://osu.ppy.sh/oauth/token'
    USER_SCOPES: list[str] = field(default_factory=lambda: ['identify', 'public'])

    API_ENDPOINT: str = 'https://osu.ppy.sh/api/v2'   

    OSU_PINK = '#FF66AA'

    ### Data
    beatmap_search_id: str = field(init=False)
    beatmap_search_results_text: str = field(init=False)

    user_search_id_or_name: str = field(init=False)
    user_search_results_text: str = field(init=False)
    
    ### Controls
    appbar_login_navigation: ft.AppBar = field(init=False)
    button_login: ft.ElevatedButton = field(init=False)

    appbar_beatmap_search_navigation: ft.AppBar = field(init=False)
    navbar_beatmap_search_navigation: ft.NavigationBar = field(init=False)
    popupmenuitem_logout: ft.PopupMenuItem = field(init=False)
    textfield_beatmap_id: ft.TextField = field(init=False)
    button_beatmap_search: ft.ElevatedButton = field(init=False)
    text_beatmap_search_results: ft.Text = field(init=False)

    appbar_user_search_navigation: ft.AppBar = field(init=False)
    navbar_user_search_navigation: ft.NavigationBar = field(init=False)
    textfield_user_id_or_name: ft.TextField = field(init=False)
    button_user_search: ft.ElevatedButton = field(init=False)
    text_user_search_results: ft.Text = field(init=False)

    def __post_init__(self) -> None:
        """after running page.on_login, go to the beatmap search scene of the App (now with an access token inside page.auth)
        likewise, after running page.on_logout, return to the login scene of the App (now without an access token)
        """
        async def login_actual(_) -> None:
            await self.display('search_beatmap')
        
        async def logout_actual(_) -> None:
            await self.display('login')

        self.page.on_login = login_actual
        self.page.on_logout = logout_actual

    async def login_click(self, _) -> None:
        provider = OAuthProvider(
            client_id = App.CLIENT_ID,
            client_secret = App.CLIENT_SECRET,
            authorization_endpoint = App.OAUTH_ENDPOINT,
            token_endpoint = App.TOKEN_ENDPOINT,
            redirect_url = App.REDIRECT_URL,
            user_scopes = App.USER_SCOPES
        )

        await self.page.login_async(provider) # type: ignore

    async def get_beatmap(self, _) -> None:
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
    
    async def get_user(self, _) -> None:
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
            case 'search_beatmap':
                ### Data
                self.beatmap_search_id = ''
                self.beatmap_search_results_text = ''

                ### Controls
                self.popupmenuitem_logout = ft.PopupMenuItem(text="Log Out", checked=False, on_click=self.logout_click) # type: ignore
                self.appbar_beatmap_search_navigation = ft.AppBar(
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

                async def navigate_click(e: ft.ControlEvent) -> None:
                    match int(e.control.selected_index): # type: ignore
                        case 0:
                            await self.display('search_beatmap')
                        case 1:
                            await self.display('search_user')
                        case _:
                            pass

                self.navbar_beatmap_search_navigation = ft.NavigationBar(
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

                self.textfield_beatmap_id = ft.TextField(label='Beatmap ID', value=self.beatmap_search_id, on_submit=self.get_beatmap, width=200, autofocus=True) # type: ignore
                self.button_beatmap_search = ft.ElevatedButton('Search', on_click=self.get_beatmap) # type: ignore
                self.text_beatmap_search_results = ft.Text(value=self.beatmap_search_results_text, color='red', selectable=True)

                ### View
                view.controls.append(self.appbar_beatmap_search_navigation)
                view.controls.append(self.navbar_beatmap_search_navigation)
                view.controls.append(self.textfield_beatmap_id)
                view.controls.append(self.button_beatmap_search)
                view.controls.append(self.text_beatmap_search_results)
            case 'search_user':
                ### Data
                self.user_search_id_or_name = ''
                self.user_search_results_text = ''

                ### Controls
                self.popupmenuitem_logout = ft.PopupMenuItem(text="Log Out", checked=False, on_click=self.logout_click) # type: ignore
                self.appbar_user_search_navigation = ft.AppBar(
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

                async def navigate_click(e: ft.ControlEvent) -> None:
                    match int(e.control.selected_index): # type: ignore
                        case 0:
                            await self.display('search_beatmap')
                        case 1:
                            await self.display('search_user')
                        case _:
                            pass

                self.navbar_user_search_navigation = ft.NavigationBar(
                    selected_index=1,
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

                self.textfield_user_id_or_name = ft.TextField(label='Username or User ID', value=self.user_search_id_or_name, on_submit=self.get_user, width=200, autofocus=True) # type: ignore
                self.button_user_search = ft.ElevatedButton('Search', on_click=self.get_user) # type: ignore
                self.text_user_search_results = ft.Text(value=self.user_search_results_text, color='red', selectable=True)

                ### View
                view.controls.append(self.appbar_user_search_navigation)
                view.controls.append(self.navbar_user_search_navigation)
                view.controls.append(self.textfield_user_id_or_name)
                view.controls.append(self.button_user_search)
                view.controls.append(self.text_user_search_results)

        self.page.views.append(view)
        await self.page.update_async() # type: ignore

    @classmethod
    async def main(cls, page: ft.Page) -> None:
        page.title = 'osu! API test'
        page.scroll = ft.ScrollMode.AUTO

        await App(page).display()

ft.app(target=App.main, port=80, view=ft.WEB_BROWSER) # type: ignore