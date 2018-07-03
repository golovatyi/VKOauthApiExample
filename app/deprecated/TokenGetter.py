#coding utf8
import requests
import getpass
import os
import urllib3
import shutil

from html.parser import HTMLParser
#TODO: переписать весь модуль
class FormParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.url         = None
        self.denial_url  = None
        self.params      = {}
        self.method      = 'GET'
        self.in_form     = False
        self.in_denial   = False
        self.form_parsed = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == 'form':
            if self.in_form:
                raise RuntimeError('Nested form tags are not supported yet')
            else:
                self.in_form = True
        if not self.in_form:
            return

        attrs = dict((name.lower(), value) for name, value in attrs)

        if tag == 'form':
            self.url = attrs['action']
            if 'method' in attrs:
                self.method = attrs['method']
        elif tag == 'input' and 'type' in attrs and 'name' in attrs:
            if attrs['type'] in ['hidden', 'text', 'password']:
                self.params[attrs['name']] = attrs['value'] if 'value' in attrs else ''
        elif tag == 'input' and 'type' in attrs:
            if attrs['type'] == 'submit':
                self.params['submit_allow_access'] = True
        elif tag == 'div' and 'class' in attrs:
            if attrs['class'] == 'near_btn':
                self.in_denial = True
        elif tag == 'a' and 'href' in attrs and self.in_denial:
            self.denial_url = attrs['href']

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == 'form':
            if not self.in_form:
                raise RuntimeError('Unexpected end of <form>')
            self.form_parsed = True
            self.in_form = False
        elif tag == 'div' and self.in_denial:
            self.in_denial = False


class VKAuth(object):

    def __init__(self, permissions, app_id, api_v, email=None, pswd=None, two_factor_auth=False, security_code=None, auto_access=True):
        """
        @args:
            permissions: list of Strings with permissions to get from API
            app_id: (String) vk app id that one can get from vk.com
            api_v: (String) vk API version
        """

        self.session        = requests.Session()
        self.form_parser    = FormParser()
        self._user_id       = None
        self._access_token  = None
        self.response       = None

        self.permissions    = permissions
        self.api_v          = api_v
        self.app_id         = app_id
        self.two_factor_auth= two_factor_auth
        self.security_code  = security_code
        self.email          = email
        self.pswd           = pswd
        self.auto_access    = auto_access

        if security_code != None and two_factor_auth == False:
            raise RuntimeError('Security code provided for non-two-factor authorization')

    def auth(self):
        """
            1. Asks vk.com for app authentication for a user
            2. If user isn't logged in, asks for email and password
            3. Retreives access token and user id
        """
        api_auth_url = 'https://oauth.vk.com/authorize'
        app_id = self.app_id
        permissions = self.permissions
        redirect_uri = 'https://oauth.vk.com/blank.html'
        display = 'mobile'
        api_version = self.api_v
#https://oauth.vk.com/authorize?client_id=3682744&scope=stats,wall&redirect_uri=https://oauth.vk.com/blank.html&%20display=page&v=5.8&response_type=token
        auth_url_template = '{0}?client_id={1}&scope={2}&redirect_uri={3}&display={4}&v={5}&response_type=token'
        auth_url = auth_url_template.format(api_auth_url, app_id, permissions, redirect_uri, display, api_version)

        self.response = self.session.get(auth_url)

        #look for <form> element in response html and parse it
        if not self._parse_form():
            raise RuntimeError('No <form> element found. Please, check url address')
        else:
            # try to log in with email and password (stored or expected to be entered)
            while not self._log_in():
                pass;

            # handling two-factor authentication
            # expecting a security code to enter here
            if self.two_factor_auth:
                self._two_fact_auth()


            #TODO: добавить чекер капчи


            # allow vk to use this app and access self.permissions
            self._allow_access()


            # now get _access_token and _user_id
            self._get_params()

            # close current session
            #self._close()

    def get_token(self):
        """
            @return value:
                None if _access_token == None
                (String) access_token that was retreived in self.auth() method
        """
        return self._access_token

    def get_user_id(self):
        """
            @return value:
                None if _user_id == None
                (String) _user_id that was retreived in self.auth() method
        """
        return self._user_id

    def _parse_form(self):

        self.form_parser = FormParser()
        parser = self.form_parser

        try:
            parser.feed(str(self.response.content))
        except:
            print('Unexpected error occured while looking for <form> element')
            return False

        return True

    def _submit_form(self, *params):

        parser = self.form_parser

        if parser.method == 'post':
            payload = parser.params
            payload.update(*params)
            try:
                self.response = self.session.post(parser.url, data=payload)
            except requests.exceptions.RequestException as err:
                print('provided ' + str(parser.url))
                new_url='https://m.vk.com'+str(parser.url)
                self.response = self.session.post(new_url,data=payload)

            except requests.exceptions.HTTPError as err:
                print("Error: ", err)
            except requests.exceptions.ConnectionError as err:
                print("Error: ConnectionError\n", err)
            except requests.exceptions.Timeout as err:
                print("Error: Timeout\n", err)
            except:
                print("Unexpecred error occured")

        else:
            self.response = None

    def _log_in(self):

        if self.email == None:
            self.email = ''
            while self.email.strip() == '':
                self.email = input('Enter an email to log in: ')

        if self.pswd == None:
            self.pswd = ''
            while self.pswd.strip() == '':
                self.pswd = getpass.getpass('Enter the password: ')

        self._submit_form({'email': self.email, 'pass': self.pswd})

        if not self._parse_form():
            raise RuntimeError('No <form> element found. Please, check url address')

        # if wrong email or password
        if 'pass' in self.form_parser.params:
            print('Wrong email or password')
            self.email = None
            self.pswd = None
            return False
        elif 'code' in self.form_parser.params and not self.two_factor_auth:
            self.two_factor_auth = True
        else:
            return True


    def _two_fact_auth(self):
        print('2fact CALLED: ' + self.form_parser.url)
        prefix = 'https://m.vk.com'

        if prefix not in self.form_parser.url:
            self.form_parser.url = prefix + self.form_parser.url

        if self.security_code == None:
            self.security_code = input('Enter security code for two-factor authentication: ')
            type(self.security_code)
            self.security_code = str(self.security_code)
            print('got ' + self.security_code + " ss")

        self._submit_form({'code': self.security_code})

        if not self._parse_form():
            raise RuntimeError('No <form> element found. Please, check url address')

    def _allow_access(self):

        parser = self.form_parser

        if 'submit_allow_access' in parser.params and 'grant_access' in parser.url:
            if not self.auto_access:
                answer = ''
                msg =   'Application needs access to the following details in your profile:\n' + \
                        str(self.permissions) + '\n' + \
                        'Allow it to use them? (yes or no)'

                attempts = 5
                while answer not in ['yes', 'no'] and attempts > 0:
                    answer = input(msg).lower().strip()
                    attempts-=1

                if answer == 'no' or attempts == 0:
                    self.form_parser.url = self.form_parser.denial_url
                    print('Access denied')

            self._submit_form({})

        self._submit_form({})

    def captcha(self):
        pass

    def _get_params(self):
        '''
        Код работает, если нет капчи у юзера
        :return: void
        '''
        try:
            #TODO: реализовать гарантированный log/pass-cc-cap-aa-token!
            init_str = self.response.url.split('#')

            if len(init_str)==1:
                try:
                    parser = ImageParser()
                    # парсинг HTMLя (void)
                    parser.feed(str(self.response.content)[2:])  # void
                    cap_text = input('введите капчу, которая сохранилась у вас в папке: ')
                    self._submit_form({'captcha_key': cap_text})


                except BaseException as be:
                    print('U mispelled 2auth code:' + str(be))



            params = self.response.url.split('#')[1].split('&')
            self._access_token = params[0].split('=')[1]
            self._user_id = params[2].split('=')[1]
        except IndexError as err:
            print('\n here are probably captcha, whis is indeed to be solved: ' + self.response.url)

        finally:
            self._allow_access()
            self._get_response()

    def _get_response(self):
        print('final call')
        params = self.response.url.split('#')[1].split('&')
        self._access_token = params[0].split('=')[1]
        self._user_id = params[2].split('=')[1]



    def _close(self):
        self.session.close()
        self.response = None
        self.form_parser = None
        self.security_code = None
        self.email = None
        self.pswd = None


class ImageParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == 'img':
            print("attrs"+str(attrs))
            # Check the list of defined attributes.
            for name, value in attrs:
                if name == "src":
                    # print value
                    if "/captcha" in value:
                        print(value)
                        f = open('cap.jpeg', 'w')
                        img_url = 'https://m.vk.com'+value
                        self.save_image(img_url)
                        f.close()

    def save_image(self, url):
        pic_url = url
        with open('pic1.jpg', 'wb') as handle:
            response = requests.get(pic_url, stream=True)
            if not response.ok:
                print(response)
            for block in response.iter_content(1024):
                if not block:
                    break
                handle.write(block)

